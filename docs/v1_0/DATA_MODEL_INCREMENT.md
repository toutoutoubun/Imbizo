# v1.0 Deliverable 3 — Data Model Increment

This document defines the additive data model for v1.0 Block A1
Noun-Class Engine, Block A2 Concord Agreement Tracker, and Block B1 4-M Model
Annotation Layer. The schema extends MVP projects without removing or
renaming MVP tables. New features are opt-in, and new token columns are
nullable.

## 1. SQLite Schema Changes

SQLite does not support `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`. The v1.0
migration runner must check `PRAGMA table_info(tokens)` before executing each
`ALTER TABLE` statement below. The `CREATE TABLE` and `CREATE INDEX`
statements use SQLite-supported `IF NOT EXISTS` forms and are safe to re-run.

```sql
PRAGMA foreign_keys = ON;

ALTER TABLE tokens
ADD COLUMN nc_class INTEGER NULL; -- Optional noun-class number suggested or assigned for this token; derived from researcher judgement or local dictionary evidence, not authoritative linguistic fact.

ALTER TABLE tokens
ADD COLUMN nc_prefix TEXT NULL; -- Optional surface prefix associated with the noun-class analysis; provenance is stored in nc_source and project provenance logs.

ALTER TABLE tokens
ADD COLUMN nc_source TEXT NULL; -- Optional source label for noun-class value: manual, suggested-accepted, or suggested-overridden.

ALTER TABLE tokens
ADD COLUMN four_m_type TEXT NULL; -- Optional 4-M morpheme category used for MLF-compatible analysis after Myers-Scotton; NULL means not assessed (Myers-Scotton, 1993; Myers-Scotton, 2002).

ALTER TABLE tokens
ADD COLUMN four_m_source TEXT NULL; -- Optional source label for 4-M category: manual, suggested-accepted, or suggested-overridden.

CREATE TABLE IF NOT EXISTS noun_class_dictionaries (
    id TEXT PRIMARY KEY, -- Stable UUID for this per-project dictionary snapshot.
    language_code TEXT NOT NULL, -- ISO-like language code for the dictionary snapshot, e.g. zul, xho, sot, or tsn.
    dictionary_version TEXT NOT NULL, -- Semver version of the shipped or project-local dictionary used for suggestions.
    schema_version TEXT NOT NULL, -- Semver version of the YAML dictionary schema used to parse this snapshot.
    source_label TEXT NOT NULL, -- Human-readable dictionary source label shown to researchers and exports.
    source_path TEXT NULL, -- Local path of the shipped dictionary or project override; never a URL.
    content_sha256 TEXT NOT NULL, -- SHA-256 hash of the exact dictionary content for reproducibility.
    snapshot_json TEXT NOT NULL, -- JSON copy of the parsed dictionary entries used by this project.
    verified_entry_count INTEGER NOT NULL DEFAULT 0, -- Count of entries marked verified by cited source or community review.
    unverified_entry_count INTEGER NOT NULL DEFAULT 0, -- Count of entries marked verified: false and requiring a note.
    is_project_override INTEGER NOT NULL DEFAULT 0, -- 1 when the snapshot comes from a project-local override rather than the shipped dictionary.
    note TEXT NULL, -- Plain-language provenance note, especially for unverified or community-reviewed material.
    created_at TEXT NOT NULL -- UTC timestamp when this snapshot was stored in the project database.
);

CREATE INDEX IF NOT EXISTS idx_noun_class_dictionaries_language
    ON noun_class_dictionaries(language_code, dictionary_version);

CREATE TABLE IF NOT EXISTS concord_links (
    id TEXT PRIMARY KEY, -- Stable UUID for one proposed or confirmed agreement relation.
    segment_id TEXT NOT NULL REFERENCES segments(id) ON DELETE CASCADE, -- Utterance or clause containing both linked tokens.
    controller_token_id TEXT NOT NULL REFERENCES tokens(id) ON DELETE CASCADE, -- Token interpreted as the agreement controller, often a noun or noun phrase.
    concord_token_id TEXT NOT NULL REFERENCES tokens(id) ON DELETE CASCADE, -- Token carrying the concord form being reviewed.
    concord_type TEXT NOT NULL CHECK (concord_type IN ('SC','OC','AC','PC','RC','DEM')), -- Concord relation type: subject, object, adjectival, possessive, relative, or demonstrative.
    controller_nc_class INTEGER NULL CHECK (controller_nc_class IS NULL OR controller_nc_class BETWEEN 1 AND 23), -- Optional noun class assigned to the controller token.
    expected_form TEXT NULL, -- Optional locally suggested form from dictionary rules; a suggestion, not a correction.
    observed_form TEXT NOT NULL, -- Surface form observed in the transcript.
    agreement_status TEXT NOT NULL CHECK (agreement_status IN ('confirmed','mismatch','uncertain','not_applicable')), -- Researcher-review state for the proposed relation.
    source TEXT NOT NULL CHECK (source IN ('manual','suggested-accepted','suggested-overridden')), -- Provenance category showing whether the researcher entered or reviewed the link.
    confidence REAL NULL CHECK (confidence IS NULL OR (confidence >= 0.0 AND confidence <= 1.0)), -- Optional local suggestion confidence; manual interpretation remains authoritative.
    dictionary_snapshot_id TEXT NULL REFERENCES noun_class_dictionaries(id) ON DELETE SET NULL, -- Dictionary snapshot used to produce the suggestion, if any.
    note TEXT NULL, -- Free-text researcher note about dialect, uncertainty, or local variety.
    created_at TEXT NOT NULL, -- UTC timestamp when this link was created.
    updated_at TEXT NOT NULL -- UTC timestamp when this link was last edited or reviewed.
);

CREATE INDEX IF NOT EXISTS idx_concord_links_segment
    ON concord_links(segment_id);

CREATE INDEX IF NOT EXISTS idx_concord_links_controller
    ON concord_links(controller_token_id);

CREATE INDEX IF NOT EXISTS idx_concord_links_concord
    ON concord_links(concord_token_id);

CREATE INDEX IF NOT EXISTS idx_concord_links_type_status
    ON concord_links(concord_type, agreement_status);

CREATE TABLE IF NOT EXISTS four_m_audit (
    id TEXT PRIMARY KEY, -- Stable UUID for one 4-M audit record.
    segment_id TEXT NOT NULL REFERENCES segments(id) ON DELETE CASCADE, -- Utterance or clause audited for MLF compatibility.
    verdict TEXT NOT NULL CHECK (verdict IN ('compatible','possibly_compatible','inconclusive','tension','not_applicable')), -- Local checker verdict; descriptive support, not theoretical enforcement.
    matrix_language_id TEXT NULL REFERENCES languages(id) ON DELETE SET NULL, -- Optional Matrix Language used for the audit, if the researcher supplied one.
    embedded_language_id TEXT NULL REFERENCES languages(id) ON DELETE SET NULL, -- Optional Embedded Language used for the audit, if the researcher supplied one.
    system_morpheme_count INTEGER NOT NULL DEFAULT 0, -- Count of tokens tagged as early, bridge late, or outsider late system morphemes.
    outsider_late_system_morpheme_count INTEGER NOT NULL DEFAULT 0, -- Count used when checking the System Morpheme Principle (Myers-Scotton, 1993; Myers-Scotton, 2002).
    content_morpheme_switch_count INTEGER NOT NULL DEFAULT 0, -- Count of content-morpheme switches useful for comparison with insertional accounts (Muysken, 2000).
    confirmed_concord_link_count INTEGER NOT NULL DEFAULT 0, -- Count of confirmed concord links used as structural evidence for integration.
    reviewed_concord_link_count INTEGER NOT NULL DEFAULT 0, -- Count of concord links reviewed by the researcher in this utterance.
    integration_score REAL NULL CHECK (integration_score IS NULL OR (integration_score >= 0.0 AND integration_score <= 1.0)), -- Optional confirmed/reviewed concord ratio used as a transparent local summary.
    source TEXT NOT NULL CHECK (source IN ('manual','suggested-accepted','suggested-overridden')), -- Provenance category for the audit verdict.
    checker_version TEXT NOT NULL, -- Local checker version so verdicts remain reproducible.
    explanation TEXT NOT NULL, -- Plain-language explanation shown in the UI and exports.
    created_at TEXT NOT NULL, -- UTC timestamp when this audit was created.
    updated_at TEXT NOT NULL -- UTC timestamp when this audit was last edited or reviewed.
);

CREATE INDEX IF NOT EXISTS idx_four_m_audit_segment
    ON four_m_audit(segment_id);

CREATE INDEX IF NOT EXISTS idx_four_m_audit_verdict
    ON four_m_audit(verdict);
```

## 2. JSON Schema Fragments

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://imbizo-cs.local/schema/v1.0/token.fragment.json",
  "title": "Extended Token",
  "type": "object",
  "required": ["id", "segment_id", "sort_order", "token_text"],
  "properties": {
    "id": {"type": "string"},
    "segment_id": {"type": "string"},
    "sort_order": {"type": "integer", "minimum": 1},
    "token_text": {"type": "string"},
    "normalized_text": {"type": ["string", "null"]},
    "char_start": {"type": ["integer", "null"], "minimum": 0},
    "char_end": {"type": ["integer", "null"], "minimum": 0},
    "external_ref": {"type": "string", "default": ""},
    "nc_class": {"type": ["integer", "null"], "minimum": 1, "maximum": 23},
    "nc_prefix": {"type": ["string", "null"]},
    "nc_source": {"type": ["string", "null"], "enum": ["manual", "suggested-accepted", "suggested-overridden", null]},
    "four_m_type": {
      "type": ["string", "null"],
      "enum": ["content", "early_system", "bridge_late_system", "outsider_late_system", null]
    },
    "four_m_source": {"type": ["string", "null"], "enum": ["manual", "suggested-accepted", "suggested-overridden", null]}
  }
}
```

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://imbizo-cs.local/schema/v1.0/concord-link.fragment.json",
  "title": "ConcordLink",
  "type": "object",
  "required": [
    "id",
    "segment_id",
    "controller_token_id",
    "concord_token_id",
    "concord_type",
    "observed_form",
    "agreement_status",
    "source",
    "created_at",
    "updated_at"
  ],
  "properties": {
    "id": {"type": "string"},
    "segment_id": {"type": "string"},
    "controller_token_id": {"type": "string"},
    "concord_token_id": {"type": "string"},
    "concord_type": {"type": "string", "enum": ["SC", "OC", "AC", "PC", "RC", "DEM"]},
    "controller_nc_class": {"type": ["integer", "null"], "minimum": 1, "maximum": 23},
    "expected_form": {"type": ["string", "null"]},
    "observed_form": {"type": "string"},
    "agreement_status": {"type": "string", "enum": ["confirmed", "mismatch", "uncertain", "not_applicable"]},
    "source": {"type": "string", "enum": ["manual", "suggested-accepted", "suggested-overridden"]},
    "confidence": {"type": ["number", "null"], "minimum": 0.0, "maximum": 1.0},
    "dictionary_snapshot_id": {"type": ["string", "null"]},
    "note": {"type": ["string", "null"]},
    "created_at": {"type": "string", "format": "date-time"},
    "updated_at": {"type": "string", "format": "date-time"}
  }
}
```

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://imbizo-cs.local/schema/v1.0/four-m-audit.fragment.json",
  "title": "FourMAudit",
  "type": "object",
  "required": ["id", "segment_id", "verdict", "source", "checker_version", "explanation", "created_at", "updated_at"],
  "properties": {
    "id": {"type": "string"},
    "segment_id": {"type": "string"},
    "verdict": {"type": "string", "enum": ["compatible", "possibly_compatible", "inconclusive", "tension", "not_applicable"]},
    "matrix_language_id": {"type": ["string", "null"]},
    "embedded_language_id": {"type": ["string", "null"]},
    "system_morpheme_count": {"type": "integer", "minimum": 0},
    "outsider_late_system_morpheme_count": {"type": "integer", "minimum": 0},
    "content_morpheme_switch_count": {"type": "integer", "minimum": 0},
    "confirmed_concord_link_count": {"type": "integer", "minimum": 0},
    "reviewed_concord_link_count": {"type": "integer", "minimum": 0},
    "integration_score": {"type": ["number", "null"], "minimum": 0.0, "maximum": 1.0},
    "source": {"type": "string", "enum": ["manual", "suggested-accepted", "suggested-overridden"]},
    "checker_version": {"type": "string"},
    "explanation": {"type": "string"},
    "created_at": {"type": "string", "format": "date-time"},
    "updated_at": {"type": "string", "format": "date-time"}
  }
}
```

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://imbizo-cs.local/schema/v1.0/project-snapshot.fragment.json",
  "title": "Extended Project Snapshot",
  "type": "object",
  "properties": {
    "schema_version": {"type": "string", "const": "1.0"},
    "project": {"type": "object"},
    "languages": {"type": "array", "items": {"type": "object"}},
    "segments": {"type": "array", "items": {"type": "object"}},
    "tokens": {
      "type": "array",
      "items": {"$ref": "https://imbizo-cs.local/schema/v1.0/token.fragment.json"}
    },
    "annotations": {"type": "array", "items": {"type": "object"}},
    "noun_class_dictionaries": {"type": "array", "items": {"type": "object"}},
    "concord_links": {
      "type": "array",
      "items": {"$ref": "https://imbizo-cs.local/schema/v1.0/concord-link.fragment.json"}
    },
    "four_m_audits": {
      "type": "array",
      "items": {"$ref": "https://imbizo-cs.local/schema/v1.0/four-m-audit.fragment.json"}
    },
    "provenance": {"type": "array", "items": {"type": "object"}}
  }
}
```

## 3. Pydantic v2 Models

```python
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


ReviewSource = Literal["manual", "suggested-accepted", "suggested-overridden"]
ConcordType = Literal["SC", "OC", "AC", "PC", "RC", "DEM"]
FourMType = Literal["content", "early_system", "bridge_late_system", "outsider_late_system"]
AgreementStatus = Literal["confirmed", "mismatch", "uncertain", "not_applicable"]
AuditVerdict = Literal["compatible", "possibly_compatible", "inconclusive", "tension", "not_applicable"]

VALID_REVIEW_SOURCES = {"manual", "suggested-accepted", "suggested-overridden"}
VALID_CONCORD_TYPES = {"SC", "OC", "AC", "PC", "RC", "DEM"}
VALID_FOUR_M_TYPES = {"content", "early_system", "bridge_late_system", "outsider_late_system"}


class ExtendedToken(BaseModel):
    """MVP token plus optional v1.0 noun-class and 4-M fields."""

    id: str = Field(description="Stable token identifier.")
    segment_id: str = Field(description="Parent segment or utterance identifier.")
    sort_order: int = Field(ge=1, description="Token order within the segment.")
    token_text: str = Field(description="Original token text as transcribed by the researcher.")
    normalized_text: str | None = Field(default=None, description="Optional non-destructive normalization.")
    char_start: int | None = Field(default=None, ge=0, description="Optional start character offset.")
    char_end: int | None = Field(default=None, ge=0, description="Optional end character offset.")
    external_ref: str = Field(default="", description="Optional external reference from imported tools.")
    nc_class: int | None = Field(default=None, description="Optional noun-class number from manual review or local suggestion.")
    nc_prefix: str | None = Field(default=None, description="Optional surface noun-class prefix.")
    nc_source: ReviewSource | None = Field(default=None, description="Review source for noun-class value.")
    four_m_type: FourMType | None = Field(default=None, description="Optional 4-M morpheme category.")
    four_m_source: ReviewSource | None = Field(default=None, description="Review source for 4-M value.")

    @field_validator("nc_class")
    @classmethod
    def validate_nc_class(cls, value: int | None) -> int | None:
        """Allow noun classes 1..23 or None; NULL preserves MVP compatibility."""

        if value is not None and value not in set(range(1, 24)):
            raise ValueError("nc_class must be in 1..23 or None.")
        return value

    @field_validator("four_m_type")
    @classmethod
    def validate_four_m_type(cls, value: str | None) -> str | None:
        """Allow only the controlled 4-M vocabulary or None."""

        if value is not None and value not in VALID_FOUR_M_TYPES:
            raise ValueError("four_m_type is outside the v1.0 controlled vocabulary.")
        return value

    @field_validator("nc_source", "four_m_source")
    @classmethod
    def validate_review_source(cls, value: str | None) -> str | None:
        """Allow only the v1.0 review-source vocabulary or None."""

        if value is not None and value not in VALID_REVIEW_SOURCES:
            raise ValueError("source must be manual, suggested-accepted, or suggested-overridden.")
        return value


class NounClassDictionarySnapshot(BaseModel):
    """Per-project snapshot of the noun-class dictionary used for suggestions."""

    id: str = Field(description="Stable dictionary snapshot identifier.")
    language_code: str = Field(description="Language code for the dictionary.")
    dictionary_version: str = Field(description="Semver dictionary version.")
    schema_version: str = Field(description="Semver YAML schema version.")
    source_label: str = Field(description="Human-readable source label.")
    source_path: str | None = Field(default=None, description="Local source path; never a URL.")
    content_sha256: str = Field(description="Hash of exact dictionary content.")
    snapshot_json: str = Field(description="Serialized parsed dictionary snapshot.")
    verified_entry_count: int = Field(ge=0, description="Count of verified entries.")
    unverified_entry_count: int = Field(ge=0, description="Count of entries marked verified: false.")
    is_project_override: bool = Field(default=False, description="Whether this came from a project-local override.")
    note: str | None = Field(default=None, description="Plain-language provenance note.")
    created_at: str = Field(description="UTC creation timestamp.")


class ConcordLink(BaseModel):
    """Reviewed or suggested concord relation between two tokens."""

    id: str = Field(description="Stable concord-link identifier.")
    segment_id: str = Field(description="Segment containing the relation.")
    controller_token_id: str = Field(description="Token interpreted as agreement controller.")
    concord_token_id: str = Field(description="Token carrying the concord form.")
    concord_type: ConcordType = Field(description="Concord type: SC, OC, AC, PC, RC, or DEM.")
    controller_nc_class: int | None = Field(default=None, description="Optional noun class of the controller.")
    expected_form: str | None = Field(default=None, description="Optional suggested concord form.")
    observed_form: str = Field(description="Observed concord form in the transcript.")
    agreement_status: AgreementStatus = Field(description="Researcher review status.")
    source: ReviewSource = Field(description="Manual or reviewed suggestion source.")
    confidence: float | None = Field(default=None, ge=0.0, le=1.0, description="Optional local suggestion confidence.")
    dictionary_snapshot_id: str | None = Field(default=None, description="Dictionary snapshot used, if any.")
    note: str | None = Field(default=None, description="Researcher note.")
    created_at: str = Field(description="UTC creation timestamp.")
    updated_at: str = Field(description="UTC update timestamp.")

    @field_validator("controller_nc_class")
    @classmethod
    def validate_controller_nc_class(cls, value: int | None) -> int | None:
        """Allow noun classes 1..23 or None."""

        if value is not None and value not in set(range(1, 24)):
            raise ValueError("controller_nc_class must be in 1..23 or None.")
        return value

    @field_validator("concord_type")
    @classmethod
    def validate_concord_type(cls, value: str) -> str:
        """Allow only SC, OC, AC, PC, RC, or DEM concord types."""

        if value not in VALID_CONCORD_TYPES:
            raise ValueError("concord_type must be one of SC, OC, AC, PC, RC, DEM.")
        return value

    @field_validator("source")
    @classmethod
    def validate_source(cls, value: str) -> str:
        """Allow only the v1.0 review-source vocabulary."""

        if value not in VALID_REVIEW_SOURCES:
            raise ValueError("source must be manual, suggested-accepted, or suggested-overridden.")
        return value


class FourMAudit(BaseModel):
    """MLF-compatible audit record for one utterance, never an enforced judgement."""

    id: str = Field(description="Stable 4-M audit identifier.")
    segment_id: str = Field(description="Segment audited.")
    verdict: AuditVerdict = Field(description="Descriptive checker verdict.")
    matrix_language_id: str | None = Field(default=None, description="Optional Matrix Language identifier.")
    embedded_language_id: str | None = Field(default=None, description="Optional Embedded Language identifier.")
    system_morpheme_count: int = Field(ge=0, description="Count of system morphemes in the audit.")
    outsider_late_system_morpheme_count: int = Field(ge=0, description="Count of outsider late system morphemes.")
    content_morpheme_switch_count: int = Field(ge=0, description="Count of switched content morphemes.")
    confirmed_concord_link_count: int = Field(ge=0, description="Confirmed concord links used as evidence.")
    reviewed_concord_link_count: int = Field(ge=0, description="Reviewed concord links in this utterance.")
    integration_score: float | None = Field(default=None, ge=0.0, le=1.0, description="Confirmed/reviewed concord ratio.")
    source: ReviewSource = Field(description="Manual or reviewed suggestion source.")
    checker_version: str = Field(description="Local checker version.")
    explanation: str = Field(description="Plain-language explanation.")
    created_at: str = Field(description="UTC creation timestamp.")
    updated_at: str = Field(description="UTC update timestamp.")

    @field_validator("source")
    @classmethod
    def validate_source(cls, value: str) -> str:
        """Allow only the v1.0 review-source vocabulary."""

        if value not in VALID_REVIEW_SOURCES:
            raise ValueError("source must be manual, suggested-accepted, or suggested-overridden.")
        return value


class ProjectSnapshotV10Fragment(BaseModel):
    """v1.0 arrays embedded in a full Imbizo-CS project export."""

    tokens: list[ExtendedToken] = Field(description="MVP tokens with nullable v1.0 fields.")
    noun_class_dictionaries: list[NounClassDictionarySnapshot] = Field(description="Dictionary snapshots used by the project.")
    concord_links: list[ConcordLink] = Field(description="Concord agreement records.")
    four_m_audits: list[FourMAudit] = Field(description="4-M audit records.")
```

The validators and `Literal` types enforce the controlled vocabularies required
for noun class, concord type, 4-M type, and review source. The 4-M categories
are optional because the System Morpheme Principle is a supported analytic
framework, not an imposed one (Myers-Scotton, 1993; Myers-Scotton, 2002).

## 4. Worked Example

All content in this worked example is fictional and is included only to show the
shape of v1.0 records. It is not a lexical, grammatical, or sociolinguistic
authority. The example includes the requested utterance
`Ngithenge i-laptop entsha izolo.` as a fictional isiZulu-English interview
line. The noun-class and concord examples are illustrative of the data model;
researchers must confirm real analyses against their data and sources
(Demuth, 2000; Poulos & Msimang, 1998).

```json
{
  "example_note": "# fictional example: not authoritative linguistic data",
  "dictionary_snapshot": {
    "id": "dict-zul-nc-v1",
    "language_code": "zul",
    "dictionary_version": "1.0.0",
    "schema_version": "1.0.0",
    "source_label": "Imbizo fictional seed snapshot for documentation",
    "source_path": "dictionaries/noun_classes/zul.yaml",
    "content_sha256": "fictional-sha256-for-example-only",
    "snapshot_json": "{\"entries\":[],\"example_note\":\"# fictional example\"}",
    "verified_entry_count": 0,
    "unverified_entry_count": 1,
    "is_project_override": false,
    "note": "All entries in this worked example are fictional; verified: false.",
    "created_at": "2026-05-27T00:00:00Z"
  },
  "utterances": [
    {
      "segment_id": "u1",
      "text": "Ngithenge i-laptop entsha izolo.",
      "translation": "I bought a new laptop yesterday.",
      "example_note": "# fictional example",
      "tokens": [
        {"id": "u1-t1", "segment_id": "u1", "sort_order": 1, "token_text": "Ngithenge", "normalized_text": null, "char_start": 0, "char_end": 8, "external_ref": "", "nc_class": null, "nc_prefix": null, "nc_source": null, "four_m_type": "outsider_late_system", "four_m_source": "suggested-accepted"},
        {"id": "u1-t2", "segment_id": "u1", "sort_order": 2, "token_text": "i-laptop", "normalized_text": null, "char_start": 9, "char_end": 17, "external_ref": "", "nc_class": 9, "nc_prefix": "i-", "nc_source": "manual", "four_m_type": "content", "four_m_source": "manual"},
        {"id": "u1-t3", "segment_id": "u1", "sort_order": 3, "token_text": "entsha", "normalized_text": null, "char_start": 18, "char_end": 24, "external_ref": "", "nc_class": 9, "nc_prefix": "en-", "nc_source": "suggested-accepted", "four_m_type": "early_system", "four_m_source": "suggested-accepted"},
        {"id": "u1-t4", "segment_id": "u1", "sort_order": 4, "token_text": "izolo", "normalized_text": null, "char_start": 25, "char_end": 30, "external_ref": "", "nc_class": null, "nc_prefix": null, "nc_source": null, "four_m_type": "content", "four_m_source": "suggested-accepted"}
      ],
      "concord_links": [
        {"id": "cl-u1-1", "segment_id": "u1", "controller_token_id": "u1-t2", "concord_token_id": "u1-t3", "concord_type": "AC", "controller_nc_class": 9, "expected_form": "en-", "observed_form": "entsha", "agreement_status": "confirmed", "source": "manual", "confidence": 1.0, "dictionary_snapshot_id": "dict-zul-nc-v1", "note": "# fictional example: confirmed link used to compute integration score 1/1 = 1.0", "created_at": "2026-05-27T00:00:00Z", "updated_at": "2026-05-27T00:00:00Z"}
      ],
      "four_m_audit": {"id": "audit-u1", "segment_id": "u1", "verdict": "possibly_compatible", "matrix_language_id": "zul", "embedded_language_id": "eng", "system_morpheme_count": 2, "outsider_late_system_morpheme_count": 1, "content_morpheme_switch_count": 1, "confirmed_concord_link_count": 1, "reviewed_concord_link_count": 1, "integration_score": 1.0, "source": "manual", "checker_version": "v1.0-fictional", "explanation": "# fictional example: English stem is treated as integrated through a confirmed adjectival concord link to entsha.", "created_at": "2026-05-27T00:00:00Z", "updated_at": "2026-05-27T00:00:00Z"}
    },
    {
      "segment_id": "u2",
      "text": "Umuntu u-checker ama-notes manje.",
      "translation": "The person is checking the notes now.",
      "example_note": "# fictional example",
      "tokens": [
        {"id": "u2-t1", "segment_id": "u2", "sort_order": 1, "token_text": "Umuntu", "normalized_text": null, "char_start": 0, "char_end": 6, "external_ref": "", "nc_class": 1, "nc_prefix": "umu-", "nc_source": "suggested-overridden", "four_m_type": "content", "four_m_source": "manual"},
        {"id": "u2-t2", "segment_id": "u2", "sort_order": 2, "token_text": "u-checker", "normalized_text": null, "char_start": 7, "char_end": 16, "external_ref": "", "nc_class": null, "nc_prefix": "u-", "nc_source": null, "four_m_type": "outsider_late_system", "four_m_source": "suggested-accepted"},
        {"id": "u2-t3", "segment_id": "u2", "sort_order": 3, "token_text": "ama-notes", "normalized_text": null, "char_start": 17, "char_end": 26, "external_ref": "", "nc_class": 6, "nc_prefix": "ama-", "nc_source": "manual", "four_m_type": "content", "four_m_source": "manual"},
        {"id": "u2-t4", "segment_id": "u2", "sort_order": 4, "token_text": "manje", "normalized_text": null, "char_start": 27, "char_end": 32, "external_ref": "", "nc_class": null, "nc_prefix": null, "nc_source": null, "four_m_type": "content", "four_m_source": "suggested-accepted"}
      ],
      "concord_links": [
        {"id": "cl-u2-1", "segment_id": "u2", "controller_token_id": "u2-t1", "concord_token_id": "u2-t2", "concord_type": "SC", "controller_nc_class": 1, "expected_form": "u-", "observed_form": "u-", "agreement_status": "confirmed", "source": "manual", "confidence": 0.9, "dictionary_snapshot_id": "dict-zul-nc-v1", "note": "# fictional example", "created_at": "2026-05-27T00:00:00Z", "updated_at": "2026-05-27T00:00:00Z"}
      ],
      "four_m_audit": {"id": "audit-u2", "segment_id": "u2", "verdict": "inconclusive", "matrix_language_id": "zul", "embedded_language_id": "eng", "system_morpheme_count": 1, "outsider_late_system_morpheme_count": 1, "content_morpheme_switch_count": 2, "confirmed_concord_link_count": 1, "reviewed_concord_link_count": 1, "integration_score": 1.0, "source": "suggested-overridden", "checker_version": "v1.0-fictional", "explanation": "# fictional example: researcher retains uncertainty because mixed urban forms may not follow standard-language expectations.", "created_at": "2026-05-27T00:00:00Z", "updated_at": "2026-05-27T00:00:00Z"}
    },
    {
      "segment_id": "u3",
      "text": "Le meeting ibalulekile namhlanje.",
      "translation": "This meeting is important today.",
      "example_note": "# fictional example",
      "tokens": [
        {"id": "u3-t1", "segment_id": "u3", "sort_order": 1, "token_text": "Le", "normalized_text": null, "char_start": 0, "char_end": 2, "external_ref": "", "nc_class": 9, "nc_prefix": "le", "nc_source": "suggested-accepted", "four_m_type": "early_system", "four_m_source": "suggested-accepted"},
        {"id": "u3-t2", "segment_id": "u3", "sort_order": 2, "token_text": "meeting", "normalized_text": null, "char_start": 3, "char_end": 10, "external_ref": "", "nc_class": 9, "nc_prefix": null, "nc_source": "manual", "four_m_type": "content", "four_m_source": "manual"},
        {"id": "u3-t3", "segment_id": "u3", "sort_order": 3, "token_text": "ibalulekile", "normalized_text": null, "char_start": 11, "char_end": 22, "external_ref": "", "nc_class": 9, "nc_prefix": "i-", "nc_source": "suggested-accepted", "four_m_type": "outsider_late_system", "four_m_source": "suggested-accepted"},
        {"id": "u3-t4", "segment_id": "u3", "sort_order": 4, "token_text": "namhlanje", "normalized_text": null, "char_start": 23, "char_end": 32, "external_ref": "", "nc_class": null, "nc_prefix": null, "nc_source": null, "four_m_type": "content", "four_m_source": "suggested-accepted"}
      ],
      "concord_links": [
        {"id": "cl-u3-1", "segment_id": "u3", "controller_token_id": "u3-t2", "concord_token_id": "u3-t1", "concord_type": "DEM", "controller_nc_class": 9, "expected_form": "le", "observed_form": "Le", "agreement_status": "confirmed", "source": "manual", "confidence": 0.8, "dictionary_snapshot_id": "dict-zul-nc-v1", "note": "# fictional example", "created_at": "2026-05-27T00:00:00Z", "updated_at": "2026-05-27T00:00:00Z"}
      ],
      "four_m_audit": {"id": "audit-u3", "segment_id": "u3", "verdict": "possibly_compatible", "matrix_language_id": "zul", "embedded_language_id": "eng", "system_morpheme_count": 2, "outsider_late_system_morpheme_count": 1, "content_morpheme_switch_count": 1, "confirmed_concord_link_count": 1, "reviewed_concord_link_count": 1, "integration_score": 1.0, "source": "manual", "checker_version": "v1.0-fictional", "explanation": "# fictional example: demonstrative agreement is treated as structural evidence but not proof of Matrix Language.", "created_at": "2026-05-27T00:00:00Z", "updated_at": "2026-05-27T00:00:00Z"}
    },
    {
      "segment_id": "u4",
      "text": "Abafana ba-printa forms ekuseni.",
      "translation": "The boys printed forms in the morning.",
      "example_note": "# fictional example",
      "tokens": [
        {"id": "u4-t1", "segment_id": "u4", "sort_order": 1, "token_text": "Abafana", "normalized_text": null, "char_start": 0, "char_end": 7, "external_ref": "", "nc_class": 2, "nc_prefix": "aba-", "nc_source": "manual", "four_m_type": "content", "four_m_source": "manual"},
        {"id": "u4-t2", "segment_id": "u4", "sort_order": 2, "token_text": "ba-printa", "normalized_text": null, "char_start": 8, "char_end": 17, "external_ref": "", "nc_class": 2, "nc_prefix": "ba-", "nc_source": "suggested-accepted", "four_m_type": "outsider_late_system", "four_m_source": "suggested-accepted"},
        {"id": "u4-t3", "segment_id": "u4", "sort_order": 3, "token_text": "forms", "normalized_text": null, "char_start": 18, "char_end": 23, "external_ref": "", "nc_class": null, "nc_prefix": null, "nc_source": null, "four_m_type": "content", "four_m_source": "manual"},
        {"id": "u4-t4", "segment_id": "u4", "sort_order": 4, "token_text": "ekuseni", "normalized_text": null, "char_start": 24, "char_end": 31, "external_ref": "", "nc_class": null, "nc_prefix": null, "nc_source": null, "four_m_type": "content", "four_m_source": "suggested-accepted"}
      ],
      "concord_links": [
        {"id": "cl-u4-1", "segment_id": "u4", "controller_token_id": "u4-t1", "concord_token_id": "u4-t2", "concord_type": "SC", "controller_nc_class": 2, "expected_form": "ba-", "observed_form": "ba-", "agreement_status": "confirmed", "source": "manual", "confidence": 0.9, "dictionary_snapshot_id": "dict-zul-nc-v1", "note": "# fictional example", "created_at": "2026-05-27T00:00:00Z", "updated_at": "2026-05-27T00:00:00Z"}
      ],
      "four_m_audit": {"id": "audit-u4", "segment_id": "u4", "verdict": "possibly_compatible", "matrix_language_id": "zul", "embedded_language_id": "eng", "system_morpheme_count": 1, "outsider_late_system_morpheme_count": 1, "content_morpheme_switch_count": 2, "confirmed_concord_link_count": 1, "reviewed_concord_link_count": 1, "integration_score": 1.0, "source": "manual", "checker_version": "v1.0-fictional", "explanation": "# fictional example: subject concord is confirmed, while English lexical material remains researcher-interpreted.", "created_at": "2026-05-27T00:00:00Z", "updated_at": "2026-05-27T00:00:00Z"}
    },
    {
      "segment_id": "u5",
      "text": "Ngibone ama-student amasha e-campus.",
      "translation": "I saw new students on campus.",
      "example_note": "# fictional example",
      "tokens": [
        {"id": "u5-t1", "segment_id": "u5", "sort_order": 1, "token_text": "Ngibone", "normalized_text": null, "char_start": 0, "char_end": 7, "external_ref": "", "nc_class": null, "nc_prefix": null, "nc_source": null, "four_m_type": "outsider_late_system", "four_m_source": "suggested-accepted"},
        {"id": "u5-t2", "segment_id": "u5", "sort_order": 2, "token_text": "ama-student", "normalized_text": null, "char_start": 8, "char_end": 19, "external_ref": "", "nc_class": 6, "nc_prefix": "ama-", "nc_source": "manual", "four_m_type": "content", "four_m_source": "manual"},
        {"id": "u5-t3", "segment_id": "u5", "sort_order": 3, "token_text": "amasha", "normalized_text": null, "char_start": 20, "char_end": 26, "external_ref": "", "nc_class": 6, "nc_prefix": "ama-", "nc_source": "suggested-accepted", "four_m_type": "early_system", "four_m_source": "suggested-accepted"},
        {"id": "u5-t4", "segment_id": "u5", "sort_order": 4, "token_text": "e-campus", "normalized_text": null, "char_start": 27, "char_end": 35, "external_ref": "", "nc_class": null, "nc_prefix": "e-", "nc_source": null, "four_m_type": "early_system", "four_m_source": "suggested-overridden"}
      ],
      "concord_links": [
        {"id": "cl-u5-1", "segment_id": "u5", "controller_token_id": "u5-t2", "concord_token_id": "u5-t3", "concord_type": "AC", "controller_nc_class": 6, "expected_form": "ama-", "observed_form": "amasha", "agreement_status": "confirmed", "source": "manual", "confidence": 1.0, "dictionary_snapshot_id": "dict-zul-nc-v1", "note": "# fictional example", "created_at": "2026-05-27T00:00:00Z", "updated_at": "2026-05-27T00:00:00Z"}
      ],
      "four_m_audit": {"id": "audit-u5", "segment_id": "u5", "verdict": "tension", "matrix_language_id": "zul", "embedded_language_id": "eng", "system_morpheme_count": 3, "outsider_late_system_morpheme_count": 1, "content_morpheme_switch_count": 2, "confirmed_concord_link_count": 1, "reviewed_concord_link_count": 1, "integration_score": 1.0, "source": "suggested-overridden", "checker_version": "v1.0-fictional", "explanation": "# fictional example: researcher marked tension because mixed locative material should not be reduced to a standard-language rule.", "created_at": "2026-05-27T00:00:00Z", "updated_at": "2026-05-27T00:00:00Z"}
    }
  ]
}
```

## 5. Citations

The noun-class fields support analysis of Bantu noun-class and agreement
systems, with isiZulu treated here as a supported but not automatically settled
case (Demuth, 2000; Poulos & Msimang, 1998). The 4-M fields support, but do not
enforce, Matrix Language Frame analysis and the System Morpheme Principle
(Myers-Scotton, 1993; Myers-Scotton, 2002). Integration and insertional
interpretations remain available for comparison with Muysken's typology
(Muysken, 2000).
