"""Click CLI for local Imbizo-CS migration and restore workflows."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import os
from pathlib import Path
import shutil
import tempfile
import zipfile

import click

from imbizo.core.migrations import v1_5


IMBIZO_VERSION = "1.5"
MIN_FREE_SPACE_FACTOR = 2


@dataclass(slots=True)
class RestoreReport:
    """Summary of a local restore operation."""

    backup_zip: Path
    project_dir: Path
    expected_db_sha256: str
    restored_db_sha256: str
    matched: bool


@click.group()
def cli() -> None:
    """Manage local Imbizo-CS projects without network access."""


@click.command()
@click.option("--project", required=True, type=click.Path(exists=True, path_type=Path))
@click.option("--target", type=click.Choice(["v1.0", "v1.5"]), default="v1.5")
@click.option("--dry-run", is_flag=True, default=False)
@click.option("--no-backup", is_flag=True, default=False)
def migrate(project: Path, target: str, dry_run: bool, no_backup: bool) -> None:
    """Upgrade a project to the requested Imbizo-CS schema version."""

    project = project.resolve()
    database_path = v1_5._find_database(project)
    current_version = v1_5.detect_schema_version(database_path)
    click.echo(f"Project: {project}")
    click.echo(f"Current schema: {current_version}")
    click.echo(f"Requested target: {target}")

    if target == "v1.0":
        _migrate_to_v1_0(project, current_version, dry_run)
        return

    if v1_5._version_key(current_version) < v1_5._version_key("1.0"):
        raise click.ClickException(
            "This is an MVP-era project. Apply the v1.0 migration first, then rerun "
            "`imbizo-cs migrate --target v1.5`."
        )
    if v1_5._version_key(current_version) >= v1_5._version_key("1.5"):
        click.echo("Project is already at v1.5 or later; no migration is needed.")
        return

    if dry_run:
        report = v1_5.migrate_project(project, dry_run=True)
        _print_v1_5_diff(report)
        return

    _assert_project_writable(project)
    _assert_enough_free_space(project)
    if no_backup:
        confirmation = click.prompt(
            "Automatic backup is strongly discouraged to disable. Type NO BACKUP to continue",
            default="",
            show_default=False,
        )
        if confirmation != "NO BACKUP":
            raise click.ClickException("Migration cancelled because backup confirmation did not match.")

    report = v1_5.migrate_project(project, dry_run=False, no_backup=no_backup)
    click.echo("Migration complete.")
    click.echo(f"Backup: {report.backup_path or 'not created'}")
    click.echo(f"Report: {report.report_path or 'not written'}")
    click.echo(f"Provenance event: {report.provenance_event_id or 'not written'}")
    click.echo(f"Pre-migration DB SHA-256: {report.pre_migration_db_sha256}")
    click.echo(f"Post-migration DB SHA-256: {report.post_migration_db_sha256}")


@click.command(name="restore")
@click.option("--from", "backup_zip", required=True, type=click.Path(exists=True, path_type=Path))
@click.option("--to", "project_dir", required=True, type=click.Path(path_type=Path))
def restore(backup_zip: Path, project_dir: Path) -> None:
    """Restore a project from a pre-migration backup zip."""

    report = restore_project_from_backup(backup_zip.resolve(), project_dir.resolve())
    click.echo("Restore complete.")
    click.echo(f"Restored project: {report.project_dir}")
    click.echo(f"Expected DB SHA-256: {report.expected_db_sha256}")
    click.echo(f"Restored DB SHA-256: {report.restored_db_sha256}")
    if not report.matched:
        raise click.ClickException("Restored database hash did not match the backup.")
    click.echo("Verification: restored database hash matches the backup.")


def restore_project_from_backup(backup_zip: Path, project_dir: Path) -> RestoreReport:
    """Restore a project directory from a local backup zip and verify DB hash."""

    expected_hash = _database_hash_from_zip(backup_zip)
    if project_dir.exists() and any(project_dir.iterdir()):
        confirmation = click.prompt(
            f"{project_dir} is not empty. Type RESTORE to replace its contents",
            default="",
            show_default=False,
        )
        if confirmation != "RESTORE":
            raise click.ClickException("Restore cancelled because confirmation did not match.")
        shutil.rmtree(project_dir)
    project_dir.mkdir(parents=True, exist_ok=True)
    _safe_extract_zip(backup_zip, project_dir)
    restored_db = v1_5._find_database(project_dir)
    restored_hash = v1_5._sha256_file(restored_db)
    return RestoreReport(
        backup_zip=backup_zip,
        project_dir=project_dir,
        expected_db_sha256=expected_hash,
        restored_db_sha256=restored_hash,
        matched=expected_hash == restored_hash,
    )


def _migrate_to_v1_0(project: Path, current_version: str, dry_run: bool) -> None:
    if v1_5._version_key(current_version) >= v1_5._version_key("1.0"):
        click.echo("Project is already at v1.0 or later; no migration is needed.")
        return
    try:
        from imbizo.core.migrations import v1_0
    except ImportError as exc:
        raise click.ClickException(
            "The v1.0 migration module is not installed in this build. Install the "
            "v1.0 offline bundle first, run its migration, then install v1.5."
        ) from exc
    if dry_run:
        click.echo("Dry run: v1.0 migration module is available; no files were modified.")
        return
    v1_0.migrate_project(project, dry_run=False)


def _print_v1_5_diff(report: v1_5.MigrationReport) -> None:
    click.echo("Dry run only; no files were modified.")
    click.echo("Columns that would be added:")
    for column in report.added_columns:
        click.echo(f"  - tokens.{column}")
    if not report.added_columns:
        click.echo("  - none")
    click.echo("Tables that would be created:")
    for table in report.created_tables:
        click.echo(f"  - {table}")
    if not report.created_tables:
        click.echo("  - none")
    click.echo("Dictionary versions detected:")
    for key, value in sorted(report.dictionary_versions.items()):
        click.echo(f"  - {key}: {value}")
    if not report.dictionary_versions:
        click.echo("  - none")


def _assert_project_writable(project: Path) -> None:
    if not os.access(project, os.W_OK):
        raise click.ClickException(f"Project folder is not writable: {project}")
    try:
        with tempfile.NamedTemporaryFile(prefix=".imbizo_write_test_", dir=project, delete=True):
            pass
    except OSError as exc:
        raise click.ClickException(f"Project folder appears to be read-only: {project}") from exc


def _assert_enough_free_space(project: Path) -> None:
    project_size = _directory_size(project)
    free_space = shutil.disk_usage(project).free
    required = project_size * MIN_FREE_SPACE_FACTOR
    if free_space < required:
        raise click.ClickException(
            f"Not enough free disk space for a safe migration. Need at least {required} bytes "
            f"(2x project size), but only {free_space} bytes are available."
        )


def _directory_size(path: Path) -> int:
    total = 0
    for item in path.rglob("*"):
        if item.is_file():
            total += item.stat().st_size
    return total


def _database_hash_from_zip(backup_zip: Path) -> str:
    candidates = {"imbizo.sqlite", "project.sqlite", "database.sqlite", "data/project.sqlite"}
    with zipfile.ZipFile(backup_zip) as archive:
        names = archive.namelist()
        for name in names:
            normalized = name.replace("\\", "/")
            if normalized in candidates or normalized.endswith(".sqlite"):
                return sha256(archive.read(name)).hexdigest()
    raise click.ClickException(f"No SQLite database found inside backup: {backup_zip}")


def _safe_extract_zip(backup_zip: Path, project_dir: Path) -> None:
    with zipfile.ZipFile(backup_zip) as archive:
        for member in archive.infolist():
            destination = (project_dir / member.filename).resolve()
            if project_dir not in destination.parents and destination != project_dir:
                raise click.ClickException(f"Unsafe path in backup zip: {member.filename}")
        archive.extractall(project_dir)


cli.add_command(migrate)
cli.add_command(restore)


if __name__ == "__main__":
    cli()
