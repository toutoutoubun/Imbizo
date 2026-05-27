"""Mixed-code variety profile loading and lexical-density detection.

Tsotsitaal, Iscamtho, Kaaps, and Sabela can challenge a clean Matrix
Language/Embedded Language split. The detector below only reports lexical
evidence from non-prescriptive profile dictionaries; it does not identify a
speaker, text, or community practice as Tsotsitaal, Iscamtho, Kaaps, or Sabela
(Slabbert & Myers-Scotton, 1997; Hurst, 2008; McCormick, 2002).
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
    """One signature-vocabulary prompt from a mixed-code profile."""

    form: str
    gloss_eng: str
    source_languages: list[str]
    verified: bool
    note: str


@dataclass(slots=True)
class MixedCodeDictionary:
    """Typed mixed-code variety profile dictionary."""

    variety_code: str
    variety_name: str
    version: str
    source: str
    social_context: str
    caveats: str
    lexicon: list[MixedCodeLexeme]
    morphosyntactic_features: list[dict[str, object]]


MixedCodeProfile = MixedCodeDictionary


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
class MixedCodeSpanCandidate:
    """Advisory mixed-code span candidate with evidence trail."""

    variety: str
    start_token_id: str
    end_token_id: str
    start_index: int
    end_index: int
    confidence: float
    lexical_density: float
    evidence_forms: list[str]
    warning: str


def load_mixed_code_dictionary(path: Path) -> MixedCodeDictionary:
    """Load a non-prescriptive local mixed-code variety YAML dictionary."""

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
    return MixedCodeDictionary(
        variety_code=str(data["variety_code"]),
        variety_name=str(data["variety_name"]),
        version=str(data["version"]),
        source=str(data["source"]),
        social_context=str(data.get("social_context", "")),
        caveats=str(data["caveats"]),
        lexicon=lexicon,
        morphosyntactic_features=list(data.get("morphosyntactic_features", [])),
    )


def load_mixed_code_profile(path: Path) -> MixedCodeDictionary:
    """Backward-compatible alias for loading a mixed-code dictionary."""

    return load_mixed_code_dictionary(path)


def detect_mixed_code_spans(
    utterance_tokens: list[Token],
    variety: str,
    dictionary: MixedCodeDictionary,
    threshold: float = 0.4,
) -> list[MixedCodeSpanCandidate]:
    """Detect candidate spans by variety-signature lexical density.

    Detect contiguous spans whose lexical density of variety-signature
    vocabulary exceeds a threshold. Return candidates with confidence and an
    evidence trail. Advisory only.

    Justified by Slabbert & Myers-Scotton (1997), Hurst (2008), and McCormick
    (2002). Detecting Tsotsitaal-flavor lexis is NOT the same as identifying a
    Tsotsitaal speaker or text. The researcher must consider the speaker,
    setting, history, and broader sociolinguistic context.
    """

    if variety != dictionary.variety_code:
        raise ValueError(f"Requested variety {variety!r} does not match dictionary {dictionary.variety_code!r}")
    if variety not in VALID_VARIETIES:
        raise ValueError(f"unsupported mixed-code variety: {variety}")
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("threshold must be in [0,1]")

    lexicon = {_clean(entry.form): entry for entry in dictionary.lexicon}
    candidates: list[MixedCodeSpanCandidate] = []
    n_tokens = len(utterance_tokens)
    for start in range(n_tokens):
        for end in range(start, n_tokens):
            window = utterance_tokens[start : end + 1]
            evidence = [token.text_for_matching for token in window if _clean(token.text_for_matching) in lexicon]
            density = len(evidence) / len(window)
            if density < threshold or len(set(_clean(form) for form in evidence)) < 2:
                continue
            confidence = _candidate_confidence(evidence, window, lexicon)
            candidates.append(
                MixedCodeSpanCandidate(
                    variety=variety,
                    start_token_id=window[0].id,
                    end_token_id=window[-1].id,
                    start_index=start,
                    end_index=end,
                    confidence=confidence,
                    lexical_density=round(density, 4),
                    evidence_forms=evidence,
                    warning=(
                        "Lexical evidence only. This does not identify a speaker, "
                        "community, or whole text as the variety."
                    ),
                )
            )
    return _maximal_non_overlapping(candidates)


def persist_mixed_code_span(conn: sqlite3.Connection, span: MixedCodeSpan) -> None:
    """Persist a reviewed mixed-code span and mark boundary token rows."""

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


def suggest_mixed_code_span(tokens: list[Token], profile: MixedCodeDictionary) -> MixedCodeSpanCandidate | None:
    """Backward-compatible helper returning the best candidate, if any."""

    candidates = detect_mixed_code_spans(tokens, profile.variety_code, profile)
    return candidates[0] if candidates else None


def _candidate_confidence(
    evidence_forms: list[str],
    window: list[Token],
    lexicon: dict[str, MixedCodeLexeme],
) -> float:
    density = len(evidence_forms) / len(window)
    verified_bonus = 0.05 * sum(1 for form in evidence_forms if lexicon[_clean(form)].verified)
    length_penalty = max(0, len(window) - len(evidence_forms)) * 0.02
    return round(max(0.0, min(0.95, density * 0.75 + verified_bonus - length_penalty)), 4)


def _maximal_non_overlapping(candidates: list[MixedCodeSpanCandidate]) -> list[MixedCodeSpanCandidate]:
    ordered = sorted(candidates, key=lambda item: (-item.confidence, item.start_index, -(item.end_index - item.start_index)))
    chosen: list[MixedCodeSpanCandidate] = []
    occupied: set[int] = set()
    for candidate in ordered:
        span_indexes = set(range(candidate.start_index, candidate.end_index + 1))
        if occupied.intersection(span_indexes):
            continue
        chosen.append(candidate)
        occupied.update(span_indexes)
    return sorted(chosen, key=lambda item: item.start_index)


def _clean(value: str) -> str:
    return re.sub(r"(^[^\w-]+|[^\w-]+$)", "", value.casefold())
