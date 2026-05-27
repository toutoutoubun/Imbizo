"""Tests for the Mafoko terminology adapter."""

from __future__ import annotations

from pathlib import Path

import yaml

from tools.adapters.mafoko import MafokoAdapter


def test_mafoko_adapter_outputs_triggers_and_glossary(tmp_path: Path) -> None:
    """Synthetic Mafoko CSV creates domain trigger and glossary YAML."""

    raw = tmp_path / "combined_dsac.csv"
    raw.write_text(
        "domain,License,English,isiZulu,isiXhosa,Setswana\n"
        "education,Nwulite Obodo Open Data License 1.0,school,isikole,isikolo,sekolo\n"
        "health,Nwulite Obodo Open Data License 1.0,nurse,umhlengikazi,umongikazi,mooki\n",
        encoding="utf-8",
    )
    triggers = tmp_path / "triggers"
    glossaries = tmp_path / "glossaries"
    license_name = "Nwulite Obodo Open Data License 1.0"
    outputs = MafokoAdapter().convert(
        raw,
        [triggers, glossaries],
        {
            "name": "Mafoko",
            "url": "https://example.invalid/mafoko",
            "license": license_name,
            "source_id": "combined_dsac",
            "retrieved_on": "2026-05-27",
        },
    )
    output_names = {path.name for path in outputs}
    assert "zul_education.yaml" in output_names
    assert "mafoko_combined_dsac_education.yaml" in output_names
    for path in outputs:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert payload["source"]["origin_license"] == license_name
        assert all(entry["verified"] is False for entry in payload["entries"])
