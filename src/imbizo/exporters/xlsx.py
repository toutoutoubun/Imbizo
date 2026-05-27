"""XLSX exporter."""

from __future__ import annotations

from pathlib import Path

from imbizo.app.errors import ExportFailure
from imbizo.exporters.base import ExportedFile, ExportOptions, ExportPackage


class XlsxExporter:
    """Write Excel-compatible annotation workbooks."""

    format_name = "xlsx"

    def export(self, package: ExportPackage, destination: Path, options: ExportOptions) -> ExportedFile:
        """Write a local XLSX export."""

        try:
            from openpyxl import Workbook
        except ImportError as exc:
            raise ExportFailure("XLSX export requires the optional openpyxl package.") from exc

        destination.parent.mkdir(parents=True, exist_ok=True)
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Annotations"
        headers = ["token_id", "token_text", "language_id", "source", "memo"]
        sheet.append(headers)
        annotations_by_token = {annotation.token_id: annotation for annotation in package.annotations if annotation.token_id}
        for token in package.tokens:
            annotation = annotations_by_token.get(token.id)
            sheet.append(
                [
                    token.id,
                    token.token_text,
                    annotation.language_id if annotation else "",
                    annotation.source.value if annotation else "",
                    annotation.memo if annotation and options.include_memos else "",
                ]
            )
        workbook.save(destination)
        return ExportedFile(path=destination, format_name=self.format_name)
