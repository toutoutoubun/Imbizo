"""Mixed-code variety profile loading and span annotation.

Tsotsitaal, Iscamtho, Kaaps, and Sabela can challenge a clean Matrix
Language/Embedded Language split. This module therefore treats variety profiles
as non-prescriptive historical snapshots, not definitions of living speech
communities (Slabbert & Myers-Scotton, 1997; Hurst, 2008; McCormick, 2002).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import re
import sqlite3
from pathlib import Path

import yaml

from .annotation import Token


VALID_VARIETIES = {"tsotsitaal", "iscamtho", "kaaps", "sabela"}
VALID_SOURCES = {"manual", "suggested-accepted", "suggested-overridden", "imported"}


@dataclass(slots=True)
class MixedCodeLexeme:
    """One lexicon prompt from a mixed-code profile."""

    form: str
    gloss_eng: str
    source_languages: list[str]
    verified: bool
    note: str


@dataclass(slots=True)
class MixedCodeProfile:
    """Typed mixed-code variety profile."""

    variety_code: str
    variety_name: str
    version: str
    source: str
    social_context: str
    caveats: str
    lexicon: list[MixedCodeLexeme]
    morphosyntactic_features: list[dict[str, object]]


@dataclass(slots=True)
class MixedCodeSpan:
    """Reviewed mixed-code span record."""

    id: str
    project_id: str
    start_token_id: str
    end_token_id: str
    variety: str
    confidence: float | None
    source: str
    note: str | None = None
    created_at: str | None = None


@dataclass(slots=True)
class MixedCodeSuggestion:
    """Advisory mixed-code span suggestion."""

    variety: str
    start_token_id: str
    end_token_id: str
    confidence: float
    matched_forms: list[str]
    narrative: str


def load_mixed_code_profile(path: Path) -> MixedCodeProfile:
    """Load a local mixed-code variety profile from YAML."""

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    for field in ["variety_code", "variety_name", "version", "source", "caveats"]:
        if not data.get(field):
            raise ValueError(f"{path} is missing required field {field}")
    lexicon = [
        MixedCodeLexeme(
            form=str(item.get("form", "")),
            gloss_eng=str(item.get("gloss_eng", "")),
            source_languages=[str(value) for value in item.get("source_languages", [])],
            verified=bool(item.get("verified", False)),
            note=str(item.get("note", "")),
        )
        for item in data.get("lexicon", [])
    ]
    return MixedCodeProfile(
        variety_code=str(data["variety_code"]),
        variety_name=str(data["variety_name"]),
        version=str(data["version"]),
        source=str(data["source"]),
        social_context=str(data.get("social_context", "")),
        caveats=str(data["caveats"]),
        lexicon=lexicon,
        morphosyntactic_features=list(data.get("morphosyntactic_features", [])),
    )


def suggest_mixed_code_span(tokens: list[Token], profile: MixedCodeProfile) -> MixedCodeSuggestion | None:
    """Return an advisory span suggestion if profile lexicon evidence appears.

    The suggestion is intentionally weak and memo-oriented. It supports
    theoretical pluralism by surfacing possible mixed-code spans without
    forcing them into MLF categories.
    """

    lexicon = {_clean(entry.form): entry for entry in profile.lexicon}
    matched: list[str] = []
    matched_tokens: list[Token] = []
    for token in tokens:
        cleaned = _clean(token.text_for_matching)
        if cleaned in lexicon:
            matched.append(lexicon[cleaned].form)
            matched_tokens.append(token)
    if not matched_tokens:
        return None
    unverified_penalty = 0.08 * sum(1 for form in matched if not lexicon[_clean(form)].verified)
    confidence = max(0.15, min(0.75, 0.25 + len(set(matched)) * 0.12 - unverified_penalty))
    return MixedCodeSuggestion(
        variety=profile.variety_code,
        start_token_id=matched_tokens[0].id,
        end_token_id=matched_tokens[-1].id,
        confidence=round(confidence, 4),
        matched_forms=matched,
        narrative=(
            f"Matched {len(matched)} {profile.variety_name} profile forms. "
            "Treat this as a review prompt, not a variety definition."
        ),
    )


def persist_mixed_code_span(conn: sqlite3.Connection, span: MixedCodeSpan) -> None:
    """Persist a reviewed mixed-code span and mark token rows with the variety."""

    if span.variety not in VALID_VARIETIES:
        raise ValueError(f"unsupported mixed-code variety: {span.variety}")
    if span.source not in VALID_SOURCES:
        raise ValueError(f"invalid mixed-code source: {span.source}")
    if span.confidence is not None and not 0.0 <= span.confidence <= 1.0:
        raise ValueError("mixed-code confidence must be in [0,1] or None")
    created_at = span.created_at or datetime.now(UTC).isoformat()
    conn.execute(
        """
        INSERT OR REPLACE INTO mixed_code_spans (
            id, project_id, start_token_id, end_token_id, variety,
            confidence, source, note, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            span.id,
            span.project_id,
            span.start_token_id,
            span.end_token_id,
            span.variety,
            span.confidence,
            span.source,
            span.note,
            created_at,
        ),
    )
    conn.execute(
        "UPDATE tokens SET mixed_code_variety = ? WHERE id IN (?, ?)",
        (span.variety, span.start_token_id, span.end_token_id),
    )


def _clean(value: str) -> str:
    return re.sub(r"(^[^\w-]+|[^\w-]+$)", "", value.casefold())
