"""Database schema creation and migration."""

from __future__ import annotations

import sqlite3

from imbizo.app.time import utc_now
from imbizo.domain.languages import default_language_tags
from imbizo.domain.project import ProjectMetadata


CURRENT_SCHEMA_VERSION = 1


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS project_metadata (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    project_uuid TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    subtitle TEXT NOT NULL DEFAULT '',
    researcher TEXT NOT NULL DEFAULT '',
    institution TEXT NOT NULL DEFAULT '',
    location TEXT NOT NULL DEFAULT '',
    project_date TEXT NOT NULL DEFAULT '',
    participants_summary TEXT NOT NULL DEFAULT '',
    expected_languages_summary TEXT NOT NULL DEFAULT '',
    ethics_notes TEXT NOT NULL DEFAULT '',
    irb_rec_reference TEXT NOT NULL DEFAULT '',
    care_acknowledgement TEXT NOT NULL DEFAULT '',
    consent_status TEXT NOT NULL DEFAULT '',
    data_sharing_constraints TEXT NOT NULL DEFAULT '',
    app_version TEXT NOT NULL DEFAULT '',
    schema_version INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS languages (
    id TEXT PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    autonym TEXT NOT NULL DEFAULT '',
    category TEXT NOT NULL DEFAULT 'language',
    color_hex TEXT NOT NULL DEFAULT '#808080',
    is_expected INTEGER NOT NULL DEFAULT 0,
    is_user_defined INTEGER NOT NULL DEFAULT 0,
    sort_order INTEGER NOT NULL DEFAULT 0,
    notes TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS participants (
    id TEXT PRIMARY KEY,
    participant_code TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL DEFAULT '',
    role TEXT NOT NULL DEFAULT '',
    demographics_json TEXT NOT NULL DEFAULT '{}',
    consent_status TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS speakers (
    id TEXT PRIMARY KEY,
    participant_id TEXT NULL REFERENCES participants(id) ON DELETE SET NULL,
    label TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS scenes (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    start_ms INTEGER NULL,
    end_ms INTEGER NULL,
    sort_order INTEGER NOT NULL DEFAULT 0,
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS import_batches (
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

CREATE TABLE IF NOT EXISTS media_assets (
    id TEXT PRIMARY KEY,
    import_batch_id TEXT NULL REFERENCES import_batches(id) ON DELETE SET NULL,
    media_type TEXT NOT NULL,
    relative_path TEXT NOT NULL UNIQUE,
    original_filename TEXT NOT NULL DEFAULT '',
    file_format TEXT NOT NULL DEFAULT '',
    mime_type TEXT NOT NULL DEFAULT '',
    duration_ms INTEGER NULL,
    sample_rate_hz INTEGER NULL,
    channels INTEGER NULL,
    sha256 TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS transcript_documents (
    id TEXT PRIMARY KEY,
    import_batch_id TEXT NULL REFERENCES import_batches(id) ON DELETE SET NULL,
    media_asset_id TEXT NULL REFERENCES media_assets(id) ON DELETE SET NULL,
    name TEXT NOT NULL,
    source_format TEXT NOT NULL,
    relative_path TEXT NOT NULL DEFAULT '',
    original_filename TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS segments (
    id TEXT PRIMARY KEY,
    transcript_document_id TEXT NOT NULL REFERENCES transcript_documents(id) ON DELETE CASCADE,
    media_asset_id TEXT NULL REFERENCES media_assets(id) ON DELETE SET NULL,
    parent_segment_id TEXT NULL REFERENCES segments(id) ON DELETE CASCADE,
    speaker_id TEXT NULL,
    scene_id TEXT NULL,
    segment_level TEXT NOT NULL,
    sort_order INTEGER NOT NULL,
    start_ms INTEGER NULL,
    end_ms INTEGER NULL,
    text_original TEXT NOT NULL,
    text_normalized TEXT NULL,
    external_ref TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_segments_document_order
    ON segments(transcript_document_id, sort_order);

CREATE TABLE IF NOT EXISTS tokens (
    id TEXT PRIMARY KEY,
    segment_id TEXT NOT NULL REFERENCES segments(id) ON DELETE CASCADE,
    sort_order INTEGER NOT NULL,
    token_text TEXT NOT NULL,
    normalized_text TEXT NULL,
    char_start INTEGER NULL,
    char_end INTEGER NULL,
    external_ref TEXT NOT NULL DEFAULT '',
    UNIQUE (segment_id, sort_order)
);

CREATE INDEX IF NOT EXISTS idx_tokens_segment_order
    ON tokens(segment_id, sort_order);

CREATE TABLE IF NOT EXISTS annotations (
    id TEXT PRIMARY KEY,
    token_id TEXT NULL REFERENCES tokens(id) ON DELETE CASCADE,
    segment_id TEXT NULL REFERENCES segments(id) ON DELETE CASCADE,
    source TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    language_id TEXT NULL REFERENCES languages(id) ON DELETE SET NULL,
    matrix_language_id TEXT NULL REFERENCES languages(id) ON DELETE SET NULL,
    embedded_language_id TEXT NULL REFERENCES languages(id) ON DELETE SET NULL,
    switch_type TEXT NULL,
    linguistic_status TEXT NULL,
    trigger_text TEXT NOT NULL DEFAULT '',
    direction_from_language_id TEXT NULL REFERENCES languages(id) ON DELETE SET NULL,
    direction_to_language_id TEXT NULL REFERENCES languages(id) ON DELETE SET NULL,
    researcher_confidence INTEGER NULL,
    auto_confidence REAL NULL,
    memo TEXT NOT NULL DEFAULT '',
    created_by TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CHECK ((token_id IS NOT NULL AND segment_id IS NULL) OR (token_id IS NULL AND segment_id IS NOT NULL))
);

CREATE INDEX IF NOT EXISTS idx_annotations_token ON annotations(token_id, status, source);
CREATE INDEX IF NOT EXISTS idx_annotations_segment ON annotations(segment_id, status, source);

CREATE TABLE IF NOT EXISTS tags (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    color_hex TEXT NOT NULL DEFAULT '#808080',
    description TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS annotation_tags (
    annotation_id TEXT NOT NULL REFERENCES annotations(id) ON DELETE CASCADE,
    tag_id TEXT NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (annotation_id, tag_id)
);

CREATE TABLE IF NOT EXISTS morpheme_dictionary_entries (
    id TEXT PRIMARY KEY,
    language_id TEXT NOT NULL REFERENCES languages(id) ON DELETE CASCADE,
    surface TEXT NOT NULL,
    category TEXT NOT NULL,
    gloss TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT '',
    source TEXT NOT NULL DEFAULT 'user',
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS morpheme_splits (
    id TEXT PRIMARY KEY,
    token_id TEXT NOT NULL REFERENCES tokens(id) ON DELETE CASCADE,
    source TEXT NOT NULL,
    status TEXT NOT NULL,
    split_text TEXT NOT NULL,
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS provenance_records (
    id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    actor_type TEXT NOT NULL,
    actor_name TEXT NOT NULL DEFAULT '',
    target_table TEXT NOT NULL DEFAULT '',
    target_id TEXT NOT NULL DEFAULT '',
    related_table TEXT NOT NULL DEFAULT '',
    related_id TEXT NOT NULL DEFAULT '',
    tool_name TEXT NOT NULL DEFAULT '',
    tool_version TEXT NOT NULL DEFAULT '',
    confidence REAL NULL,
    message TEXT NOT NULL DEFAULT '',
    payload_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS lid_runs (
    id TEXT PRIMARY KEY,
    provider_name TEXT NOT NULL,
    provider_version TEXT NOT NULL DEFAULT '',
    layer TEXT NOT NULL,
    parameters_json TEXT NOT NULL DEFAULT '{}',
    status TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT NULL,
    error_message TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS lid_suggestions (
    id TEXT PRIMARY KEY,
    lid_run_id TEXT NOT NULL REFERENCES lid_runs(id) ON DELETE CASCADE,
    token_id TEXT NULL REFERENCES tokens(id) ON DELETE CASCADE,
    segment_id TEXT NULL REFERENCES segments(id) ON DELETE CASCADE,
    language_id TEXT NULL REFERENCES languages(id) ON DELETE SET NULL,
    layer TEXT NOT NULL,
    rank INTEGER NOT NULL DEFAULT 1,
    confidence REAL NULL,
    evidence_json TEXT NOT NULL DEFAULT '{}',
    accepted_annotation_id TEXT NULL REFERENCES annotations(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS metric_runs (
    id TEXT PRIMARY KEY,
    run_name TEXT NOT NULL DEFAULT '',
    formula_version TEXT NOT NULL,
    input_filter_json TEXT NOT NULL DEFAULT '{}',
    status TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT NULL,
    error_message TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS metric_results (
    id TEXT PRIMARY KEY,
    metric_run_id TEXT NOT NULL REFERENCES metric_runs(id) ON DELETE CASCADE,
    metric_name TEXT NOT NULL,
    scope_type TEXT NOT NULL,
    scope_id TEXT NOT NULL DEFAULT '',
    value_json TEXT NOT NULL,
    input_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS exports (
    id TEXT PRIMARY KEY,
    export_format TEXT NOT NULL,
    relative_path TEXT NOT NULL,
    options_json TEXT NOT NULL DEFAULT '{}',
    sha256 TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);
"""


def initialize_database(connection: sqlite3.Connection, metadata: ProjectMetadata) -> None:
    """Create a new project database and seed required rows."""

    connection.executescript(SCHEMA_SQL)
    now = metadata.created_at or utc_now()
    connection.execute(
        """
        INSERT OR REPLACE INTO project_metadata (
            id, project_uuid, title, subtitle, researcher, institution,
            location, project_date, participants_summary,
            expected_languages_summary, ethics_notes, irb_rec_reference,
            care_acknowledgement, consent_status, data_sharing_constraints,
            app_version, schema_version, created_at, updated_at
        ) VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            metadata.project_uuid,
            metadata.title,
            metadata.subtitle,
            metadata.researcher,
            metadata.institution,
            metadata.location,
            metadata.project_date,
            metadata.participants_summary,
            metadata.expected_languages_summary,
            metadata.ethics_notes,
            metadata.irb_rec_reference,
            metadata.care_acknowledgement,
            metadata.consent_status,
            metadata.data_sharing_constraints,
            metadata.app_version,
            CURRENT_SCHEMA_VERSION,
            now,
            metadata.updated_at or now,
        ),
    )
    for language in default_language_tags():
        connection.execute(
            """
            INSERT OR IGNORE INTO languages (
                id, code, name, autonym, category, color_hex, is_expected,
                is_user_defined, sort_order, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                language.id,
                language.code,
                language.name,
                language.autonym,
                language.category.value,
                language.color_hex,
                int(language.is_expected),
                int(language.is_user_defined),
                language.sort_order,
                language.notes,
            ),
        )
    connection.execute(
        "INSERT OR REPLACE INTO schema_migrations (version, name, applied_at) VALUES (?, ?, ?)",
        (CURRENT_SCHEMA_VERSION, "initial", now),
    )
    connection.commit()


def migrate_database(connection: sqlite3.Connection) -> None:
    """Apply pending migrations to an existing project database."""

    connection.executescript(SCHEMA_SQL)
    for column in (
        "institution TEXT NOT NULL DEFAULT ''",
        "irb_rec_reference TEXT NOT NULL DEFAULT ''",
        "care_acknowledgement TEXT NOT NULL DEFAULT ''",
        "consent_status TEXT NOT NULL DEFAULT ''",
        "data_sharing_constraints TEXT NOT NULL DEFAULT ''",
    ):
        name = column.split()[0]
        existing = [row[1] for row in connection.execute("PRAGMA table_info(project_metadata)").fetchall()]
        if name not in existing:
            connection.execute(f"ALTER TABLE project_metadata ADD COLUMN {column}")
    connection.commit()


def get_schema_version(connection: sqlite3.Connection) -> int:
    """Return the current project database schema version."""

    row = connection.execute("SELECT schema_version FROM project_metadata WHERE id = 1").fetchone()
    if row is None:
        return 0
    return int(row["schema_version"])
