"""Additive v1.0 migration for noun class, concord, and 4-M data.

The migration adds optional noun-class fields, concord links, dictionary
snapshots, and 4-M audit records. All token columns are nullable so MVP
projects remain readable, and all features remain opt-in. Noun-class and
concord support follows Bantu agreement analysis as described for isiZulu and
related languages (Poulos & Msimang, 1998; Demuth, 2000). The 4-M audit table
supports, but does not enforce, Matrix Language Frame analysis
(Myers-Scotton, 1993; Myers-Scotton, 2002).
"""

from __future__ import annotations

import json
import shutil
import sqlite3
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from imbizo.app.time import utc_now


TARGET_VERSION = "1.0.0"


@dataclass(slots=True)
class MigrationReport:
    """Result of a v1.0 project migration."""

    project_path: Path
    database_path: Path
    previous_version: str
    target_version: str
    dry_run: bool
    backup_path: Path | None = None
    provenance_event_id: str = ""
    applied: bool = False
    statements: list[str] = field(default_factory=list)
    skipped_columns: list[str] = field(default_factory=list)
    message: str = ""


TOKEN_COLUMNS: dict[str, str] = {
    "nc_class": "ALTER TABLE tokens ADD COLUMN nc_class INTEGER NULL",
    "nc_prefix": "ALTER TABLE tokens ADD COLUMN nc_prefix TEXT NULL",
    "nc_source": "ALTER TABLE tokens ADD COLUMN nc_source TEXT NULL",
    "four_m_type": "ALTER TABLE tokens ADD COLUMN four_m_type TEXT NULL",
    "four_m_source": "ALTER TABLE tokens ADD COLUMN four_m_source TEXT NULL",
}


CREATE_SCHEMA_VERSION_SQL = """
CREATE TABLE IF NOT EXISTS schema_version (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    version TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
"""


CREATE_NOUN_CLASS_DICTIONARIES_SQL = """
CREATE TABLE IF NOT EXISTS noun_class_dictionaries (
    id TEXT PRIMARY KEY,
    language_code TEXT NOT NULL,
    dictionary_version TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    source_label TEXT NOT NULL,
    source_path TEXT NULL,
    content_sha256 TEXT NOT NULL,
    snapshot_json TEXT NOT NULL,
    verified_entry_count INTEGER NOT NULL DEFAULT 0,
    unverified_entry_count INTEGER NOT NULL DEFAULT 0,
    is_project_override INTEGER NOT NULL DEFAULT 0,
    note TEXT NULL,
    created_at TEXT NOT NULL
)
"""


CREATE_CONCORD_LINKS_SQL = """
CREATE TABLE IF NOT EXISTS concord_links (
    id TEXT PRIMARY KEY,
    segment_id TEXT NOT NULL REFERENCES segments(id) ON DELETE CASCADE,
    controller_token_id TEXT NOT NULL REFERENCES tokens(id) ON DELETE CASCADE,
    concord_token_id TEXT NOT NULL REFERENCES tokens(id) ON DELETE CASCADE,
    concord_type TEXT NOT NULL CHECK (concord_type IN ('SC','OC','AC','PC','RC','DEM')),
    controller_nc_class INTEGER NULL CHECK (controller_nc_class IS NULL OR controller_nc_class BETWEEN 1 AND 23),
    expected_form TEXT NULL,
    observed_form TEXT NOT NULL,
    agreement_status TEXT NOT NULL CHECK (agreement_status IN ('confirmed','mismatch','uncertain','not_applicable')),
    source TEXT NOT NULL CHECK (source IN ('manual','suggested-accepted','suggested-overridden')),
    confidence REAL NULL CHECK (confidence IS NULL OR (confidence >= 0.0 AND confidence <= 1.0)),
    dictionary_snapshot_id TEXT NULL REFERENCES noun_class_dictionaries(id) ON DELETE SET NULL,
    note TEXT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
"""


CREATE_FOUR_M_AUDIT_SQL = """
CREATE TABLE IF NOT EXISTS four_m_audit (
    id TEXT PRIMARY KEY,
    segment_id TEXT NOT NULL REFERENCES segments(id) ON DELETE CASCADE,
    verdict TEXT NOT NULL CHECK (verdict IN ('compatible','possibly_compatible','inconclusive','tension','not_applicable')),
    matrix_language_id TEXT NULL REFERENCES languages(id) ON DELETE SET NULL,
    embedded_language_id TEXT NULL REFERENCES languages(id) ON DELETE SET NULL,
    system_morpheme_count INTEGER NOT NULL DEFAULT 0,
    outsider_late_system_morpheme_count INTEGER NOT NULL DEFAULT 0,
    content_morpheme_switch_count INTEGER NOT NULL DEFAULT 0,
    confirmed_concord_link_count INTEGER NOT NULL DEFAULT 0,
    reviewed_concord_link_count INTEGER NOT NULL DEFAULT 0,
    integration_score REAL NULL CHECK (integration_score IS NULL OR (integration_score >= 0.0 AND integration_score <= 1.0)),
    source TEXT NOT NULL CHECK (source IN ('manual','suggested-accepted','suggested-overridden')),
    checker_version TEXT NOT NULL,
    explanation TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
"""


INDEX_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_noun_class_dictionaries_language ON noun_class_dictionaries(language_code, dictionary_version)",
    "CREATE INDEX IF NOT EXISTS idx_concord_links_segment ON concord_links(segment_id)",
    "CREATE INDEX IF NOT EXISTS idx_concord_links_controller ON concord_links(controller_token_id)",
    "CREATE INDEX IF NOT EXISTS idx_concord_links_concord ON concord_links(concord_token_id)",
    "CREATE INDEX IF NOT EXISTS idx_concord_links_type_status ON concord_links(concord_type, agreement_status)",
    "CREATE INDEX IF NOT EXISTS idx_four_m_audit_segment ON four_m_audit(segment_id)",
    "CREATE INDEX IF NOT EXISTS idx_four_m_audit_verdict ON four_m_audit(verdict)",
]


def migrate_project(project_path: Path, dry_run: bool = False, *, create_backup: bool = True) -> MigrationReport:
    """Migrate one local project to v1.0 and record provenance.

    The migration is idempotent and additive. By default it creates a local
    SQLite backup before applying changes, because preserving researcher data
    has priority over convenience. The migration records its own provenance
    event in both SQLite and `logs/provenance.jsonl` when not run in dry-run
    mode.
    """

    root = project_path.expanduser().resolve()
    database_path = _resolve_database_path(root)
    if not database_path.exists():
        raise FileNotFoundError(f"Project database not found: {database_path}")

    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        previous_version = _detect_schema_version_readonly(connection)
        statements, skipped_columns = _planned_statements(connection)

    report = MigrationReport(
        project_path=root,
        database_path=database_path,
        previous_version=previous_version,
        target_version=TARGET_VERSION,
        dry_run=dry_run,
        statements=statements,
        skipped_columns=skipped_columns,
    )
    if dry_run:
        report.message = "Dry run only; no backup or database writes performed."
        return report

    if create_backup:
        report.backup_path = _backup_database(root, database_path)
    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            connection.execute("BEGIN")
            _ensure_schema_version_table(connection)
            _apply_token_columns(connection)
            for statement in (
                CREATE_NOUN_CLASS_DICTIONARIES_SQL,
                CREATE_CONCORD_LINKS_SQL,
                CREATE_FOUR_M_AUDIT_SQL,
                *INDEX_SQL,
            ):
                connection.execute(statement)
            _set_schema_version(connection, TARGET_VERSION)
            report.provenance_event_id = _record_provenance(connection, root, report)
            connection.commit()
        except Exception:
            connection.rollback()
            raise

    report.applied = True
    report.message = "v1.0 migration applied successfully."
    return report


def _resolve_database_path(project_path: Path) -> Path:
    if project_path.is_file():
        return project_path
    return project_path / "project.sqlite"


def _ensure_schema_version_table(connection: sqlite3.Connection) -> None:
    connection.execute(CREATE_SCHEMA_VERSION_SQL)
    row = connection.execute("SELECT version FROM schema_version WHERE id = 1").fetchone()
    if row is None:
        legacy = connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='project_metadata'").fetchone()
        version = "0.1.0"
        if legacy is not None:
            metadata = connection.execute("SELECT schema_version FROM project_metadata WHERE id = 1").fetchone()
            if metadata is not None:
                version = str(metadata["schema_version"])
        connection.execute(
            "INSERT INTO schema_version (id, version, updated_at) VALUES (1, ?, ?)",
            (version, utc_now()),
        )


def _get_schema_version(connection: sqlite3.Connection) -> str:
    row = connection.execute("SELECT version FROM schema_version WHERE id = 1").fetchone()
    return str(row["version"]) if row is not None else "0.1.0"


def _detect_schema_version_readonly(connection: sqlite3.Connection) -> str:
    schema_table = connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'").fetchone()
    if schema_table is not None:
        row = connection.execute("SELECT version FROM schema_version WHERE id = 1").fetchone()
        if row is not None:
            return str(row["version"])
    metadata_table = connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='project_metadata'").fetchone()
    if metadata_table is not None:
        row = connection.execute("SELECT schema_version FROM project_metadata WHERE id = 1").fetchone()
        if row is not None:
            return str(row["schema_version"])
    return "0.1.0"


def _set_schema_version(connection: sqlite3.Connection, version: str) -> None:
    connection.execute(
        """
        INSERT INTO schema_version (id, version, updated_at) VALUES (1, ?, ?)
        ON CONFLICT(id) DO UPDATE SET version = excluded.version, updated_at = excluded.updated_at
        """,
        (version, utc_now()),
    )


def _planned_statements(connection: sqlite3.Connection) -> tuple[list[str], list[str]]:
    existing = _existing_columns(connection, "tokens")
    statements: list[str] = [CREATE_SCHEMA_VERSION_SQL]
    skipped: list[str] = []
    for column, statement in TOKEN_COLUMNS.items():
        if column in existing:
            skipped.append(column)
        else:
            statements.append(statement)
    statements.extend([CREATE_NOUN_CLASS_DICTIONARIES_SQL, CREATE_CONCORD_LINKS_SQL, CREATE_FOUR_M_AUDIT_SQL, *INDEX_SQL])
    return statements, skipped


def _apply_token_columns(connection: sqlite3.Connection) -> None:
    existing = _existing_columns(connection, "tokens")
    for column, statement in TOKEN_COLUMNS.items():
        if column not in existing:
            connection.execute(statement)


def _existing_columns(connection: sqlite3.Connection, table_name: str) -> set[str]:
    return {str(row["name"]) for row in connection.execute(f"PRAGMA table_info({table_name})").fetchall()}


def _backup_database(project_path: Path, database_path: Path) -> Path:
    backup_dir = project_path / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / f"project.sqlite.v1_0_pre_{utc_now().replace(':', '').replace('-', '')}.bak"
    shutil.copy2(database_path, backup_path)
    return backup_path


def _record_provenance(connection: sqlite3.Connection, project_path: Path, report: MigrationReport) -> str:
    event_id = str(uuid.uuid4())
    created_at = utc_now()
    payload = {
        "previous_version": report.previous_version,
        "target_version": report.target_version,
        "backup_path": str(report.backup_path) if report.backup_path else None,
        "skipped_columns": report.skipped_columns,
    }
    connection.execute(
        """
        INSERT INTO provenance_records (
            id, event_type, actor_type, actor_name, target_table, target_id,
            related_table, related_id, tool_name, tool_version, confidence,
            message, payload_json, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event_id,
            "migration_v1_0",
            "system",
            "Imbizo-CS Workbench",
            "schema_version",
            "1",
            "",
            "",
            "core.migrations.v1_0",
            TARGET_VERSION,
            None,
            "Applied additive v1.0 noun-class, concord, and 4-M schema migration.",
            json.dumps(payload, ensure_ascii=False),
            created_at,
        ),
    )
    log_dir = project_path / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    with (log_dir / "provenance.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "id": event_id,
                    "event_type": "migration_v1_0",
                    "actor_type": "system",
                    "target_table": "schema_version",
                    "target_id": "1",
                    "tool_name": "core.migrations.v1_0",
                    "tool_version": TARGET_VERSION,
                    "message": "Applied additive v1.0 noun-class, concord, and 4-M schema migration.",
                    "payload": payload,
                    "created_at": created_at,
                },
                ensure_ascii=False,
        )
            + "\n"
        )
    return event_id
