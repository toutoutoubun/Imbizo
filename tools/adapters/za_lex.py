"""Adapter for ZA_LEX pronunciation resources."""

from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Any, Mapping

from tools.adapters.base import SourceAdapter
from tools.adapters.utils.processing import unpack_archive, write_index, write_processing_provenance

CAVEATS = (
    "This ZA_LEX mirror was generated automatically from a local archive. "
    "Entries are unverified; treat them as starting suggestions, not authoritative "
    "claims. Per-language LICENCE files are preserved and must be checked before reuse."
)
ISO_CODES = {"afr", "eng", "sot", "tsn", "xho", "zul"}


class ZaLexAdapter(SourceAdapter):
    """Mirror selected ZA_LEX per-language data directories."""

    def convert(self, raw_path: Path, output_dirs: list[Path], source_metadata: Mapping[str, Any]) -> list[Path]:
        """Copy per-language data only when a LICENCE file is present."""

        if not output_dirs:
            raise ValueError("ZA_LEX conversion requires processing/za_lex output directory.")
        root = output_dirs[0]
        extracted_root = root / "_extracted"
        unpack_archive(raw_path, extracted_root)
        written: list[Path] = []
        for lang_dir in _language_dirs(extracted_root):
            iso = lang_dir.name.casefold()
            licence = _license_file(lang_dir)
            if licence is None:
                raise ValueError(f"ZA_LEX language directory lacks LICENCE file: {lang_dir}")
            target = root / iso
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(lang_dir, target)
            copied_files = [path for path in target.rglob("*") if path.is_file()]
            index = write_index(
                target / "index.yaml",
                resource_kind="toolkit",
                languages=[iso],
                usable_by=["v1.5_g2p", "v1.5_phonological_integration"],
                source_metadata=source_metadata,
                raw_path=raw_path,
                adapter_path="tools/adapters/za_lex.py",
                adapter_version=self.adapter_version,
                caveats=CAVEATS,
                extra={
                    "upstream_license_file": licence.name,
                    "file_inventory": [path.relative_to(target).as_posix() for path in sorted(copied_files)],
                },
            )
            written.extend(copied_files + [index])
        provenance = write_processing_provenance(str(source_metadata.get("id", "za_lex")), raw_path, written, source_metadata)
        return written + [provenance]


def _language_dirs(root: Path) -> list[Path]:
    dirs: list[Path] = []
    for path in root.rglob("*"):
        if path.is_dir() and path.name.casefold() in ISO_CODES:
            dirs.append(path)
    return sorted(dirs)


def _license_file(directory: Path) -> Path | None:
    for child in directory.iterdir():
        if child.is_file() and re.fullmatch(r"licen[cs]e(\..*)?", child.name, flags=re.IGNORECASE):
            return child
    return None


Adapter = ZaLexAdapter
