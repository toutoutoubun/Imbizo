"""Command-line tools for local Imbizo-CS project maintenance."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import zipfile
from pathlib import Path

import click
import yaml

from imbizo import __version__
from imbizo.app.time import utc_now
from imbizo.core.migrations.v1_0 import MigrationReport, migrate_project


@click.group()
def cli() -> None:
    """Local Imbizo-CS maintenance commands."""


@cli.command()
@click.option("--project", required=True, type=click.Path(exists=True, path_type=Path))
@click.option("--dry-run", is_flag=True, default=False)
@click.option("--no-backup", is_flag=True, default=False, help="Disable automatic backup. Discouraged.")
def migrate(project: Path, dry_run: bool, no_backup: bool) -> None:
    """Upgrade an MVP-era project to the Imbizo-CS v1.0 schema."""

    project_root = project.expanduser().resolve()
    if not project_root.is_dir():
        raise click.ClickException(f"Project path must be a folder: {project_root}")
    database_path = project_root / "project.sqlite"
    if not database_path.exists():
        raise click.ClickException(f"Project database not found: {database_path}")

    try:
        _validate_sqlite_database(database_path)
        dry_report = migrate_project(project_root, dry_run=True)
    except (OSError, sqlite3.Error, RuntimeError, ValueError) as exc:
        raise click.ClickException(f"Could not inspect project database. No migration was applied. {exc}") from exc

    if dry_run:
        _print_dry_run(dry_report)
        return

    _ensure_project_writable(project_root)
    _ensure_free_space(project_root)
    pre_hash = _sha256_file(database_path)
    backup_zip: Path | None = None
    if not no_backup:
        backup_zip = _create_backup_zip(project_root)
        click.echo(f"Backup zip: {backup_zip}")
    else:
        click.echo("Warning: automatic backup disabled by --no-backup.")

    try:
        report = migrate_project(project_root, create_backup=not no_backup)
    except (OSError, sqlite3.Error, RuntimeError, ValueError) as exc:
        raise click.ClickException(f"Migration failed after backup step. {exc}") from exc

    post_hash = _sha256_file(database_path)
    version = _schema_version_from_db(database_path)
    dictionary_versions = _collect_dictionary_versions(project_root)
    report_path = _write_migration_report(
        project_root=project_root,
        report=report,
        backup_zip=backup_zip,
        pre_db_sha256=pre_hash,
        post_db_sha256=post_hash,
        dictionary_versions=dictionary_versions,
    )
    click.echo("Migration verification summary")
    click.echo(f"- Schema version: {version}")
    click.echo(f"- Backup zip exists: {bool(backup_zip and backup_zip.exists())}")
    click.echo(f"- SQLite backup exists: {bool(report.backup_path and report.backup_path.exists())}")
    click.echo(f"- Provenance event id: {report.provenance_event_id}")
    click.echo(f"- Migration report: {report_path}")


@cli.command()
@click.option("--from", "backup_zip", required=True, type=click.Path(exists=True, path_type=Path))
@click.option("--to", "project_dir", required=True, type=click.Path(path_type=Path))
def restore(backup_zip: Path, project_dir: Path) -> None:
    """Restore a project from a pre-migration backup zip."""

    source = backup_zip.expanduser().resolve()
    target = project_dir.expanduser().resolve()
    if target.exists() and any(target.iterdir()):
        raise click.ClickException(
            "Restore target already exists and is not empty. Choose an empty folder to avoid overwriting research data."
        )
    target.mkdir(parents=True, exist_ok=True)
    try:
        _safe_extract_zip(source, target)
    except (OSError, zipfile.BadZipFile, ValueError) as exc:
        raise click.ClickException(f"Restore failed. {exc}") from exc
    database_path = target / "project.sqlite"
    if not database_path.exists():
        raise click.ClickException("Restore completed, but project.sqlite was not found in the restored folder.")
    version = _schema_version_from_db(database_path)
    click.echo("Restore complete.")
    click.echo(f"- Restored project: {target}")
    click.echo(f"- Schema version: {version}")
    click.echo("- If this restored an MVP backup, schema version should be the MVP version or lack v1.0 tables.")


def _print_dry_run(report: MigrationReport) -> None:
    click.echo("Imbizo-CS v1.0 migration dry run")
    click.echo(f"Project: {report.project_path}")
    click.echo(f"Database: {report.database_path}")
    click.echo(f"Current schema version: {report.previous_version}")
    click.echo(f"Target schema version: {report.target_version}")
    click.echo("Schema diff:")
    for statement in report.statements:
        click.echo(f"- {_summarize_statement(statement)}")
    if report.skipped_columns:
        click.echo(f"Already-present token columns: {', '.join(report.skipped_columns)}")
    click.echo("No files were modified.")


def _validate_sqlite_database(database_path: Path) -> None:
    with sqlite3.connect(database_path) as connection:
        row = connection.execute("PRAGMA quick_check").fetchone()
        if row is None or row[0] != "ok":
            raise sqlite3.DatabaseError(f"SQLite quick_check failed: {row[0] if row else 'no result'}")
        required = {"project_metadata", "tokens"}
        existing = {
            item[0]
            for item in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('project_metadata', 'tokens')"
            ).fetchall()
        }
        missing = required - existing
        if missing:
            raise sqlite3.DatabaseError(f"Not an Imbizo MVP project database; missing tables: {sorted(missing)}")


def _ensure_project_writable(project_root: Path) -> None:
    if not os.access(project_root, os.W_OK):
        raise click.ClickException(f"Project folder is not writable: {project_root}")
    probe = project_root / ".imbizo_write_check"
    try:
        probe.write_text("write-check", encoding="utf-8")
    except OSError as exc:
        raise click.ClickException(f"Project folder appears to be on read-only media: {project_root}") from exc
    finally:
        if probe.exists():
            probe.unlink()


def _ensure_free_space(project_root: Path) -> None:
    project_size = _directory_size(project_root)
    free = shutil.disk_usage(project_root).free
    if free < project_size * 2:
        raise click.ClickException(
            f"Insufficient free disk space. Need at least 2x project size ({project_size * 2} bytes), "
            f"but only {free} bytes are free."
        )


def _directory_size(path: Path) -> int:
    total = 0
    for item in path.rglob("*"):
        if item.is_file():
            total += item.stat().st_size
    return total


def _create_backup_zip(project_root: Path) -> Path:
    backup_dir = project_root / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = utc_now().replace(":", "").replace("-", "")
    backup_path = backup_dir / f"{project_root.name}.v1_0_pre_{stamp}.zip"
    with zipfile.ZipFile(backup_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for item in sorted(project_root.rglob("*")):
            if not item.is_file() or item == backup_path:
                continue
            archive.write(item, item.relative_to(project_root))
    return backup_path


def _safe_extract_zip(source: Path, target: Path) -> None:
    with zipfile.ZipFile(source) as archive:
        for member in archive.infolist():
            resolved = (target / member.filename).resolve()
            if os.path.commonpath([str(target), str(resolved)]) != str(target):
                raise ValueError(f"Unsafe path in backup zip: {member.filename}")
        archive.extractall(target)


def _schema_version_from_db(database_path: Path) -> str:
    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
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
    return "unknown"


def _collect_dictionary_versions(project_root: Path) -> list[dict[str, str]]:
    roots = [
        project_root / "dictionaries",
        Path.cwd() / "dictionaries",
        Path(__file__).resolve().parents[2] / "dictionaries",
    ]
    seen: set[Path] = set()
    versions: list[dict[str, str]] = []
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.yaml")):
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            with path.open("r", encoding="utf-8") as handle:
                data = yaml.safe_load(handle) or {}
            if isinstance(data, dict):
                versions.append(
                    {
                        "path": str(path),
                        "language_code": str(data.get("language_code", "")),
                        "version": str(data.get("version", "")),
                        "source": str(data.get("source", "")),
                    }
                )
    return versions


def _write_migration_report(
    *,
    project_root: Path,
    report: MigrationReport,
    backup_zip: Path | None,
    pre_db_sha256: str,
    post_db_sha256: str,
    dictionary_versions: list[dict[str, str]],
) -> Path:
    report_path = project_root / "migration_report_v1_0.md"
    dictionary_lines = "\n".join(
        f"- `{item['path']}`: language `{item['language_code']}`, version `{item['version']}`, source {item['source']}"
        for item in dictionary_versions
    ) or "- No dictionary YAML files were found during migration."
    diff_lines = "\n".join(f"- {_summarize_statement(statement)}" for statement in report.statements)
    report_path.write_text(
        f"""# Imbizo-CS v1.0 Migration Report

Timestamp: {utc_now()}

Imbizo-CS version: MVP-era project -> {__version__}

Schema version: {report.previous_version} -> {report.target_version}

Backup zip: {backup_zip if backup_zip else 'disabled by --no-backup'}

SQLite pre-migration backup: {report.backup_path if report.backup_path else 'not created'}

## Schema Diff Summary

{diff_lines}

## Dictionary Versions Loaded

{dictionary_lines}

## Provenance

Provenance event id: {report.provenance_event_id}

## Database Hashes

- Pre-migration `project.sqlite` SHA-256: `{pre_db_sha256}`
- Post-migration `project.sqlite` SHA-256: `{post_db_sha256}`

## Reproducibility Statement

To reproduce this migration, restore the backup zip, install Imbizo-CS v1.0
from the same offline bundle, and run `imbizo-cs migrate --project <project>`.
No telemetry, network service, or external API is required.
""",
        encoding="utf-8",
    )
    return report_path


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _summarize_statement(statement: str) -> str:
    compact = " ".join(statement.strip().split())
    if compact.upper().startswith("ALTER TABLE TOKENS ADD COLUMN"):
        return compact
    if compact.upper().startswith("CREATE TABLE IF NOT EXISTS"):
        return compact.split("(")[0].strip()
    if compact.upper().startswith("CREATE INDEX IF NOT EXISTS"):
        return compact.split(" ON ")[0].strip()
    return compact


if __name__ == "__main__":
    cli()
