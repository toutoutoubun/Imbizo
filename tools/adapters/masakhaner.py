"""Adapter for MasakhaNER 2.0 CoNLL data."""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Mapping

from tools.adapters.base import SourceAdapter
from tools.adapters.utils.processing import conll_inventory, unpack_archive, write_index, write_processing_provenance

DISCLAIMER = "Dataset license is CC-BY-NC-4.0: non-commercial use only; named-entity evidence is advisory."
CAVEATS = (
    "This MasakhaNER index was generated automatically from local CoNLL files. "
    "Entries are unverified; treat them as starting suggestions, not authoritative "
    "claims. NER tags can suggest proper-noun trigger candidates but never prove triggering."
)
ISO_CODES = {"zul", "xho", "sot", "tsn"}


class MasakhaNERAdapter(SourceAdapter):
    """Copy MasakhaNER CoNLL files and write language indexes."""

    def convert(self, raw_path: Path, output_dirs: list[Path], source_metadata: Mapping[str, Any]) -> list[Path]:
        """Return copied CoNLL files, indexes, and provenance."""

        if not output_dirs:
            raise ValueError("MasakhaNER conversion requires corpora/masakhaner output directory.")
        root = output_dirs[0]
        files = unpack_archive(raw_path, root / "_extracted")
        by_lang: dict[str, list[Path]] = defaultdict(list)
        written: list[Path] = []
        for file in files:
            iso = _infer_iso(file)
            if iso is None:
                continue
            split = _infer_split(file)
            target = root / iso / f"{split}.conll"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(file.read_bytes())
            by_lang[iso].append(target)
            written.append(target)
        for iso, lang_files in sorted(by_lang.items()):
            index = write_index(
                root / iso / "index.yaml",
                resource_kind="dataset",
                languages=[iso],
                usable_by=["v1.5_trigger_detector", "proper_noun_candidates"],
                source_metadata=source_metadata,
                raw_path=raw_path,
                adapter_path="tools/adapters/masakhaner.py",
                adapter_version=self.adapter_version,
                caveats=CAVEATS,
                extra={
                    "license_disclaimer": DISCLAIMER,
                    "files": [{"path": path.name, **conll_inventory(path)} for path in sorted(lang_files)],
                },
            )
            written.append(index)
        provenance = write_processing_provenance(str(source_metadata.get("id", "masakhaner")), raw_path, written, source_metadata)
        return written + [provenance]


def _infer_iso(path: Path) -> str | None:
    text = "/".join(path.parts).casefold()
    for iso in ISO_CODES:
        if re.search(rf"(^|[/_\-.]){iso}([/_\-.]|$)", text):
            return iso
    return None


def _infer_split(path: Path) -> str:
    text = path.name.casefold()
    for split in ("train", "dev", "test"):
        if split in text:
            return split
    return path.stem


Adapter = MasakhaNERAdapter
