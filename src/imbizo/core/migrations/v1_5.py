"""Additive v1.5 migration for Imbizo-CS project databases.

The migration adds fields for sister-language disambiguation, Clyne-style
trigger candidates, mixed-code spans, phonological borrowing evidence, and
offline community review. It is intentionally additive: MVP projects must first
be upgraded to v1.0, and all v1.5 token columns are nullable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import uuid
import zipfile

import yaml


TARGET_SCHEMA_VERSION = "1.5"
MINIMUM_SOURCE_VERSION = "1.0"


@dataclass(slots=True)
class MigrationReport:
    """Summary of a v1.5 migration or dry-run."""

    project_path: Path
    database_path: Path
    from_version: str
    to_version: str
    dry_run: bool
    applied: bool
    backup_path: Path | None = None
    provenance_event_id: str | None = None
    dictionary_versions: dict[str, str] = field(default_factory=dict)
    added_columns: list[str] = field(default_factory=list)
    created_tables: list[str] = field(default_factory=list)
    pre_migration_db_sha256: str | None = None
    post_migration_db_sha256: str | None = None
    message: str = ""


TOKEN_COLUMNS: dict[str, str] = {
    "sister_lang_confidence": """
        ALTER TABLE tokens ADD COLUMN sister_lang_confidence REAL
            CHECK (
                sister_lang_confidence IS NULL
                OR (sister_lang_confidence >= 0.0 AND sister_lang_confidence <= 1.0)
            )
    """,
    "sister_lang_evidence": "ALTER TABLE tokens ADD COLUMN sister_lang_evidence TEXT",
    "trigger_role": """
        ALTER TABLE tokens ADD COLUMN trigger_role TEXT
            CHECK (trigger_role IS NULL OR trigger_role IN ('trigger', 'triggered', 'none'))
    """,
    "mixed_code_variety": """
        ALTER TABLE tokens ADD COLUMN mixed_code_variety TEXT
            CHECK (
                mixed_code_variety IS NULL
                OR mixed_code_variety IN ('tsotsitaal', 'iscamtho', 'kaaps', 'sabela')
            )
    """,
    "phon_integration_score": """
        ALTER TABLE tokens ADD COLUMN phon_integration_score REAL
            CHECK (
                phon_integration_score IS NULL
                OR (phon_integration_score >= 0.0 AND phon_integration_score <= 1.0)
            )
    """,
}


CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS trigger_links (
    head_token_id TEXT NOT NULL,
    triggered_token_id TEXT NOT NULL,
    trigger_type TEXT NOT NULL,
    confidence REAL NOT NULL CHECK (confidence >= 0.0 AND confidence <= 1.0),
    source TEXT NOT NULL CHECK (source IN ('manual', 'suggested-accepted', 'suggested-overridden', 'imported')),
    note TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (head_token_id, triggered_token_id, trigger_type),
    FOREIGN KEY (head_token_id) REFERENCES tokens(id) ON DELETE CASCADE,
    FOREIGN KEY (triggered_token_id) REFERENCES tokens(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_trigger_links_head ON trigger_links(head_token_id);
CREATE INDEX IF NOT EXISTS idx_trigger_links_triggered ON trigger_links(triggered_token_id);

CREATE TABLE IF NOT EXISTS mixed_code_spans (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    start_token_id TEXT NOT NULL,
    end_token_id TEXT NOT NULL,
    variety TEXT NOT NULL CHECK (variety IN ('tsotsitaal', 'iscamtho', 'kaaps', 'sabela')),
    confidence REAL CHECK (confidence IS NULL OR (confidence >= 0.0 AND confidence <= 1.0)),
    source TEXT NOT NULL CHECK (source IN ('manual', 'suggested-accepted', 'suggested-overridden', 'imported')),
    note TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (start_token_id) REFERENCES tokens(id) ON DELETE CASCADE,
    FOREIGN KEY (end_token_id) REFERENCES tokens(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_mixed_code_spans_project ON mixed_code_spans(project_id);
CREATE INDEX IF NOT EXISTS idx_mixed_code_spans_bounds ON mixed_code_spans(start_token_id, end_token_id);

CREATE TABLE IF NOT EXISTS phonological_features (
    id TEXT PRIMARY KEY,
    token_id TEXT NOT NULL,
    feature_type TEXT NOT NULL,
    value TEXT NOT NULL,
    source TEXT NOT NULL CHECK (source IN ('manual', 'suggested-accepted', 'suggested-overridden', 'imported')),
    note TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (token_id) REFERENCES tokens(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_phonological_features_token ON phonological_features(token_id);
CREATE INDEX IF NOT EXISTS idx_phonological_features_type ON phonological_features(feature_type);

CREATE TABLE IF NOT EXISTS community_reviews (
    id TEXT PRIMARY KEY,
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
    ),
    target_id TEXT NOT NULL,
    reviewer_alias TEXT NOT NULL,
    comment TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'accepted', 'rejected', 'superseded')),
    signature_hash TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    applied_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_community_reviews_target ON community_reviews(target_kind, target_id);
CREATE INDEX IF NOT EXISTS idx_community_reviews_status ON community_reviews(status);
"""


def migrate_project(project_path: Path, dry_run: bool = False, no_backup: bool = False) -> MigrationReport:
    """Upgrade a v1.0 Imbizo-CS project to the v1.5 additive schema.

    The migration supports Clyne-style trigger candidates (Clyne, 1967, 2003),
    mixed-code variety annotation (Slabbert & Myers-Scotton, 1997), optional
    phonological evidence, and offline community review. MVP projects are
    refused because v1.0 noun-class, concord, and 4-M structures must exist
    before v1.5 is meaningful.
    """

    project_path = project_path.resolve()
    database_path = _find_database(project_path)
    dictionary_versions = collect_dictionary_versions(project_path)
    from_version = detect_schema_version(database_path)
    pre_hash = _sha256_file(database_path)

    if _version_key(from_version) < _version_key(MINIMUM_SOURCE_VERSION):
        raise RuntimeError(
            "This appears to be an MVP-era project. Apply the v1.0 migration before v1.5."
        )
    if _version_key(from_version) >= _version_key(TARGET_SCHEMA_VERSION):
        return MigrationReport(
            project_path=project_path,
            database_path=database_path,
            from_version=from_version,
            to_version=TARGET_SCHEMA_VERSION,
            dry_run=dry_run,
            applied=False,
            dictionary_versions=dictionary_versions,
            pre_migration_db_sha256=pre_hash,
            post_migration_db_sha256=pre_hash,
            message="Project is already at v1.5 or later.",
        )

    with sqlite3.connect(database_path) as conn:
        existing_columns = _token_columns(conn)
        added_columns = [name for name in TOKEN_COLUMNS if name not in existing_columns]
        created_tables = [
            table
            for table in ["trigger_links", "mixed_code_spans", "phonological_features", "community_reviews"]
            if not _table_exists(conn, table)
        ]

    if dry_run:
        return MigrationReport(
            project_path=project_path,
            database_path=database_path,
            from_version=from_version,
            to_version=TARGET_SCHEMA_VERSION,
            dry_run=True,
            applied=False,
            dictionary_versions=dictionary_versions,
            added_columns=added_columns,
            created_tables=created_tables,
            pre_migration_db_sha256=pre_hash,
            post_migration_db_sha256=pre_hash,
            message="Dry run only; no files were modified.",
        )

    backup_path = None if no_backup else _create_backup(project_path)

    with sqlite3.connect(database_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("BEGIN")
        try:
            for name in added_columns:
                conn.execute(TOKEN_COLUMNS[name])
            conn.executescript(CREATE_TABLES_SQL)
            _set_schema_version(conn, TARGET_SCHEMA_VERSION)
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    post_hash = _sha256_file(database_path)
    event_id = _write_provenance(
        project_path,
        {
            "event_type": "migration.v1_5",
            "from_version": from_version,
            "to_version": TARGET_SCHEMA_VERSION,
            "backup_path": str(backup_path) if backup_path else None,
            "dictionary_versions": dictionary_versions,
            "pre_migration_db_sha256": pre_hash,
            "post_migration_db_sha256": post_hash,
        },
    )
    return MigrationReport(
        project_path=project_path,
        database_path=database_path,
        from_version=from_version,
        to_version=TARGET_SCHEMA_VERSION,
        dry_run=False,
        applied=True,
        backup_path=backup_path,
        provenance_event_id=event_id,
        dictionary_versions=dictionary_versions,
        added_columns=added_columns,
        created_tables=created_tables,
        pre_migration_db_sha256=pre_hash,
        post_migration_db_sha256=post_hash,
        message="v1.5 migration applied.",
    )


def detect_schema_version(database_path: Path) -> str:
    """Return the project schema version, or ``0`` for MVP-era databases."""

    with sqlite3.connect(database_path) as conn:
        if not _table_exists(conn, "schema_version"):
            return "0"
        columns = {row[1] for row in conn.execute("PRAGMA table_info(schema_version)")}
        if "version" in columns:
            row = conn.execute("SELECT version FROM schema_version ORDER BY rowid DESC LIMIT 1").fetchone()
            return str(row[0]) if row else "0"
        if "schema_version" in columns:
            row = conn.execute("SELECT schema_version FROM schema_version ORDER BY rowid DESC LIMIT 1").fetchone()
            return str(row[0]) if row else "0"
    return "0"


def collect_dictionary_versions(project_path: Path) -> dict[str, str]:
    """Collect v1.5 dictionary versions from bundled and project-local YAML files."""

    roots = [Path.cwd() / "dictionaries", project_path / "dictionaries"]
    versions: dict[str, str] = {}
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(root.glob("**/*.yaml")):
            try:
                data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            except Exception:
                continue
            if "version" in data:
                key = ".".join(path.with_suffix("").parts[-2:])
                versions[key] = str(data["version"])
    return versions


def _find_database(project_path: Path) -> Path:
    candidates = [
        project_path / "imbizo.sqlite",
        project_path / "project.sqlite",
        project_path / "database.sqlite",
        project_path / "data" / "project.sqlite",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    matches = sorted(project_path.glob("*.sqlite"))
    if matches:
        return matches[0]
    raise FileNotFoundError(f"No SQLite project database found in {project_path}")


def _create_backup(project_path: Path) -> Path:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    backup_dir = project_path / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / f"pre_v1_5_{timestamp}.zip"
    with zipfile.ZipFile(backup_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for item in project_path.rglob("*"):
            if item == backup_path or backup_dir in item.parents:
                continue
            archive.write(item, item.relative_to(project_path))
    return backup_path


def _set_schema_version(conn: sqlite3.Connection, version: str) -> None:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_version (version TEXT NOT NULL, applied_at TEXT NOT NULL)"
    )
    conn.execute(
        "INSERT INTO schema_version (version, applied_at) VALUES (?, ?)",
        (version, datetime.now(UTC).isoformat()),
    )


def _token_columns(conn: sqlite3.Connection) -> set[str]:
    return {row[1] for row in conn.execute("PRAGMA table_xinfo(tokens)")}


def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    ).fetchone()
    return row is not None


def _write_provenance(project_path: Path, payload: dict[str, object]) -> str:
    event_id = str(uuid.uuid4())
    event = {
        "id": event_id,
        "timestamp": datetime.now(UTC).isoformat(),
        **payload,
    }
    log_dir = project_path / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    with (log_dir / "provenance.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=True, sort_keys=True) + "\n")
    return event_id


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _version_key(version: str) -> tuple[int, ...]:
    parts: list[int] = []
    for piece in str(version).replace("v", "").split("."):
        if piece.isdigit():
            parts.append(int(piece))
        else:
            digits = "".join(char for char in piece if char.isdigit())
            parts.append(int(digits or 0))
    while len(parts) < 2:
        parts.append(0)
    return tuple(parts)
