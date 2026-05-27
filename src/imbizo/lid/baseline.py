"""Lightweight local baseline LID provider."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Sequence

from imbizo.lid.providers import LanguageScore, LidOptions


AFRIKAANS_HINTS = {"die", "en", "van", "ek", "jy", "nie", "het", "is", "ons", "hulle"}
ENGLISH_HINTS = {"the", "and", "is", "are", "was", "were", "i", "you", "we", "they", "this", "that"}
ZULU_XHOSA_HINTS = {"ng", "ku", "kwa", "ngi", "uku", "aba", "ama", "isi", "ezi"}
SOTHO_TSWANA_HINTS = {"ke", "le", "ba", "ho", "ya", "tsa", "se", "mo", "re"}


class BaselineLidProvider:
    """CPU-friendly local baseline LID provider.

    The provider attempts to use a local fastText `lid.176` model following
    Joulin et al. (2017). If no model file or fastText Python binding is
    available, it gracefully degrades to a deterministic heuristic fallback and
    reports that method in the evidence payload.
    """

    name = "baseline_fasttext_or_heuristic"
    version = "0.1"

    def __init__(self, model_path: Path | None = None) -> None:
        self.model_path = model_path or Path(os.environ.get("IMBIZO_FASTTEXT_LID_MODEL", ""))
        self._model: object | None = None

    def load(self) -> None:
        """Load local model resources."""
        if self._model is not None or not str(self.model_path):
            return
        if not self.model_path.exists():
            return
        try:
            import fasttext  # type: ignore[import-not-found]
        except ImportError:
            return
        self._model = fasttext.load_model(str(self.model_path))

    def predict(self, texts: Sequence[str], options: LidOptions) -> list[list[LanguageScore]]:
        """Predict ranked language labels."""

        self.load()
        if self._model is not None:
            return [self._predict_fasttext(text, options.max_languages) for text in texts]
        return [self._predict_one(text)[: options.max_languages] for text in texts]

    def _predict_fasttext(self, text: str, max_languages: int) -> list[LanguageScore]:
        labels, probabilities = self._model.predict(text.replace("\n", " "), k=max_languages)  # type: ignore[attr-defined]
        scores: list[LanguageScore] = []
        for label, probability in zip(labels, probabilities, strict=False):
            code = str(label).replace("__label__", "")
            scores.append(LanguageScore(code, float(probability), {"method": "fastText lid.176"}))
        return scores

    def _predict_one(self, text: str) -> list[LanguageScore]:
        lower = text.lower()
        words = re.findall(r"[a-zA-Z']+", lower)
        scores = {"eng": 0.05, "afr": 0.05, "zul": 0.05, "xho": 0.05, "sot": 0.05, "tsn": 0.05}
        for word in words:
            if word in ENGLISH_HINTS:
                scores["eng"] += 0.35
            if word in AFRIKAANS_HINTS:
                scores["afr"] += 0.35
            if any(word.startswith(prefix) for prefix in ZULU_XHOSA_HINTS):
                scores["zul"] += 0.2
                scores["xho"] += 0.2
            if word in SOTHO_TSWANA_HINTS or any(word.startswith(prefix) for prefix in SOTHO_TSWANA_HINTS):
                scores["sot"] += 0.16
                scores["tsn"] += 0.16
        if re.search(r"[qx]", lower):
            scores["xho"] += 0.18
        if re.search(r"\b(ngiy|ngi|uku|kwa)", lower):
            scores["zul"] += 0.2
        total = sum(scores.values()) or 1.0
        ranked = sorted(
            (LanguageScore(code, min(1.0, value / total), {"method": "heuristic"}) for code, value in scores.items()),
            key=lambda item: item.confidence,
            reverse=True,
        )
        if ranked[0].confidence < 0.22:
            return [LanguageScore("und", 0.5, {"method": "heuristic", "reason": "low evidence"})]
        return ranked
