"""Adapter for UNISA / SADiLaR Lexonomy linguistic terminology XML exports.

UNISA / SADiLaR terminology exports do not necessarily share one blanket
licence. This adapter therefore reads the rights statement embedded in each
XML file and converts only files whose metadata resolves to a Tier-1 licence.
Unknown, missing, or NonCommercial rights statements are skipped rather than
being silently re-labelled as OER.
"""

from __future__ import annotations

from collections import defaultdict
import logging
from pathlib import Path
from typing import Any, Mapping

import yaml
from lxml import etree

from tools.adapters.base import SourceAdapter
from tools.adapters.utils.provenance import build_header, sha256_of

LANG_MAP: dict[str, str] = {
    "english": "eng",
    "eng": "eng",
    "en": "eng",
    "afrikaans": "afr",
    "afr": "afr",
    "isizulu": "zul",
    "zulu": "zul",
    "zul": "zul",
    "isixhosa": "xho",
    "xhosa": "xho",
    "xho": "xho",
    "sesotho": "sot",
    "sot": "sot",
    "setswana": "tsn",
    "tsn": "tsn",
    "sepedi": "nso",
    "northern_sotho": "nso",
    "northern sotho": "nso",
    "nso": "nso",
}

CAVEATS = (
    "This file was converted automatically from a UNISA / SADiLaR Lexonomy "
    "terminology export after reading the source file's own rights metadata. "
    "Entries are unverified; treat them as starting suggestions, not "
    "authoritative claims. Definitions are preserved where the source XML "
    "provides them. Files whose rights metadata is missing, unclear, or "
    "outside the Tier-1 allow-list are skipped rather than assumed to be OER."
)

LOGGER = logging.getLogger(__name__)

ALLOWED_LICENCE_PROFILES: tuple[dict[str, Any], ...] = (
    {
        "spdx_id": "CC-BY-4.0",
        "markers": (
            "cc-by-4.0",
            "cc by 4.0",
            "creative commons attribution 4.0",
            "creative commons attribution international 4.0",
        ),
        "origin_license": "CC-BY-4.0",
        "licence_classification": {
            "spdx_id": "CC-BY-4.0",
            "tier": 1,
            "fosl_compatible": True,
            "combinable_with_agpl": "combination",
            "commercial_use_restricted": False,
            "sharealike_required": False,
            "downstream_obligations": ["attribution"],
            "redistribution_notice": (
                "This UNISA / SADiLaR terminology file declares CC-BY-4.0 in "
                "its own rights metadata. Converted glossary outputs preserve "
                "attribution and provenance."
            ),
        },
    },
    {
        "spdx_id": "OER-UNISA",
        "markers": (
            "oer",
            "open educational resource",
            "unisa open educational resource",
        ),
        "origin_license": "OER-UNISA",
        "licence_classification": {
            "spdx_id": "OER-UNISA",
            "tier": 1,
            "fosl_compatible": True,
            "combinable_with_agpl": "combination",
            "commercial_use_restricted": False,
            "sharealike_required": False,
            "downstream_obligations": ["attribution"],
            "redistribution_notice": (
                "This UNISA / SADiLaR terminology file declares an Open "
                "Educational Resource rights statement. Converted glossary "
                "outputs preserve attribution and provenance."
            ),
        },
    },
)

DISALLOWED_MARKERS: tuple[str, ...] = (
    "cc-by-nc",
    "cc by-nc",
    "noncommercial",
    "non-commercial",
    "all rights reserved",
)


class UNISATermbankAdapter(SourceAdapter):
    """Convert Lexonomy XML to per-language glossary YAML files."""

    def convert(
        self,
        raw_path: Path,
        output_dirs: list[Path],
        source_metadata: Mapping[str, Any],
    ) -> list[Path]:
        """Return one glossary YAML per non-English language in the XML."""

        if not output_dirs:
            raise ValueError("UNISA termbank conversion requires an output directory.")
        output_dir = output_dirs[0]
        output_dir.mkdir(parents=True, exist_ok=True)
        raw_sha = sha256_of(raw_path)
        tree = etree.parse(str(raw_path))
        rights = _extract_rights_statement(tree.getroot())
        licence_profile = _licence_profile_for_rights(rights)
        if licence_profile is None:
            LOGGER.warning(
                "Skipping UNISA termbank file %s because rights metadata is missing or not Tier-1 allowed: %s",
                raw_path,
                rights or "MISSING",
            )
            return []

        file_metadata = dict(source_metadata)
        file_metadata["origin_license"] = licence_profile["origin_license"]
        file_metadata["license"] = licence_profile["origin_license"]
        file_metadata["licence_classification"] = dict(licence_profile["licence_classification"])
        entries_by_lang: dict[str, list[dict[str, Any]]] = defaultdict(list)

        for index, entry_node in enumerate(_entry_nodes(tree.getroot()), start=1):
            terms = _extract_terms(entry_node)
            english = terms.get("eng", {})
            eng_term = english.get("term", "")
            eng_definition = english.get("definition", "")
            if not eng_term:
                continue
            for iso in sorted(code for code in terms if code != "eng"):
                entries_by_lang[iso].append(
                    {
                        "id": f"unisa_term_{iso}_{index:05d}",
                        "eng_term": eng_term,
                        "eng_definition": eng_definition,
                        "translations": terms,
                        "verified": False,
                    }
                )

        written: list[Path] = []
        for iso, entries in sorted(entries_by_lang.items()):
            header = build_header(
                dictionary_kind="glossaries",
                language_code=iso,
                language_pair=None,
                source_metadata=file_metadata,
                raw_sha256=raw_sha,
                adapter_path="tools/adapters/unisa_termbank.py",
                adapter_version=self.adapter_version,
                caveats=CAVEATS,
            )
            header["source"]["rights_statement"] = rights
            out_path = output_dir / f"unisa_linguistic_terminology_{iso}.yaml"
            out_path.write_text(
                yaml.safe_dump({**header, "entries": entries}, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )
            written.append(out_path)
        return written


def _extract_rights_statement(root: etree._Element) -> str:
    """Return rights / licence text declared in the XML metadata, if present."""

    values: list[str] = []
    metadata_nodes = root.xpath(
        ".//*[local-name()='rights' or local-name()='license' or local-name()='licence']"
    )
    for node in metadata_nodes:
        text = " ".join(node.itertext()).strip()
        if text:
            values.append(text)
    for node in root.xpath(".//*[@rights or @license or @licence]"):
        for attribute in ("rights", "license", "licence"):
            value = node.get(attribute)
            if value:
                values.append(value.strip())
    return " | ".join(dict.fromkeys(values))


def _licence_profile_for_rights(rights: str) -> Mapping[str, Any] | None:
    """Resolve a rights statement to a Tier-1 licence profile or None."""

    folded = rights.casefold()
    if not folded:
        return None
    if any(marker in folded for marker in DISALLOWED_MARKERS):
        return None
    for profile in ALLOWED_LICENCE_PROFILES:
        if any(marker in folded for marker in profile["markers"]):
            return profile
    return None


def _entry_nodes(root: etree._Element) -> list[etree._Element]:
    nodes = root.xpath(".//*[local-name()='entry' or local-name()='Entry']")
    if nodes:
        return list(nodes)
    return [root]


def _extract_terms(entry_node: etree._Element) -> dict[str, dict[str, str]]:
    terms: dict[str, dict[str, str]] = {}
    for child in entry_node:
        iso = _language_for_node(child)
        if iso is None:
            continue
        term = _field_text(child, ("term", "Term", "lemma", "headword")) or " ".join(child.itertext()).strip()
        definition = _field_text(child, ("definition", "Definition", "def")) or ""
        if term:
            terms[iso] = {"term": term, "definition": definition}
    if not terms:
        for node in entry_node.xpath(".//*[@lang or @xml:lang]", namespaces={"xml": "http://www.w3.org/XML/1998/namespace"}):
            iso = _language_for_node(node)
            if iso is not None:
                text = " ".join(node.itertext()).strip()
                if text:
                    terms.setdefault(iso, {"term": text, "definition": ""})
    return terms


def _language_for_node(node: etree._Element) -> str | None:
    raw = (
        node.get("lang")
        or node.get("{http://www.w3.org/XML/1998/namespace}lang")
        or etree.QName(node).localname
    )
    return LANG_MAP.get(str(raw).replace("-", "_").casefold())


def _field_text(node: etree._Element, names: tuple[str, ...]) -> str | None:
    for name in names:
        matches = node.xpath(f".//*[local-name()='{name}']")
        if matches:
            text = " ".join(matches[0].itertext()).strip()
            if text:
                return text
    return None


Adapter = UNISATermbankAdapter
