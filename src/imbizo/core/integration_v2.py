"""Borrowing Integration Score v2.

The v1.5 score combines v1.0 morphological evidence with optional
phonological evidence. It remains a transparent, editable research instrument,
not a theoretical verdict about borrowing status (Poplack, 1980; Muysken,
2000; Mesthrie, 2002).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import sqlite3
from pathlib import Path

import yaml

from .annotation import ConcordLink, Token


VALID_SOURCES = {"manual", "suggested-accepted", "suggested-overridden", "imported"}


@dataclass(frozen=True, slots=True)
class IntegrationWeightsV2:
    """Project-editable weights for Integration Score v2."""

    class_prefix: float = 0.25
    concord_links: float = 0.25
    inflection: float = 0.15
    phonology: float = 0.25
    frequency: float = 0.10

    def __post_init__(self) -> None:
        """Ensure the transparent weighted sum remains normalized."""

        total = self.class_prefix + self.concord_links + self.inflection + self.phonology + self.frequency
        if abs(total - 1.0) > 1e-6:
            raise ValueError("IntegrationWeightsV2 must sum to 1.0")


DEFAULT_WEIGHTS_V2 = IntegrationWeightsV2()


@dataclass(slots=True)
class PhonologyPattern:
    """One dictionary cue for phonological adaptation."""

    feature_type: str
    description: str
    example: str
    verified: bool
    note: str
    citation: str


@dataclass(slots=True)
class PhonologyDictionary:
    """Typed phonology YAML dictionary."""

    language_code: str
    language_name: str
    version: str
    source: str
    transcription_basis: str
    patterns: list[PhonologyPattern]


@dataclass(slots=True)
class PhonologicalFeature:
    """Reviewed phonological or tonal evidence attached to a token."""

    id: str
    token_id: str
    feature_type: str
    value: str
    source: str
    note: str | None = None
    created_at: str | None = None


@dataclass(slots=True)
class IntegrationFactor:
    """One contributing factor in the transparent weighted score."""

    name: str
    value: float
    weight: float
    contribution: float
    explanation: str


@dataclass(slots=True)
class IntegrationScoreV2Result:
    """Full Integration Score v2 result for UI and export."""

    token_id: str
    score: float
    factors: list[IntegrationFactor]
    explanation: str


IntegrationV2Result = IntegrationScoreV2Result


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
    concord_links: list[ConcordLink],
    phonological_features: list[PhonologicalFeature],
    project_frequency: int,
    project_threshold: int,
    weights: IntegrationWeightsV2 = DEFAULT_WEIGHTS_V2,
) -> IntegrationScoreV2Result:
    """Compute a transparent borrowing-integration score in [0,1].

    The weighted sum uses morphological evidence (class prefix, concord links,
    inflection) and phonological evidence (vowel epenthesis, cluster
    simplification, tonal reassignment). The formula is justified by debates
    on borrowing and code-mixing continua (Poplack, 1980; Muysken, 2000;
    Mesthrie, 2002). Weights are project-editable for sensitivity analysis.
    """

    class_prefix_value = 1.0 if stem_token.nc_class is not None or stem_token.nc_prefix else 0.0
    concord_value = _concord_value(stem_token, concord_links)
    inflection_value = _inflection_value(stem_token)
    phonology_value = _phonology_value(phonological_features)
    frequency_value = 0.0 if project_threshold <= 0 else _unit(project_frequency / project_threshold)

    factors = [
        _factor("class_prefix", class_prefix_value, weights.class_prefix, "Noun-class prefix or class assignment is present."),
        _factor("concord_links", concord_value, weights.concord_links, "Reviewed concord links connect the stem to host grammar."),
        _factor("inflection", inflection_value, weights.inflection, "Surface form shows host-language inflectional material."),
        _factor("phonology", phonology_value, weights.phonology, "Reviewed phonological adaptation evidence is present."),
        _factor("frequency", frequency_value, weights.frequency, "Repeated project use can support integration analysis."),
    ]
    score = round(_unit(sum(item.contribution for item in factors)), 4)
    explanation = (
        f"Integration Score v2 for '{stem_token.surface}' is {score:.2f}. "
        "This is a transparent weighted sum, not an automatic classification; "
        "researchers may edit weights and override interpretation."
    )
    return IntegrationScoreV2Result(token_id=stem_token.id, score=score, factors=factors, explanation=explanation)


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
        (feature.id, feature.token_id, feature.feature_type, feature.value, feature.source, feature.note, created_at),
    )


def persist_integration_score(conn: sqlite3.Connection, result: IntegrationScoreV2Result) -> None:
    """Persist the v1.5 integration score to the token row."""

    conn.execute("UPDATE tokens SET phon_integration_score = ? WHERE id = ?", (result.score, result.token_id))


def _concord_value(stem_token: Token, concord_links: list[ConcordLink]) -> float:
    relevant = [
        link
        for link in concord_links
        if link.head_token_id == stem_token.id or link.dependent_token_id == stem_token.id
    ]
    if not relevant:
        return 0.0
    return _unit(sum(max(0.0, min(1.0, link.confidence)) for link in relevant) / min(3, len(relevant)))


def _inflection_value(stem_token: Token) -> float:
    text = stem_token.text_for_matching.casefold()
    if "-" in text and (stem_token.nc_prefix or stem_token.nc_class is not None):
        return 0.85
    if stem_token.nc_prefix and text.startswith(stem_token.nc_prefix.casefold()):
        return 0.75
    return 0.0


def _phonology_value(features: list[PhonologicalFeature]) -> float:
    if not features:
        return 0.0
    feature_weights = {
        "vowel_epenthesis": 0.35,
        "consonant_cluster_simplification": 0.3,
        "tonal_reassignment": 0.25,
        "stress_pattern_shift": 0.2,
        "click_reduction": 0.2,
    }
    source_factor = {
        "manual": 1.0,
        "imported": 0.85,
        "suggested-accepted": 0.75,
        "suggested-overridden": 0.25,
    }
    total = sum(feature_weights.get(feature.feature_type, 0.15) * source_factor.get(feature.source, 0.0) for feature in features)
    return _unit(total)


def _factor(name: str, value: float, weight: float, explanation: str) -> IntegrationFactor:
    value = _unit(value)
    return IntegrationFactor(
        name=name,
        value=value,
        weight=weight,
        contribution=round(value * weight, 4),
        explanation=explanation,
    )


def _unit(value: float) -> float:
    return round(max(0.0, min(1.0, float(value))), 4)
