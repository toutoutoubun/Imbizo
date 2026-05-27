"""Praat TextGrid exporter."""

from __future__ import annotations

from pathlib import Path

from imbizo.exporters.base import ExportedFile, ExportOptions, ExportPackage


def _escape(value: str) -> str:
    return value.replace('"', '""')


class TextGridExporter:
    """Write Praat TextGrid files."""

    format_name = "textgrid"

    def export(self, package: ExportPackage, destination: Path, options: ExportOptions) -> ExportedFile:
        """Write a local TextGrid export."""

        destination.parent.mkdir(parents=True, exist_ok=True)
        timed_segments = [segment for segment in package.segments if segment.start_ms is not None and segment.end_ms is not None]
        xmax = max((segment.end_ms or 0) / 1000 for segment in timed_segments) if timed_segments else 0.0
        lines = [
            'File type = "ooTextFile"',
            'Object class = "TextGrid"',
            "",
            "xmin = 0",
            f"xmax = {xmax:.3f}",
            "tiers? <exists>",
            "size = 1",
            "item []:",
            "    item [1]:",
            '        class = "IntervalTier"',
            '        name = "Transcript"',
            "        xmin = 0",
            f"        xmax = {xmax:.3f}",
            f"        intervals: size = {len(timed_segments)}",
        ]
        for index, segment in enumerate(timed_segments, start=1):
            lines.extend(
                [
                    f"        intervals [{index}]:",
                    f"            xmin = {(segment.start_ms or 0) / 1000:.3f}",
                    f"            xmax = {(segment.end_ms or 0) / 1000:.3f}",
                    f'            text = "{_escape(segment.text_original)}"',
                ]
            )
        destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return ExportedFile(path=destination, format_name=self.format_name)
