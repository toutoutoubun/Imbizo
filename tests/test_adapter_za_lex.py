"""Tests for ZA_LEX adapter."""

from __future__ import annotations

import tarfile
from pathlib import Path

import yaml

from tools.adapters.za_lex import ZaLexAdapter


def test_za_lex_adapter_preserves_language_licences(tmp_path: Path) -> None:
    """A tiny tar with language directories is mirrored with LICENCE files."""

    source = tmp_path / "src"
    (source / "za_lex" / "zul").mkdir(parents=True)
    (source / "za_lex" / "xho").mkdir(parents=True)
    (source / "za_lex" / "zul" / "LICENCE").write_text("Zulu data licence", encoding="utf-8")
    (source / "za_lex" / "zul" / "lex.txt").write_text("a a\n", encoding="utf-8")
    (source / "za_lex" / "xho" / "LICENCE").write_text("Xhosa data licence", encoding="utf-8")
    (source / "za_lex" / "xho" / "lex.txt").write_text("b b\n", encoding="utf-8")
    raw = tmp_path / "za_lex.tar.gz"
    with tarfile.open(raw, "w:gz") as archive:
        archive.add(source / "za_lex", arcname="za_lex")
    out = tmp_path / "processing" / "za_lex"
    ZaLexAdapter().convert(
        raw,
        [out],
        {"id": "za_lex", "name": "ZA_LEX", "url": "https://example.invalid/za_lex", "license": "Apache-2.0 / MIT", "project_root": tmp_path},
    )
    assert (out / "zul" / "LICENCE").exists()
    payload = yaml.safe_load((out / "zul" / "index.yaml").read_text(encoding="utf-8"))
    assert payload["upstream_license_file"] == "LICENCE"
