"""Local export service."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from imbizo.app.errors import ExportFailure
from imbizo.app.time import utc_now
from imbizo.core.security import require_local_export_destination
from imbizo.domain.exports import ExportRecord
from imbizo.domain.project import ProjectContext
from imbizo.domain.provenance import make_provenance_record
from imbizo.exporters.base import ExportOptions, ExportPackage, Exporter
from imbizo.exporters.csv_exporter import CsvExporter
from imbizo.exporters.eaf import EafExporter
from imbizo.exporters.html import HtmlExporter
from imbizo.exporters.json_exporter import JsonExporter
from imbizo.exporters.pdf import PdfExporter
from imbizo.exporters.quotation import QuotationExporter
from imbizo.exporters.textgrid import TextGridExporter
from imbizo.exporters.xlsx import XlsxExporter
from imbizo.persistence.repositories import AnnotationRepository, ExportRepository, LanguageRepository, ProjectRepository, TranscriptRepository
from imbizo.services.provenance_service import ProvenanceService


@dataclass(slots=True)
class ExportRequest:
    """A local export request."""

    format_name: str
    destination: Path
    options: ExportOptions = field(default_factory=ExportOptions)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class ExportService:
    """Coordinate local project exports."""

    def __init__(self, exporters: list[Exporter] | None = None) -> None:
        self.exporters = exporters or [
            CsvExporter(),
            XlsxExporter(),
            JsonExporter(),
            EafExporter(),
            TextGridExporter(),
            HtmlExporter(),
            PdfExporter(),
            QuotationExporter(),
        ]

    def list_supported_exports(self) -> list[str]:
        """Return supported export format names."""

        return [exporter.format_name for exporter in self.exporters]

    def export(self, context: ProjectContext, request: ExportRequest) -> ExportRecord:
        """Write a local export file and record it in project storage."""

        require_local_export_destination(request.destination)
        exporter = next((item for item in self.exporters if item.format_name == request.format_name), None)
        if exporter is None:
            raise ExportFailure(f"No local exporter is available for {request.format_name}.")
        package = self._build_package(context)
        exported = exporter.export(package, request.destination, request.options)
        self._write_citation_sidecar(exported.path, context)
        record = ExportRecord(
            id=str(uuid.uuid4()),
            export_format=request.format_name,
            relative_path=str(exported.path),
            options={"include_auto": request.options.include_auto, "include_memos": request.options.include_memos},
            sha256=_sha256(exported.path),
            created_at=utc_now(),
        )
        ExportRepository(context.connection).save(record)
        ProvenanceService().record(
            context,
            make_provenance_record("export", "exporter", target_id=record.id, format=request.format_name, path=str(exported.path)),
        )
        return record

    def _write_citation_sidecar(self, exported_path: Path, context: ProjectContext) -> None:
        citation = f"""cff-version: 1.2.0
message: "If you use this Imbizo-CS export, cite the software and preserve the project provenance."
title: "Imbizo-CS Workbench export from {context.metadata.title}"
version: "0.1.0"
doi: "10.0000/imbizo-cs-workbench.placeholder"
license: "GPL-3.0-or-later"
authors:
  - name: "Imbizo-CS Workbench Contributors"
"""
        exported_path.with_name(exported_path.name + ".CITATION.cff").write_text(citation, encoding="utf-8")

    def _build_package(self, context: ProjectContext) -> ExportPackage:
        transcript_repo = TranscriptRepository(context.connection)
        documents = transcript_repo.list_documents()
        segments = []
        tokens = []
        for document in documents:
            document_segments = transcript_repo.list_segments(document.id)
            segments.extend(document_segments)
            for segment in document_segments:
                tokens.extend(transcript_repo.list_tokens(segment.id))
        return ExportPackage(
            metadata=ProjectRepository(context.connection).get_metadata(),
            languages=LanguageRepository(context.connection).list_languages(),
            documents=documents,
            segments=segments,
            tokens=tokens,
            annotations=AnnotationRepository(context.connection).list_annotations(),
        )
