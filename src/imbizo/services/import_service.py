"""Safe local import service."""

from __future__ import annotations

import hashlib
import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from imbizo.app.errors import ImportFailure
from imbizo.domain.project import ProjectContext
from imbizo.domain.provenance import make_provenance_record
from imbizo.importers.audio import AudioImporter
from imbizo.importers.base import ImportedBundle, ImportOptions, Importer
from imbizo.importers.csv_importer import CsvTranscriptImporter
from imbizo.importers.eaf import EafImporter
from imbizo.importers.json_importer import JsonTranscriptImporter
from imbizo.importers.spreadsheet import SpreadsheetImporter
from imbizo.importers.textgrid import TextGridImporter
from imbizo.importers.txt import TxtImporter
from imbizo.importers.video import VideoImporter
from imbizo.importers.xml_importer import XmlTranscriptImporter
from imbizo.persistence.repositories import ImportRepository, MediaRepository, TranscriptRepository
from imbizo.services.provenance_service import ProvenanceService


@dataclass(slots=True)
class ImportResult:
    """Result of one local import."""

    batch_id: str
    bundle: ImportedBundle
    copied_path: Path
    report: dict[str, object]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class ImportService:
    """Coordinate safe local imports."""

    def __init__(self, importers: Sequence[Importer] | None = None) -> None:
        self.importers: list[Importer] = list(importers) if importers else [
            TxtImporter(),
            CsvTranscriptImporter(),
            EafImporter(),
            XmlTranscriptImporter(),
            TextGridImporter(),
            JsonTranscriptImporter(),
            SpreadsheetImporter(),
            AudioImporter(),
            VideoImporter(),
        ]

    def list_supported_formats(self) -> list[str]:
        """Return supported import format names."""

        return [importer.name for importer in self.importers]

    def import_file(self, context: ProjectContext, source_path: Path, options: ImportOptions | None = None) -> ImportResult:
        """Copy and import a source file into a project."""

        options = options or ImportOptions()
        source_path = source_path.expanduser().resolve()
        if not source_path.exists():
            raise ImportFailure(f"The source file does not exist: {source_path}")
        importer = next((item for item in self.importers if item.can_import(source_path)), None)
        if importer is None:
            raise ImportFailure(f"No local importer is available for {source_path.name}.")

        batch_id = str(uuid.uuid4())
        copied_path = context.paths.imports_original / f"{batch_id}_{source_path.name}"
        shutil.copy2(source_path, copied_path)
        source_hash = _sha256(copied_path)
        bundle = importer.import_file(copied_path, options)
        relative_copied = copied_path.relative_to(context.paths.root)

        ImportRepository(context.connection).save_import_batch(
            batch_id=batch_id,
            source_label=source_path.name,
            original_path=str(source_path),
            copied_path=str(relative_copied),
            importer_name=importer.name,
            source_sha256=source_hash,
            report=bundle.report,
        )
        for media in bundle.media_assets:
            media.import_batch_id = batch_id
            media.relative_path = str(relative_copied)
            media.sha256 = source_hash
            MediaRepository(context.connection).save_media(media)
        if bundle.document:
            bundle.document.import_batch_id = batch_id
            bundle.document.relative_path = str(relative_copied)
            TranscriptRepository(context.connection).save_document_bundle(bundle.document, bundle.segments, bundle.tokens)
        ProvenanceService().record(
            context,
            make_provenance_record(
                "import",
                "importer",
                target_id=batch_id,
                source=str(source_path),
                copied_path=str(relative_copied),
                importer=importer.name,
                report=bundle.report,
            ),
        )
        return ImportResult(batch_id=batch_id, bundle=bundle, copied_path=copied_path, report=bundle.report)

    def import_many(self, context: ProjectContext, source_paths: Sequence[Path], options: ImportOptions | None = None) -> list[ImportResult]:
        """Import multiple files sequentially with individual reports."""

        return [self.import_file(context, path, options) for path in source_paths]
