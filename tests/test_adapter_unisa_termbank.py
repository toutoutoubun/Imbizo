"""Tests for the UNISA termbank adapter."""

from __future__ import annotations

from pathlib import Path

import yaml

from tools.adapters.unisa_termbank import UNISATermbankAdapter


def test_unisa_termbank_outputs_one_file_per_language(tmp_path: Path) -> None:
    """Synthetic Lexonomy-like XML creates language-specific glossaries."""

    raw = tmp_path / "terms.xml"
    raw.write_text(
        """<lexonomy xmlns:dc="http://purl.org/dc/elements/1.1/">
  <metadata>
    <dc:rights>Creative Commons Attribution 4.0 International</dc:rights>
  </metadata>
  <entry>
    <eng><term>noun class</term><definition>classification system</definition></eng>
    <zul><term>isigaba sebizo</term><definition>fictional</definition></zul>
    <xho><term>udidi lwesibizo</term><definition>fictional</definition></xho>
    <sot><term>sehlopha sa lebitso</term><definition>fictional</definition></sot>
  </entry>
  <entry>
    <eng><term>concord</term><definition>agreement marker</definition></eng>
    <zul><term>isivumelwano</term><definition>fictional</definition></zul>
    <tsn><term>tumelano</term><definition>fictional</definition></tsn>
  </entry>
</lexonomy>""",
        encoding="utf-8",
    )
    outputs = UNISATermbankAdapter().convert(
        raw,
        [tmp_path / "glossaries"],
        {
            "name": "UNISA Termbank",
            "url": "https://example.invalid/unisa",
            "license": "PER-FILE-SADILAR-METADATA",
            "retrieved_on": "2026-05-27",
        },
    )
    names = {path.name for path in outputs}
    assert names == {
        "unisa_linguistic_terminology_sot.yaml",
        "unisa_linguistic_terminology_tsn.yaml",
        "unisa_linguistic_terminology_xho.yaml",
        "unisa_linguistic_terminology_zul.yaml",
    }
    payload = yaml.safe_load((tmp_path / "glossaries" / "unisa_linguistic_terminology_zul.yaml").read_text(encoding="utf-8"))
    assert payload["source"]["origin_license"] == "CC-BY-4.0"
    assert payload["source"]["licence_classification"]["spdx_id"] == "CC-BY-4.0"
    assert "Creative Commons Attribution 4.0" in payload["source"]["rights_statement"]
    assert payload["entries"][0]["eng_term"] == "noun class"
    assert payload["entries"][0]["translations"]["zul"]["term"] == "isigaba sebizo"


def test_unisa_termbank_skips_unverified_or_non_tier1_rights(tmp_path: Path) -> None:
    """The adapter refuses to infer a blanket OER licence from unclear metadata."""

    raw = tmp_path / "terms_nc.xml"
    raw.write_text(
        """<lexonomy xmlns:dc="http://purl.org/dc/elements/1.1/">
  <metadata>
    <dc:rights>Creative Commons Attribution-NonCommercial 4.0 International</dc:rights>
  </metadata>
  <entry>
    <eng><term>noun class</term><definition>classification system</definition></eng>
    <zul><term>isigaba sebizo</term><definition>fictional</definition></zul>
  </entry>
</lexonomy>""",
        encoding="utf-8",
    )

    outputs = UNISATermbankAdapter().convert(
        raw,
        [tmp_path / "glossaries"],
        {
            "name": "UNISA Termbank",
            "url": "https://example.invalid/unisa",
            "license": "PER-FILE-SADILAR-METADATA",
            "retrieved_on": "2026-05-27",
        },
    )

    assert outputs == []
    assert not list((tmp_path / "glossaries").glob("*.yaml"))
