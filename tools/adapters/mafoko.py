"""Adapter for Mafoko / za-mavito CSV terminology sources."""

from __future__ import annotations

import csv
import logging
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Mapping

import yaml

from tools.adapters.base import SourceAdapter
from tools.adapters.utils.provenance import build_header, sha256_of

LOGGER = logging.getLogger(__name__)

LANG_COLUMN_MAP: dict[str, str] = {
    "english": "eng",
    "en": "eng",
    "eng": "eng",
    "afrikaans": "afr",
    "afr": "afr",
    "isizulu": "zul",
    "zulu": "zul",
    "zul": "zul",
    "isixhosa": "xho",
    "xhosa": "xho",
    "xho": "xho",
    "sesotho": "sot",
    "southern sotho": "sot",
    "sot": "sot",
    "setswana": "tsn",
    "tswana": "tsn",
    "tsn": "tsn",
    "sepedi": "nso",
    "northern sotho": "nso",
    "nso": "nso",
    "tshivenda": "ven",
    "venda": "ven",
    "ven": "ven",
    "xitsonga": "tso",
    "tso": "tso",
    "siswati": "ssw",
    "swati": "ssw",
    "ssw": "ssw",
    "isindebele": "nbl",
    "ndebele": "nbl",
    "nbl": "nbl",
}

BANTU_TRIGGER_LANGS = {"zul", "xho", "sot", "tsn", "nso", "ven", "tso", "ssw", "nbl"}

CAVEATS = (
    "This file was converted automatically from the Mafoko / za-mavito "
    "terminology collections. Entries are unverified; treat them as starting "
    "suggestions, not authoritative claims. Domain labels are inherited from "
    "source rows when present and otherwise marked general."
)


class MafokoAdapter(SourceAdapter):
    """Convert a Mafoko CSV file to trigger seeds and multilingual glossaries."""

    def convert(
        self,
        raw_path: Path,
        output_dirs: list[Path],
        source_metadata: Mapping[str, Any],
    ) -> list[Path]:
        """Return YAML files written from one Mafoko CSV."""

        triggers_dir, glossaries_dir = _resolve_dirs(output_dirs)
        triggers_dir.mkdir(parents=True, exist_ok=True)
        glossaries_dir.mkdir(parents=True, exist_ok=True)

        raw_sha = sha256_of(raw_path)
        rows = _read_rows(raw_path)
        source_id = str(source_metadata.get("source_id") or raw_path.stem)
        license_text = _row_license(rows) or str(source_metadata.get("origin_license") or source_metadata.get("license", ""))
        base_metadata = dict(source_metadata)
        base_metadata["origin_license"] = license_text

        trigger_entries: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        glossary_entries: dict[str, list[dict[str, Any]]] = defaultdict(list)
        linguistic_terms: list[dict[str, Any]] = []

        for index, row in enumerate(rows, start=1):
            domain = _clean_domain(row.get("domain") or row.get("Domain") or source_metadata.get("domain") or "general")
            terms = _extract_terms(row)
            if not terms:
                LOGGER.info("Skipping Mafoko row %s without language columns", index)
                continue
            glossary_entries[domain].append(
                {
                    "id": f"mafoko_{source_id}_{domain}_{index:05d}",
                    "domain": domain,
                    "terms": terms,
                    "source_row": index,
                    "verified": False,
                }
            )
            for iso, term in terms.items():
                if iso in BANTU_TRIGGER_LANGS and term:
                    key = (iso, domain)
                    trigger_entries[key].append(
                        {
                            "id": f"mafoko_trigger_{iso}_{domain}_{len(trigger_entries[key]) + 1:05d}",
                            "term": term,
                            "domain": domain,
                            "source_row": index,
                            "trigger_type": "domain_term",
                            "verified": False,
                        }
                    )
            if "unisa_multilingual_linguistic_terminology" in raw_path.stem.casefold():
                linguistic_terms.append(
                    {
                        "id": f"unisa_linguistic_{index:05d}",
                        "domain": domain,
                        "terms": terms,
                        "source_row": index,
                        "verified": False,
                    }
                )

        written: list[Path] = []
        for (iso, domain), entries in sorted(trigger_entries.items()):
            header = build_header(
                dictionary_kind="triggers",
                language_code=iso,
                language_pair=None,
                source_metadata=base_metadata,
                raw_sha256=raw_sha,
                adapter_path="tools/adapters/mafoko.py",
                adapter_version=self.adapter_version,
                caveats=CAVEATS,
            )
            out_path = triggers_dir / f"{iso}_{domain}.yaml"
            _write_yaml(out_path, {**header, "entries": entries})
            written.append(out_path)

        for domain, entries in sorted(glossary_entries.items()):
            header = build_header(
                dictionary_kind="glossaries",
                language_code=None,
                language_pair=None,
                source_metadata=base_metadata,
                raw_sha256=raw_sha,
                adapter_path="tools/adapters/mafoko.py",
                adapter_version=self.adapter_version,
                caveats=CAVEATS,
            )
            out_path = glossaries_dir / f"mafoko_{source_id}_{domain}.yaml"
            _write_yaml(out_path, {**header, "entries": entries})
            written.append(out_path)

        if linguistic_terms:
            header = build_header(
                dictionary_kind="glossaries",
                language_code=None,
                language_pair=None,
                source_metadata=base_metadata,
                raw_sha256=raw_sha,
                adapter_path="tools/adapters/mafoko.py",
                adapter_version=self.adapter_version,
                caveats=CAVEATS,
            )
            out_path = glossaries_dir / "unisa_linguistic_terms.yaml"
            _write_yaml(out_path, {**header, "entries": linguistic_terms})
            written.append(out_path)
        return written


def _resolve_dirs(output_dirs: list[Path]) -> tuple[Path, Path]:
    if len(output_dirs) >= 2:
        trigger = next((path for path in output_dirs if path.name == "triggers"), output_dirs[0])
        glossary = next((path for path in output_dirs if path.name == "glossaries"), output_dirs[1])
        return trigger, glossary
    if len(output_dirs) == 1:
        base = output_dirs[0]
        return base / "triggers", base / "glossaries"
    raise ValueError("Mafoko conversion requires trigger and glossary output directories.")


def _read_rows(raw_path: Path) -> list[dict[str, str]]:
    with raw_path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _extract_terms(row: Mapping[str, str]) -> dict[str, str]:
    terms: dict[str, str] = {}
    for column, value in row.items():
        iso = LANG_COLUMN_MAP.get(str(column).strip().casefold())
        if iso is not None and value is not None and str(value).strip():
            terms[iso] = str(value).strip()
    return terms


def _row_license(rows: list[Mapping[str, str]]) -> str:
    for row in rows:
        for key, value in row.items():
            if str(key).strip().casefold() in {"license", "licence", "rights"} and str(value).strip():
                return str(value).strip()
    return ""


def _clean_domain(value: object) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "_", str(value).casefold()).strip("_")
    return cleaned or "general"


def _write_yaml(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(dict(payload), allow_unicode=True, sort_keys=False), encoding="utf-8")


Adapter = MafokoAdapter
