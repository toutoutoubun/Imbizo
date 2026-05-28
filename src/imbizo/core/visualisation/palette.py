"""Colour and glyph palettes for accessible local visualisations.

The default colours use Wong's colourblind-safe palette (Wong, 2011,
*Nature Methods*). Imbizo-CS never encodes meaning in colour alone: every
language also receives a deterministic glyph so figures and GUI highlights
remain interpretable under WCAG 1.4.1.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import re
from typing import Any

import yaml


WONG_COLOURS: tuple[str, ...] = (
    "#000000",
    "#E69F00",
    "#56B4E9",
    "#009E73",
    "#F0E442",
    "#0072B2",
    "#D55E00",
    "#CC79A7",
)

DEFAULT_GLYPHS: tuple[str, ...] = ("●", "▲", "■", "◆", "★", "✚", "✱", "✦", "◐", "◇", "□", "△")
HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


@dataclass(slots=True)
class PaletteEntry:
    """One editable language palette entry."""

    colour: str
    glyph: str


class LanguagePalette:
    """Project-local language palette with YAML persistence.

    Parameters may point either at a project root, where `palette.yaml` will be
    stored, or at an explicit palette file. The class is deterministic even
    without a saved file: a given language code always maps to the same colour
    and glyph within Wong's colourblind-safe palette (Wong, 2011).
    """

    def __init__(self, project_root: Path | None = None, palette_path: Path | None = None) -> None:
        self.project_root = project_root.expanduser().resolve() if project_root else None
        self.palette_path = palette_path or (self.project_root / "palette.yaml" if self.project_root else None)
        self._custom: dict[str, PaletteEntry] = {}
        if self.palette_path and self.palette_path.exists():
            self._load()

    def colour_for(self, language_code: str) -> str:
        """Return the hex colour for a language code."""

        code = _normalise_code(language_code)
        if code in self._custom:
            return self._custom[code].colour
        return WONG_COLOURS[_stable_index(code, len(WONG_COLOURS))]

    def glyph_for(self, language_code: str) -> str:
        """Return the deterministic non-colour glyph for a language code."""

        code = _normalise_code(language_code)
        if code in self._custom:
            return self._custom[code].glyph
        return DEFAULT_GLYPHS[_stable_index(code, len(DEFAULT_GLYPHS))]

    def is_colourblind_safe(self) -> bool:
        """Return True if all configured colours are in the safe default set."""

        return all(entry.colour.upper() in {colour.upper() for colour in WONG_COLOURS} for entry in self._custom.values())

    def customise(self, language_code: str, colour: str | None = None, glyph: str | None = None) -> None:
        """Persist a project-specific colour or glyph override to `palette.yaml`."""

        code = _normalise_code(language_code)
        current = self._custom.get(code, PaletteEntry(self.colour_for(code), self.glyph_for(code)))
        new_colour = colour or current.colour
        new_glyph = glyph or current.glyph
        if not HEX_RE.match(new_colour):
            raise ValueError(f"Palette colour must be a #RRGGBB value, got {new_colour!r}.")
        if not new_glyph:
            raise ValueError("Palette glyph must not be empty.")
        self._custom[code] = PaletteEntry(new_colour, new_glyph)
        self._save()

    def as_dict(self, language_codes: list[str]) -> dict[str, dict[str, str]]:
        """Return serialisable palette entries for the supplied languages."""

        return {
            _normalise_code(code): {"colour": self.colour_for(code), "glyph": self.glyph_for(code)}
            for code in language_codes
        }

    def _load(self) -> None:
        data = yaml.safe_load(self.palette_path.read_text(encoding="utf-8")) or {}
        for code, raw in dict(data.get("languages", {})).items():
            if isinstance(raw, dict):
                colour = str(raw.get("colour", ""))
                glyph = str(raw.get("glyph", ""))
                if HEX_RE.match(colour) and glyph:
                    self._custom[_normalise_code(code)] = PaletteEntry(colour, glyph)

    def _save(self) -> None:
        if self.palette_path is None:
            return
        self.palette_path.parent.mkdir(parents=True, exist_ok=True)
        data: dict[str, Any] = {
            "schema_version": "1.0",
            "accessibility_note": "Colours are always paired with glyphs; meaning is never encoded in colour alone.",
            "languages": {
                code: {"colour": entry.colour, "glyph": entry.glyph}
                for code, entry in sorted(self._custom.items())
            },
        }
        self.palette_path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def _normalise_code(language_code: str) -> str:
    return (language_code or "und").strip().lower() or "und"


def _stable_index(value: str, size: int) -> int:
    digest = sha256(value.encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big") % size
