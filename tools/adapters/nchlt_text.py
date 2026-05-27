"""Adapter for NCHLT text corpora bundles."""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Mapping

from tools.adapters.base import SourceAdapter
from tools.adapters.utils.processing import token_count, unpack_archive, write_index, write_processing_provenance

CAVEATS = (
    "This NCHLT text corpus index was generated automatically from a local "
    "bundle. Entries are unverified; treat them as starting suggestions, not "
    "authoritative claims. Counts are simple whitespace token counts for "
    "offline inventory, not linguistic tokenization."
)

ISO_CODES = {"afr", "eng", "nbl", "nso", "sot", "ssw", "tsn", "tso", "ven", "xho", "zul"}


class NchltTextAdapter(SourceAdapter):
    """Unpack NCHLT text corpora and write per-language indexes."""

    def convert(
        self,
        raw_path: Path,
        output_dirs: list[Path],
        source_metadata: Mapping[str, Any],
    ) -> list[Path]:
        """Extract the corpus archive and summarize text inventories."""

        if not output_dirs:
            raise ValueError("NCHLT conversion requires corpora/nchlt output directory.")
        root = output_dirs[0]
        extracted = unpack_archive(raw_path, root / "_extracted")
        by_lang: dict[str, list[Path]] = defaultdict(list)
        for path in extracted:
            iso = _infer_iso(path)
            if iso:
                target = root / iso / path.name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(path.read_bytes())
                by_lang[iso].append(target)

        written: list[Path] = []
        for iso, files in sorted(by_lang.items()):
            inventory = [
                {"path": file.name, "bytes": file.stat().st_size, "tokens": token_count(file)}
                for file in sorted(files)
            ]
            index = write_index(
                root / iso / "index.yaml",
                resource_kind="corpus",
                languages=[iso],
                usable_by=["validation", "frequency_lists", "baseline_lexicons"],
                source_metadata=source_metadata,
                raw_path=raw_path,
                adapter_path="tools/adapters/nchlt_text.py",
                adapter_version=self.adapter_version,
                caveats=CAVEATS,
                extra={"file_inventory": inventory, "license": source_metadata.get("license", "CC-BY-2.5-SA")},
            )
            written.append(index)
        provenance = write_processing_provenance(str(source_metadata.get("id", "nchlt_text_corpora")), raw_path, written, source_metadata)
        return written + [provenance]


def _infer_iso(path: Path) -> str | None:
    parts = [part.casefold() for part in path.parts] + [path.name.casefold()]
    for part in parts:
        for code in ISO_CODES:
            if part == code or re.search(rf"(^|[_\-.]){code}([_\-.]|$)", part):
                return code
    return None


Adapter = NchltTextAdapter
