"""Triggered-switching detection with local dictionaries only.

The detector implements Clyne's triggering lens as a transparent candidate
flagger (Clyne, 1967, 2003). It never infers speaker intention, never explains
a switch by itself, and never writes to SQLite unless the researcher explicitly
accepts a candidate.
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
TYPOLOGY_WEIGHT = {
    "proper_noun": 0.75,
    "borrowing": 0.68,
    "cognate": 0.6,
    "discourse_marker": 0.52,
}
_TRIGGER_DICTIONARIES: dict[str, "TriggerDictionary"] = {}


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
    """Advisory trigger candidate around a switch point."""

    head_token_id: str
    triggered_token_id: str
    trigger_type: str
    confidence: float
    distance: int
    matched_form: str
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


def load_trigger_dictionary(path: Path, register: bool = True) -> TriggerDictionary:
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
    dictionary = TriggerDictionary(
        language_code=str(data["language_code"]),
        language_name=str(data["language_name"]),
        version=str(data["version"]),
        source=str(data["source"]),
        entries=entries,
    )
    if register:
        _TRIGGER_DICTIONARIES[dictionary.language_code] = dictionary
    return dictionary


def load_trigger_dictionaries(directory: Path) -> dict[str, TriggerDictionary]:
    """Load and register all trigger YAML files in a local directory."""

    dictionaries: dict[str, TriggerDictionary] = {}
    for path in sorted(directory.glob("*.yaml")):
        dictionary = load_trigger_dictionary(path, register=True)
        dictionaries[dictionary.language_code] = dictionary
    return dictionaries


def find_trigger_candidates(
    utterance_tokens: list[Token],
    switch_index: int,
    window_left: int = 2,
    window_right: int = 0,
) -> list[TriggerCandidate]:
    """Scan a switch-point context for Clyne-style trigger candidates.

    Given a switch point in an utterance, scan the preceding window for tokens
    that match the local trigger dictionary: proper nouns, borrowings, cognates,
    or discourse markers. Return candidates ranked by Clyne's typology with a
    transparent confidence score (Clyne, 1967, 2003).

    Returns candidates; never auto-applies them.
    """

    if not 0 <= switch_index < len(utterance_tokens):
        raise IndexError("switch_index is outside utterance_tokens")
    if not _TRIGGER_DICTIONARIES:
        _load_default_trigger_dictionaries()

    triggered_tokens = utterance_tokens[switch_index : switch_index + window_right + 1]
    left = max(0, switch_index - window_left)
    candidates: list[TriggerCandidate] = []
    for head_index in range(left, switch_index):
        head = utterance_tokens[head_index]
        entry = _match_entry(head)
        if entry is None:
            continue
        for triggered in triggered_tokens:
            if triggered.id == head.id:
                continue
            distance = abs(switch_index - head_index)
            candidates.append(
                TriggerCandidate(
                    head_token_id=head.id,
                    triggered_token_id=triggered.id,
                    trigger_type=entry.trigger_type,
                    confidence=_confidence(entry, distance),
                    distance=distance,
                    matched_form=entry.form,
                    note=(
                        f"Matched '{entry.form}' as a {entry.trigger_type}; "
                        "candidate trigger context only, not causal proof."
                    ),
                )
            )
    return sorted(candidates, key=lambda item: (-item.confidence, item.distance, item.head_token_id))


def persist_trigger_link(conn: sqlite3.Connection, link: TriggerLink) -> None:
    """Persist an explicitly accepted trigger candidate to `trigger_links`."""

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


def _match_entry(token: Token) -> TriggerEntry | None:
    text = _clean(token.text_for_matching)
    dictionary = _TRIGGER_DICTIONARIES.get(str(token.language or ""))
    dictionaries = [dictionary] if dictionary else list(_TRIGGER_DICTIONARIES.values())
    for trigger_dictionary in dictionaries:
        if trigger_dictionary is None:
            continue
        for entry in trigger_dictionary.entries:
            if text == _clean(entry.form):
                return entry
    return None


def _confidence(entry: TriggerEntry, distance: int) -> float:
    base = TYPOLOGY_WEIGHT.get(entry.trigger_type, 0.45)
    if entry.verified:
        base += 0.08
    distance_penalty = max(0, distance - 1) * 0.08
    return round(max(0.05, min(1.0, base - distance_penalty)), 4)


def _load_default_trigger_dictionaries() -> None:
    root = Path.cwd() / "dictionaries" / "triggers"
    if root.exists():
        load_trigger_dictionaries(root)


def _clean(value: str) -> str:
    return re.sub(r"(^[^\w-]+|[^\w-]+$)", "", value.casefold())
