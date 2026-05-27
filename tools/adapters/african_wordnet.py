"""Adapter for open-license African Wordnet XML exports."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Mapping

import yaml
from lxml import etree

from tools.adapters.base import SourceAdapter
from tools.adapters.utils.nc_hints import suggest_class
from tools.adapters.utils.provenance import build_header, sha256_of

LOGGER = logging.getLogger(__name__)

ALLOWED_LICENSE_MARKERS = (
    "CC-BY-4.0",
    "CC BY 4.0",
    "CC-BY-NC-4.0",
    "CC BY-NC 4.0",
    "CC BY NC 4.0",
    "Creative Commons Attribution 4.0",
    "Creative Commons Attribution-NonCommercial 4.0",
)

BANTU_HINT_LANGS = {"zul", "xho", "sot", "tsn", "nso", "ven", "tso", "ssw", "nbl"}

CAVEATS = (
    "This file was converted automatically from an African Wordnet XML export. "
    "Entries are unverified; treat them as starting suggestions, not authoritative "
    "claims. Synsets without an allowed license marker are skipped."
)


class AfricanWordnetAdapter(SourceAdapter):
    """Convert one SADiLaR African Wordnet XML file to semantic-domain YAML."""

    def convert(
        self,
        raw_path: Path,
        output_dirs: list[Path],
        source_metadata: Mapping[str, Any],
    ) -> list[Path]:
        """Return one semantic-domain YAML file for an allowed XML export."""

        if not output_dirs:
            raise ValueError("African Wordnet conversion requires an output directory.")
        output_dir = output_dirs[0]
        output_dir.mkdir(parents=True, exist_ok=True)
        raw_sha = sha256_of(raw_path)
        tree = etree.parse(str(raw_path))
        root = tree.getroot()
        language_code = _detect_language(root, source_metadata)

        file_license = _license_text(root) or str(source_metadata.get("origin_license") or source_metadata.get("license", ""))
        if file_license and not _license_allowed(file_license):
            LOGGER.warning("Skipping %s because license is not allowed: %s", raw_path, file_license)
            return []

        entries: list[dict[str, Any]] = []
        skipped = 0
        for synset in root.xpath(".//*[local-name()='SYNSET' or local-name()='Synset' or local-name()='synset']"):
            synset_license = _license_text(synset) or file_license
            if synset_license and not _license_allowed(synset_license):
                skipped += 1
                continue
            entry = _synset_to_entry(synset, language_code, len(entries) + 1)
            if entry is not None:
                entries.append(entry)

        if skipped:
            LOGGER.warning("Skipped %s African Wordnet synset(s) with disallowed license metadata.", skipped)
        metadata = dict(source_metadata)
        metadata["origin_license"] = file_license or metadata.get("license", "")
        header = build_header(
            dictionary_kind="semantic_domains",
            language_code=language_code,
            language_pair=None,
            source_metadata=metadata,
            raw_sha256=raw_sha,
            adapter_path="tools/adapters/african_wordnet.py",
            adapter_version=self.adapter_version,
            caveats=CAVEATS,
        )
        out_path = output_dir / f"{language_code}_wordnet.yaml"
        out_path.write_text(
            yaml.safe_dump({**header, "entries": entries}, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        return [out_path]


def _detect_language(root: etree._Element, source_metadata: Mapping[str, Any]) -> str:
    metadata_lang = source_metadata.get("language_code")
    if metadata_lang:
        return str(metadata_lang)
    for attr in ("language_code", "lang", "{http://www.w3.org/XML/1998/namespace}lang"):
        value = root.get(attr)
        if value:
            return str(value).split("-")[0]
    return "und"


def _license_text(element: etree._Element) -> str:
    values: list[str] = []
    for attr_name, attr_value in element.attrib.items():
        if "license" in attr_name.lower() or "rights" in attr_name.lower():
            values.append(str(attr_value))
    for node in element.xpath(".//*[local-name()='rights' or local-name()='license']"):
        text = " ".join(node.itertext()).strip()
        if text:
            values.append(text)
    return " ".join(values).strip()


def _license_allowed(text: str) -> bool:
    folded = text.casefold()
    return any(marker.casefold() in folded for marker in ALLOWED_LICENSE_MARKERS)


def _synset_to_entry(synset: etree._Element, language_code: str, ordinal: int) -> dict[str, Any] | None:
    synset_id = _first_text(synset, "ID") or synset.get("id") or f"synset_{ordinal:05d}"
    literals: list[dict[str, Any]] = []
    for literal in synset.xpath(".//*[local-name()='LITERAL' or local-name()='Literal' or local-name()='literal']"):
        form = " ".join(literal.itertext()).strip()
        if not form:
            continue
        suggested, ambiguous = suggest_class(form, language_code) if language_code in BANTU_HINT_LANGS else (None, [])
        literals.append(
            {
                "form": form,
                "sense": literal.get("sense") or _first_text(literal, "SENSE"),
                "suggested_nc_class": suggested,
                "ambiguous_candidates": ambiguous,
            }
        )
    if not literals:
        return None
    return {
        "id": str(synset_id).strip(),
        "pos": _first_text(synset, "POS"),
        "definition": _first_text(synset, "DEF"),
        "english_links": _english_links(synset),
        "literals": literals,
        "verified": False,
    }


def _first_text(element: etree._Element, local_name: str) -> str | None:
    nodes = element.xpath(f".//*[local-name()='{local_name}']")
    if not nodes:
        return None
    text = " ".join(nodes[0].itertext()).strip()
    return text or None


def _english_links(synset: etree._Element) -> list[str]:
    links: list[str] = []
    for node in synset.xpath(".//*[local-name()='ILR' or local-name()='ilr']"):
        target = node.get("target") or node.get("link") or node.get("id") or " ".join(node.itertext()).strip()
        if target:
            links.append(str(target))
    return links


Adapter = AfricanWordnetAdapter
