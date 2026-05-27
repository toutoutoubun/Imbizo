"""Adapter for the University of Pretoria multilingual lexicons.

The adapter converts an already-downloaded JSON file into Imbizo-CS bilingual
base-lexicon YAML. It does not fetch network resources; bootstrap.py is solely
responsible for retrieval and license verification.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Mapping

import yaml

from tools.adapters.base import SourceAdapter
from tools.adapters.utils.nc_hints import suggest_class
from tools.adapters.utils.provenance import build_header, sha256_of

LOGGER = logging.getLogger(__name__)

LANG_MAP: dict[str, str] = {
    "en": "eng",
    "eng": "eng",
    "af": "afr",
    "afr": "afr",
    "zul": "zul",
    "zu": "zul",
    "xho": "xho",
    "xh": "xho",
    "st": "sot",
    "sot": "sot",
    "tn": "tsn",
    "tsn": "tsn",
    "nso": "nso",
    "ven": "ven",
    "tso": "tso",
    "nbl": "nbl",
    "ssw": "ssw",
}

BANTU_HINT_LANGS = {"zul", "xho", "sot", "tsn", "nso"}

CAVEATS = (
    "This file was converted automatically from the University of Pretoria "
    "multilingual lexicons. Entries are unverified; treat them as starting "
    "suggestions, not authoritative claims. Noun-class hints are produced by "
    "minimal prefix matching and must be checked by a researcher."
)


class UPLexiconsAdapter(SourceAdapter):
    """Convert UP JSON lexicon pairs to Imbizo-CS base-lexicon YAML."""

    def convert(
        self,
        raw_path: Path,
        output_dirs: list[Path],
        source_metadata: Mapping[str, Any],
    ) -> list[Path]:
        """Return YAML files written from one UP JSON export."""

        if not output_dirs:
            raise ValueError("UP lexicon conversion requires an output directory.")
        output_dir = output_dirs[0]
        output_dir.mkdir(parents=True, exist_ok=True)

        data = json.loads(raw_path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("UP lexicon JSON must be an object keyed by language pair.")

        raw_sha = sha256_of(raw_path)
        written: list[Path] = []
        for pair_key, rows in data.items():
            src_iso, tgt_iso = _parse_pair_key(pair_key)
            if src_iso != "eng":
                LOGGER.info("Skipping non-English source pair %s", pair_key)
                continue
            if not isinstance(rows, list):
                raise ValueError(f"UP lexicon pair {pair_key} must contain a list of pairs.")
            entries: list[dict[str, Any]] = []
            for index, row in enumerate(rows, start=1):
                if not isinstance(row, (list, tuple)) or len(row) < 2:
                    raise ValueError(f"UP lexicon row {index} in {pair_key} is not a two-item pair.")
                english = str(row[0]).strip()
                target = str(row[1]).strip()
                suggested, ambiguous = suggest_class(target, tgt_iso) if tgt_iso in BANTU_HINT_LANGS else (None, [])
                entry: dict[str, Any] = {
                    "id": f"up_eng_{tgt_iso}_{index:05d}",
                    "eng": english,
                    tgt_iso: target,
                    "suggested_nc_class": suggested,
                    "ambiguous_candidates": ambiguous,
                    "verified": False,
                }
                entries.append(entry)

            header = build_header(
                dictionary_kind="base_lexicon",
                language_code=None,
                language_pair=["eng", tgt_iso],
                source_metadata=source_metadata,
                raw_sha256=raw_sha,
                adapter_path="tools/adapters/up_lexicons.py",
                adapter_version=self.adapter_version,
                caveats=CAVEATS,
            )
            payload = {**header, "entries": entries}
            out_path = output_dir / f"eng_{tgt_iso}.yaml"
            out_path.write_text(
                yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )
            written.append(out_path)
        return written


def _parse_pair_key(pair_key: str) -> tuple[str, str]:
    parts = pair_key.replace("_", "-").split("-")
    if len(parts) != 2:
        raise ValueError(f"Unsupported UP lexicon language-pair key: {pair_key}")
    try:
        return LANG_MAP[parts[0].casefold()], LANG_MAP[parts[1].casefold()]
    except KeyError as exc:
        raise ValueError(f"Unsupported language code in UP lexicon pair: {pair_key}") from exc


Adapter = UPLexiconsAdapter
