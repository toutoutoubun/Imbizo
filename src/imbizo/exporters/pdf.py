"""Minimal local PDF exporter."""

from __future__ import annotations

from pathlib import Path

from imbizo.exporters.base import ExportedFile, ExportOptions, ExportPackage


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


class PdfExporter:
    """Write a simple local PDF print report.

    This intentionally avoids online rendering. A richer WeasyPrint-backed
    renderer can replace this class when packaged locally.
    """

    format_name = "pdf"

    def export(self, package: ExportPackage, destination: Path, options: ExportOptions) -> ExportedFile:
        """Write a local PDF report."""

        destination.parent.mkdir(parents=True, exist_ok=True)
        text_lines = [package.metadata.title, "Imbizo-CS Workbench local report", ""]
        for segment in package.segments[:80]:
            text_lines.append(f"{segment.sort_order}. {segment.text_original}")
        stream_lines = ["BT", "/F1 11 Tf", "50 780 Td"]
        for line in text_lines:
            stream_lines.append(f"({_pdf_escape(line[:95])}) Tj")
            stream_lines.append("0 -14 Td")
        stream_lines.append("ET")
        stream = "\n".join(stream_lines).encode("utf-8")
        objects = [
            b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
            b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream",
        ]
        content = bytearray(b"%PDF-1.4\n")
        offsets = [0]
        for index, obj in enumerate(objects, start=1):
            offsets.append(len(content))
            content.extend(f"{index} 0 obj\n".encode("ascii"))
            content.extend(obj)
            content.extend(b"\nendobj\n")
        xref_start = len(content)
        content.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
        content.extend(b"0000000000 65535 f \n")
        for offset in offsets[1:]:
            content.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
        content.extend(
            f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_start}\n%%EOF\n".encode("ascii")
        )
        destination.write_bytes(bytes(content))
        return ExportedFile(path=destination, format_name=self.format_name)
