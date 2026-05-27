from pathlib import Path

import yaml

from imbizo.core.visualisation.palette import LanguagePalette


def test_default_palette_is_colourblind_safe() -> None:
    palette = LanguagePalette()
    assert palette.is_colourblind_safe()
    assert palette.colour_for("zul").startswith("#")
    assert palette.glyph_for("zul")


def test_glyph_is_stable() -> None:
    palette = LanguagePalette()
    assert palette.glyph_for("xho") == palette.glyph_for("xho")


def test_customisation_persists(tmp_path: Path) -> None:
    palette_path = tmp_path / "palette.yaml"
    palette = LanguagePalette(palette_path=palette_path)
    palette.customise("eng", colour="#0072B2", glyph="◆")
    loaded = LanguagePalette(palette_path=palette_path)
    assert loaded.colour_for("eng") == "#0072B2"
    assert loaded.glyph_for("eng") == "◆"
    data = yaml.safe_load(palette_path.read_text(encoding="utf-8"))
    assert data["languages"]["eng"]["glyph"] == "◆"
