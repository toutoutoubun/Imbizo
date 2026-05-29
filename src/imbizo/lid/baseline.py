"""Lightweight local baseline LID provider."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Sequence

from imbizo.lid.providers import LanguageScore, LidOptions


AFRIKAANS_WORDS = {"die", "en", "van", "ek", "jy", "nie", "het", "ons", "hulle", "met", "maar", "wat"}
ENGLISH_WORDS = {
    "a",
    "am",
    "and",
    "are",
    "at",
    "for",
    "friend",
    "go",
    "going",
    "hello",
    "home",
    "i",
    "in",
    "is",
    "market",
    "my",
    "of",
    "that",
    "the",
    "this",
    "to",
    "was",
    "we",
    "went",
    "were",
    "with",
    "you",
}
ZULU_WORDS = {"ngiyabonga", "sawubona", "yebo", "cha", "kahle", "ekhaya", "umuntu", "abantu", "umsebenzi"}
XHOSA_WORDS = {"enkosi", "molo", "ewe", "hayi", "umntu"}
SOTHO_TSWANA_WORDS = {"dumela", "ke", "le", "ba", "re"}
ZULU_PREFIXES = ("ngiya", "ngi", "uku", "kwa", "aba", "ama", "isi", "ezi", "umu", "imi")
XHOSA_PREFIXES = ("ndiya", "ndi", "uku", "kwa", "aba", "ama", "isi", "izi", "um", "imi")
SOTHO_TSWANA_PREFIXES = ("ho", "mo", "se", "di", "ma")
MODEL_FILENAMES = ("lid.176.ftz", "lid.176.bin")
FASTTEXT_TO_PROJECT_CODE = {
    "af": "afr",
    "en": "eng",
    "st": "sot",
    "tn": "tsn",
    "xh": "xho",
    "zu": "zul",
}


class BaselineLidProvider:
    """CPU-friendly local baseline LID provider.

    The provider attempts to use a local fastText `lid.176` model following
    Joulin et al. (2017). If no model file or fastText Python binding is
    available, it gracefully degrades to a deterministic heuristic fallback and
    reports that method in the evidence payload.
    """

    name = "baseline_fasttext_or_heuristic"
    version = "0.1"

    def __init__(self, model_path: Path | None = None, search_roots: Sequence[Path] | None = None) -> None:
        env_path = os.environ.get("IMBIZO_FASTTEXT_LID_MODEL", "").strip()
        self.model_path = model_path or (Path(env_path).expanduser() if env_path else None)
        self.search_roots = [path.expanduser() for path in (search_roots or [])]
        self._model: object | None = None
        self.load_error: str = ""
        self.active_method = "heuristic"

    @property
    def is_model_loaded(self) -> bool:
        """Return whether fastText is active for this provider."""

        return self._model is not None

    def configure_search_roots(self, roots: Sequence[Path]) -> None:
        """Replace model search roots before the first prediction."""

        if self._model is not None:
            return
        self.search_roots = [path.expanduser() for path in roots]

    def load(self) -> None:
        """Load local model resources."""
        if self._model is not None:
            return
        model_path = self._resolve_model_path()
        if model_path is None:
            self.active_method = "heuristic"
            self.load_error = "No local fastText lid.176 model found; using deterministic heuristic fallback."
            return
        try:
            import fasttext  # type: ignore[import-not-found]
        except ImportError:
            self.active_method = "heuristic"
            self.load_error = "fasttext Python package is not installed; using deterministic heuristic fallback."
            return
        try:
            self._model = fasttext.load_model(str(model_path))
        except Exception as exc:  # noqa: BLE001 - provider must degrade, not crash the GUI.
            self.active_method = "heuristic"
            self.load_error = f"Could not load local fastText model at {model_path}: {exc}"
            self._model = None
            return
        self.model_path = model_path
        self.active_method = "fastText lid.176"
        self.load_error = ""

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
            raw_code = str(label).replace("__label__", "")
            code = FASTTEXT_TO_PROJECT_CODE.get(raw_code, raw_code)
            scores.append(LanguageScore(code, float(probability), {"method": "fastText lid.176", "model_path": str(self.model_path)}))
        return scores

    def _predict_one(self, text: str) -> list[LanguageScore]:
        lower = text.lower()
        words = re.findall(r"[a-zA-ZÀ-ÿ']+", lower)
        scores = {"eng": 0.03, "afr": 0.03, "zul": 0.03, "xho": 0.03, "sot": 0.03, "tsn": 0.03}
        evidence: dict[str, list[str]] = {code: [] for code in scores}
        for word in words:
            if word in ENGLISH_WORDS:
                scores["eng"] += 0.42
                evidence["eng"].append(f"word:{word}")
            if word in AFRIKAANS_WORDS:
                scores["afr"] += 0.42
                evidence["afr"].append(f"word:{word}")
            if word in ZULU_WORDS:
                scores["zul"] += 0.55
                evidence["zul"].append(f"word:{word}")
            if word in XHOSA_WORDS:
                scores["xho"] += 0.55
                evidence["xho"].append(f"word:{word}")
            if word in SOTHO_TSWANA_WORDS:
                scores["sot"] += 0.20
                scores["tsn"] += 0.20
                evidence["sot"].append(f"shared_word:{word}")
                evidence["tsn"].append(f"shared_word:{word}")
            if len(word) >= 4 and any(word.startswith(prefix) for prefix in ZULU_PREFIXES):
                scores["zul"] += 0.24
                evidence["zul"].append(f"prefix:{word}")
            if len(word) >= 4 and any(word.startswith(prefix) for prefix in XHOSA_PREFIXES):
                scores["xho"] += 0.24
                evidence["xho"].append(f"prefix:{word}")
            if len(word) >= 4 and any(word.startswith(prefix) for prefix in SOTHO_TSWANA_PREFIXES):
                scores["sot"] += 0.14
                scores["tsn"] += 0.14
                evidence["sot"].append(f"shared_prefix:{word}")
                evidence["tsn"].append(f"shared_prefix:{word}")
        if re.search(r"[qx]", lower):
            scores["xho"] += 0.20
            evidence["xho"].append("orthography:q_or_x")
        if re.search(r"\b(ngiy|ngi)", lower):
            scores["zul"] += 0.28
            evidence["zul"].append("subject_concord:ngi")
        if re.search(r"\b(ndiy|ndi)", lower):
            scores["xho"] += 0.28
            evidence["xho"].append("subject_concord:ndi")
        total = sum(scores.values()) or 1.0
        ranked = sorted(
            (
                LanguageScore(
                    code,
                    min(1.0, value / total),
                    {
                        "method": "heuristic",
                        "matched_evidence": evidence[code],
                        "model_status": self.load_error,
                    },
                )
                for code, value in scores.items()
            ),
            key=lambda item: item.confidence,
            reverse=True,
        )
        if ranked[0].confidence < 0.34 or not ranked[0].evidence.get("matched_evidence"):
            return [LanguageScore("und", 0.5, {"method": "heuristic", "reason": "low evidence", "model_status": self.load_error})]
        return ranked

    def _resolve_model_path(self) -> Path | None:
        if self.model_path is not None:
            if self.model_path.is_dir():
                for filename in MODEL_FILENAMES:
                    candidate = self.model_path / filename
                    if candidate.exists():
                        return candidate
                return None
            return self.model_path if self.model_path.exists() else None
        candidates: list[Path] = []
        for root in self.search_roots:
            candidates.extend((root / "models" / "lid" / filename for filename in MODEL_FILENAMES))
            candidates.extend((root / "lid" / filename for filename in MODEL_FILENAMES))
        candidates.extend((Path.cwd() / "models" / "lid" / filename for filename in MODEL_FILENAMES))
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None
