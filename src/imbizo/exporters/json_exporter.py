"""JSON snapshot exporter."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from imbizo.app.time import utc_now
from imbizo.exporters.base import ExportedFile, ExportOptions, ExportPackage


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {key: _jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    return value


class JsonExporter:
    """Write full project snapshot JSON."""

    format_name = "json"

    def export(self, package: ExportPackage, destination: Path, options: ExportOptions) -> ExportedFile:
        """Write a local JSON export."""

        destination.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "schema_version": 1,
            "exported_at": utc_now(),
            "application": {"name": "Imbizo-CS Workbench"},
            "project": _jsonable(package.metadata),
            "languages": _jsonable(package.languages),
            "transcript_documents": _jsonable(package.documents),
            "segments": _jsonable(package.segments),
            "tokens": _jsonable(package.tokens),
            "annotations": _jsonable(package.annotations),
            "metrics": _jsonable(package.metrics),
        }
        destination.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return ExportedFile(path=destination, format_name=self.format_name)
