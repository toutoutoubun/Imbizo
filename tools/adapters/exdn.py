"""Adapter for the public-domain English-Xhosa Dictionary for Nurses."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Mapping

import yaml

from tools.adapters.base import SourceAdapter
from tools.adapters.utils.provenance import build_header, sha256_of

try:  # rdflib is a bootstrap-only optional dependency.
    import rdflib  # type: ignore[import-not-found]
except Exception:  # pragma: no cover - exercised when rdflib is unavailable.
    rdflib = None  # type: ignore[assignment]

CAVEATS = (
    "This file was converted automatically from the English-Xhosa Dictionary "
    "for Nurses. Entries are unverified; treat them as starting suggestions, "
    "not authoritative claims. Source is a 1935 public-domain medical "
    "dictionary; orthography may differ from modern isiXhosa standards."
)

ORTHOGRAPHY_NOTE = "Source is a 1935 public-domain medical dictionary; orthography may differ from modern isiXhosa standards."


class EXDNAdapter(SourceAdapter):
    """Convert EXDN RDF/Turtle into medical trigger seed YAML."""

    def convert(
        self,
        raw_path: Path,
        output_dirs: list[Path],
        source_metadata: Mapping[str, Any],
    ) -> list[Path]:
        """Return the isiXhosa medical trigger dictionary written."""

        if not output_dirs:
            raise ValueError("EXDN conversion requires an output directory.")
        output_dir = output_dirs[0] / "medical" if output_dirs[0].name != "medical" else output_dirs[0]
        output_dir.mkdir(parents=True, exist_ok=True)
        entries = _parse_with_rdflib(raw_path) if rdflib is not None else _parse_turtle_fallback(raw_path)
        raw_sha = sha256_of(raw_path)
        metadata = dict(source_metadata)
        metadata["origin_license"] = metadata.get("origin_license") or "PUBLIC-DOMAIN"
        header = build_header(
            dictionary_kind="triggers",
            language_code="xho",
            language_pair=None,
            source_metadata=metadata,
            raw_sha256=raw_sha,
            adapter_path="tools/adapters/exdn.py",
            adapter_version=self.adapter_version,
            caveats=CAVEATS,
        )
        out_path = output_dir / "xho_exdn.yaml"
        out_path.write_text(
            yaml.safe_dump({**header, "entries": entries}, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        return [out_path]


def _parse_with_rdflib(raw_path: Path) -> list[dict[str, Any]]:
    graph = rdflib.Graph()  # type: ignore[union-attr]
    graph.parse(str(raw_path), format="turtle")
    by_subject: dict[str, dict[str, str]] = {}
    for subject, predicate, obj in graph:
        if not isinstance(obj, rdflib.term.Literal):  # type: ignore[union-attr]
            continue
        subject_key = str(subject)
        slot = by_subject.setdefault(subject_key, {})
        language = str(obj.language or "").casefold()
        pred = str(predicate).casefold()
        value = str(obj)
        if language in {"en", "eng"} and ("label" in pred or "headword" in pred):
            slot["eng_headword"] = value
        elif language in {"xh", "xho"} and ("label" in pred or "equivalent" in pred):
            slot["xho_equivalent"] = value
        elif language in {"en", "eng", ""} and ("definition" in pred or "gloss" in pred):
            slot["original_gloss"] = value
    return _rows_to_entries(by_subject.values())


def _parse_turtle_fallback(raw_path: Path) -> list[dict[str, Any]]:
    text = raw_path.read_text(encoding="utf-8")
    rows: list[dict[str, str]] = []
    for block in re.split(r"\n\s*\n|(?<=\.)\s*\n(?=\w|<)", text):
        eng = _first_lang_literal(block, ("en", "eng"), ("label", "headword", "prefLabel"))
        xho = _first_lang_literal(block, ("xh", "xho"), ("label", "equivalent", "prefLabel"))
        gloss = _first_lang_literal(block, ("en", "eng", ""), ("definition", "gloss", "comment"))
        if eng or xho:
            rows.append({"eng_headword": eng, "xho_equivalent": xho, "original_gloss": gloss})
    return _rows_to_entries(rows)


def _first_lang_literal(block: str, langs: tuple[str, ...], predicate_markers: tuple[str, ...]) -> str:
    for predicate in predicate_markers:
        pattern = re.compile(
            rf"{re.escape(predicate)}[^\"']*[\"']([^\"']+)[\"'](?:@([a-zA-Z-]+))?",
            re.IGNORECASE,
        )
        for match in pattern.finditer(block):
            lang = (match.group(2) or "").casefold()
            if lang in langs:
                return match.group(1)
    return ""


def _rows_to_entries(rows: Any) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        eng = str(row.get("eng_headword", "")).strip()
        xho = str(row.get("xho_equivalent", "")).strip()
        if not eng and not xho:
            continue
        entries.append(
            {
                "id": f"exdn_xho_medical_{index:05d}",
                "eng_headword": eng,
                "xho_equivalent": xho,
                "original_gloss": str(row.get("original_gloss", "")).strip(),
                "trigger_type": "medical_term",
                "note": ORTHOGRAPHY_NOTE,
                "verified": False,
            }
        )
    return entries


Adapter = EXDNAdapter
