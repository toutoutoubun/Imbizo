# Deliverable 3: Data Model

This document defines the MVP data model for Imbizo-CS Workbench:

1. SQLite schema for `project.sqlite`.
2. JSON Schema for full local project export.
3. Internal Python dataclass model shapes.

The model is designed for local-first research work. It keeps raw imports,
automatic suggestions, manual scholarly decisions, and provenance distinct.
Manual annotations are authoritative; automatic labels are always editable and
auditable.

## Data Model Rules

- One research project uses one local SQLite database: `project.sqlite`.
- The project folder stores plain files for media, transcripts, exports,
  dictionaries, logs, and caches.
- All paths stored in SQLite are relative to the project folder unless a field
  explicitly says otherwise.
- Imported source files are copied into the project folder before parsing.
- Automatic decisions use `source = 'auto'` and must have provenance.
- Manual decisions use `source = 'manual'` and override automatic suggestions.
- No table should require a cloud account, API key, telemetry identity, or
  network resource.
- Unknown or ambiguous linguistic data must be represented explicitly rather
  than silently dropped.

## Identifier Policy

The MVP uses text UUIDs for stable object identity. This makes JSON export,
round-trip import, and future merge tooling simpler than integer-only IDs.

Timestamps are ISO 8601 UTC strings, for example `2026-05-27T10:15:30Z`.

## SQLite Schema

```sql
PRAGMA foreign_keys = ON;

CREATE TABLE schema_migrations (
    version INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    applied_at TEXT NOT NULL
);

CREATE TABLE project_metadata (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    project_uuid TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    subtitle TEXT NOT NULL DEFAULT '',
    researcher TEXT NOT NULL DEFAULT '',
    location TEXT NOT NULL DEFAULT '',
    project_date TEXT NOT NULL DEFAULT '',
    participants_summary TEXT NOT NULL DEFAULT '',
    expected_languages_summary TEXT NOT NULL DEFAULT '',
    ethics_notes TEXT NOT NULL DEFAULT '',
    app_version TEXT NOT NULL DEFAULT '',
    schema_version INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE project_settings (
    key TEXT PRIMARY KEY,
    value_json TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE languages (
    id TEXT PRIMARY KEY,
    code TEXT NOT NULL,
    name TEXT NOT NULL,
    autonym TEXT NOT NULL DEFAULT '',
    category TEXT NOT NULL DEFAULT 'language'
        CHECK (category IN (
            'language',
            'unknown',
            'mixed',
            'borrowing',
            'proper_noun',
            'user_defined'
        )),
    color_hex TEXT NOT NULL DEFAULT '#808080',
    is_expected INTEGER NOT NULL DEFAULT 0 CHECK (is_expected IN (0, 1)),
    is_user_defined INTEGER NOT NULL DEFAULT 0 CHECK (is_user_defined IN (0, 1)),
    sort_order INTEGER NOT NULL DEFAULT 0,
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (code)
);

CREATE TABLE participants (
    id TEXT PRIMARY KEY,
    participant_code TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL DEFAULT '',
    role TEXT NOT NULL DEFAULT '',
    demographics_json TEXT NOT NULL DEFAULT '{}',
    consent_status TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE speakers (
    id TEXT PRIMARY KEY,
    participant_id TEXT NULL REFERENCES participants(id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    label TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE scenes (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    start_ms INTEGER NULL CHECK (start_ms IS NULL OR start_ms >= 0),
    end_ms INTEGER NULL CHECK (end_ms IS NULL OR end_ms >= 0),
    sort_order INTEGER NOT NULL DEFAULT 0,
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CHECK (end_ms IS NULL OR start_ms IS NULL OR end_ms >= start_ms)
);

CREATE TABLE import_batches (
    id TEXT PRIMARY KEY,
    source_label TEXT NOT NULL,
    original_path TEXT NOT NULL DEFAULT '',
    copied_path TEXT NOT NULL DEFAULT '',
    importer_name TEXT NOT NULL,
    importer_version TEXT NOT NULL DEFAULT '',
    source_sha256 TEXT NOT NULL DEFAULT '',
    import_report_json TEXT NOT NULL DEFAULT '{}',
    imported_at TEXT NOT NULL
);

CREATE TABLE media_assets (
    id TEXT PRIMARY KEY,
    import_batch_id TEXT NULL REFERENCES import_batches(id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    media_type TEXT NOT NULL CHECK (media_type IN ('audio', 'video')),
    relative_path TEXT NOT NULL,
    original_filename TEXT NOT NULL DEFAULT '',
    file_format TEXT NOT NULL DEFAULT '',
    mime_type TEXT NOT NULL DEFAULT '',
    duration_ms INTEGER NULL CHECK (duration_ms IS NULL OR duration_ms >= 0),
    sample_rate_hz INTEGER NULL CHECK (sample_rate_hz IS NULL OR sample_rate_hz > 0),
    channels INTEGER NULL CHECK (channels IS NULL OR channels > 0),
    sha256 TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (relative_path)
);

CREATE TABLE transcript_documents (
    id TEXT PRIMARY KEY,
    import_batch_id TEXT NULL REFERENCES import_batches(id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    media_asset_id TEXT NULL REFERENCES media_assets(id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    name TEXT NOT NULL,
    source_format TEXT NOT NULL CHECK (source_format IN (
        'txt',
        'csv',
        'tsv',
        'json',
        'eaf',
        'textgrid',
        'xlsx',
        'ods',
        'manual'
    )),
    relative_path TEXT NOT NULL DEFAULT '',
    original_filename TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE segments (
    id TEXT PRIMARY KEY,
    transcript_document_id TEXT NOT NULL REFERENCES transcript_documents(id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    media_asset_id TEXT NULL REFERENCES media_assets(id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    parent_segment_id TEXT NULL REFERENCES segments(id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    speaker_id TEXT NULL REFERENCES speakers(id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    scene_id TEXT NULL REFERENCES scenes(id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    segment_level TEXT NOT NULL CHECK (segment_level IN (
        'utterance',
        'clause_phrase'
    )),
    sort_order INTEGER NOT NULL,
    start_ms INTEGER NULL CHECK (start_ms IS NULL OR start_ms >= 0),
    end_ms INTEGER NULL CHECK (end_ms IS NULL OR end_ms >= 0),
    text_original TEXT NOT NULL,
    text_normalized TEXT NULL,
    external_ref TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CHECK (end_ms IS NULL OR start_ms IS NULL OR end_ms >= start_ms)
);

CREATE INDEX idx_segments_document_order
    ON segments(transcript_document_id, sort_order);

CREATE INDEX idx_segments_media_time
    ON segments(media_asset_id, start_ms, end_ms);

CREATE TABLE tokens (
    id TEXT PRIMARY KEY,
    segment_id TEXT NOT NULL REFERENCES segments(id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    sort_order INTEGER NOT NULL,
    token_text TEXT NOT NULL,
    normalized_text TEXT NULL,
    char_start INTEGER NULL CHECK (char_start IS NULL OR char_start >= 0),
    char_end INTEGER NULL CHECK (char_end IS NULL OR char_end >= 0),
    external_ref TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (segment_id, sort_order),
    CHECK (char_end IS NULL OR char_start IS NULL OR char_end >= char_start)
);

CREATE INDEX idx_tokens_segment_order
    ON tokens(segment_id, sort_order);

CREATE TABLE annotations (
    id TEXT PRIMARY KEY,
    token_id TEXT NULL REFERENCES tokens(id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    segment_id TEXT NULL REFERENCES segments(id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    source TEXT NOT NULL CHECK (source IN ('manual', 'auto', 'imported')),
    status TEXT NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'rejected', 'superseded')),
    language_id TEXT NULL REFERENCES languages(id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    matrix_language_id TEXT NULL REFERENCES languages(id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    embedded_language_id TEXT NULL REFERENCES languages(id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    switch_type TEXT NULL CHECK (
        switch_type IS NULL OR switch_type IN (
            'intra_sentential',
            'inter_sentential',
            'extra_sentential'
        )
    ),
    linguistic_status TEXT NULL CHECK (
        linguistic_status IS NULL OR linguistic_status IN (
            'borrowing',
            'insertion',
            'alternation'
        )
    ),
    trigger_text TEXT NOT NULL DEFAULT '',
    direction_from_language_id TEXT NULL REFERENCES languages(id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    direction_to_language_id TEXT NULL REFERENCES languages(id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    researcher_confidence INTEGER NULL CHECK (
        researcher_confidence IS NULL
        OR researcher_confidence BETWEEN 1 AND 5
    ),
    auto_confidence REAL NULL CHECK (
        auto_confidence IS NULL
        OR (auto_confidence >= 0.0 AND auto_confidence <= 1.0)
    ),
    memo TEXT NOT NULL DEFAULT '',
    created_by TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CHECK (
        (token_id IS NOT NULL AND segment_id IS NULL)
        OR (token_id IS NULL AND segment_id IS NOT NULL)
    )
);

CREATE INDEX idx_annotations_token
    ON annotations(token_id, status, source);

CREATE INDEX idx_annotations_segment
    ON annotations(segment_id, status, source);

CREATE INDEX idx_annotations_language
    ON annotations(language_id);

CREATE UNIQUE INDEX idx_one_active_manual_token_annotation
    ON annotations(token_id)
    WHERE token_id IS NOT NULL
      AND source = 'manual'
      AND status = 'active';

CREATE UNIQUE INDEX idx_one_active_manual_segment_annotation
    ON annotations(segment_id)
    WHERE segment_id IS NOT NULL
      AND source = 'manual'
      AND status = 'active';

CREATE TABLE tags (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    color_hex TEXT NOT NULL DEFAULT '#808080',
    description TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE annotation_tags (
    annotation_id TEXT NOT NULL REFERENCES annotations(id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    tag_id TEXT NOT NULL REFERENCES tags(id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    PRIMARY KEY (annotation_id, tag_id)
);

CREATE TABLE morpheme_dictionary_entries (
    id TEXT PRIMARY KEY,
    language_id TEXT NOT NULL REFERENCES languages(id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    surface TEXT NOT NULL,
    category TEXT NOT NULL CHECK (category IN (
        'prefix',
        'root',
        'suffix',
        'negation',
        'tense_aspect',
        'agreement',
        'other'
    )),
    gloss TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT '',
    source TEXT NOT NULL DEFAULT 'default'
        CHECK (source IN ('default', 'user')),
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (language_id, surface, category, gloss)
);

CREATE TABLE morpheme_splits (
    id TEXT PRIMARY KEY,
    token_id TEXT NOT NULL REFERENCES tokens(id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    source TEXT NOT NULL CHECK (source IN ('manual', 'suggestion', 'imported')),
    status TEXT NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'historical', 'rejected')),
    split_text TEXT NOT NULL,
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX idx_morpheme_splits_token
    ON morpheme_splits(token_id, status, source);

CREATE TABLE morphemes (
    id TEXT PRIMARY KEY,
    split_id TEXT NOT NULL REFERENCES morpheme_splits(id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    sort_order INTEGER NOT NULL,
    surface TEXT NOT NULL,
    gloss TEXT NOT NULL DEFAULT '',
    category TEXT NOT NULL DEFAULT 'other',
    language_id TEXT NULL REFERENCES languages(id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    dictionary_entry_id TEXT NULL REFERENCES morpheme_dictionary_entries(id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    UNIQUE (split_id, sort_order)
);

CREATE TABLE lid_runs (
    id TEXT PRIMARY KEY,
    provider_name TEXT NOT NULL,
    provider_version TEXT NOT NULL DEFAULT '',
    layer TEXT NOT NULL CHECK (layer IN ('layer1_baseline', 'layer2_afrolid', 'layer3_masklid')),
    parameters_json TEXT NOT NULL DEFAULT '{}',
    status TEXT NOT NULL CHECK (status IN ('running', 'completed', 'failed', 'cancelled')),
    started_at TEXT NOT NULL,
    finished_at TEXT NULL,
    error_message TEXT NOT NULL DEFAULT ''
);

CREATE TABLE lid_suggestions (
    id TEXT PRIMARY KEY,
    lid_run_id TEXT NOT NULL REFERENCES lid_runs(id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    token_id TEXT NULL REFERENCES tokens(id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    segment_id TEXT NULL REFERENCES segments(id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    language_id TEXT NULL REFERENCES languages(id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    layer TEXT NOT NULL CHECK (layer IN ('layer1_baseline', 'layer2_afrolid', 'layer3_masklid')),
    rank INTEGER NOT NULL DEFAULT 1 CHECK (rank > 0),
    confidence REAL NULL CHECK (
        confidence IS NULL
        OR (confidence >= 0.0 AND confidence <= 1.0)
    ),
    evidence_json TEXT NOT NULL DEFAULT '{}',
    accepted_annotation_id TEXT NULL REFERENCES annotations(id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    created_at TEXT NOT NULL,
    CHECK (
        (token_id IS NOT NULL AND segment_id IS NULL)
        OR (token_id IS NULL AND segment_id IS NOT NULL)
    )
);

CREATE INDEX idx_lid_suggestions_token
    ON lid_suggestions(token_id, layer, rank);

CREATE INDEX idx_lid_suggestions_segment
    ON lid_suggestions(segment_id, layer, rank);

CREATE TABLE provenance_records (
    id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL CHECK (event_type IN (
        'import',
        'auto_label',
        'manual_create',
        'manual_update',
        'manual_reject',
        'bulk_edit',
        'morpheme_split',
        'metric_run',
        'export',
        'error'
    )),
    actor_type TEXT NOT NULL CHECK (actor_type IN (
        'researcher',
        'system',
        'importer',
        'lid_layer',
        'metric',
        'exporter'
    )),
    actor_name TEXT NOT NULL DEFAULT '',
    target_table TEXT NOT NULL DEFAULT '',
    target_id TEXT NOT NULL DEFAULT '',
    related_table TEXT NOT NULL DEFAULT '',
    related_id TEXT NOT NULL DEFAULT '',
    tool_name TEXT NOT NULL DEFAULT '',
    tool_version TEXT NOT NULL DEFAULT '',
    confidence REAL NULL CHECK (
        confidence IS NULL
        OR (confidence >= 0.0 AND confidence <= 1.0)
    ),
    message TEXT NOT NULL DEFAULT '',
    payload_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);

CREATE INDEX idx_provenance_target
    ON provenance_records(target_table, target_id, created_at);

CREATE TABLE metric_runs (
    id TEXT PRIMARY KEY,
    run_name TEXT NOT NULL DEFAULT '',
    formula_version TEXT NOT NULL,
    input_filter_json TEXT NOT NULL DEFAULT '{}',
    status TEXT NOT NULL CHECK (status IN ('running', 'completed', 'failed', 'cancelled')),
    started_at TEXT NOT NULL,
    finished_at TEXT NULL,
    error_message TEXT NOT NULL DEFAULT ''
);

CREATE TABLE metric_results (
    id TEXT PRIMARY KEY,
    metric_run_id TEXT NOT NULL REFERENCES metric_runs(id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    metric_name TEXT NOT NULL CHECK (metric_name IN (
        'language_proportion',
        'switch_count',
        'switch_density',
        'dominant_language',
        'm_index',
        'i_index',
        'burstiness',
        'trigger_cooccurrence',
        'kwic'
    )),
    scope_type TEXT NOT NULL CHECK (scope_type IN (
        'project',
        'speaker',
        'scene',
        'segment',
        'custom_filter'
    )),
    scope_id TEXT NOT NULL DEFAULT '',
    value_json TEXT NOT NULL,
    input_count INTEGER NOT NULL DEFAULT 0 CHECK (input_count >= 0),
    created_at TEXT NOT NULL
);

CREATE INDEX idx_metric_results_name_scope
    ON metric_results(metric_name, scope_type, scope_id);

CREATE TABLE exports (
    id TEXT PRIMARY KEY,
    export_format TEXT NOT NULL CHECK (export_format IN (
        'csv',
        'xlsx',
        'json',
        'eaf',
        'textgrid',
        'html',
        'pdf',
        'quotation'
    )),
    relative_path TEXT NOT NULL,
    options_json TEXT NOT NULL DEFAULT '{}',
    sha256 TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);

CREATE TABLE edit_log (
    id TEXT PRIMARY KEY,
    action_type TEXT NOT NULL CHECK (action_type IN (
        'create',
        'update',
        'delete',
        'bulk_update'
    )),
    table_name TEXT NOT NULL,
    row_id TEXT NOT NULL,
    before_json TEXT NOT NULL DEFAULT '{}',
    after_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);
```

## Default Language Rows

Every new project should create language rows for the mandatory language set
plus special annotation labels. Color values are defaults only and must be
editable by the researcher.

```sql
INSERT INTO languages (
    id, code, name, autonym, category, color_hex,
    is_expected, is_user_defined, sort_order, notes, created_at, updated_at
) VALUES
    ('lang-eng', 'eng', 'English', 'English', 'language', '#2F6BFF', 1, 0, 10, '', :now, :now),
    ('lang-afr', 'afr', 'Afrikaans', 'Afrikaans', 'language', '#E07A2F', 1, 0, 20, '', :now, :now),
    ('lang-zul', 'zul', 'isiZulu', 'isiZulu', 'language', '#1F9D55', 1, 0, 30, '', :now, :now),
    ('lang-xho', 'xho', 'isiXhosa', 'isiXhosa', 'language', '#8E44AD', 1, 0, 40, '', :now, :now),
    ('lang-sot', 'sot', 'Sesotho', 'Sesotho', 'language', '#C0392B', 1, 0, 50, '', :now, :now),
    ('lang-tsn', 'tsn', 'Setswana', 'Setswana', 'language', '#008B8B', 1, 0, 60, '', :now, :now),
    ('lang-und', 'und', 'Unknown', 'Unknown', 'unknown', '#808080', 0, 0, 900, '', :now, :now),
    ('lang-mixed', 'mixed', 'Mixed', 'Mixed', 'mixed', '#6C757D', 0, 0, 910, '', :now, :now),
    ('lang-borrowing', 'borrowing', 'Borrowing', 'Borrowing', 'borrowing', '#7A5C00', 0, 0, 920, '', :now, :now),
    ('lang-proper-noun', 'proper_noun', 'Proper noun', 'Proper noun', 'proper_noun', '#555555', 0, 0, 930, '', :now, :now);
```

Post-MVP languages such as Sepedi, siSwati, Xitsonga, Tshivenda, and
isiNdebele should be normal `languages` rows. Non-standard varieties such as
Tsotsitaal, Iscamtho, and Kaaps should use `category = 'user_defined'`.

## Effective Annotation Rule

For a token or segment, the effective annotation is resolved in this order:

1. Most recent active manual annotation.
2. Most recent active imported annotation.
3. Highest-ranked active auto suggestion accepted into `annotations`.
4. No annotation.

Automatic suggestions in `lid_suggestions` do not become effective until they
are written to `annotations` or accepted by the researcher.

## JSON Export Schema

The JSON export is a full project snapshot for local archiving or migration. It
must contain enough data to recreate `project.sqlite` and preserve references to
plain files inside the exported project package.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://local.imbizo/schema/project-export.schema.json",
  "title": "Imbizo-CS Workbench Project Export",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema_version",
    "exported_at",
    "application",
    "project",
    "languages",
    "participants",
    "speakers",
    "scenes",
    "media_assets",
    "transcript_documents",
    "segments",
    "tokens",
    "annotations",
    "tags",
    "morphology",
    "lid",
    "provenance",
    "metrics",
    "exports",
    "files"
  ],
  "properties": {
    "schema_version": {
      "type": "integer",
      "minimum": 1
    },
    "exported_at": {
      "type": "string",
      "format": "date-time"
    },
    "application": {
      "type": "object",
      "additionalProperties": false,
      "required": ["name", "version"],
      "properties": {
        "name": {"type": "string", "const": "Imbizo-CS Workbench"},
        "version": {"type": "string"}
      }
    },
    "project": {"$ref": "#/$defs/project"},
    "languages": {
      "type": "array",
      "items": {"$ref": "#/$defs/language"}
    },
    "participants": {
      "type": "array",
      "items": {"$ref": "#/$defs/participant"}
    },
    "speakers": {
      "type": "array",
      "items": {"$ref": "#/$defs/speaker"}
    },
    "scenes": {
      "type": "array",
      "items": {"$ref": "#/$defs/scene"}
    },
    "media_assets": {
      "type": "array",
      "items": {"$ref": "#/$defs/media_asset"}
    },
    "transcript_documents": {
      "type": "array",
      "items": {"$ref": "#/$defs/transcript_document"}
    },
    "segments": {
      "type": "array",
      "items": {"$ref": "#/$defs/segment"}
    },
    "tokens": {
      "type": "array",
      "items": {"$ref": "#/$defs/token"}
    },
    "annotations": {
      "type": "array",
      "items": {"$ref": "#/$defs/annotation"}
    },
    "tags": {
      "type": "array",
      "items": {"$ref": "#/$defs/tag"}
    },
    "morphology": {
      "type": "object",
      "additionalProperties": false,
      "required": ["dictionary_entries", "splits"],
      "properties": {
        "dictionary_entries": {
          "type": "array",
          "items": {"$ref": "#/$defs/morpheme_dictionary_entry"}
        },
        "splits": {
          "type": "array",
          "items": {"$ref": "#/$defs/morpheme_split"}
        }
      }
    },
    "lid": {
      "type": "object",
      "additionalProperties": false,
      "required": ["runs", "suggestions"],
      "properties": {
        "runs": {
          "type": "array",
          "items": {"$ref": "#/$defs/lid_run"}
        },
        "suggestions": {
          "type": "array",
          "items": {"$ref": "#/$defs/lid_suggestion"}
        }
      }
    },
    "provenance": {
      "type": "array",
      "items": {"$ref": "#/$defs/provenance_record"}
    },
    "metrics": {
      "type": "object",
      "additionalProperties": false,
      "required": ["runs", "results"],
      "properties": {
        "runs": {
          "type": "array",
          "items": {"$ref": "#/$defs/metric_run"}
        },
        "results": {
          "type": "array",
          "items": {"$ref": "#/$defs/metric_result"}
        }
      }
    },
    "exports": {
      "type": "array",
      "items": {"$ref": "#/$defs/export_record"}
    },
    "files": {
      "type": "array",
      "items": {"$ref": "#/$defs/file_record"}
    }
  },
  "$defs": {
    "uuid": {
      "type": "string",
      "minLength": 1
    },
    "timestamp": {
      "type": "string",
      "format": "date-time"
    },
    "nullable_string": {
      "type": ["string", "null"]
    },
    "nullable_integer": {
      "type": ["integer", "null"]
    },
    "nullable_number": {
      "type": ["number", "null"]
    },
    "json_object": {
      "type": "object",
      "additionalProperties": true
    },
    "project": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "project_uuid",
        "title",
        "subtitle",
        "researcher",
        "location",
        "project_date",
        "participants_summary",
        "expected_languages_summary",
        "ethics_notes",
        "created_at",
        "updated_at"
      ],
      "properties": {
        "project_uuid": {"$ref": "#/$defs/uuid"},
        "title": {"type": "string"},
        "subtitle": {"type": "string"},
        "researcher": {"type": "string"},
        "location": {"type": "string"},
        "project_date": {"type": "string"},
        "participants_summary": {"type": "string"},
        "expected_languages_summary": {"type": "string"},
        "ethics_notes": {"type": "string"},
        "settings": {"$ref": "#/$defs/json_object"},
        "created_at": {"$ref": "#/$defs/timestamp"},
        "updated_at": {"$ref": "#/$defs/timestamp"}
      }
    },
    "language": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "id",
        "code",
        "name",
        "autonym",
        "category",
        "color_hex",
        "is_expected",
        "is_user_defined",
        "sort_order"
      ],
      "properties": {
        "id": {"$ref": "#/$defs/uuid"},
        "code": {"type": "string"},
        "name": {"type": "string"},
        "autonym": {"type": "string"},
        "category": {
          "type": "string",
          "enum": ["language", "unknown", "mixed", "borrowing", "proper_noun", "user_defined"]
        },
        "color_hex": {"type": "string", "pattern": "^#[0-9A-Fa-f]{6}$"},
        "is_expected": {"type": "boolean"},
        "is_user_defined": {"type": "boolean"},
        "sort_order": {"type": "integer"},
        "notes": {"type": "string"}
      }
    },
    "participant": {
      "type": "object",
      "additionalProperties": false,
      "required": ["id", "participant_code"],
      "properties": {
        "id": {"$ref": "#/$defs/uuid"},
        "participant_code": {"type": "string"},
        "display_name": {"type": "string"},
        "role": {"type": "string"},
        "demographics": {"$ref": "#/$defs/json_object"},
        "consent_status": {"type": "string"},
        "notes": {"type": "string"}
      }
    },
    "speaker": {
      "type": "object",
      "additionalProperties": false,
      "required": ["id", "label"],
      "properties": {
        "id": {"$ref": "#/$defs/uuid"},
        "participant_id": {"$ref": "#/$defs/nullable_string"},
        "label": {"type": "string"},
        "display_name": {"type": "string"},
        "notes": {"type": "string"}
      }
    },
    "scene": {
      "type": "object",
      "additionalProperties": false,
      "required": ["id", "name", "sort_order"],
      "properties": {
        "id": {"$ref": "#/$defs/uuid"},
        "name": {"type": "string"},
        "description": {"type": "string"},
        "start_ms": {"$ref": "#/$defs/nullable_integer"},
        "end_ms": {"$ref": "#/$defs/nullable_integer"},
        "sort_order": {"type": "integer"},
        "notes": {"type": "string"}
      }
    },
    "media_asset": {
      "type": "object",
      "additionalProperties": false,
      "required": ["id", "media_type", "relative_path"],
      "properties": {
        "id": {"$ref": "#/$defs/uuid"},
        "import_batch_id": {"$ref": "#/$defs/nullable_string"},
        "media_type": {"type": "string", "enum": ["audio", "video"]},
        "relative_path": {"type": "string"},
        "original_filename": {"type": "string"},
        "file_format": {"type": "string"},
        "mime_type": {"type": "string"},
        "duration_ms": {"$ref": "#/$defs/nullable_integer"},
        "sample_rate_hz": {"$ref": "#/$defs/nullable_integer"},
        "channels": {"$ref": "#/$defs/nullable_integer"},
        "sha256": {"type": "string"},
        "notes": {"type": "string"}
      }
    },
    "transcript_document": {
      "type": "object",
      "additionalProperties": false,
      "required": ["id", "name", "source_format"],
      "properties": {
        "id": {"$ref": "#/$defs/uuid"},
        "import_batch_id": {"$ref": "#/$defs/nullable_string"},
        "media_asset_id": {"$ref": "#/$defs/nullable_string"},
        "name": {"type": "string"},
        "source_format": {
          "type": "string",
          "enum": ["txt", "csv", "tsv", "json", "eaf", "textgrid", "xlsx", "ods", "manual"]
        },
        "relative_path": {"type": "string"},
        "original_filename": {"type": "string"},
        "notes": {"type": "string"}
      }
    },
    "segment": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "id",
        "transcript_document_id",
        "segment_level",
        "sort_order",
        "text_original"
      ],
      "properties": {
        "id": {"$ref": "#/$defs/uuid"},
        "transcript_document_id": {"$ref": "#/$defs/uuid"},
        "media_asset_id": {"$ref": "#/$defs/nullable_string"},
        "parent_segment_id": {"$ref": "#/$defs/nullable_string"},
        "speaker_id": {"$ref": "#/$defs/nullable_string"},
        "scene_id": {"$ref": "#/$defs/nullable_string"},
        "segment_level": {"type": "string", "enum": ["utterance", "clause_phrase"]},
        "sort_order": {"type": "integer"},
        "start_ms": {"$ref": "#/$defs/nullable_integer"},
        "end_ms": {"$ref": "#/$defs/nullable_integer"},
        "text_original": {"type": "string"},
        "text_normalized": {"$ref": "#/$defs/nullable_string"},
        "external_ref": {"type": "string"},
        "notes": {"type": "string"}
      }
    },
    "token": {
      "type": "object",
      "additionalProperties": false,
      "required": ["id", "segment_id", "sort_order", "token_text"],
      "properties": {
        "id": {"$ref": "#/$defs/uuid"},
        "segment_id": {"$ref": "#/$defs/uuid"},
        "sort_order": {"type": "integer"},
        "token_text": {"type": "string"},
        "normalized_text": {"$ref": "#/$defs/nullable_string"},
        "char_start": {"$ref": "#/$defs/nullable_integer"},
        "char_end": {"$ref": "#/$defs/nullable_integer"},
        "external_ref": {"type": "string"}
      }
    },
    "annotation": {
      "type": "object",
      "additionalProperties": false,
      "required": ["id", "source", "status"],
      "properties": {
        "id": {"$ref": "#/$defs/uuid"},
        "token_id": {"$ref": "#/$defs/nullable_string"},
        "segment_id": {"$ref": "#/$defs/nullable_string"},
        "source": {"type": "string", "enum": ["manual", "auto", "imported"]},
        "status": {"type": "string", "enum": ["active", "rejected", "superseded"]},
        "language_id": {"$ref": "#/$defs/nullable_string"},
        "matrix_language_id": {"$ref": "#/$defs/nullable_string"},
        "embedded_language_id": {"$ref": "#/$defs/nullable_string"},
        "switch_type": {
          "type": ["string", "null"],
          "enum": ["intra_sentential", "inter_sentential", "extra_sentential", null]
        },
        "linguistic_status": {
          "type": ["string", "null"],
          "enum": ["borrowing", "insertion", "alternation", null]
        },
        "trigger_text": {"type": "string"},
        "direction_from_language_id": {"$ref": "#/$defs/nullable_string"},
        "direction_to_language_id": {"$ref": "#/$defs/nullable_string"},
        "researcher_confidence": {"$ref": "#/$defs/nullable_integer"},
        "auto_confidence": {"$ref": "#/$defs/nullable_number"},
        "memo": {"type": "string"},
        "tag_ids": {
          "type": "array",
          "items": {"$ref": "#/$defs/uuid"}
        },
        "created_by": {"type": "string"},
        "created_at": {"$ref": "#/$defs/timestamp"},
        "updated_at": {"$ref": "#/$defs/timestamp"}
      },
      "oneOf": [
        {
          "required": ["token_id"],
          "properties": {
            "token_id": {"type": "string"},
            "segment_id": {"type": "null"}
          }
        },
        {
          "required": ["segment_id"],
          "properties": {
            "token_id": {"type": "null"},
            "segment_id": {"type": "string"}
          }
        }
      ]
    },
    "tag": {
      "type": "object",
      "additionalProperties": false,
      "required": ["id", "name"],
      "properties": {
        "id": {"$ref": "#/$defs/uuid"},
        "name": {"type": "string"},
        "color_hex": {"type": "string", "pattern": "^#[0-9A-Fa-f]{6}$"},
        "description": {"type": "string"}
      }
    },
    "morpheme_dictionary_entry": {
      "type": "object",
      "additionalProperties": false,
      "required": ["id", "language_id", "surface", "category"],
      "properties": {
        "id": {"$ref": "#/$defs/uuid"},
        "language_id": {"$ref": "#/$defs/uuid"},
        "surface": {"type": "string"},
        "category": {
          "type": "string",
          "enum": ["prefix", "root", "suffix", "negation", "tense_aspect", "agreement", "other"]
        },
        "gloss": {"type": "string"},
        "notes": {"type": "string"},
        "source": {"type": "string", "enum": ["default", "user"]},
        "is_active": {"type": "boolean"}
      }
    },
    "morpheme_split": {
      "type": "object",
      "additionalProperties": false,
      "required": ["id", "token_id", "source", "status", "split_text", "morphemes"],
      "properties": {
        "id": {"$ref": "#/$defs/uuid"},
        "token_id": {"$ref": "#/$defs/uuid"},
        "source": {"type": "string", "enum": ["manual", "suggestion", "imported"]},
        "status": {"type": "string", "enum": ["active", "historical", "rejected"]},
        "split_text": {"type": "string"},
        "notes": {"type": "string"},
        "morphemes": {
          "type": "array",
          "items": {"$ref": "#/$defs/morpheme"}
        },
        "created_at": {"$ref": "#/$defs/timestamp"},
        "updated_at": {"$ref": "#/$defs/timestamp"}
      }
    },
    "morpheme": {
      "type": "object",
      "additionalProperties": false,
      "required": ["id", "sort_order", "surface"],
      "properties": {
        "id": {"$ref": "#/$defs/uuid"},
        "sort_order": {"type": "integer"},
        "surface": {"type": "string"},
        "gloss": {"type": "string"},
        "category": {"type": "string"},
        "language_id": {"$ref": "#/$defs/nullable_string"},
        "dictionary_entry_id": {"$ref": "#/$defs/nullable_string"}
      }
    },
    "lid_run": {
      "type": "object",
      "additionalProperties": false,
      "required": ["id", "provider_name", "layer", "status", "started_at"],
      "properties": {
        "id": {"$ref": "#/$defs/uuid"},
        "provider_name": {"type": "string"},
        "provider_version": {"type": "string"},
        "layer": {"type": "string", "enum": ["layer1_baseline", "layer2_afrolid", "layer3_masklid"]},
        "parameters": {"$ref": "#/$defs/json_object"},
        "status": {"type": "string", "enum": ["running", "completed", "failed", "cancelled"]},
        "started_at": {"$ref": "#/$defs/timestamp"},
        "finished_at": {"type": ["string", "null"], "format": "date-time"},
        "error_message": {"type": "string"}
      }
    },
    "lid_suggestion": {
      "type": "object",
      "additionalProperties": false,
      "required": ["id", "lid_run_id", "layer", "rank", "created_at"],
      "properties": {
        "id": {"$ref": "#/$defs/uuid"},
        "lid_run_id": {"$ref": "#/$defs/uuid"},
        "token_id": {"$ref": "#/$defs/nullable_string"},
        "segment_id": {"$ref": "#/$defs/nullable_string"},
        "language_id": {"$ref": "#/$defs/nullable_string"},
        "layer": {"type": "string", "enum": ["layer1_baseline", "layer2_afrolid", "layer3_masklid"]},
        "rank": {"type": "integer", "minimum": 1},
        "confidence": {"$ref": "#/$defs/nullable_number"},
        "evidence": {"$ref": "#/$defs/json_object"},
        "accepted_annotation_id": {"$ref": "#/$defs/nullable_string"},
        "created_at": {"$ref": "#/$defs/timestamp"}
      }
    },
    "provenance_record": {
      "type": "object",
      "additionalProperties": false,
      "required": ["id", "event_type", "actor_type", "created_at"],
      "properties": {
        "id": {"$ref": "#/$defs/uuid"},
        "event_type": {"type": "string"},
        "actor_type": {"type": "string"},
        "actor_name": {"type": "string"},
        "target_table": {"type": "string"},
        "target_id": {"type": "string"},
        "related_table": {"type": "string"},
        "related_id": {"type": "string"},
        "tool_name": {"type": "string"},
        "tool_version": {"type": "string"},
        "confidence": {"$ref": "#/$defs/nullable_number"},
        "message": {"type": "string"},
        "payload": {"$ref": "#/$defs/json_object"},
        "created_at": {"$ref": "#/$defs/timestamp"}
      }
    },
    "metric_run": {
      "type": "object",
      "additionalProperties": false,
      "required": ["id", "formula_version", "status", "started_at"],
      "properties": {
        "id": {"$ref": "#/$defs/uuid"},
        "run_name": {"type": "string"},
        "formula_version": {"type": "string"},
        "input_filter": {"$ref": "#/$defs/json_object"},
        "status": {"type": "string", "enum": ["running", "completed", "failed", "cancelled"]},
        "started_at": {"$ref": "#/$defs/timestamp"},
        "finished_at": {"type": ["string", "null"], "format": "date-time"},
        "error_message": {"type": "string"}
      }
    },
    "metric_result": {
      "type": "object",
      "additionalProperties": false,
      "required": ["id", "metric_run_id", "metric_name", "scope_type", "value", "input_count"],
      "properties": {
        "id": {"$ref": "#/$defs/uuid"},
        "metric_run_id": {"$ref": "#/$defs/uuid"},
        "metric_name": {"type": "string"},
        "scope_type": {"type": "string"},
        "scope_id": {"type": "string"},
        "value": true,
        "input_count": {"type": "integer", "minimum": 0},
        "created_at": {"$ref": "#/$defs/timestamp"}
      }
    },
    "export_record": {
      "type": "object",
      "additionalProperties": false,
      "required": ["id", "export_format", "relative_path", "created_at"],
      "properties": {
        "id": {"$ref": "#/$defs/uuid"},
        "export_format": {"type": "string"},
        "relative_path": {"type": "string"},
        "options": {"$ref": "#/$defs/json_object"},
        "sha256": {"type": "string"},
        "created_at": {"$ref": "#/$defs/timestamp"}
      }
    },
    "file_record": {
      "type": "object",
      "additionalProperties": false,
      "required": ["relative_path", "kind"],
      "properties": {
        "relative_path": {"type": "string"},
        "kind": {
          "type": "string",
          "enum": ["media", "transcript", "dictionary", "export", "log", "cache", "other"]
        },
        "sha256": {"type": "string"},
        "size_bytes": {"type": "integer", "minimum": 0},
        "included": {"type": "boolean"}
      }
    }
  }
}
```

## Internal Python Dataclasses

The MVP should use standard-library dataclasses for domain models. This keeps
core data objects lightweight and avoids making Pydantic a core dependency.
Validation that requires database lookups belongs in services or repositories.

```python
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, NewType


Id = NewType("Id", str)
JsonObject = dict[str, Any]


class LanguageCategory(StrEnum):
    """Kinds of language labels available to researchers."""

    LANGUAGE = "language"
    UNKNOWN = "unknown"
    MIXED = "mixed"
    BORROWING = "borrowing"
    PROPER_NOUN = "proper_noun"
    USER_DEFINED = "user_defined"


class SegmentLevel(StrEnum):
    """Supported transcript segmentation levels for the MVP."""

    UTTERANCE = "utterance"
    CLAUSE_PHRASE = "clause_phrase"


class AnnotationSource(StrEnum):
    """Origin of an annotation record."""

    MANUAL = "manual"
    AUTO = "auto"
    IMPORTED = "imported"


class AnnotationStatus(StrEnum):
    """Lifecycle state for annotations and suggestions."""

    ACTIVE = "active"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class SwitchType(StrEnum):
    """Code-switch type labels used by the annotation model."""

    INTRA_SENTENTIAL = "intra_sentential"
    INTER_SENTENTIAL = "inter_sentential"
    EXTRA_SENTENTIAL = "extra_sentential"


class LinguisticStatus(StrEnum):
    """MLF-compatible linguistic status labels."""

    BORROWING = "borrowing"
    INSERTION = "insertion"
    ALTERNATION = "alternation"


class MediaType(StrEnum):
    """Media classes supported by imports."""

    AUDIO = "audio"
    VIDEO = "video"


class SourceFormat(StrEnum):
    """Transcript source formats supported by the MVP."""

    TXT = "txt"
    CSV = "csv"
    TSV = "tsv"
    JSON = "json"
    EAF = "eaf"
    TEXTGRID = "textgrid"
    XLSX = "xlsx"
    ODS = "ods"
    MANUAL = "manual"


class LidLayer(StrEnum):
    """Local LID layers."""

    LAYER1_BASELINE = "layer1_baseline"
    LAYER2_AFROLID = "layer2_afrolid"
    LAYER3_MASKLID = "layer3_masklid"


class JobStatus(StrEnum):
    """Shared status for background work."""

    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(slots=True)
class ProjectMetadata:
    """Human-readable metadata for one local research project."""

    project_uuid: Id
    title: str
    subtitle: str = ""
    researcher: str = ""
    location: str = ""
    project_date: str = ""
    participants_summary: str = ""
    expected_languages_summary: str = ""
    ethics_notes: str = ""
    app_version: str = ""
    schema_version: int = 1
    created_at: str = ""
    updated_at: str = ""


@dataclass(slots=True)
class LanguageTag:
    """A project language, special label, or user-defined variety."""

    id: Id
    code: str
    name: str
    autonym: str = ""
    category: LanguageCategory = LanguageCategory.LANGUAGE
    color_hex: str = "#808080"
    is_expected: bool = False
    is_user_defined: bool = False
    sort_order: int = 0
    notes: str = ""


@dataclass(slots=True)
class Participant:
    """A research participant or described person in the project."""

    id: Id
    participant_code: str
    display_name: str = ""
    role: str = ""
    demographics: JsonObject = field(default_factory=dict)
    consent_status: str = ""
    notes: str = ""


@dataclass(slots=True)
class Speaker:
    """A speaker label used in transcript segments."""

    id: Id
    label: str
    participant_id: Id | None = None
    display_name: str = ""
    notes: str = ""


@dataclass(slots=True)
class Scene:
    """A scene, interview section, or analytical time span."""

    id: Id
    name: str
    description: str = ""
    start_ms: int | None = None
    end_ms: int | None = None
    sort_order: int = 0
    notes: str = ""


@dataclass(slots=True)
class ImportBatch:
    """One import action and its copied source file context."""

    id: Id
    source_label: str
    importer_name: str
    original_path: str = ""
    copied_path: str = ""
    importer_version: str = ""
    source_sha256: str = ""
    import_report: JsonObject = field(default_factory=dict)
    imported_at: str = ""


@dataclass(slots=True)
class MediaAsset:
    """A copied audio or video file inside the project folder."""

    id: Id
    media_type: MediaType
    relative_path: str
    import_batch_id: Id | None = None
    original_filename: str = ""
    file_format: str = ""
    mime_type: str = ""
    duration_ms: int | None = None
    sample_rate_hz: int | None = None
    channels: int | None = None
    sha256: str = ""
    notes: str = ""


@dataclass(slots=True)
class TranscriptDocument:
    """A transcript source or manually created transcript document."""

    id: Id
    name: str
    source_format: SourceFormat
    import_batch_id: Id | None = None
    media_asset_id: Id | None = None
    relative_path: str = ""
    original_filename: str = ""
    notes: str = ""


@dataclass(slots=True)
class TranscriptSegment:
    """A transcript segment at utterance or clause/phrase level."""

    id: Id
    transcript_document_id: Id
    segment_level: SegmentLevel
    sort_order: int
    text_original: str
    media_asset_id: Id | None = None
    parent_segment_id: Id | None = None
    speaker_id: Id | None = None
    scene_id: Id | None = None
    start_ms: int | None = None
    end_ms: int | None = None
    text_normalized: str | None = None
    external_ref: str = ""
    notes: str = ""


@dataclass(slots=True)
class Token:
    """A token belonging to a transcript segment."""

    id: Id
    segment_id: Id
    sort_order: int
    token_text: str
    normalized_text: str | None = None
    char_start: int | None = None
    char_end: int | None = None
    external_ref: str = ""


@dataclass(slots=True)
class Annotation:
    """Manual, automatic, or imported linguistic annotation."""

    id: Id
    source: AnnotationSource
    status: AnnotationStatus = AnnotationStatus.ACTIVE
    token_id: Id | None = None
    segment_id: Id | None = None
    language_id: Id | None = None
    matrix_language_id: Id | None = None
    embedded_language_id: Id | None = None
    switch_type: SwitchType | None = None
    linguistic_status: LinguisticStatus | None = None
    trigger_text: str = ""
    direction_from_language_id: Id | None = None
    direction_to_language_id: Id | None = None
    researcher_confidence: int | None = None
    auto_confidence: float | None = None
    memo: str = ""
    tag_ids: list[Id] = field(default_factory=list)
    created_by: str = ""
    created_at: str = ""
    updated_at: str = ""


@dataclass(slots=True)
class Tag:
    """A user-defined tag that can be attached to annotations."""

    id: Id
    name: str
    color_hex: str = "#808080"
    description: str = ""


@dataclass(slots=True)
class MorphemeDictionaryEntry:
    """Editable local morphology dictionary entry."""

    id: Id
    language_id: Id
    surface: str
    category: str
    gloss: str = ""
    notes: str = ""
    source: str = "default"
    is_active: bool = True


@dataclass(slots=True)
class Morpheme:
    """One morpheme inside a token split."""

    id: Id
    split_id: Id
    sort_order: int
    surface: str
    gloss: str = ""
    category: str = "other"
    language_id: Id | None = None
    dictionary_entry_id: Id | None = None


@dataclass(slots=True)
class MorphemeSplit:
    """A manual or suggested token-level morpheme segmentation."""

    id: Id
    token_id: Id
    source: str
    status: str
    split_text: str
    morphemes: list[Morpheme] = field(default_factory=list)
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""


@dataclass(slots=True)
class LidRun:
    """One local language-identification run."""

    id: Id
    provider_name: str
    layer: LidLayer
    status: JobStatus
    provider_version: str = ""
    parameters: JsonObject = field(default_factory=dict)
    started_at: str = ""
    finished_at: str | None = None
    error_message: str = ""


@dataclass(slots=True)
class LidSuggestion:
    """A language suggestion from a local LID layer."""

    id: Id
    lid_run_id: Id
    layer: LidLayer
    rank: int = 1
    token_id: Id | None = None
    segment_id: Id | None = None
    language_id: Id | None = None
    confidence: float | None = None
    evidence: JsonObject = field(default_factory=dict)
    accepted_annotation_id: Id | None = None
    created_at: str = ""


@dataclass(slots=True)
class ProvenanceRecord:
    """Auditable record of imports, auto labels, edits, metrics, and exports."""

    id: Id
    event_type: str
    actor_type: str
    actor_name: str = ""
    target_table: str = ""
    target_id: str = ""
    related_table: str = ""
    related_id: str = ""
    tool_name: str = ""
    tool_version: str = ""
    confidence: float | None = None
    message: str = ""
    payload: JsonObject = field(default_factory=dict)
    created_at: str = ""


@dataclass(slots=True)
class MetricRun:
    """One metrics calculation run."""

    id: Id
    formula_version: str
    status: JobStatus
    run_name: str = ""
    input_filter: JsonObject = field(default_factory=dict)
    started_at: str = ""
    finished_at: str | None = None
    error_message: str = ""


@dataclass(slots=True)
class MetricResult:
    """One metric value scoped to a project, speaker, scene, segment, or filter."""

    id: Id
    metric_run_id: Id
    metric_name: str
    scope_type: str
    value: Any
    scope_id: str = ""
    input_count: int = 0
    created_at: str = ""


@dataclass(slots=True)
class ExportRecord:
    """A local export produced by the researcher."""

    id: Id
    export_format: str
    relative_path: str
    options: JsonObject = field(default_factory=dict)
    sha256: str = ""
    created_at: str = ""
```

## Validation Notes For Services

The dataclasses intentionally do not perform cross-record validation. Services
and repositories must enforce these rules:

- An annotation must target exactly one token or one segment.
- A researcher confidence value must be between 1 and 5.
- An automatic confidence value must be between 0.0 and 1.0.
- Manual active annotations must be unique per token or segment.
- Automatic suggestions must not overwrite manual annotations.
- Segment and token sort order must remain stable after import unless the
  researcher explicitly edits segmentation.
- A morpheme split marked `active` is the current researcher-facing split, but
  historical splits must remain available.
- Metrics must document formula version, input filters, and input counts.
- Exports must record format, path, options, timestamp, and checksum when
  checksum calculation is practical.

## Mapping To Project Files

SQLite stores structured records. The file system stores large or inspectable
artifacts:

| Data | SQLite table | Project file location |
| --- | --- | --- |
| Audio and video | `media_assets` | `media/audio/`, `media/video/` |
| Imported transcripts | `transcript_documents` | `transcripts/source/` |
| Normalized transcript views | `segments.text_normalized`, `tokens.normalized_text` | `transcripts/normalized/` when exported |
| Editable dictionaries | `morpheme_dictionary_entries`, `languages` | `dictionaries/` |
| Provenance | `provenance_records` | `logs/provenance.jsonl` mirror |
| Metrics | `metric_runs`, `metric_results` | `exports/csv/`, `exports/xlsx/` on export |
| Project snapshot | all tables | `exports/json/` |

## Future Compatibility

The schema leaves room for optional plugins without making them core
dependencies:

- AfroLID stores results through `lid_runs` and `lid_suggestions`.
- Future ASR imports can create `transcript_documents`, `segments`, `tokens`,
  and provenance records without changing annotation tables.
- Additional language varieties are ordinary rows in `languages`.
- Richer morphology tools can write suggestions to `morpheme_splits` while
  preserving manual splits.
- New metrics can add rows to `metric_results` if they document formula version
  and input filters.
