"""Safe local import service."""

from __future__ import annotations

import hashlib
import shutil
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from imbizo.app.errors import ImportFailure
from imbizo.app.time import utc_now
from imbizo.domain.annotations import Annotation, AnnotationSource
from imbizo.domain.project import ProjectContext
from imbizo.domain.provenance import make_provenance_record
from imbizo.importers.audio import AudioImporter
from imbizo.importers.base import ImportedBundle, ImportOptions, ImportProgress, Importer
from imbizo.importers.csv_importer import CsvTranscriptImporter
from imbizo.importers.eaf import EafImporter
from imbizo.importers.json_importer import JsonTranscriptImporter
from imbizo.importers.spreadsheet import SpreadsheetImporter
from imbizo.importers.textgrid import TextGridImporter
from imbizo.importers.txt import TxtImporter
from imbizo.importers.video import VideoImporter
from imbizo.importers.xml_importer import XmlTranscriptImporter
from imbizo.persistence.repositories import AnnotationRepository, ImportRepository, LanguageRepository, MediaRepository, TranscriptRepository
from imbizo.services.provenance_service import ProvenanceService


@dataclass(slots=True)
class ImportResult:
    """Result of one local import."""

    batch_id: str
    bundle: ImportedBundle
    copied_path: Path
    report: dict[str, object]


def _sha256(path: Path, options: ImportOptions | None = None) -> str:
    digest = hashlib.sha256()
    total = max(path.stat().st_size, 1)
    done = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
            done += len(chunk)
            if options is not None:
                _emit_progress(options, "hash", f"Verifying {path.name}", _scaled(done, total, 25, 35), 100)
    return digest.hexdigest()


def _emit_progress(options: ImportOptions, stage: str, message: str, current: int, total: int) -> None:
    """Notify a GUI or CLI progress observer when one is attached."""

    if options.progress_callback is not None:
        options.progress_callback(ImportProgress(stage=stage, message=message, current=current, total=total))


def _scaled(done: int, total: int, start: int, end: int) -> int:
    """Scale byte progress into an inclusive integer range."""

    if total <= 0:
        return end
    return min(end, max(start, start + int(done / total * (end - start))))


def _copy_with_progress(source_path: Path, copied_path: Path, options: ImportOptions) -> None:
    """Copy a file in chunks so large imports can update the progress UI."""

    total = max(source_path.stat().st_size, 1)
    done = 0
    copied_path.parent.mkdir(parents=True, exist_ok=True)
    with source_path.open("rb") as source, copied_path.open("wb") as destination:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            destination.write(chunk)
            done += len(chunk)
            _emit_progress(options, "copy", f"Copying {source_path.name}", _scaled(done, total, 10, 25), 100)
    shutil.copystat(source_path, copied_path)


def _save_progress_callback(options: ImportOptions) -> Callable[[str, int, int], None]:
    """Return a repository callback that maps row-save progress to 85-99%."""

    def update(message: str, done: int, total: int) -> None:
        _emit_progress(options, "save", message, _scaled(done, total, 85, 99), 100)

    return update


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

        _emit_progress(options, "preflight", f"Preparing {source_path.name}", 0, 100)
        batch_id = str(uuid.uuid4())
        copied_path = context.paths.imports_original / f"{batch_id}_{source_path.name}"
        _emit_progress(options, "copy", f"Copying {source_path.name} into the project", 10, 100)
        _copy_with_progress(source_path, copied_path, options)
        _emit_progress(options, "hash", f"Verifying local copy of {source_path.name}", 25, 100)
        source_hash = _sha256(copied_path, options)
        _emit_progress(options, "parse", f"Reading {source_path.name}", 35, 100)
        bundle = importer.import_file(copied_path, options)
        relative_copied = copied_path.relative_to(context.paths.root)

        _emit_progress(options, "save", "Saving imported rows to the project database", 85, 100)
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
            TranscriptRepository(context.connection).save_document_bundle(
                bundle.document,
                bundle.segments,
                bundle.tokens,
                progress_callback=_save_progress_callback(options),
            )
            self._save_imported_language_annotations(context, bundle.token_language_codes)
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
        _emit_progress(options, "complete", f"Finished importing {source_path.name}", 100, 100)
        return ImportResult(batch_id=batch_id, bundle=bundle, copied_path=copied_path, report=bundle.report)

    def import_many(self, context: ProjectContext, source_paths: Sequence[Path], options: ImportOptions | None = None) -> list[ImportResult]:
        """Import multiple files sequentially with individual reports."""

        return [self.import_file(context, path, options) for path in source_paths]

    def _save_imported_language_annotations(self, context: ProjectContext, token_language_codes: dict[str, str]) -> None:
        """Persist language labels that came from the imported local file."""

        if not token_language_codes:
            return
        languages_by_code = {language.code.lower(): language.id for language in LanguageRepository(context.connection).list_languages()}
        now = utc_now()
        annotations: list[Annotation] = []
        for token_id, code in token_language_codes.items():
            language_id = languages_by_code.get(code.strip().lower())
            if language_id is None:
                continue
            annotations.append(
                Annotation(
                    id=str(uuid.uuid4()),
                    token_id=token_id,
                    source=AnnotationSource.IMPORTED,
                    language_id=language_id,
                    auto_confidence=1.0,
                    created_by="importer",
                    created_at=now,
                    updated_at=now,
                )
            )
        AnnotationRepository(context.connection).save_imported_annotations(annotations)
