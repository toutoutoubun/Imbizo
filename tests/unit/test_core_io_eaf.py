"""Unit tests for the public core.io.eaf compatibility module."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from imbizo.core.io.eaf import EafExporter, EafImporter
from imbizo.domain.project import ProjectMetadata
from imbizo.exporters.base import ExportOptions, ExportPackage
from imbizo.importers.base import ImportOptions


def test_eaf_import_and_export_round_trip_shape(tmp_path: Path) -> None:
    """ELAN EAF import/export preserves timed utterance text for MVP round-trips."""

    source = tmp_path / "sample.eaf"
    source.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<ANNOTATION_DOCUMENT>
  <TIME_ORDER>
    <TIME_SLOT TIME_SLOT_ID="ts1" TIME_VALUE="0" />
    <TIME_SLOT TIME_SLOT_ID="ts2" TIME_VALUE="1200" />
  </TIME_ORDER>
  <TIER TIER_ID="Transcript">
    <ANNOTATION>
      <ALIGNABLE_ANNOTATION ANNOTATION_ID="a1" TIME_SLOT_REF1="ts1" TIME_SLOT_REF2="ts2">
        <ANNOTATION_VALUE>ngiyabonga my friend</ANNOTATION_VALUE>
      </ALIGNABLE_ANNOTATION>
    </ANNOTATION>
  </TIER>
</ANNOTATION_DOCUMENT>
""",
        encoding="utf-8",
    )

    bundle = EafImporter().import_file(source, ImportOptions())

    assert bundle.document is not None
    assert len(bundle.segments) == 1
    assert bundle.segments[0].text_original == "ngiyabonga my friend"
    assert bundle.segments[0].start_ms == 0
    assert bundle.segments[0].end_ms == 1200
    assert [token.token_text for token in bundle.tokens] == ["ngiyabonga", "my", "friend"]

    destination = tmp_path / "roundtrip.eaf"
    EafExporter().export(
        ExportPackage(
            metadata=ProjectMetadata(project_uuid="project-1", title="EAF Test"),
            languages=[],
            documents=[bundle.document],
            segments=bundle.segments,
            tokens=bundle.tokens,
            annotations=[],
        ),
        destination,
        ExportOptions(),
    )

    exported_root = ET.parse(destination).getroot()
    exported_values = [node.text for node in exported_root.findall(".//ANNOTATION_VALUE")]
    assert exported_values == ["ngiyabonga my friend"]
