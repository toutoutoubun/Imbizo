"""Tests for bootstrap-aware baseline LID loader."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

from imbizo.core.lid.baseline import load_baseline_lid


class _FakeModel:
    def predict(self, text: str, k: int) -> tuple[list[str], list[float]]:
        return ["__label__zul", "__label__eng"][:k], [0.8, 0.2][:k]


def test_load_baseline_lid_uses_bootstrap_model(tmp_path: Path, monkeypatch) -> None:
    """The loader reads models/lid/lid.176.ftz without bundling a real model."""

    model_dir = tmp_path / "models" / "lid"
    model_dir.mkdir(parents=True)
    (model_dir / "lid.176.ftz").write_bytes(b"fixture")
    monkeypatch.setitem(sys.modules, "fasttext", SimpleNamespace(load_model=lambda path: _FakeModel()))
    lid = load_baseline_lid(model_dir)
    predictions = lid.identify("sawubona", top_k=2)
    assert predictions[0].language_code == "zul"
    assert predictions[0].confidence == 0.8


def test_load_baseline_lid_degrades_when_missing(tmp_path: Path) -> None:
    """Missing model gives a clear local bootstrap instruction."""

    lid = load_baseline_lid(tmp_path / "missing")
    prediction = lid.identify("hello")[0]
    assert prediction.language_code == "und"
    assert "bootstrap" in str(prediction.evidence["message"])
