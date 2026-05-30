"""Project-open progress regression tests."""

from __future__ import annotations

from pathlib import Path

from imbizo.domain.project import ProjectMetadata
from imbizo.services.project_service import ProjectOpenProgress, ProjectService


def test_open_project_reports_progress_without_changing_context(tmp_path: Path) -> None:
    """Opening a project emits visible milestones for the GUI progress bar."""

    service = ProjectService()
    created = service.create_project(
        tmp_path / "project",
        ProjectMetadata(project_uuid="", title="Progress Test"),
    )
    service.close_project(created)
    updates: list[ProjectOpenProgress] = []

    opened = service.open_project(created.paths.root, progress_callback=updates.append)

    try:
        assert opened.metadata.title == "Progress Test"
        assert [update.stage for update in updates] == [
            "check_folder",
            "open_database",
            "migrate_database",
            "load_metadata",
            "prepare_workspace",
            "ready",
        ]
        assert updates[0].current == 5
        assert updates[-1].current == 100
        assert updates[-1].message == "Project ready"
    finally:
        service.close_project(opened)


def test_open_project_still_supports_plain_synchronous_call(tmp_path: Path) -> None:
    """CLI callers can keep using open_project without a progress callback."""

    service = ProjectService()
    created = service.create_project(
        tmp_path / "project",
        ProjectMetadata(project_uuid="", title="Plain Open Test"),
    )
    service.close_project(created)

    opened = service.open_project(created.paths.root)

    try:
        assert opened.metadata.title == "Plain Open Test"
    finally:
        service.close_project(opened)
