# v1.5 Deliverable 3 - Data Model Increment

This document defines additive v1.5 data-model changes for C1 Sister Language
Disambiguator, C2 Triggered Switching Detector, C3 Mixed-Code Variety Mode, D1
Borrowing Integration Score v2, D2 Comparable Subcorpus Exporter, and D3
Community Review Workflow. These changes are backward-compatible with MVP and
v1.0 projects: all new token columns are nullable, all feature blocks are
opt-in, and automatic decisions remain advisory.

## 1. SQLite Schema Changes

SQLite supports `CREATE TABLE IF NOT EXISTS`, but it does not provide a
portable `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`. The v1.5 migration runner
must therefore check `PRAGMA table_xinfo('tokens')` before each `ALTER TABLE`
statement below. The table-creation and index statements are directly
idempotent.

```sql
PRAGMA foreign_keys = ON;

-- Migration-runner guard: apply only if tokens.sister_lang_confidence is absent.
ALTER TABLE tokens ADD COLUMN sister_lang_confidence REAL
    CHECK (
        sister_lang_confidence IS NULL
        OR (sister_lang_confidence >= 0.0 AND sister_lang_confidence <= 1.0)
    ); -- Advisory confidence in [0,1] for sister-language disambiguation when the token language is ambiguous.

-- Migration-runner guard: apply only if tokens.sister_lang_evidence is absent.
ALTER TABLE tokens ADD COLUMN sister_lang_evidence TEXT; -- Comma-separated local evidence codes matched by C1, for example "click_x,neg_anga,vocab_lefatshe".

-- Migration-runner guard: apply only if tokens.trigger_role is absent.
ALTER TABLE tokens ADD COLUMN trigger_role TEXT
    CHECK (trigger_role IS NULL OR trigger_role IN ('trigger', 'triggered', 'none')); -- C2 role in a reviewed or suggested trigger relationship after Clyne-style triggering analysis.

-- Migration-runner guard: apply only if tokens.mixed_code_variety is absent.
ALTER TABLE tokens ADD COLUMN mixed_code_variety TEXT
    CHECK (
        mixed_code_variety IS NULL
        OR mixed_code_variety IN ('tsotsitaal', 'iscamtho', 'kaaps', 'sabela')
    ); -- Optional C3 named mixed-code variety label for spans that should not be forced into simple ML/EL analysis.

-- Migration-runner guard: apply only if tokens.phon_integration_score is absent.
ALTER TABLE tokens ADD COLUMN phon_integration_score REAL
    CHECK (
        phon_integration_score IS NULL
        OR (phon_integration_score >= 0.0 AND phon_integration_score <= 1.0)
    ); -- Optional D1 borrowing-integration score including phonological or tonal evidence where available.

CREATE TABLE IF NOT EXISTS trigger_links (
    head_token_id TEXT NOT NULL, -- Token hypothesized to act as the trigger context.
    triggered_token_id TEXT NOT NULL, -- Token hypothesized to be affected by the trigger context.
    trigger_type TEXT NOT NULL, -- Local trigger category such as cognate, repetition, discourse_marker, named_entity, technical_term, or prior_switch.
    confidence REAL NOT NULL CHECK (confidence >= 0.0 AND confidence <= 1.0), -- Advisory confidence in [0,1], never an automatic explanation of speaker intent.
    source TEXT NOT NULL CHECK (source IN ('manual', 'suggested-accepted', 'suggested-overridden', 'imported')), -- Review state showing whether the researcher accepted, changed, or imported the relation.
    note TEXT, -- Researcher memo or plain-language explanation for this trigger link.
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, -- Local timestamp when the relation was created.
    PRIMARY KEY (head_token_id, triggered_token_id, trigger_type),
    FOREIGN KEY (head_token_id) REFERENCES tokens(id) ON DELETE CASCADE,
    FOREIGN KEY (triggered_token_id) REFERENCES tokens(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_trigger_links_head
    ON trigger_links(head_token_id); -- Speeds lookup of all tokens potentially triggered by a selected head token.

CREATE INDEX IF NOT EXISTS idx_trigger_links_triggered
    ON trigger_links(triggered_token_id); -- Speeds lookup of the trigger source for a selected triggered token.

CREATE TABLE IF NOT EXISTS mixed_code_spans (
    id TEXT PRIMARY KEY, -- Stable local identifier for a mixed-code span.
    project_id TEXT NOT NULL, -- Local project identifier; kept textual for compatibility with MVP/v1.0 project metadata.
    start_token_id TEXT NOT NULL, -- First token included in the mixed-code span.
    end_token_id TEXT NOT NULL, -- Last token included in the mixed-code span.
    variety TEXT NOT NULL CHECK (variety IN ('tsotsitaal', 'iscamtho', 'kaaps', 'sabela')), -- Named mixed-code variety selected by the researcher.
    confidence REAL CHECK (confidence IS NULL OR (confidence >= 0.0 AND confidence <= 1.0)), -- Optional researcher confidence in [0,1] for the span label.
    source TEXT NOT NULL CHECK (source IN ('manual', 'suggested-accepted', 'suggested-overridden', 'imported')), -- Review state for the span label.
    note TEXT, -- Researcher memo explaining why mixed-code mode is appropriate or contested.
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, -- Local timestamp when the span record was created.
    FOREIGN KEY (start_token_id) REFERENCES tokens(id) ON DELETE CASCADE,
    FOREIGN KEY (end_token_id) REFERENCES tokens(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_mixed_code_spans_project
    ON mixed_code_spans(project_id); -- Speeds project-level filtering of mixed-code spans.

CREATE INDEX IF NOT EXISTS idx_mixed_code_spans_bounds
    ON mixed_code_spans(start_token_id, end_token_id); -- Speeds overlap checks against the annotation grid.

CREATE TABLE IF NOT EXISTS phonological_features (
    id TEXT PRIMARY KEY, -- Stable local identifier for one phonological or tonal observation.
    token_id TEXT NOT NULL, -- Token to which the phonological observation applies.
    feature_type TEXT NOT NULL, -- Feature category such as vowel_epenthesis, tone_adaptation, click_reduction, stress_shift, or consonant_substitution.
    value TEXT NOT NULL, -- Researcher-entered value or dictionary cue for the observed feature.
    source TEXT NOT NULL CHECK (source IN ('manual', 'suggested-accepted', 'suggested-overridden', 'imported')), -- Review state for the feature observation.
    note TEXT, -- Researcher memo, uncertainty note, or transcription-standard caveat.
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, -- Local timestamp when the feature was recorded.
    FOREIGN KEY (token_id) REFERENCES tokens(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_phonological_features_token
    ON phonological_features(token_id); -- Speeds lookup of optional D1 evidence for a token.

CREATE INDEX IF NOT EXISTS idx_phonological_features_type
    ON phonological_features(feature_type); -- Speeds metric filtering by phonological feature type.

CREATE TABLE IF NOT EXISTS community_reviews (
    id TEXT PRIMARY KEY, -- Stable local identifier for an offline community-review record.
    target_kind TEXT NOT NULL CHECK (
        target_kind IN (
            'token',
            'utterance',
            'concord_link',
            'four_m_audit',
            'trigger_link',
            'mixed_code_span',
            'phonological_feature',
            'dictionary_entry'
        )
    ), -- Kind of record or dictionary item reviewed in an offline packet.
    target_id TEXT NOT NULL, -- Local identifier of the reviewed target; dynamic targets cannot use a single foreign key.
    reviewer_alias TEXT NOT NULL, -- Reviewer-chosen name, initials, or pseudonym recorded locally.
    comment TEXT NOT NULL, -- Human-readable review comment or correction.
    status TEXT NOT NULL CHECK (status IN ('pending', 'accepted', 'rejected', 'superseded')), -- Local workflow state for the review.
    signature_hash TEXT, -- SHA-256 hash of the review-packet signature or attestation file when supplied.
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, -- Local timestamp when the review was imported or created.
    applied_at TEXT -- Local timestamp when an accepted review was applied; NULL while pending or rejected.
);

CREATE INDEX IF NOT EXISTS idx_community_reviews_target
    ON community_reviews(target_kind, target_id); -- Speeds review lookup for a selected annotation or dictionary entry.

CREATE INDEX IF NOT EXISTS idx_community_reviews_status
    ON community_reviews(status); -- Speeds filtering by pending, accepted, rejected, or superseded reviews.
```

## 2. JSON Schema Fragments

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://imbizo-cs.local/schema/v1_5/fragments.json",
  "$defs": {
    "Token": {
      "type": "object",
      "additionalProperties": false,
      "required": ["id", "utterance_id", "position", "surface", "language"],
      "properties": {
        "id": { "type": "string" },
        "utterance_id": { "type": "string" },
        "position": { "type": "integer", "minimum": 0 },
        "surface": { "type": "string" },
        "normalized": { "type": ["string", "null"] },
        "language": { "type": ["string", "null"] },
        "language_source": { "type": ["string", "null"] },
        "start_time": { "type": ["number", "null"], "minimum": 0 },
        "end_time": { "type": ["number", "null"], "minimum": 0 },
        "speaker_id": { "type": ["string", "null"] },
        "nc_class": { "type": ["integer", "null"], "minimum": 1, "maximum": 23 },
        "nc_prefix": { "type": ["string", "null"] },
        "nc_source": { "type": ["string", "null"] },
        "four_m_type": {
          "type": ["string", "null"],
          "enum": ["content", "early_system", "bridge_late_system", "outsider_late_system", "unassigned", null]
        },
        "four_m_source": { "type": ["string", "null"] },
        "sister_lang_confidence": { "type": ["number", "null"], "minimum": 0, "maximum": 1 },
        "sister_lang_evidence": { "type": ["string", "null"] },
        "trigger_role": {
          "type": ["string", "null"],
          "enum": ["trigger", "triggered", "none", null]
        },
        "mixed_code_variety": {
          "type": ["string", "null"],
          "enum": ["tsotsitaal", "iscamtho", "kaaps", "sabela", null]
        },
        "phon_integration_score": { "type": ["number", "null"], "minimum": 0, "maximum": 1 }
      }
    },
    "TriggerLink": {
      "type": "object",
      "additionalProperties": false,
      "required": ["head_token_id", "triggered_token_id", "trigger_type", "confidence", "source", "created_at"],
      "properties": {
        "head_token_id": { "type": "string" },
        "triggered_token_id": { "type": "string" },
        "trigger_type": { "type": "string" },
        "confidence": { "type": "number", "minimum": 0, "maximum": 1 },
        "source": { "type": "string", "enum": ["manual", "suggested-accepted", "suggested-overridden", "imported"] },
        "note": { "type": ["string", "null"] },
        "created_at": { "type": "string", "format": "date-time" }
      }
    },
    "MixedCodeSpan": {
      "type": "object",
      "additionalProperties": false,
      "required": ["id", "project_id", "start_token_id", "end_token_id", "variety", "source", "created_at"],
      "properties": {
        "id": { "type": "string" },
        "project_id": { "type": "string" },
        "start_token_id": { "type": "string" },
        "end_token_id": { "type": "string" },
        "variety": { "type": "string", "enum": ["tsotsitaal", "iscamtho", "kaaps", "sabela"] },
        "confidence": { "type": ["number", "null"], "minimum": 0, "maximum": 1 },
        "source": { "type": "string", "enum": ["manual", "suggested-accepted", "suggested-overridden", "imported"] },
        "note": { "type": ["string", "null"] },
        "created_at": { "type": "string", "format": "date-time" }
      }
    },
    "PhonologicalFeature": {
      "type": "object",
      "additionalProperties": false,
      "required": ["id", "token_id", "feature_type", "value", "source", "created_at"],
      "properties": {
        "id": { "type": "string" },
        "token_id": { "type": "string" },
        "feature_type": { "type": "string" },
        "value": { "type": "string" },
        "source": { "type": "string", "enum": ["manual", "suggested-accepted", "suggested-overridden", "imported"] },
        "note": { "type": ["string", "null"] },
        "created_at": { "type": "string", "format": "date-time" }
      }
    },
    "CommunityReview": {
      "type": "object",
      "additionalProperties": false,
      "required": ["id", "target_kind", "target_id", "reviewer_alias", "comment", "status", "created_at"],
      "properties": {
        "id": { "type": "string" },
        "target_kind": {
          "type": "string",
          "enum": ["token", "utterance", "concord_link", "four_m_audit", "trigger_link", "mixed_code_span", "phonological_feature", "dictionary_entry"]
        },
        "target_id": { "type": "string" },
        "reviewer_alias": { "type": "string" },
        "comment": { "type": "string" },
        "status": { "type": "string", "enum": ["pending", "accepted", "rejected", "superseded"] },
        "signature_hash": { "type": ["string", "null"], "pattern": "^[a-fA-F0-9]{64}$" },
        "created_at": { "type": "string", "format": "date-time" },
        "applied_at": { "type": ["string", "null"], "format": "date-time" }
      }
    },
    "ProjectSnapshot": {
      "type": "object",
      "additionalProperties": true,
      "required": ["schema_version", "project", "tokens"],
      "properties": {
        "schema_version": { "const": "1.5" },
        "project": { "type": "object" },
        "tokens": {
          "type": "array",
          "items": { "$ref": "#/$defs/Token" }
        },
        "concord_links": { "type": "array", "items": { "type": "object" } },
        "four_m_audit": { "type": "array", "items": { "type": "object" } },
        "trigger_links": {
          "type": "array",
          "items": { "$ref": "#/$defs/TriggerLink" }
        },
        "mixed_code_spans": {
          "type": "array",
          "items": { "$ref": "#/$defs/MixedCodeSpan" }
        },
        "phonological_features": {
          "type": "array",
          "items": { "$ref": "#/$defs/PhonologicalFeature" }
        },
        "community_reviews": {
          "type": "array",
          "items": { "$ref": "#/$defs/CommunityReview" }
        }
      }
    }
  }
}
```

## 3. Pydantic v2 Models

```python
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


ReviewSource = Literal["manual", "suggested-accepted", "suggested-overridden", "imported"]
TriggerRole = Literal["trigger", "triggered", "none"]
MixedCodeVariety = Literal["tsotsitaal", "iscamtho", "kaaps", "sabela"]
FourMType = Literal[
    "content",
    "early_system",
    "bridge_late_system",
    "outsider_late_system",
    "unassigned",
]
TargetKind = Literal[
    "token",
    "utterance",
    "concord_link",
    "four_m_audit",
    "trigger_link",
    "mixed_code_span",
    "phonological_feature",
    "dictionary_entry",
]
ReviewStatus = Literal["pending", "accepted", "rejected", "superseded"]


class TokenV15(BaseModel):
    """Token export model with MVP, v1.0, and v1.5 annotation fields."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(description="Stable token identifier.")
    utterance_id: str = Field(description="Identifier of the utterance containing the token.")
    position: int = Field(ge=0, description="Zero-based token position inside the utterance.")
    surface: str = Field(description="Original token text, preserving non-standard orthography.")
    normalized: str | None = Field(default=None, description="Optional normalized form; never overwrites surface.")
    language: str | None = Field(default=None, description="Current researcher-visible language tag.")
    language_source: str | None = Field(default=None, description="Provenance source for the language tag.")
    start_time: float | None = Field(default=None, ge=0, description="Optional token start time in seconds.")
    end_time: float | None = Field(default=None, ge=0, description="Optional token end time in seconds.")
    speaker_id: str | None = Field(default=None, description="Optional speaker identifier.")
    nc_class: int | None = Field(default=None, description="v1.0 noun class number, if assigned.")
    nc_prefix: str | None = Field(default=None, description="v1.0 noun-class prefix or augment evidence.")
    nc_source: str | None = Field(default=None, description="Review source for noun-class assignment.")
    four_m_type: FourMType | None = Field(default=None, description="v1.0 optional 4-M morpheme type.")
    four_m_source: str | None = Field(default=None, description="Review source for 4-M assignment.")
    sister_lang_confidence: float | None = Field(
        default=None,
        description="v1.5 C1 confidence in [0,1] for sister-language disambiguation.",
    )
    sister_lang_evidence: str | None = Field(
        default=None,
        description="Comma-separated C1 evidence codes matched by local dictionaries.",
    )
    trigger_role: TriggerRole | None = Field(
        default=None,
        description="v1.5 C2 trigger role: trigger, triggered, none, or unset.",
    )
    mixed_code_variety: MixedCodeVariety | None = Field(
        default=None,
        description="v1.5 C3 mixed-code variety label when opted in.",
    )
    phon_integration_score: float | None = Field(
        default=None,
        description="v1.5 D1 integration score including optional phonological evidence.",
    )

    @field_validator("nc_class")
    @classmethod
    def validate_nc_class(cls, value: int | None) -> int | None:
        """Require noun class to be in 1..23 when present."""
        if value is not None and not 1 <= value <= 23:
            raise ValueError("nc_class must be in 1..23 or None")
        return value

    @field_validator("sister_lang_confidence", "phon_integration_score")
    @classmethod
    def validate_optional_unit_interval(cls, value: float | None) -> float | None:
        """Require optional v1.5 scores to be in [0,1]."""
        if value is not None and not 0.0 <= value <= 1.0:
            raise ValueError("score must be in [0,1] or None")
        return value


class TriggerLink(BaseModel):
    """Reviewed or suggested trigger relation after Clyne-style triggering analysis."""

    model_config = ConfigDict(extra="forbid")

    head_token_id: str = Field(description="Token hypothesized to provide the trigger context.")
    triggered_token_id: str = Field(description="Token hypothesized to be triggered.")
    trigger_type: str = Field(description="Local trigger category, such as technical_term or prior_switch.")
    confidence: float = Field(description="Advisory confidence in [0,1].")
    source: ReviewSource = Field(description="Manual, accepted suggestion, overridden suggestion, or import source.")
    note: str | None = Field(default=None, description="Researcher note for the relation.")
    created_at: datetime = Field(description="Local timestamp for relation creation.")

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, value: float) -> float:
        """Require trigger confidence to be in [0,1]."""
        if not 0.0 <= value <= 1.0:
            raise ValueError("confidence must be in [0,1]")
        return value


class MixedCodeSpan(BaseModel):
    """Optional span-level label for named mixed-code varieties."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(description="Stable mixed-code span identifier.")
    project_id: str = Field(description="Local project identifier.")
    start_token_id: str = Field(description="First token in the span.")
    end_token_id: str = Field(description="Last token in the span.")
    variety: MixedCodeVariety = Field(description="Named mixed-code variety.")
    confidence: float | None = Field(default=None, description="Optional researcher confidence in [0,1].")
    source: ReviewSource = Field(description="Review source for the span label.")
    note: str | None = Field(default=None, description="Researcher note explaining the span label.")
    created_at: datetime = Field(description="Local timestamp for span creation.")

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, value: float | None) -> float | None:
        """Require optional span confidence to be in [0,1]."""
        if value is not None and not 0.0 <= value <= 1.0:
            raise ValueError("confidence must be in [0,1] or None")
        return value


class PhonologicalFeature(BaseModel):
    """Optional phonological or tonal evidence for Borrowing Integration Score v2."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(description="Stable phonological-feature identifier.")
    token_id: str = Field(description="Token to which this feature applies.")
    feature_type: str = Field(description="Feature type, such as vowel_epenthesis or tone_adaptation.")
    value: str = Field(description="Observed value or local cue label.")
    source: ReviewSource = Field(description="Review source for the feature.")
    note: str | None = Field(default=None, description="Researcher note or uncertainty statement.")
    created_at: datetime = Field(description="Local timestamp for feature creation.")


class CommunityReview(BaseModel):
    """Offline community-review record for annotations, dictionaries, and v1.5 evidence."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(description="Stable community-review identifier.")
    target_kind: TargetKind = Field(description="Kind of reviewed target.")
    target_id: str = Field(description="Identifier of the reviewed target.")
    reviewer_alias: str = Field(description="Reviewer-chosen name, initials, or pseudonym.")
    comment: str = Field(description="Human-readable review comment.")
    status: ReviewStatus = Field(description="Local workflow status for the review.")
    signature_hash: str | None = Field(default=None, description="Optional SHA-256 hash of signature or attestation.")
    created_at: datetime = Field(description="Local timestamp when the review was created or imported.")
    applied_at: datetime | None = Field(default=None, description="Timestamp when an accepted review was applied.")

    @field_validator("signature_hash")
    @classmethod
    def validate_signature_hash(cls, value: str | None) -> str | None:
        """Require SHA-256 format when a signature hash is supplied."""
        if value is not None:
            normalized = value.lower()
            if len(normalized) != 64 or any(char not in "0123456789abcdef" for char in normalized):
                raise ValueError("signature_hash must be a 64-character SHA-256 hex digest")
            return normalized
        return value


class ProjectSnapshotV15(BaseModel):
    """Project snapshot with v1.5 arrays added to MVP and v1.0 exports."""

    model_config = ConfigDict(extra="allow")

    schema_version: Literal["1.5"] = Field(description="Export schema version.")
    project: dict = Field(description="Project metadata object.")
    tokens: list[TokenV15] = Field(description="All exported token records.")
    trigger_links: list[TriggerLink] = Field(default_factory=list, description="C2 trigger links.")
    mixed_code_spans: list[MixedCodeSpan] = Field(default_factory=list, description="C3 mixed-code spans.")
    phonological_features: list[PhonologicalFeature] = Field(
        default_factory=list,
        description="D1 phonological or tonal integration evidence.",
    )
    community_reviews: list[CommunityReview] = Field(
        default_factory=list,
        description="D3 offline community-review records.",
    )
```

## 4. Worked Example

The records below extend the fictional v1.0 isiZulu-English interview. All
utterances and linguistic analyses are fictional examples for schema
illustration only; they are not presented as authoritative language data.

```json
{
  "_comment": "# fictional example",
  "schema_version": "1.5",
  "project": {
    "id": "proj_fictional_zul_eng",
    "title": "Fictional isiZulu-English Interview",
    "dictionary_versions": {
      "noun_classes.zul": "0.1.0",
      "concord.zul": "0.1.0",
      "phonology.zul": "0.1.0",
      "triggers.eng": "0.1.0",
      "mixed_code.tsotsitaal": "0.1.0"
    }
  },
  "utterances": [
    {
      "_comment": "# fictional example",
      "id": "utt_001",
      "speaker_id": "S01",
      "start_time": 12.4,
      "end_time": 15.2,
      "raw_text": "Ngithenge i-laptop entsha izolo.",
      "translation": "I bought a new laptop yesterday."
    },
    {
      "_comment": "# fictional example",
      "id": "utt_004",
      "speaker_id": "S01",
      "start_time": 38.1,
      "end_time": 43.8,
      "raw_text": "U-manager uthe we must finish today.",
      "translation": "The manager said we must finish today."
    },
    {
      "_comment": "# fictional example",
      "id": "utt_005",
      "speaker_id": "S02",
      "start_time": 51.0,
      "end_time": 54.0,
      "raw_text": "Eish mfethu, we move sharp namhlanje.",
      "translation": "Friend, we move quickly today."
    }
  ],
  "tokens": [
    {
      "_comment": "# fictional example",
      "id": "tok_001_01",
      "utterance_id": "utt_001",
      "position": 0,
      "surface": "Ngithenge",
      "normalized": null,
      "language": "zul",
      "language_source": "manual",
      "start_time": 12.4,
      "end_time": 12.9,
      "speaker_id": "S01",
      "nc_class": null,
      "nc_prefix": null,
      "nc_source": null,
      "four_m_type": "outsider_late_system",
      "four_m_source": "manual",
      "sister_lang_confidence": null,
      "sister_lang_evidence": null,
      "trigger_role": "none",
      "mixed_code_variety": null,
      "phon_integration_score": null
    },
    {
      "_comment": "# fictional example",
      "id": "tok_001_02",
      "utterance_id": "utt_001",
      "position": 1,
      "surface": "i-laptop",
      "normalized": "i-laptop",
      "language": "mixed",
      "language_source": "manual",
      "start_time": 12.9,
      "end_time": 13.6,
      "speaker_id": "S01",
      "nc_class": 9,
      "nc_prefix": "i-",
      "nc_source": "manual",
      "four_m_type": "content",
      "four_m_source": "manual",
      "sister_lang_confidence": null,
      "sister_lang_evidence": null,
      "trigger_role": "none",
      "mixed_code_variety": null,
      "phon_integration_score": 0.82
    },
    {
      "_comment": "# fictional example",
      "id": "tok_001_03",
      "utterance_id": "utt_001",
      "position": 2,
      "surface": "entsha",
      "normalized": null,
      "language": "zul",
      "language_source": "manual",
      "start_time": 13.6,
      "end_time": 14.1,
      "speaker_id": "S01",
      "nc_class": null,
      "nc_prefix": null,
      "nc_source": null,
      "four_m_type": "early_system",
      "four_m_source": "manual",
      "sister_lang_confidence": null,
      "sister_lang_evidence": null,
      "trigger_role": "none",
      "mixed_code_variety": null,
      "phon_integration_score": null
    },
    {
      "_comment": "# fictional example",
      "id": "tok_004_01",
      "utterance_id": "utt_004",
      "position": 0,
      "surface": "U-manager",
      "normalized": "u-manager",
      "language": "mixed",
      "language_source": "manual",
      "start_time": 38.1,
      "end_time": 38.9,
      "speaker_id": "S01",
      "nc_class": 1,
      "nc_prefix": "u-",
      "nc_source": "manual",
      "four_m_type": "content",
      "four_m_source": "manual",
      "sister_lang_confidence": null,
      "sister_lang_evidence": null,
      "trigger_role": "trigger",
      "mixed_code_variety": null,
      "phon_integration_score": 0.74
    },
    {
      "_comment": "# fictional example",
      "id": "tok_004_02",
      "utterance_id": "utt_004",
      "position": 1,
      "surface": "uthe",
      "normalized": null,
      "language": "zul",
      "language_source": "manual",
      "start_time": 38.9,
      "end_time": 39.4,
      "speaker_id": "S01",
      "nc_class": null,
      "nc_prefix": null,
      "nc_source": null,
      "four_m_type": "outsider_late_system",
      "four_m_source": "manual",
      "sister_lang_confidence": null,
      "sister_lang_evidence": null,
      "trigger_role": "none",
      "mixed_code_variety": null,
      "phon_integration_score": null
    },
    {
      "_comment": "# fictional example",
      "id": "tok_004_03",
      "utterance_id": "utt_004",
      "position": 2,
      "surface": "we",
      "normalized": null,
      "language": "eng",
      "language_source": "manual",
      "start_time": 39.4,
      "end_time": 39.6,
      "speaker_id": "S01",
      "nc_class": null,
      "nc_prefix": null,
      "nc_source": null,
      "four_m_type": "outsider_late_system",
      "four_m_source": "manual",
      "sister_lang_confidence": null,
      "sister_lang_evidence": null,
      "trigger_role": "triggered",
      "mixed_code_variety": null,
      "phon_integration_score": null
    },
    {
      "_comment": "# fictional example",
      "id": "tok_004_04",
      "utterance_id": "utt_004",
      "position": 3,
      "surface": "must",
      "normalized": null,
      "language": "eng",
      "language_source": "manual",
      "start_time": 39.6,
      "end_time": 39.9,
      "speaker_id": "S01",
      "nc_class": null,
      "nc_prefix": null,
      "nc_source": null,
      "four_m_type": "outsider_late_system",
      "four_m_source": "manual",
      "sister_lang_confidence": null,
      "sister_lang_evidence": null,
      "trigger_role": "triggered",
      "mixed_code_variety": null,
      "phon_integration_score": null
    },
    {
      "_comment": "# fictional example",
      "id": "tok_004_05",
      "utterance_id": "utt_004",
      "position": 4,
      "surface": "finish",
      "normalized": null,
      "language": "eng",
      "language_source": "manual",
      "start_time": 39.9,
      "end_time": 40.4,
      "speaker_id": "S01",
      "nc_class": null,
      "nc_prefix": null,
      "nc_source": null,
      "four_m_type": "content",
      "four_m_source": "manual",
      "sister_lang_confidence": null,
      "sister_lang_evidence": null,
      "trigger_role": "triggered",
      "mixed_code_variety": null,
      "phon_integration_score": null
    },
    {
      "_comment": "# fictional example",
      "id": "tok_004_06",
      "utterance_id": "utt_004",
      "position": 5,
      "surface": "today",
      "normalized": null,
      "language": "eng",
      "language_source": "manual",
      "start_time": 40.4,
      "end_time": 40.8,
      "speaker_id": "S01",
      "nc_class": null,
      "nc_prefix": null,
      "nc_source": null,
      "four_m_type": "content",
      "four_m_source": "manual",
      "sister_lang_confidence": null,
      "sister_lang_evidence": null,
      "trigger_role": "triggered",
      "mixed_code_variety": null,
      "phon_integration_score": null
    },
    {
      "_comment": "# fictional example",
      "id": "tok_005_01",
      "utterance_id": "utt_005",
      "position": 0,
      "surface": "Eish",
      "normalized": null,
      "language": "mixed",
      "language_source": "manual",
      "start_time": 51.0,
      "end_time": 51.3,
      "speaker_id": "S02",
      "nc_class": null,
      "nc_prefix": null,
      "nc_source": null,
      "four_m_type": "unassigned",
      "four_m_source": "manual",
      "sister_lang_confidence": null,
      "sister_lang_evidence": null,
      "trigger_role": "none",
      "mixed_code_variety": "tsotsitaal",
      "phon_integration_score": null
    },
    {
      "_comment": "# fictional example",
      "id": "tok_005_02",
      "utterance_id": "utt_005",
      "position": 1,
      "surface": "mfethu",
      "normalized": null,
      "language": "mixed",
      "language_source": "manual",
      "start_time": 51.3,
      "end_time": 51.8,
      "speaker_id": "S02",
      "nc_class": null,
      "nc_prefix": null,
      "nc_source": null,
      "four_m_type": "unassigned",
      "four_m_source": "manual",
      "sister_lang_confidence": 0.45,
      "sister_lang_evidence": "shared_form",
      "trigger_role": "none",
      "mixed_code_variety": "tsotsitaal",
      "phon_integration_score": null
    },
    {
      "_comment": "# fictional example",
      "id": "tok_005_03",
      "utterance_id": "utt_005",
      "position": 2,
      "surface": "we",
      "normalized": null,
      "language": "mixed",
      "language_source": "manual",
      "start_time": 51.8,
      "end_time": 52.0,
      "speaker_id": "S02",
      "nc_class": null,
      "nc_prefix": null,
      "nc_source": null,
      "four_m_type": "unassigned",
      "four_m_source": "manual",
      "sister_lang_confidence": null,
      "sister_lang_evidence": null,
      "trigger_role": "none",
      "mixed_code_variety": "tsotsitaal",
      "phon_integration_score": null
    },
    {
      "_comment": "# fictional example",
      "id": "tok_005_04",
      "utterance_id": "utt_005",
      "position": 3,
      "surface": "move",
      "normalized": null,
      "language": "mixed",
      "language_source": "manual",
      "start_time": 52.0,
      "end_time": 52.4,
      "speaker_id": "S02",
      "nc_class": null,
      "nc_prefix": null,
      "nc_source": null,
      "four_m_type": "unassigned",
      "four_m_source": "manual",
      "sister_lang_confidence": null,
      "sister_lang_evidence": null,
      "trigger_role": "none",
      "mixed_code_variety": "tsotsitaal",
      "phon_integration_score": null
    },
    {
      "_comment": "# fictional example",
      "id": "tok_005_05",
      "utterance_id": "utt_005",
      "position": 4,
      "surface": "sharp",
      "normalized": null,
      "language": "mixed",
      "language_source": "manual",
      "start_time": 52.4,
      "end_time": 52.8,
      "speaker_id": "S02",
      "nc_class": null,
      "nc_prefix": null,
      "nc_source": null,
      "four_m_type": "unassigned",
      "four_m_source": "manual",
      "sister_lang_confidence": null,
      "sister_lang_evidence": null,
      "trigger_role": "none",
      "mixed_code_variety": "tsotsitaal",
      "phon_integration_score": null
    },
    {
      "_comment": "# fictional example",
      "id": "tok_005_06",
      "utterance_id": "utt_005",
      "position": 5,
      "surface": "namhlanje",
      "normalized": null,
      "language": "mixed",
      "language_source": "manual",
      "start_time": 52.8,
      "end_time": 53.3,
      "speaker_id": "S02",
      "nc_class": null,
      "nc_prefix": null,
      "nc_source": null,
      "four_m_type": "unassigned",
      "four_m_source": "manual",
      "sister_lang_confidence": 0.55,
      "sister_lang_evidence": "shared_nguni_form",
      "trigger_role": "none",
      "mixed_code_variety": "tsotsitaal",
      "phon_integration_score": null
    }
  ],
  "trigger_links": [
    {
      "_comment": "# fictional example",
      "head_token_id": "tok_004_01",
      "triggered_token_id": "tok_004_03",
      "trigger_type": "technical_or_workplace_role",
      "confidence": 0.63,
      "source": "suggested-accepted",
      "note": "Researcher accepted as a candidate trigger context only, not a claim about speaker intention.",
      "created_at": "2026-05-27T12:00:00Z"
    },
    {
      "_comment": "# fictional example",
      "head_token_id": "tok_004_01",
      "triggered_token_id": "tok_004_04",
      "trigger_type": "technical_or_workplace_role",
      "confidence": 0.61,
      "source": "suggested-accepted",
      "note": "Second token in the following English clause, treated as the same candidate trigger context.",
      "created_at": "2026-05-27T12:00:00Z"
    },
    {
      "_comment": "# fictional example",
      "head_token_id": "tok_004_01",
      "triggered_token_id": "tok_004_05",
      "trigger_type": "technical_or_workplace_role",
      "confidence": 0.59,
      "source": "suggested-accepted",
      "note": "Content verb in the following English clause, recorded as candidate evidence only.",
      "created_at": "2026-05-27T12:00:00Z"
    },
    {
      "_comment": "# fictional example",
      "head_token_id": "tok_004_01",
      "triggered_token_id": "tok_004_06",
      "trigger_type": "technical_or_workplace_role",
      "confidence": 0.55,
      "source": "suggested-accepted",
      "note": "Clause-final English token included in the same candidate triggered stretch.",
      "created_at": "2026-05-27T12:00:00Z"
    }
  ],
  "mixed_code_spans": [
    {
      "_comment": "# fictional example",
      "id": "span_005_tsotsi",
      "project_id": "proj_fictional_zul_eng",
      "start_token_id": "tok_005_01",
      "end_token_id": "tok_005_06",
      "variety": "tsotsitaal",
      "confidence": 0.5,
      "source": "manual",
      "note": "Fictional Tsotsitaal-flavored example for schema illustration; verify any real analysis with local speakers and project notes.",
      "created_at": "2026-05-27T12:01:00Z"
    }
  ],
  "phonological_features": [
    {
      "_comment": "# fictional example",
      "id": "phon_001_laptop_vowel",
      "token_id": "tok_001_02",
      "feature_type": "vowel_insertion",
      "value": "initial_i_before_english_stem",
      "source": "manual",
      "note": "Fictional example of vowel insertion evidence; not authoritative phonological analysis.",
      "created_at": "2026-05-27T12:02:00Z"
    }
  ],
  "community_reviews": [
    {
      "_comment": "# fictional example",
      "id": "review_001",
      "target_kind": "phonological_feature",
      "target_id": "phon_001_laptop_vowel",
      "reviewer_alias": "PENDING_LOCAL_REVIEW",
      "comment": "Fictional placeholder review showing how a local reviewer might question the vowel-insertion label.",
      "status": "pending",
      "signature_hash": null,
      "created_at": "2026-05-27T12:03:00Z",
      "applied_at": null
    }
  ]
}
```

## 5. Citations

The trigger-link model is designed for candidate contexts inspired by Clyne's
triggering work, not for automatic causal explanation of code-switching
choices (Clyne, 1967, 2003). The mixed-code span model exists because
Tsotsitaal, Iscamtho, Kaaps, and related practices can challenge simple
standard-language CS categories and should be represented without forcing a
single ML/EL theoretical mould (Slabbert & Myers-Scotton, 1997; Hurst, 2008;
McCormick, 2002). Sister-language ambiguity and reviewer governance are
included because South African language labels sit in wider sociolinguistic
and political contexts, not merely in classifier outputs (Mesthrie, 2002,
2008). The project snapshot retains sidecar-friendly arrays so future
LIDES-oriented export can preserve Imbizo-specific evidence while supporting
comparability with international code-switching corpora (Barnett et al.,
2000).
