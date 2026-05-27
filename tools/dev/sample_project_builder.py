"""Build a tiny local sample project for manual testing."""

from __future__ import annotations

from pathlib import Path

from imbizo.domain.project import ProjectMetadata
from imbizo.services.project_service import ProjectService


def main() -> int:
    """Create a tiny sample project under examples/demo_project_minimal/project."""

    root = Path("examples/demo_project_minimal/project")
    if root.exists():
        print(f"Project already exists: {root}")
        return 0
    ProjectService().create_project(root, ProjectMetadata(project_uuid="", title="Demo Project"))
    print(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
