"""Tests for processing resource index catalogue."""

from __future__ import annotations

import ast
from pathlib import Path

import yaml

from imbizo.core.lid.processing_index import scan_processing_resources


def test_processing_index_scans_local_indexes(tmp_path: Path) -> None:
    """Processing catalogue reads local index.yaml files only."""

    index = tmp_path / "models" / "lid" / "index.yaml"
    index.parent.mkdir(parents=True)
    index.write_text(
        yaml.safe_dump({"resource_kind": "model", "languages": ["zul"], "usable_by": ["F4_lid_baseline"], "source": {}, "verified": False}),
        encoding="utf-8",
    )
    resources = scan_processing_resources([tmp_path / "models"])
    assert resources[0].resource_kind == "model"
    assert resources[0].languages == ["zul"]


def test_processing_index_module_has_no_network_imports() -> None:
    """The startup catalogue must remain offline-only."""

    root = Path(__file__).resolve().parents[1]
    path = root / "src" / "imbizo" / "core" / "lid" / "processing_index.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    assert not {"urllib.request", "requests", "httpx", "aiohttp", "socket"} & imports
