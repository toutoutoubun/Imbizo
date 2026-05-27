"""Project lifecycle service."""

from __future__ import annotations

import json
import shutil
import uuid
import zipfile
from pathlib import Path

from imbizo import __version__
from imbizo.app.errors import ProjectError
from imbizo.app.time import utc_now
from imbizo.domain.project import ProjectContext, ProjectMetadata, ProjectPaths
from imbizo.domain.provenance import make_provenance_record
from imbizo.persistence.connection import open_project_database
from imbizo.persistence.migrations import CURRENT_SCHEMA_VERSION, initialize_database, migrate_database
from imbizo.persistence.repositories import ProjectRepository
from imbizo.services.provenance_service import ProvenanceService


class ProjectService:
    """Coordinate local project lifecycle operations."""

    def create_project(self, root: Path, metadata: ProjectMetadata) -> ProjectContext:
        """Create a project folder, database, and standard subdirectories."""

        paths = ProjectPaths.from_root(root)
        if paths.database.exists():
            raise ProjectError("A project already exists in that folder.")
        paths.ensure_all()
        now = utc_now()
        metadata.project_uuid = metadata.project_uuid or str(uuid.uuid4())
        metadata.app_version = __version__
        metadata.schema_version = CURRENT_SCHEMA_VERSION
        metadata.created_at = metadata.created_at or now
        metadata.updated_at = metadata.updated_at or now
        connection = open_project_database(paths.database)
        initialize_database(connection, metadata)
        context = ProjectContext(paths=paths, metadata=ProjectRepository(connection).get_metadata(), connection=connection)
        self._write_project_json(context)
        ProvenanceService().record(context, make_provenance_record("import", "system", message="Project created locally."))
        return context

    def open_project(self, root: Path) -> ProjectContext:
        """Open an existing local project folder."""

        paths = ProjectPaths.from_root(root)
        if not paths.database.exists():
            raise ProjectError("No project.sqlite file was found in that folder.")
        paths.ensure_all()
        connection = open_project_database(paths.database)
        migrate_database(connection)
        metadata = ProjectRepository(connection).get_metadata()
        return ProjectContext(paths=paths, metadata=metadata, connection=connection)

    def close_project(self, context: ProjectContext) -> None:
        """Close local resources for an open project."""

        context.connection.close()

    def export_project_zip(self, context: ProjectContext, destination: Path) -> Path:
        """Write a local zip archive containing the project folder contents."""

        destination.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in context.paths.root.rglob("*"):
                if path.is_file():
                    archive.write(path, path.relative_to(context.paths.root))
        return destination

    def import_project_zip(self, archive_path: Path, destination_root: Path) -> ProjectContext:
        """Import a local project zip into a new project folder."""

        destination_root.mkdir(parents=True, exist_ok=False)
        with zipfile.ZipFile(archive_path, "r") as archive:
            archive.extractall(destination_root)
        return self.open_project(destination_root)

    def _write_project_json(self, context: ProjectContext) -> None:
        data = {
            "project_uuid": context.metadata.project_uuid,
            "title": context.metadata.title,
            "researcher": context.metadata.researcher,
            "institution": context.metadata.institution,
            "location": context.metadata.location,
            "project_date": context.metadata.project_date,
            "irb_rec_reference": context.metadata.irb_rec_reference,
            "care_acknowledgement": context.metadata.care_acknowledgement,
            "schema_version": context.metadata.schema_version,
            "updated_at": context.metadata.updated_at,
        }
        context.paths.project_json.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
