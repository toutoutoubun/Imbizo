"""Quotation extract exporter."""

from __future__ import annotations

from pathlib import Path

from imbizo.exporters.base import ExportedFile, ExportOptions, ExportPackage


class QuotationExporter:
    """Write quotation extracts for qualitative writing."""

    format_name = "quotation"

    def export(self, package: ExportPackage, destination: Path, options: ExportOptions) -> ExportedFile:
        """Write a local Markdown quotation extract file."""

        destination.parent.mkdir(parents=True, exist_ok=True)
        lines = [f"# Quotation Extracts: {package.metadata.title}", ""]
        annotations_by_token = {annotation.token_id: annotation for annotation in package.annotations if annotation.token_id}
        for segment in package.segments:
            segment_tokens = [token for token in package.tokens if token.segment_id == segment.id]
            annotated = [annotations_by_token.get(token.id) for token in segment_tokens]
            if not any(annotation and annotation.memo for annotation in annotated):
                continue
            time = ""
            if segment.start_ms is not None and segment.end_ms is not None:
                time = f" ({segment.start_ms / 1000:.2f}-{segment.end_ms / 1000:.2f}s)"
            lines.append(f"## Segment {segment.sort_order}{time}")
            lines.append("")
            lines.append(f"> {segment.text_original}")
            lines.append("")
            for token, annotation in zip(segment_tokens, annotated, strict=False):
                if annotation and annotation.memo:
                    lines.append(f"- `{token.token_text}`: {annotation.memo}")
            lines.append("")
        destination.write_text("\n".join(lines), encoding="utf-8")
        return ExportedFile(path=destination, format_name=self.format_name)
