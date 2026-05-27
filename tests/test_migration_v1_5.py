from __future__ import annotations

from pathlib import Path
import sqlite3

from click.testing import CliRunner
import pytest

from imbizo.cli import migrate, restore_project_from_backup
from imbizo.core.migrations.v1_5 import detect_schema_version, migrate_project


def _create_project(tmp_path: Path, version: str | None = "1.0", with_v1_data: bool = False) -> Path:
    project = tmp_path / "project"
    project.mkdir()
    db = project / "project.sqlite"
    with sqlite3.connect(db) as conn:
        conn.execute("CREATE TABLE tokens (id TEXT PRIMARY KEY, surface TEXT NOT NULL)")
        conn.execute("INSERT INTO tokens (id, surface) VALUES ('t1', 'i-laptop')")
        if version is not None:
            conn.execute("CREATE TABLE schema_version (version TEXT NOT NULL, applied_at TEXT NOT NULL)")
            conn.execute("INSERT INTO schema_version (version, applied_at) VALUES (?, '2026-05-27T00:00:00Z')", (version,))
        if with_v1_data:
            conn.execute(
                "CREATE TABLE concord_links (id TEXT PRIMARY KEY, head_token_id TEXT, dependent_token_id TEXT)"
            )
            conn.execute(
                "CREATE TABLE four_m_audit (id TEXT PRIMARY KEY, utterance_id TEXT, verdict TEXT)"
            )
            conn.execute("INSERT INTO concord_links VALUES ('cl1', 't1', 't1')")
            conn.execute("INSERT INTO four_m_audit VALUES ('fm1', 'u1', 'consistent')")
    return project


def _db_hash(project: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with (project / "project.sqlite").open("rb") as handle:
        digest.update(handle.read())
    return digest.hexdigest()


def test_migrate_v1_project_with_zero_v1_annotations(tmp_path: Path) -> None:
    project = _create_project(tmp_path)
    report = migrate_project(project)
    assert report.applied
    assert detect_schema_version(project / "project.sqlite") == "1.5"
    with sqlite3.connect(project / "project.sqlite") as conn:
        columns = {row[1] for row in conn.execute("PRAGMA table_xinfo(tokens)")}
        assert "sister_lang_confidence" in columns
        row = conn.execute("SELECT sister_lang_confidence FROM tokens WHERE id='t1'").fetchone()
        assert row == (None,)
    assert (project / "migration_report_v1_5.md").exists()


def test_migrate_preserves_v1_concord_and_four_m_data(tmp_path: Path) -> None:
    project = _create_project(tmp_path, with_v1_data=True)
    migrate_project(project)
    with sqlite3.connect(project / "project.sqlite") as conn:
        assert conn.execute("SELECT COUNT(*) FROM concord_links").fetchone() == (1,)
        assert conn.execute("SELECT COUNT(*) FROM four_m_audit").fetchone() == (1,)
        assert conn.execute("SELECT phon_integration_score FROM tokens WHERE id='t1'").fetchone() == (None,)


def test_migrate_mvp_project_is_refused(tmp_path: Path) -> None:
    project = _create_project(tmp_path, version=None)
    with pytest.raises(RuntimeError, match="v1.0 migration"):
        migrate_project(project)


def test_migrate_twice_is_noop(tmp_path: Path) -> None:
    project = _create_project(tmp_path)
    first = migrate_project(project)
    second = migrate_project(project)
    assert first.applied
    assert not second.applied
    assert second.message == "Project is already at v1.5 or later."


def test_restore_from_backup_has_exact_database_hash(tmp_path: Path) -> None:
    project = _create_project(tmp_path)
    report = migrate_project(project)
    assert report.backup_path is not None
    restored = tmp_path / "restored"
    restore_report = restore_project_from_backup(report.backup_path, restored)
    assert restore_report.matched
    assert restore_report.expected_db_sha256 == restore_report.restored_db_sha256
    assert detect_schema_version(restored / "project.sqlite") == "1.0"


def test_cli_migrate_dry_run_has_no_writes_and_prints_diff(tmp_path: Path) -> None:
    project = _create_project(tmp_path)
    before = _db_hash(project)
    result = CliRunner().invoke(migrate, ["--project", str(project), "--target", "v1.5", "--dry-run"])
    after = _db_hash(project)
    assert result.exit_code == 0
    assert before == after
    assert "Columns that would be added" in result.output
    assert "trigger_links" in result.output


def test_migrate_with_mixed_code_disabled_populates_no_spans(tmp_path: Path) -> None:
    project = _create_project(tmp_path)
    migrate_project(project)
    with sqlite3.connect(project / "project.sqlite") as conn:
        assert conn.execute("SELECT COUNT(*) FROM mixed_code_spans").fetchone() == (0,)
