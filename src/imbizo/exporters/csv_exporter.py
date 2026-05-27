"""CSV exporter."""

from __future__ import annotations

import csv
from pathlib import Path

from imbizo.exporters.base import ExportedFile, ExportOptions, ExportPackage


class CsvExporter:
    """Write annotation CSV files."""

    format_name = "csv"

    def export(self, package: ExportPackage, destination: Path, options: ExportOptions) -> ExportedFile:
        """Write a local CSV export."""

        destination.parent.mkdir(parents=True, exist_ok=True)
        annotations_by_token = {annotation.token_id: annotation for annotation in package.annotations if annotation.token_id}
        segments_by_id = {segment.id: segment for segment in package.segments}
        with destination.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=[
                    "document_id",
                    "segment_id",
                    "segment_order",
                    "token_id",
                    "token_order",
                    "token_text",
                    "language_id",
                    "source",
                    "matrix_language_id",
                    "embedded_language_id",
                    "switch_type",
                    "linguistic_status",
                    "trigger_text",
                    "researcher_confidence",
                    "memo",
                ],
            )
            writer.writeheader()
            for token in package.tokens:
                segment = segments_by_id[token.segment_id]
                annotation = annotations_by_token.get(token.id)
                writer.writerow(
                    {
                        "document_id": segment.transcript_document_id,
                        "segment_id": segment.id,
                        "segment_order": segment.sort_order,
                        "token_id": token.id,
                        "token_order": token.sort_order,
                        "token_text": token.token_text,
                        "language_id": annotation.language_id if annotation else "",
                        "source": annotation.source.value if annotation else "",
                        "matrix_language_id": annotation.matrix_language_id if annotation else "",
                        "embedded_language_id": annotation.embedded_language_id if annotation else "",
                        "switch_type": annotation.switch_type.value if annotation and annotation.switch_type else "",
                        "linguistic_status": annotation.linguistic_status.value if annotation and annotation.linguistic_status else "",
                        "trigger_text": annotation.trigger_text if annotation else "",
                        "researcher_confidence": annotation.researcher_confidence if annotation else "",
                        "memo": annotation.memo if annotation and options.include_memos else "",
                    }
                )
        return ExportedFile(path=destination, format_name=self.format_name)
