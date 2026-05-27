"""Rule-based triggered-switching candidate detection.

The detector implements local string matching for Clyne-style trigger
candidates (Clyne, 1967, 2003). It does not infer speaker intention and does
not claim causality; it only proposes contexts for researcher review.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import re
import sqlite3
from pathlib import Path

import yaml

from .annotation import Token


VALID_SOURCES = {"manual", "suggested-accepted", "suggested-overridden", "imported"}


@dataclass(slots=True)
class TriggerEntry:
    """One trigger dictionary entry."""

    form: str
    trigger_type: str
    verified: bool
    note: str


@dataclass(slots=True)
class TriggerDictionary:
    """Typed trigger dictionary for one language."""

    language_code: str
    language_name: str
    version: str
    source: str
    entries: list[TriggerEntry]


@dataclass(slots=True)
class TriggerCandidate:
    """Advisory trigger relation candidate."""

    head_token_id: str
    triggered_token_id: str
    trigger_type: str
    confidence: float
    note: str


@dataclass(slots=True)
class TriggerLink:
    """Reviewed trigger relation persisted to SQLite."""

    head_token_id: str
    triggered_token_id: str
    trigger_type: str
    confidence: float
    source: str
    note: str | None = None
    created_at: str | None = None


def load_trigger_dictionary(path: Path) -> TriggerDictionary:
    """Load a local Clyne-style trigger dictionary from YAML."""

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    for field in ["language_code", "language_name", "version", "source"]:
        if not data.get(field):
            raise ValueError(f"{path} is missing required field {field}")
    entries: list[TriggerEntry] = []
    for group in data.get("trigger_candidates", {}).values():
        for item in group or []:
            entries.append(
                TriggerEntry(
                    form=str(item.get("form", "")),
                    trigger_type=str(item.get("trigger_type", "")),
                    verified=bool(item.get("verified", False)),
                    note=str(item.get("note", "")),
                )
            )
    return TriggerDictionary(
        language_code=str(data["language_code"]),
        language_name=str(data["language_name"]),
        version=str(data["version"]),
        source=str(data["source"]),
        entries=entries,
    )


def find_trigger_candidates(
    utterance_tokens: list[Token],
    dictionaries: dict[str, TriggerDictionary],
    window: int = 4,
) -> list[TriggerCandidate]:
    """Find advisory trigger candidates in one utterance.

    The procedure scans for local dictionary matches and proposes nearby tokens
    as possible triggered material. This operationalizes Clyne's triggering
    lens (Clyne, 1967, 2003) as a candidate flagger only; researcher review is
    required before persistence.
    """

    candidates: list[TriggerCandidate] = []
    for index, token in enumerate(utterance_tokens):
        dictionary = dictionaries.get(str(token.language or ""))
        if dictionary is None:
            continue
        entry = _match_entry(token, dictionary)
        if entry is None:
            continue
        for neighbor in utterance_tokens[index + 1 : index + 1 + window]:
            if neighbor.id == token.id:
                continue
            if token.language and neighbor.language and token.language == neighbor.language:
                continue
            distance = max(1, neighbor.position - token.position)
            confidence = _confidence(entry, distance)
            candidates.append(
                TriggerCandidate(
                    head_token_id=token.id,
                    triggered_token_id=neighbor.id,
                    trigger_type=entry.trigger_type,
                    confidence=confidence,
                    note=(
                        f"'{entry.form}' matched a {entry.trigger_type} trigger candidate; "
                        "this is context evidence only."
                    ),
                )
            )
    return candidates


def persist_trigger_link(conn: sqlite3.Connection, link: TriggerLink) -> None:
    """Persist a reviewed trigger link to SQLite."""

    if link.source not in VALID_SOURCES:
        raise ValueError(f"invalid trigger link source: {link.source}")
    if not 0.0 <= link.confidence <= 1.0:
        raise ValueError("trigger link confidence must be in [0,1]")
    created_at = link.created_at or datetime.now(UTC).isoformat()
    conn.execute(
        """
        INSERT OR REPLACE INTO trigger_links (
            head_token_id, triggered_token_id, trigger_type, confidence,
            source, note, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            link.head_token_id,
            link.triggered_token_id,
            link.trigger_type,
            link.confidence,
            link.source,
            link.note,
            created_at,
        ),
    )
    conn.execute("UPDATE tokens SET trigger_role = 'trigger' WHERE id = ?", (link.head_token_id,))
    conn.execute("UPDATE tokens SET trigger_role = 'triggered' WHERE id = ?", (link.triggered_token_id,))


def _match_entry(token: Token, dictionary: TriggerDictionary) -> TriggerEntry | None:
    text = _clean(token.text_for_matching)
    for entry in dictionary.entries:
        if text == _clean(entry.form):
            return entry
    return None


def _confidence(entry: TriggerEntry, distance: int) -> float:
    base_by_type = {
        "proper_noun": 0.62,
        "borrowing": 0.58,
        "cognate": 0.54,
        "discourse_marker": 0.5,
    }
    base = base_by_type.get(entry.trigger_type, 0.45)
    if entry.verified:
        base += 0.08
    return round(max(0.05, min(1.0, base - (distance - 1) * 0.06)), 4)


def _clean(value: str) -> str:
    return re.sub(r"(^[^\w-]+|[^\w-]+$)", "", value.casefold())
