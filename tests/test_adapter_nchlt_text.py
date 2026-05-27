"""Tests for NCHLT text corpus adapter."""

from __future__ import annotations

import zipfile
from pathlib import Path

import yaml

from tools.adapters.nchlt_text import NchltTextAdapter


def test_nchlt_text_adapter_extracts_and_indexes(tmp_path: Path) -> None:
    """A synthetic zip creates per-language corpus indexes."""

    raw = tmp_path / "nchlt.zip"
    with zipfile.ZipFile(raw, "w") as archive:
        archive.writestr("zul/zul_sample.txt", "sawubona mhlaba\n")
        archive.writestr("xho/xho_sample.txt", "molo hlabathi\n")
    out = tmp_path / "corpora" / "nchlt"
    outputs = NchltTextAdapter().convert(
        raw,
        [out],
        {"id": "nchlt_text_corpora", "name": "NCHLT", "url": "https://example.invalid/nchlt", "license": "CC-BY-2.5-SA", "project_root": tmp_path},
    )
    assert out / "zul" / "index.yaml" in outputs
    payload = yaml.safe_load((out / "zul" / "index.yaml").read_text(encoding="utf-8"))
    assert payload["languages"] == ["zul"]
    assert payload["file_inventory"][0]["tokens"] == 2
    assert payload["source"]["origin_license"] == "CC-BY-2.5-SA"
