"""Tests for offline morphologically annotated corpus loader."""

from __future__ import annotations

from pathlib import Path

import yaml

from imbizo.core.morphology.annotated_corpus_loader import load_morph_corpus


def test_load_morph_corpus_reads_index_tag_inventory(tmp_path: Path) -> None:
    """Loader exposes prefix tag frequencies from local index.yaml."""

    lang_dir = tmp_path / "zul"
    lang_dir.mkdir()
    (lang_dir / "zul_morph.txt").write_text("umuntu NPre+NRoot\n", encoding="utf-8")
    (lang_dir / "index.yaml").write_text(
        yaml.safe_dump({"corpus_file": "zul_morph.txt", "tag_inventory": {"NPre": 3, "NRoot": 2, "Fut": 1}}),
        encoding="utf-8",
    )
    corpus = load_morph_corpus("zul", tmp_path)
    assert corpus.tag_frequency("N") == {"NPre": 3, "NRoot": 2}
