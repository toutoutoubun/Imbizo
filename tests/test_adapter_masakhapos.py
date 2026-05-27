"""Tests for MasakhaPOS adapter."""

from __future__ import annotations

import zipfile
from pathlib import Path

import yaml

from tools.adapters.masakhapos import MasakhaPOSAdapter


def test_masakhapos_adapter_indexes_conll_and_disclaimer(tmp_path: Path) -> None:
    """Synthetic CoNLL POS data is copied with CC-BY-NC disclaimer."""

    raw = tmp_path / "pos.zip"
    with zipfile.ZipFile(raw, "w") as archive:
        archive.writestr("zul/zul_train.conll", "Sawubona INTJ\nmhlaba NOUN\n\n")
    out = tmp_path / "corpora" / "masakhapos"
    MasakhaPOSAdapter().convert(
        raw,
        [out],
        {"id": "masakhapos", "name": "MasakhaPOS", "url": "https://example.invalid/pos", "license": "CC-BY-NC-4.0", "project_root": tmp_path},
    )
    payload = yaml.safe_load((out / "zul" / "index.yaml").read_text(encoding="utf-8"))
    assert payload["license_disclaimer"].startswith("Dataset license is CC-BY-NC-4.0")
    assert payload["files"][0]["tag_inventory"]["NOUN"] == 1
