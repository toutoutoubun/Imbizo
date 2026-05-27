"""Tests for MasakhaNER adapter."""

from __future__ import annotations

import zipfile
from pathlib import Path

import yaml

from tools.adapters.masakhaner import MasakhaNERAdapter


def test_masakhaner_adapter_indexes_conll_and_disclaimer(tmp_path: Path) -> None:
    """Synthetic CoNLL NER data is copied with CC-BY-NC disclaimer."""

    raw = tmp_path / "ner.zip"
    with zipfile.ZipFile(raw, "w") as archive:
        archive.writestr("xho/xho_test.conll", "Cape B-LOC\nTown I-LOC\n\n")
    out = tmp_path / "corpora" / "masakhaner"
    MasakhaNERAdapter().convert(
        raw,
        [out],
        {"id": "masakhaner", "name": "MasakhaNER", "url": "https://example.invalid/ner", "license": "CC-BY-NC-4.0", "project_root": tmp_path},
    )
    payload = yaml.safe_load((out / "xho" / "index.yaml").read_text(encoding="utf-8"))
    assert payload["license_disclaimer"].startswith("Dataset license is CC-BY-NC-4.0")
    assert payload["files"][0]["tag_inventory"]["B-LOC"] == 1
