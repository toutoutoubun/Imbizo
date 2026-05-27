"""Tests for the African Wordnet adapter."""

from __future__ import annotations

from pathlib import Path

import yaml

from tools.adapters.african_wordnet import AfricanWordnetAdapter


def test_african_wordnet_skips_disallowed_synsets(tmp_path: Path) -> None:
    """Only allowed-license synsets are emitted from synthetic XML."""

    raw = tmp_path / "wordnet.xml"
    raw.write_text(
        """<WORDNET language_code="zul" license="CC-BY-4.0">
  <SYNSET>
    <rights>CC-BY-4.0</rights>
    <ID>zul-0001</ID><POS>n</POS><DEF>fictional school concept</DEF>
    <LITERAL>isikole<SENSE>1</SENSE></LITERAL>
    <ILR target="eng-0001"/>
  </SYNSET>
  <SYNSET>
    <rights>All rights reserved</rights>
    <ID>zul-0002</ID><POS>n</POS><LITERAL>umuntu</LITERAL>
  </SYNSET>
</WORDNET>""",
        encoding="utf-8",
    )
    outputs = AfricanWordnetAdapter().convert(
        raw,
        [tmp_path / "semantic_domains"],
        {
            "name": "African Wordnet",
            "url": "https://example.invalid/wordnet",
            "license": "CC-BY-4.0",
            "retrieved_on": "2026-05-27",
        },
    )
    assert [path.name for path in outputs] == ["zul_wordnet.yaml"]
    payload = yaml.safe_load(outputs[0].read_text(encoding="utf-8"))
    assert len(payload["entries"]) == 1
    assert payload["entries"][0]["english_links"] == ["eng-0001"]
    assert payload["entries"][0]["literals"][0]["suggested_nc_class"] == 7
    assert payload["entries"][0]["verified"] is False
