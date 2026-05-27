"""Offline catalogue of bootstrap-installed processing resources."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(slots=True)
class ProcessingResource:
    """One locally installed processing resource index."""

    path: Path
    resource_kind: str
    languages: list[str]
    usable_by: list[str]
    source: dict[str, Any]
    verified: bool


def scan_processing_resources(roots: list[Path] | None = None) -> list[ProcessingResource]:
    """Scan local models, corpora, and processing directories for index.yaml."""

    search_roots = roots or [Path("models"), Path("corpora"), Path("processing")]
    resources: list[ProcessingResource] = []
    for root in search_roots:
        if not root.exists():
            continue
        for index_path in sorted(root.rglob("index.yaml")):
            payload = yaml.safe_load(index_path.read_text(encoding="utf-8")) or {}
            if not isinstance(payload, dict):
                continue
            resources.append(
                ProcessingResource(
                    path=index_path,
                    resource_kind=str(payload.get("resource_kind", payload.get("dictionary_kind", "unknown"))),
                    languages=[str(item) for item in payload.get("languages", [])],
                    usable_by=[str(item) for item in payload.get("usable_by", [])],
                    source=dict(payload.get("source", {})),
                    verified=bool(payload.get("verified", False)),
                )
            )
    return resources
