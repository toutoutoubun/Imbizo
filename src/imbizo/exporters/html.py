"""Self-contained HTML exporter."""

from __future__ import annotations

import html
from pathlib import Path

from imbizo.exporters.base import ExportedFile, ExportOptions, ExportPackage


class HtmlExporter:
    """Write self-contained HTML reports."""

    format_name = "html"

    def export(self, package: ExportPackage, destination: Path, options: ExportOptions) -> ExportedFile:
        """Write a local HTML report."""

        destination.parent.mkdir(parents=True, exist_ok=True)
        annotations_by_token = {annotation.token_id: annotation for annotation in package.annotations if annotation.token_id}
        rows = []
        for token in package.tokens:
            annotation = annotations_by_token.get(token.id)
            rows.append(
                "<tr>"
                f"<td>{html.escape(token.token_text)}</td>"
                f"<td>{html.escape(annotation.language_id if annotation and annotation.language_id else '')}</td>"
                f"<td>{html.escape(annotation.source.value if annotation else '')}</td>"
                f"<td>{html.escape(annotation.memo if annotation and options.include_memos else '')}</td>"
                "</tr>"
            )
        document = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{html.escape(package.metadata.title)}</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem; color: #1f2933; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #c8d0d8; padding: 0.4rem; text-align: left; }}
    th {{ background: #eef2f6; }}
  </style>
</head>
<body>
  <h1>{html.escape(package.metadata.title)}</h1>
  <p>Local export from Imbizo-CS Workbench. No external resources are required.</p>
  <table>
    <thead><tr><th>Token</th><th>Language</th><th>Source</th><th>Memo</th></tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
</body>
</html>
"""
        destination.write_text(document, encoding="utf-8")
        return ExportedFile(path=destination, format_name=self.format_name)
