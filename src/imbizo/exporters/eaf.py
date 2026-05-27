"""ELAN EAF exporter."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from imbizo.exporters.base import ExportedFile, ExportOptions, ExportPackage


class EafExporter:
    """Write a simple ELAN-compatible EAF file."""

    format_name = "eaf"

    def export(self, package: ExportPackage, destination: Path, options: ExportOptions) -> ExportedFile:
        """Write a local EAF export."""

        destination.parent.mkdir(parents=True, exist_ok=True)
        root = ET.Element("ANNOTATION_DOCUMENT", {"AUTHOR": "", "DATE": "", "FORMAT": "3.0", "VERSION": "3.0"})
        time_order = ET.SubElement(root, "TIME_ORDER")
        tier = ET.SubElement(root, "TIER", {"TIER_ID": "Transcript"})
        slot_index = 1
        for segment in package.segments:
            if segment.start_ms is None or segment.end_ms is None:
                continue
            start_id = f"ts{slot_index}"
            end_id = f"ts{slot_index + 1}"
            slot_index += 2
            ET.SubElement(time_order, "TIME_SLOT", {"TIME_SLOT_ID": start_id, "TIME_VALUE": str(segment.start_ms)})
            ET.SubElement(time_order, "TIME_SLOT", {"TIME_SLOT_ID": end_id, "TIME_VALUE": str(segment.end_ms)})
            annotation = ET.SubElement(tier, "ANNOTATION")
            alignable = ET.SubElement(
                annotation,
                "ALIGNABLE_ANNOTATION",
                {"ANNOTATION_ID": segment.id, "TIME_SLOT_REF1": start_id, "TIME_SLOT_REF2": end_id},
            )
            ET.SubElement(alignable, "ANNOTATION_VALUE").text = segment.text_original
        ET.ElementTree(root).write(destination, encoding="utf-8", xml_declaration=True)
        return ExportedFile(path=destination, format_name=self.format_name)
