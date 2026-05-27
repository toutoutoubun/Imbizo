"""Noun-class dictionary loading, suggestion, and SQLite persistence.

The suggester uses conservative surface-prefix matching over local YAML
dictionaries. It is inspired by noun-class descriptions for isiZulu and
isiXhosa (Poulos & Msimang, 1998; Du Plessis & Visser, 1992), but it never
decides analysis for the researcher. All suggestions are advisory and should
be reviewed in context, especially for code-switched varieties.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from imbizo.app.time import utc_now


ReviewSource = str
VALID_REVIEW_SOURCES = {"manual", "suggested-accepted", "suggested-overridden"}


@dataclass(slots=True)
class NounClassEntry:
    """One noun-class entry from a local dictionary."""

    class_label: str
    class_number: int | None
    prefixes: list[str]
    semantic_domain: str
    verified: bool
    note: str = ""
    frequency: int = 0


@dataclass(slots=True)
class NounClassDictionary:
    """Parsed noun-class dictionary with provenance metadata."""

    language_code: str
    language_name: str
    version: str
    source: str
    last_reviewed_by: str
    last_reviewed_on: str
    entries: list[NounClassEntry] = field(default_factory=list)
    path: Path | None = None


@dataclass(slots=True)
class ClassSuggestion:
    """Ranked noun-class suggestion for one token."""

    language_code: str
    class_label: str
    class_number: int | None
    prefix: str
    semantic_domain: str
    verified: bool
    note: str
    match_length: int
    frequency: int
    rank: int
    source: str


def load_noun_class_dictionary(path: Path) -> NounClassDictionary:
    """Load one noun-class YAML dictionary from disk.

    The YAML must include the v1.0 dictionary metadata and a `classes` list.
    Unverified entries are allowed and preserved so the UI can display their
    caution notes instead of hiding uncertainty.
    """

    data = _load_yaml_mapping(path)
    entries: list[NounClassEntry] = []
    for raw_entry in _as_list(data.get("classes"), "classes"):
        class_label = str(raw_entry.get("class_number", "")).strip()
        entries.append(
            NounClassEntry(
                class_label=class_label,
                class_number=_class_label_to_int(class_label),
                prefixes=[str(prefix) for prefix in _as_list(raw_entry.get("prefixes"), "prefixes")],
                semantic_domain=str(raw_entry.get("semantic_domain", "")),
                verified=bool(raw_entry.get("verified", False)),
                note=str(raw_entry.get("note", "")),
                frequency=int(raw_entry.get("frequency", 0) or 0),
            )
        )
    return NounClassDictionary(
        language_code=str(data["language_code"]),
        language_name=str(data["language_name"]),
        version=str(data["version"]),
        source=str(data["source"]),
        last_reviewed_by=str(data["last_reviewed_by"]),
        last_reviewed_on=str(data["last_reviewed_on"]),
        entries=entries,
        path=path,
    )


def load_default_noun_class_dictionary(language_code: str, project_path: Path | None = None) -> NounClassDictionary:
    """Load a project override or shipped noun-class dictionary for a language."""

    for root in _dictionary_roots(project_path):
        candidate = root / "noun_classes" / f"{language_code}.yaml"
        if candidate.exists():
            return load_noun_class_dictionary(candidate)
    raise FileNotFoundError(f"No noun-class dictionary found for language code: {language_code}")


def suggest_class(token_surface: str, prefix_guess: str, language_code: str) -> list[ClassSuggestion]:
    """Return ranked noun-class suggestions for a manually split token.

    Implements a small, local prefix-matching procedure based on the kind of
    noun-class prefix evidence described in Poulos & Msimang (1998) and
    Du Plessis & Visser (1992) for isiZulu and isiXhosa. Suggestions are ranked
    by exact-match length, then by optional dictionary frequency. The researcher
    is the final arbiter; results are advisory only.
    """

    dictionary = load_default_noun_class_dictionary(language_code)
    surface = token_surface.strip().lower()
    guess = prefix_guess.strip().lower()
    suggestions: list[ClassSuggestion] = []
    for entry in dictionary.entries:
        for raw_prefix in entry.prefixes:
            for prefix in _expand_prefix(raw_prefix):
                normalized_prefix = prefix.lower()
                if not normalized_prefix or normalized_prefix == "ø":
                    continue
                matched = guess == normalized_prefix or surface.startswith(normalized_prefix)
                if not matched:
                    continue
                suggestions.append(
                    ClassSuggestion(
                        language_code=dictionary.language_code,
                        class_label=entry.class_label,
                        class_number=entry.class_number,
                        prefix=prefix,
                        semantic_domain=entry.semantic_domain,
                        verified=entry.verified,
                        note=entry.note,
                        match_length=len(normalized_prefix),
                        frequency=entry.frequency,
                        rank=0,
                        source=dictionary.source,
                    )
                )
    suggestions.sort(key=lambda item: (-item.match_length, -item.frequency, str(item.class_label)))
    for index, suggestion in enumerate(suggestions, start=1):
        suggestion.rank = index
    return suggestions


def save_token_noun_class(
    connection: sqlite3.Connection,
    token_id: str,
    nc_class: int | None,
    nc_prefix: str | None,
    nc_source: ReviewSource,
) -> None:
    """Persist a reviewed noun-class value on a token.

    `nc_source` must be one of `manual`, `suggested-accepted`, or
    `suggested-overridden`. The target columns are nullable so MVP tokens remain
    valid when A1 is disabled.
    """

    _validate_review_source(nc_source)
    if nc_class is not None and not 1 <= nc_class <= 23:
        raise ValueError("nc_class must be between 1 and 23, or None.")
    _require_token_columns(connection)
    cursor = connection.execute(
        """
        UPDATE tokens
        SET nc_class = ?, nc_prefix = ?, nc_source = ?
        WHERE id = ?
        """,
        (nc_class, nc_prefix, nc_source, token_id),
    )
    if cursor.rowcount == 0:
        raise ValueError(f"Token not found: {token_id}")
    connection.commit()


def snapshot_dictionary(
    connection: sqlite3.Connection,
    dictionary: NounClassDictionary,
    *,
    is_project_override: bool = False,
    note: str = "",
) -> str:
    """Store a per-project snapshot of a noun-class dictionary.

    Snapshots make later noun-class suggestions reproducible from the project
    database, even if the shipped YAML changes in a future release.
    """

    path = dictionary.path
    raw_bytes = path.read_bytes() if path else json.dumps(_dictionary_to_json(dictionary), sort_keys=True).encode("utf-8")
    snapshot_id = str(uuid.uuid4())
    verified_count = sum(1 for entry in dictionary.entries if entry.verified)
    unverified_count = len(dictionary.entries) - verified_count
    connection.execute(
        """
        INSERT INTO noun_class_dictionaries (
            id, language_code, dictionary_version, schema_version, source_label,
            source_path, content_sha256, snapshot_json, verified_entry_count,
            unverified_entry_count, is_project_override, note, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            snapshot_id,
            dictionary.language_code,
            dictionary.version,
            "1.0.0",
            dictionary.source,
            str(path) if path else None,
            hashlib.sha256(raw_bytes).hexdigest(),
            json.dumps(_dictionary_to_json(dictionary), ensure_ascii=False),
            verified_count,
            unverified_count,
            int(is_project_override),
            note,
            utc_now(),
        ),
    )
    connection.commit()
    return snapshot_id


def _load_yaml_mapping(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"YAML file must contain a mapping: {path}")
    for key in ("language_code", "language_name", "version", "source", "last_reviewed_by", "last_reviewed_on"):
        if key not in data:
            raise ValueError(f"Missing required key `{key}` in {path}")
    return data


def _as_list(value: object, name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"`{name}` must be a list.")
    return value


def _class_label_to_int(label: str) -> int | None:
    digits = "".join(char for char in label if char.isdigit())
    return int(digits) if digits else None


def _expand_prefix(prefix: str) -> list[str]:
    cleaned = prefix.strip()
    variants = {cleaned}
    variants.add(cleaned.replace("(", "").replace(")", ""))
    variants.add(cleaned.replace("N", "n"))
    variants.add(cleaned.replace("N", "m"))
    variants.add(cleaned.replace("iN", "in"))
    variants.add(cleaned.replace("iN", "im"))
    return sorted(variant for variant in variants if variant)


def _dictionary_roots(project_path: Path | None) -> list[Path]:
    roots: list[Path] = []
    if project_path is not None:
        roots.append(project_path.expanduser().resolve() / "dictionaries")
    roots.append(Path(__file__).resolve().parents[3] / "dictionaries")
    return roots


def _validate_review_source(source: str) -> None:
    if source not in VALID_REVIEW_SOURCES:
        raise ValueError("source must be manual, suggested-accepted, or suggested-overridden.")


def _require_token_columns(connection: sqlite3.Connection) -> None:
    existing = {row[1] for row in connection.execute("PRAGMA table_info(tokens)").fetchall()}
    missing = {"nc_class", "nc_prefix", "nc_source"} - existing
    if missing:
        raise RuntimeError(f"v1.0 noun-class migration has not been applied; missing columns: {sorted(missing)}")


def _dictionary_to_json(dictionary: NounClassDictionary) -> dict[str, object]:
    return {
        "language_code": dictionary.language_code,
        "language_name": dictionary.language_name,
        "version": dictionary.version,
        "source": dictionary.source,
        "last_reviewed_by": dictionary.last_reviewed_by,
        "last_reviewed_on": dictionary.last_reviewed_on,
        "classes": [
            {
                "class_number": entry.class_label,
                "prefixes": entry.prefixes,
                "semantic_domain": entry.semantic_domain,
                "verified": entry.verified,
                "note": entry.note,
                "frequency": entry.frequency,
            }
            for entry in dictionary.entries
        ],
    }
