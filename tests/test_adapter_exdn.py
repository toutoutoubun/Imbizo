"""Tests for the EXDN adapter."""

from __future__ import annotations

from pathlib import Path

import yaml

from tools.adapters.exdn import EXDNAdapter, ORTHOGRAPHY_NOTE


def test_exdn_adapter_outputs_public_domain_medical_triggers(tmp_path: Path) -> None:
    """Synthetic Turtle entries become unverified isiXhosa medical triggers."""

    raw = tmp_path / "exdn.ttl"
    raw.write_text(
        """@prefix ex: <http://example.invalid/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .

ex:e1 rdfs:label "nurse"@en ;
  skos:prefLabel "umongikazi"@xh ;
  skos:definition "medical worker"@en .

ex:e2 rdfs:label "fever"@en ;
  skos:prefLabel "ifiva"@xh ;
  skos:definition "high temperature"@en .

ex:e3 rdfs:label "bandage"@en ;
  skos:prefLabel "ibhandeji"@xh ;
  skos:definition "dressing"@en .
""",
        encoding="utf-8",
    )
    outputs = EXDNAdapter().convert(
        raw,
        [tmp_path / "triggers"],
        {
            "name": "EXDN",
            "url": "https://example.invalid/exdn",
            "license": "PUBLIC-DOMAIN",
            "retrieved_on": "2026-05-27",
        },
    )
    payload = yaml.safe_load(outputs[0].read_text(encoding="utf-8"))
    assert outputs[0].name == "xho_exdn.yaml"
    assert payload["source"]["origin_license"] == "PUBLIC-DOMAIN"
    assert len(payload["entries"]) == 3
    assert all(entry["verified"] is False for entry in payload["entries"])
    assert all(entry["note"] == ORTHOGRAPHY_NOTE for entry in payload["entries"])
