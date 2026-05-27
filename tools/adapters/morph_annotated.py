"""Adapter for updated morphologically annotated corpora."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping

from tools.adapters.base import SourceAdapter
from tools.adapters.utils.processing import unpack_archive, write_index, write_processing_provenance

CAVEATS = (
    "This morphological corpus index was generated automatically from local "
    "SADiLaR corpus files. Entries are unverified; treat them as starting "
    "suggestions, not authoritative claims. Tag inventories are descriptive "
    "counts from the source lines, not a normalized tagset."
)

ALLOWED_LICENSE_MARKERS = ("CC-BY-4.0", "CC BY 4.0", "Creative Commons Attribution 4.0")
ISO_CODES = {"nbl", "xho", "zul", "ssw", "nso", "sot", "tsn", "ven", "tso"}


class MorphAnnotatedAdapter(SourceAdapter):
    """Split/index SADiLaR morphologically annotated corpus files."""

    def convert(
        self,
        raw_path: Path,
        output_dirs: list[Path],
        source_metadata: Mapping[str, Any],
    ) -> list[Path]:
        """Write per-language morph corpus files and tag-inventory indexes."""

        if not _license_allowed(raw_path, source_metadata):
            return []
        if not output_dirs:
            raise ValueError("Morph annotated conversion requires corpora/morph_annotated output directory.")
        root = output_dirs[0]
        files = unpack_archive(raw_path, root / "_extracted")
        rows_by_lang: dict[str, list[str]] = defaultdict(list)
        tag_counts: dict[str, Counter[str]] = defaultdict(Counter)

        for file in files:
            if file.suffix.lower() not in {".txt", ".tsv", ".conll", ".csv", ""}:
                continue
            for line in file.read_text(encoding="utf-8", errors="replace").splitlines():
                parsed = _parse_line(line, file)
                if parsed is None:
                    continue
                iso, token, tags = parsed
                rows_by_lang[iso].append(f"{token}\t{'+'.join(tags)}")
                tag_counts[iso].update(tags)

        written: list[Path] = []
        for iso, rows in sorted(rows_by_lang.items()):
            lang_dir = root / iso
            lang_dir.mkdir(parents=True, exist_ok=True)
            corpus_file = lang_dir / f"{iso}_morph.txt"
            corpus_file.write_text("\n".join(rows) + "\n", encoding="utf-8")
            index = write_index(
                lang_dir / "index.yaml",
                resource_kind="corpus",
                languages=[iso],
                usable_by=["v1.0_noun_class", "v1.0_concord", "morphology_validation"],
                source_metadata=source_metadata,
                raw_path=raw_path,
                adapter_path="tools/adapters/morph_annotated.py",
                adapter_version=self.adapter_version,
                caveats=CAVEATS,
                extra={"corpus_file": corpus_file.name, "tag_inventory": dict(sorted(tag_counts[iso].items()))},
            )
            written.extend([corpus_file, index])
        provenance = write_processing_provenance(str(source_metadata.get("id", "morph_annotated_corpora")), raw_path, written, source_metadata)
        return written + [provenance]


def _license_allowed(raw_path: Path, source_metadata: Mapping[str, Any]) -> bool:
    text = raw_path.read_text(encoding="utf-8", errors="ignore") if raw_path.is_file() and raw_path.stat().st_size < 5_000_000 else ""
    license_text = text[:2000] + " " + str(source_metadata.get("license", ""))
    return any(marker.casefold() in license_text.casefold() for marker in ALLOWED_LICENSE_MARKERS)


def _parse_line(line: str, file: Path) -> tuple[str, str, list[str]] | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None
    parts = re.split(r"\s+", stripped)
    if len(parts) >= 3 and parts[0].casefold() in ISO_CODES:
        iso, token, analysis = parts[0].casefold(), parts[1], parts[2]
    elif len(parts) >= 2:
        iso = _infer_iso(file)
        if iso is None:
            return None
        token, analysis = parts[0], parts[1]
    else:
        return None
    tags = [tag for tag in re.split(r"[+|,;:/]+", analysis) if tag]
    return iso, token, tags or ["UNK"]


def _infer_iso(path: Path) -> str | None:
    text = "/".join(path.parts).casefold()
    for iso in ISO_CODES:
        if re.search(rf"(^|[/_\-.]){iso}([/_\-.]|$)", text):
            return iso
    return None


Adapter = MorphAnnotatedAdapter
