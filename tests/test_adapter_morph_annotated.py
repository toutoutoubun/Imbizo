"""Tests for morphologically annotated corpus adapter."""

from __future__ import annotations

from pathlib import Path

import yaml

from tools.adapters.morph_annotated import MorphAnnotatedAdapter


def test_morph_annotated_adapter_extracts_tag_inventory(tmp_path: Path) -> None:
    """A synthetic morph file is split and indexed by language."""

    raw = tmp_path / "morph.txt"
    raw.write_text(
        "# license: CC-BY-4.0\n"
        "zul umuntu NPre+NRoot\n"
        "zul uzohamba SC+Fut+Verb\n"
        "xho umntu NPre+NRoot\n"
        "xho uza SC+Fut\n",
        encoding="utf-8",
    )
    out = tmp_path / "corpora" / "morph_annotated"
    outputs = MorphAnnotatedAdapter().convert(
        raw,
        [out],
        {"id": "morph_annotated_corpora", "name": "Morph Corpora", "url": "https://example.invalid/morph", "license": "CC-BY-4.0", "project_root": tmp_path},
    )
    assert out / "zul" / "zul_morph.txt" in outputs
    payload = yaml.safe_load((out / "zul" / "index.yaml").read_text(encoding="utf-8"))
    assert payload["tag_inventory"]["NPre"] == 1
    assert payload["tag_inventory"]["Fut"] == 1
