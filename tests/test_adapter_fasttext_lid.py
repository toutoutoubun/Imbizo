"""Tests for fastText LID processing-resource adapter."""

from __future__ import annotations

from pathlib import Path

import yaml

from tools.adapters.fasttext_lid import FastTextLidAdapter


def test_fasttext_lid_adapter_writes_model_and_index(tmp_path: Path) -> None:
    """A tiny dummy .ftz is copied and indexed without network access."""

    raw = tmp_path / "lid.176.ftz"
    raw.write_bytes(b"not a real model, just a fixture")
    out = tmp_path / "models" / "lid"
    outputs = FastTextLidAdapter().convert(
        raw,
        [out],
        {"id": "fasttext_lid176_ftz", "name": "fastText lid.176", "url": "https://example.invalid/lid.176.ftz", "license": "CC-BY-SA-3.0", "project_root": tmp_path},
    )
    assert out / "lid.176.ftz" in outputs
    payload = yaml.safe_load((out / "index.yaml").read_text(encoding="utf-8"))
    assert payload["resource_kind"] == "model"
    assert payload["source"]["origin_license"] == "CC-BY-SA-3.0"
    assert len(payload["model_sha256"]) == 64
    assert "F4_lid_baseline" in payload["usable_by"]
    assert payload["verified"] is False
