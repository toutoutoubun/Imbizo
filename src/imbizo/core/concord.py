"""Concord dictionary loading, suggestion, and SQLite persistence.

The concord tracker provides local, reviewable agreement candidates for Bantu
noun-class analysis. It is designed as descriptive support only: confirmed
links can help a researcher reason about integration and agreement, but they
do not prove a Matrix Language analysis by themselves (Poulos & Msimang, 1998;
Demuth, 2000; Myers-Scotton, 1993).
"""

from __future__ import annotations

import sqlite3
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import yaml

from imbizo.app.time import utc_now
from imbizo.domain.transcripts import Token


ConcordType = Literal["SC", "OC", "AC", "PC", "RC", "DEM"]
AgreementStatus = Literal["confirmed", "mismatch", "uncertain", "not_applicable"]
ReviewSource = Literal["manual", "suggested-accepted", "suggested-overridden"]

VALID_CONCORD_TYPES = {"SC", "OC", "AC", "PC", "RC", "DEM"}
VALID_AGREEMENT_STATUS = {"confirmed", "mismatch", "uncertain", "not_applicable"}
VALID_REVIEW_SOURCES = {"manual", "suggested-accepted", "suggested-overridden"}


@dataclass(slots=True)
class ConcordMarker:
    """Forms and review status for one concord marker type."""

    forms: list[str]
    verified: bool
    note: str = ""


@dataclass(slots=True)
class ConcordEntry:
    """Concord markers associated with one noun class."""

    class_label: str
    class_number: int | None
    subject_concord: ConcordMarker
    object_concord: ConcordMarker
    adjective_concord: ConcordMarker
    possessive_concord: ConcordMarker
    relative_concord: ConcordMarker
    demonstrative: ConcordMarker


@dataclass(slots=True)
class ConcordDictionary:
    """Parsed concord dictionary with provenance metadata."""

    language_code: str
    language_name: str
    version: str
    source: str
    last_reviewed_by: str
    last_reviewed_on: str
    entries: list[ConcordEntry] = field(default_factory=list)
    path: Path | None = None


@dataclass(slots=True)
class TokenForConcord:
    """Minimal token view used by the concord suggester."""

    id: str
    segment_id: str
    token_text: str
    sort_order: int
    nc_class: int | None = None


@dataclass(slots=True)
class ConcordLink:
    """Persistable concord relation between a controller and a concord token."""

    id: str
    segment_id: str
    controller_token_id: str
    concord_token_id: str
    concord_type: ConcordType
    observed_form: str
    agreement_status: AgreementStatus
    source: ReviewSource
    controller_nc_class: int | None = None
    expected_form: str | None = None
    confidence: float | None = None
    dictionary_snapshot_id: str | None = None
    note: str | None = None
    created_at: str = ""
    updated_at: str = ""


@dataclass(slots=True)
class ConcordCandidate:
    """Unpersisted concord candidate from pure dictionary string matching."""

    token_id: str
    token_index: int
    token_surface: str
    concord_type: ConcordType
    matched_marker: str
    confidence: float
    distance_from_head: int
    verified: bool
    note: str


@dataclass(frozen=True, slots=True)
class IntegrationWeights:
    """Transparent weights for borrowed-stem integration scoring.

    Defaults are the v1.0 specification weights: 0.35 concord evidence,
    0.35 noun-class evidence, 0.20 project frequency, and 0.10 researcher
    review evidence. The sum must be 1.0 so scores remain interpretable in
    [0, 1] (Poplack, 1980; Muysken, 2000).
    """

    concord: float = 0.35
    noun_class: float = 0.35
    frequency: float = 0.20
    researcher_review: float = 0.10

    def __post_init__(self) -> None:
        """Reject negative weights or totals that do not sum to 1.0."""

        values = (self.concord, self.noun_class, self.frequency, self.researcher_review)
        if any(value < 0 for value in values):
            raise ValueError("Integration weights must be non-negative.")
        if abs(sum(values) - 1.0) > 1e-9:
            raise ValueError("Integration weights must sum to 1.0.")


DEFAULT_WEIGHTS = IntegrationWeights()


def load_concord_dictionary(path: Path) -> ConcordDictionary:
    """Load a local concord YAML dictionary.

    Concord fields are preserved even when marked `verified: false`, because
    uncertainty is part of the research record rather than an error to hide.
    """

    data = _load_yaml_mapping(path)
    entries: list[ConcordEntry] = []
    for raw_entry in _as_list(data.get("concords"), "concords"):
        class_label = str(raw_entry.get("class_number", "")).strip()
        entries.append(
            ConcordEntry(
                class_label=class_label,
                class_number=_class_label_to_int(class_label),
                subject_concord=_marker(raw_entry.get("subject_concord")),
                object_concord=_marker(raw_entry.get("object_concord")),
                adjective_concord=_marker(raw_entry.get("adjective_concord")),
                possessive_concord=_marker(raw_entry.get("possessive_concord")),
                relative_concord=_marker(raw_entry.get("relative_concord")),
                demonstrative=_demonstrative_marker(raw_entry.get("demonstrative")),
            )
        )
    return ConcordDictionary(
        language_code=str(data["language_code"]),
        language_name=str(data["language_name"]),
        version=str(data["version"]),
        source=str(data["source"]),
        last_reviewed_by=str(data["last_reviewed_by"]),
        last_reviewed_on=str(data["last_reviewed_on"]),
        entries=entries,
        path=path,
    )


def load_default_concord_dictionary(language_code: str, project_path: Path | None = None) -> ConcordDictionary:
    """Load a project override or shipped concord dictionary for a language."""

    for root in _dictionary_roots(project_path):
        candidate = root / "concord" / f"{language_code}.yaml"
        if candidate.exists():
            return load_concord_dictionary(candidate)
    raise FileNotFoundError(f"No concord dictionary found for language code: {language_code}")


def find_concord_candidates(
    utterance_tokens: list[Token],
    head_token_index: int,
    head_class: int,
    language_code: str,
) -> list[ConcordCandidate]:
    """Scan an utterance for concord markers matching one noun class.

    This is pure string matching against the local concord dictionary. It does
    not use ML, statistics, remote services, or hidden linguistic assumptions.
    Confidence is based only on matched marker length and distance from the
    head token. The procedure offers review targets for integration and System
    Morpheme Principle analysis, but never overrides researcher annotation
    (Muysken, 2000; Myers-Scotton, 1993; Myers-Scotton, 2002).
    """

    if head_token_index < 0 or head_token_index >= len(utterance_tokens):
        raise IndexError("head_token_index is outside utterance_tokens.")
    dictionary = load_default_concord_dictionary(language_code)
    entry = next((item for item in dictionary.entries if item.class_number == head_class), None)
    if entry is None:
        return []
    markers = _markers_for_entry(entry)
    max_marker_length = max((len(form) for _, marker in markers for form in marker.forms if form), default=1)
    candidates: list[ConcordCandidate] = []
    for index, token in enumerate(utterance_tokens):
        if index == head_token_index:
            continue
        distance = abs(index - head_token_index)
        for concord_type, marker in markers:
            matched = _matching_form(token.token_text, marker.forms)
            if matched is None:
                continue
            length_component = len(matched) / max_marker_length
            position_component = 1.0 / (distance + 1)
            confidence = max(0.0, min(1.0, 0.75 * length_component + 0.25 * position_component))
            candidates.append(
                ConcordCandidate(
                    token_id=token.id,
                    token_index=index,
                    token_surface=token.token_text,
                    concord_type=concord_type,
                    matched_marker=matched,
                    confidence=confidence,
                    distance_from_head=distance,
                    verified=marker.verified,
                    note=marker.note or "Dictionary string match; researcher review required.",
                )
            )
    candidates.sort(key=lambda item: (-item.confidence, item.distance_from_head, item.token_index, item.concord_type))
    return candidates


def suggest_concord_links(tokens: list[TokenForConcord], language_code: str) -> list[ConcordLink]:
    """Return local concord candidates for reviewed noun-class tokens.

    The algorithm compares nearby token surfaces with dictionary concord forms.
    It is intentionally conservative and shallow so it can run on low-resource
    laptops. Candidates remain unpersisted until a researcher accepts or
    overrides them (Poulos & Msimang, 1998; Demuth, 2000).
    """

    dictionary = load_default_concord_dictionary(language_code)
    by_class = {entry.class_number: entry for entry in dictionary.entries if entry.class_number is not None}
    suggestions: list[ConcordLink] = []
    ordered = sorted(tokens, key=lambda item: (item.segment_id, item.sort_order))
    for index, controller in enumerate(ordered):
        if controller.nc_class is None or controller.nc_class not in by_class:
            continue
        entry = by_class[controller.nc_class]
        for candidate in ordered[index + 1 : index + 4]:
            if candidate.segment_id != controller.segment_id:
                break
            for concord_type, marker in _markers_for_entry(entry):
                form = _matching_form(candidate.token_text, marker.forms)
                if form is None:
                    continue
                suggestions.append(
                    ConcordLink(
                        id=str(uuid.uuid4()),
                        segment_id=controller.segment_id,
                        controller_token_id=controller.id,
                        concord_token_id=candidate.id,
                        concord_type=concord_type,
                        controller_nc_class=controller.nc_class,
                        expected_form=form,
                        observed_form=candidate.token_text,
                        agreement_status="uncertain",
                        source="suggested-accepted",
                        confidence=0.5 if marker.verified else 0.25,
                        note=marker.note or "Local concord suggestion; researcher review required.",
                    )
                )
    return suggestions


def integration_score(
    stem_token: Token,
    concord_links: list[ConcordLink],
    project_frequency: int,
    project_threshold: int,
    weights: IntegrationWeights = DEFAULT_WEIGHTS,
) -> float:
    """Compute a transparent weighted integration score in [0, 1].

    The default weights are 0.35/0.35/0.20/0.10 as specified in the v1.0
    increment. Components are confirmed concord ratio, noun-class evidence,
    project frequency, and researcher review evidence. Researchers may override
    weights per project for sensitivity analysis (Poplack, 1980; Muysken, 2000).
    """

    if project_frequency < 0:
        raise ValueError("project_frequency must be non-negative.")
    if project_threshold <= 0:
        raise ValueError("project_threshold must be positive.")
    reviewed = [link for link in concord_links if link.agreement_status in {"confirmed", "mismatch", "uncertain"}]
    confirmed = [link for link in reviewed if link.agreement_status == "confirmed"]
    concord_component = len(confirmed) / len(reviewed) if reviewed else 0.0
    token_nc = getattr(stem_token, "nc_class", None)
    link_nc_present = any(link.controller_nc_class is not None for link in concord_links)
    noun_class_component = 1.0 if (token_nc is not None or link_nc_present) else 0.0
    frequency_component = min(project_frequency / project_threshold, 1.0)
    review_component = 1.0 if any(link.source in {"manual", "suggested-accepted"} for link in concord_links) else 0.0
    score = (
        weights.concord * concord_component
        + weights.noun_class * noun_class_component
        + weights.frequency * frequency_component
        + weights.researcher_review * review_component
    )
    return max(0.0, min(1.0, score))


def save_concord_link(connection: sqlite3.Connection, link: ConcordLink) -> None:
    """Persist a reviewed concord link in SQLite."""

    _validate_link(link)
    _require_table(connection, "concord_links")
    now = utc_now()
    created_at = link.created_at or now
    updated_at = link.updated_at or now
    connection.execute(
        """
        INSERT INTO concord_links (
            id, segment_id, controller_token_id, concord_token_id, concord_type,
            controller_nc_class, expected_form, observed_form, agreement_status,
            source, confidence, dictionary_snapshot_id, note, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            concord_type = excluded.concord_type,
            controller_nc_class = excluded.controller_nc_class,
            expected_form = excluded.expected_form,
            observed_form = excluded.observed_form,
            agreement_status = excluded.agreement_status,
            source = excluded.source,
            confidence = excluded.confidence,
            dictionary_snapshot_id = excluded.dictionary_snapshot_id,
            note = excluded.note,
            updated_at = excluded.updated_at
        """,
        (
            link.id,
            link.segment_id,
            link.controller_token_id,
            link.concord_token_id,
            link.concord_type,
            link.controller_nc_class,
            link.expected_form,
            link.observed_form,
            link.agreement_status,
            link.source,
            link.confidence,
            link.dictionary_snapshot_id,
            link.note,
            created_at,
            updated_at,
        ),
    )
    connection.commit()


def list_concord_links(connection: sqlite3.Connection, segment_id: str | None = None) -> list[ConcordLink]:
    """Return stored concord links, optionally filtered by segment."""

    _require_table(connection, "concord_links")
    if segment_id is None:
        rows = connection.execute("SELECT * FROM concord_links ORDER BY segment_id, created_at").fetchall()
    else:
        rows = connection.execute(
            "SELECT * FROM concord_links WHERE segment_id = ? ORDER BY created_at",
            (segment_id,),
        ).fetchall()
    return [_link_from_row(row) for row in rows]


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


def _marker(value: object) -> ConcordMarker:
    if not isinstance(value, dict):
        return ConcordMarker(forms=[], verified=False, note="Needs verification against reference grammar.")
    return ConcordMarker(
        forms=[str(form) for form in value.get("forms", [])],
        verified=bool(value.get("verified", False)),
        note=str(value.get("note", "")),
    )


def _demonstrative_marker(value: object) -> ConcordMarker:
    if not isinstance(value, dict):
        return ConcordMarker(forms=[], verified=False, note="Needs verification against reference grammar.")
    forms: list[str] = []
    for key in ("proximal", "medial", "distal"):
        forms.extend(str(form) for form in value.get(key, []))
    return ConcordMarker(forms=forms, verified=bool(value.get("verified", False)), note=str(value.get("note", "")))


def _markers_for_entry(entry: ConcordEntry) -> list[tuple[ConcordType, ConcordMarker]]:
    return [
        ("SC", entry.subject_concord),
        ("OC", entry.object_concord),
        ("AC", entry.adjective_concord),
        ("PC", entry.possessive_concord),
        ("RC", entry.relative_concord),
        ("DEM", entry.demonstrative),
    ]


def _matching_form(token_surface: str, forms: list[str]) -> str | None:
    surface = token_surface.strip().lower()
    matches = []
    for form in forms:
        normalized_form = form.strip().lower().replace("-", "")
        if normalized_form and surface.startswith(normalized_form):
            matches.append(form)
    if not matches:
        return None
    return sorted(matches, key=len, reverse=True)[0]


def _dictionary_roots(project_path: Path | None) -> list[Path]:
    roots: list[Path] = []
    if project_path is not None:
        roots.append(project_path.expanduser().resolve() / "dictionaries")
    roots.append(Path(__file__).resolve().parents[3] / "dictionaries")
    return roots


def _class_label_to_int(label: str) -> int | None:
    digits = "".join(char for char in label if char.isdigit())
    return int(digits) if digits else None


def _validate_link(link: ConcordLink) -> None:
    if link.concord_type not in VALID_CONCORD_TYPES:
        raise ValueError("concord_type must be one of SC, OC, AC, PC, RC, DEM.")
    if link.agreement_status not in VALID_AGREEMENT_STATUS:
        raise ValueError("agreement_status is outside the v1.0 controlled vocabulary.")
    if link.source not in VALID_REVIEW_SOURCES:
        raise ValueError("source must be manual, suggested-accepted, or suggested-overridden.")
    if link.controller_nc_class is not None and not 1 <= link.controller_nc_class <= 23:
        raise ValueError("controller_nc_class must be between 1 and 23, or None.")


def _require_table(connection: sqlite3.Connection, table_name: str) -> None:
    row = connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,)).fetchone()
    if row is None:
        raise RuntimeError(f"v1.0 migration has not been applied; missing table: {table_name}")


def _link_from_row(row: sqlite3.Row) -> ConcordLink:
    return ConcordLink(
        id=row["id"],
        segment_id=row["segment_id"],
        controller_token_id=row["controller_token_id"],
        concord_token_id=row["concord_token_id"],
        concord_type=row["concord_type"],
        controller_nc_class=row["controller_nc_class"],
        expected_form=row["expected_form"],
        observed_form=row["observed_form"],
        agreement_status=row["agreement_status"],
        source=row["source"],
        confidence=row["confidence"],
        dictionary_snapshot_id=row["dictionary_snapshot_id"],
        note=row["note"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
