"""Verify that the package imports from local files."""

from __future__ import annotations


def main() -> int:
    """Import core modules used by offline workflows."""

    import imbizo
    from imbizo.services.project_service import ProjectService

    print(f"Imported Imbizo-CS Workbench {imbizo.__version__}")
    print(ProjectService.__name__)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
