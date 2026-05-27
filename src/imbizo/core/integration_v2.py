"""Borrowing Integration Score v2 with optional phonological evidence.

Version 1.0 measured integration using morphology and concord evidence. v1.5
adds optional phonological and tonal evidence when a project actually has the
transcription or audio review needed to support it. Missing phonological data
is reported as unavailable, not as negative evidence (Poplack, 1980; Muysken,
2000; Mesthrie, 2008).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import sqlite3
from pathlib import Path

import yaml

from .annotation import Token


VALID_SOURCES = {"manual", "suggested-accepted", "suggested-overridden", "imported"}


@dataclass(frozen=True, slots=True)
class IntegrationV2Weights:
    """Configurable transparent weights for integration v2."""

    morphology: float = 0.3
    concord: float = 0.25
    frequency: float = 0.15
    phonology: float = 0.25
    researcher_override: float = 0.05

    def __post_init__(self) -> None:
        """Validate that weights sum to 1.0."""

        total = self.morphology + self.concord + self.frequency + self.phonology + self.researcher_override
        if abs(total - 1.0) > 1e-6:
            raise ValueError("IntegrationV2Weights must sum to 1.0")


DEFAULT_WEIGHTS = IntegrationV2Weights()


@dataclass(slots=True)
class PhonologyPattern:
    """One phonological adaptation cue from a dictionary."""

    feature_type: str
    description: str
    example: str
    verified: bool
    note: str
    citation: str


@dataclass(slots=True)
class PhonologyDictionary:
    """Typed phonology dictionary for optional integration evidence."""

    language_code: str
    language_name: str
    version: str
    source: str
    transcription_basis: str
    patterns: list[PhonologyPattern]


@dataclass(slots=True)
class PhonologicalFeature:
    """Reviewed phonological or tonal feature attached to a token."""

    id: str
    token_id: str
    feature_type: str
    value: str
    source: str
    note: str | None = None
    created_at: str | None = None


@dataclass(slots=True)
class IntegrationV2Result:
    """Transparent v1.5 integration result."""

    token_id: str
    score: float
    morphology_component: float
    concord_component: float
    frequency_component: float
    phonology_component: float | None
    researcher_override_component: float
    evidence_summary: str


def load_phonology_dictionary(path: Path) -> PhonologyDictionary:
    """Load a local phonology dictionary for optional D1 scoring."""

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    for field in ["language_code", "language_name", "version", "source"]:
        if not data.get(field):
            raise ValueError(f"{path} is missing required field {field}")
    patterns = [
        PhonologyPattern(
            feature_type=str(item.get("feature_type", "")),
            description=str(item.get("description", "")),
            example=str(item.get("example", "")),
            verified=bool(item.get("verified", False)),
            note=str(item.get("note", "")),
            citation=str(item.get("citation", "")),
        )
        for item in data.get("patterns", [])
    ]
    return PhonologyDictionary(
        language_code=str(data["language_code"]),
        language_name=str(data["language_name"]),
        version=str(data["version"]),
        source=str(data["source"]),
        transcription_basis=str(data.get("transcription_basis", "unknown")),
        patterns=patterns,
    )


def integration_score_v2(
    stem_token: Token,
    morphology_score: float,
    concord_score: float,
    project_frequency: int,
    project_threshold: int,
    phonological_features: list[PhonologicalFeature] | None = None,
    researcher_override_score: float | None = None,
    weights: IntegrationV2Weights = DEFAULT_WEIGHTS,
) -> IntegrationV2Result:
    """Compute transparent borrowing integration score v2 in [0,1].

    The score extends v1.0 morphology/concord integration with optional
    phonological or tonal evidence. Phonology contributes only when reviewed
    evidence exists; text-only projects are not penalized for missing audio.
    """

    morphology_component = _unit(morphology_score)
    concord_component = _unit(concord_score)
    frequency_component = 0.0 if project_threshold <= 0 else _unit(project_frequency / project_threshold)
    phonology_component = _phonology_component(phonological_features or [])
    override_component = _unit(researcher_override_score or 0.0)

    if phonology_component is None:
        active_total = weights.morphology + weights.concord + weights.frequency + weights.researcher_override
        raw = (
            morphology_component * weights.morphology
            + concord_component * weights.concord
            + frequency_component * weights.frequency
            + override_component * weights.researcher_override
        ) / active_total
        summary = "No reviewed phonological evidence was supplied; score was reweighted over available components."
    else:
        raw = (
            morphology_component * weights.morphology
            + concord_component * weights.concord
            + frequency_component * weights.frequency
            + phonology_component * weights.phonology
            + override_component * weights.researcher_override
        )
        summary = "Reviewed phonological evidence contributed to the v1.5 score."

    return IntegrationV2Result(
        token_id=stem_token.id,
        score=round(_unit(raw), 4),
        morphology_component=morphology_component,
        concord_component=concord_component,
        frequency_component=frequency_component,
        phonology_component=phonology_component,
        researcher_override_component=override_component,
        evidence_summary=summary,
    )


def persist_phonological_feature(conn: sqlite3.Connection, feature: PhonologicalFeature) -> None:
    """Persist one reviewed phonological feature to SQLite."""

    if feature.source not in VALID_SOURCES:
        raise ValueError(f"invalid phonological feature source: {feature.source}")
    created_at = feature.created_at or datetime.now(UTC).isoformat()
    conn.execute(
        """
        INSERT OR REPLACE INTO phonological_features (
            id, token_id, feature_type, value, source, note, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            feature.id,
            feature.token_id,
            feature.feature_type,
            feature.value,
            feature.source,
            feature.note,
            created_at,
        ),
    )


def persist_integration_score(conn: sqlite3.Connection, result: IntegrationV2Result) -> None:
    """Persist a v1.5 phonological integration score on the token row."""

    conn.execute(
        "UPDATE tokens SET phon_integration_score = ? WHERE id = ?",
        (result.score, result.token_id),
    )


def _phonology_component(features: list[PhonologicalFeature]) -> float | None:
    if not features:
        return None
    reviewed = [feature for feature in features if feature.source in {"manual", "suggested-accepted", "imported"}]
    if not reviewed:
        return None
    source_weight = {
        "manual": 1.0,
        "imported": 0.85,
        "suggested-accepted": 0.75,
        "suggested-overridden": 0.35,
    }
    total = sum(source_weight.get(feature.source, 0.0) for feature in reviewed)
    return round(_unit(total / 3.0), 4)


def _unit(value: float) -> float:
    return round(max(0.0, min(1.0, float(value))), 4)
