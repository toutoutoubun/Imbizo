"""Tests for the UP multilingual lexicon adapter."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from tools.adapters.up_lexicons import UPLexiconsAdapter


def test_up_lexicons_adapter_writes_bilingual_yaml(tmp_path: Path) -> None:
    """Synthetic UP-style JSON produces per-pair YAML with provenance."""

    raw = tmp_path / "up.json"
    raw.write_text(
        json.dumps(
            {
                "en-zul": [["computer", "ikhompyutha"], ["school", "isikole"]],
                "en-xho": [["person", "umntu"]],
                "en-tsn": [["language", "puo"]],
            }
        ),
        encoding="utf-8",
    )
    out_dir = tmp_path / "base_lexicon"
    outputs = UPLexiconsAdapter().convert(
        raw,
        [out_dir],
        {
            "name": "South African multilingual lexicons",
            "url": "https://example.invalid/up",
            "license": "CC-BY-4.0",
            "origin_authors": ["UP"],
            "retrieved_on": "2026-05-27",
        },
    )
    assert {path.name for path in outputs} == {"eng_zul.yaml", "eng_xho.yaml", "eng_tsn.yaml"}
    payload = yaml.safe_load((out_dir / "eng_zul.yaml").read_text(encoding="utf-8"))
    assert payload["source"]["origin_license"] == "CC-BY-4.0"
    assert payload["source"]["origin_url"] == "https://example.invalid/up"
    assert len(payload["source"]["retrieved_sha256"]) == 64
    assert payload["source"]["retrieved_on"] == "2026-05-27"
    assert all(entry["verified"] is False for entry in payload["entries"])
    assert payload["entries"][1]["suggested_nc_class"] == 7
