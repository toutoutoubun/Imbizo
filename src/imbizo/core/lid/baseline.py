"""Bootstrap-aware fastText-compatible local baseline LID API."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from imbizo.lid.baseline import FASTTEXT_TO_PROJECT_CODE, BaselineLidProvider
from imbizo.lid.providers import LanguageScore, LidOptions


@dataclass(slots=True)
class LIDPrediction:
    """One baseline language-identification prediction."""

    language_code: str
    confidence: float
    evidence: dict[str, Any] = field(default_factory=dict)


class BaselineLID:
    """Local fastText lid.176 wrapper installed by the bootstrap subsystem.

    The model follows Joulin et al. (2017). If the model file or Python binding
    is missing, `identify` returns an `und` prediction with a clear local setup
    message instead of attempting any network access.
    """

    def __init__(self, model_path: Path) -> None:
        self.model_path = model_path
        self._model: object | None = None
        self.error_message: str | None = None
        self._load()

    @property
    def is_available(self) -> bool:
        """Return whether a local fastText model is loaded."""

        return self._model is not None

    def identify(self, text: str, top_k: int = 3) -> list[LIDPrediction]:
        """Return local LID predictions for one text string."""

        if self._model is None:
            return [
                LIDPrediction(
                    language_code="und",
                    confidence=0.0,
                    evidence={
                        "method": "fastText lid.176 unavailable",
                        "message": self.error_message or "Run dictionary/resource bootstrap to install models/lid/lid.176.ftz.",
                    },
                )
            ]
        labels, probabilities = self._model.predict(text.replace("\n", " "), k=top_k)  # type: ignore[attr-defined]
        predictions: list[LIDPrediction] = []
        for label, probability in zip(labels, probabilities, strict=False):
            raw_code = str(label).replace("__label__", "")
            predictions.append(
                LIDPrediction(
                    language_code=FASTTEXT_TO_PROJECT_CODE.get(raw_code, raw_code),
                    confidence=float(probability),
                    evidence={"method": "fastText lid.176", "model_path": str(self.model_path)},
                )
            )
        return predictions

    def _load(self) -> None:
        if not self.model_path.exists():
            self.error_message = f"Baseline LID model missing at {self.model_path}. Run tools/bootstrap.py for fasttext_lid176_ftz."
            return
        try:
            import fasttext  # type: ignore[import-not-found]
        except ImportError:
            self.error_message = "fasttext Python package is not installed; install the offline wheelhouse and rerun."
            return
        try:
            self._model = fasttext.load_model(str(self.model_path))
        except Exception as exc:  # noqa: BLE001 - UI-facing API must degrade gracefully.
            self.error_message = f"Could not load baseline LID model at {self.model_path}: {exc}"
            self._model = None


def load_baseline_lid(model_dir: Path = Path("models/lid")) -> BaselineLID:
    """Load the bootstrap-installed fastText lid.176 baseline model."""

    preferred = model_dir / "lid.176.ftz"
    fallback = model_dir / "lid.176.bin"
    return BaselineLID(preferred if preferred.exists() else fallback)


__all__ = [
    "BaselineLID",
    "BaselineLidProvider",
    "LIDPrediction",
    "LanguageScore",
    "LidOptions",
    "load_baseline_lid",
]
