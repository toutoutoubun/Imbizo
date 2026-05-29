"""Local dictionary and morphology features for offline LID.

This module intentionally uses only local files bundled with Imbizo-CS or
project-local dictionary overrides. It gives the heuristic LID fallback a
slightly richer evidence base without changing the project's core posture:
automatic labels remain advisory and overridable.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from importlib import resources
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import yaml


LANGUAGE_RESOURCE_TO_CODE = {
    "isizulu_morphemes.json": "zul",
    "isixhosa_morphemes.json": "xho",
    "sesotho_morphemes.json": "sot",
    "setswana_morphemes.json": "tsn",
}
SHORT_PREFIXES_REQUIRING_DICTIONARY_WORD = {"ba", "bo", "di", "go", "ho", "ka", "ke", "ko", "le", "ma", "me", "mo", "se"}
MIN_PREFIXED_TOKEN_LENGTH = 5


@dataclass(frozen=True, slots=True)
class LocalFeatureMatch:
    """One local dictionary or morphology feature matched against text."""

    language_code: str
    weight: float
    evidence: str


@dataclass(frozen=True, slots=True)
class _WeightedFeature:
    language_code: str
    form: str
    weight: float
    evidence: str


class LocalFeatureIndex:
    """Index of local lexeme and morpheme cues used by the LID fallback."""

    def __init__(
        self,
        exact: Mapping[str, Sequence[_WeightedFeature]],
        prefixes: Sequence[_WeightedFeature],
        suffixes: Sequence[_WeightedFeature],
    ) -> None:
        self._exact = {key: tuple(value) for key, value in exact.items()}
        self._prefixes = tuple(sorted(prefixes, key=lambda item: len(item.form), reverse=True))
        self._suffixes = tuple(sorted(suffixes, key=lambda item: len(item.form), reverse=True))

    @classmethod
    def from_roots(cls, roots: Sequence[Path]) -> "LocalFeatureIndex":
        """Build an index from bundled resources plus optional local roots."""

        exact: dict[str, list[_WeightedFeature]] = {}
        prefixes: list[_WeightedFeature] = []
        suffixes: list[_WeightedFeature] = []
        _add_packaged_lid_features(exact, prefixes, suffixes)
        _add_packaged_morpheme_features(exact, prefixes)
        for dictionary_root in _dictionary_roots(roots):
            _add_trigger_features(dictionary_root, exact)
            _add_four_m_features(dictionary_root, exact, prefixes, suffixes)
            _add_noun_class_features(dictionary_root, prefixes)
        return cls(exact, prefixes, suffixes)

    def match(self, text: str, known_words: set[str] | None = None) -> list[LocalFeatureMatch]:
        """Return local feature matches for a token or short phrase."""

        normalized = _normalize_text(text)
        if not normalized:
            return []
        words = _words(normalized)
        known_words = known_words or set()
        matches: list[LocalFeatureMatch] = []
        for feature in self._exact.get(normalized, ()):
            matches.append(_to_match(feature, "exact"))
        if len(words) == 1:
            word = words[0]
            word_is_known_elsewhere = word in known_words
            for feature in self._prefixes:
                if not _prefix_matches(word, feature.form, word_is_known_elsewhere):
                    continue
                matches.append(_to_match(feature, "prefix"))
            for feature in self._suffixes:
                if len(word) <= len(feature.form) + 2 or not word.endswith(feature.form):
                    continue
                matches.append(_to_match(feature, "suffix"))
        return _deduplicate_matches(matches)


@lru_cache(maxsize=16)
def cached_local_feature_index(root_key: tuple[str, ...]) -> LocalFeatureIndex:
    """Return a cached feature index for a stable root tuple."""

    return LocalFeatureIndex.from_roots([Path(item) for item in root_key])


def cache_key_for_roots(roots: Sequence[Path]) -> tuple[str, ...]:
    """Build the cache key used by BaselineLidProvider."""

    return tuple(sorted(str(path.expanduser().resolve()) for path in roots if path.exists()))


def _dictionary_roots(roots: Sequence[Path]) -> list[Path]:
    candidates: list[Path] = []
    for root in roots:
        candidates.append(root.expanduser())
        candidates.append(root.expanduser() / "dictionaries")
    candidates.append(Path.cwd() / "dictionaries")
    package_file = Path(__file__).resolve()
    for parent in package_file.parents:
        candidates.append(parent / "dictionaries")
    seen: set[Path] = set()
    existing: list[Path] = []
    for candidate in candidates:
        resolved = candidate.resolve() if candidate.exists() else candidate
        if resolved in seen or not candidate.exists() or not candidate.is_dir():
            continue
        seen.add(resolved)
        existing.append(candidate)
    return existing


def _add_packaged_morpheme_features(exact: dict[str, list[_WeightedFeature]], prefixes: list[_WeightedFeature]) -> None:
    try:
        base = resources.files("imbizo.resources.dictionaries")
    except ModuleNotFoundError:
        return
    for filename, language_code in LANGUAGE_RESOURCE_TO_CODE.items():
        try:
            raw = (base / filename).read_text(encoding="utf-8")
        except FileNotFoundError:
            continue
        try:
            entries = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            form = _normalize_form(entry.get("surface"))
            if not form:
                continue
            category = str(entry.get("category", "morpheme"))
            feature = _WeightedFeature(
                language_code=language_code,
                form=form,
                weight=0.22,
                evidence=f"packaged_morpheme:{category}:{form}",
            )
            if len(form) <= 2:
                _append_exact(exact, form, feature)
            else:
                prefixes.append(feature)
                _append_exact(exact, form, feature)


def _add_packaged_lid_features(
    exact: dict[str, list[_WeightedFeature]],
    prefixes: list[_WeightedFeature],
    suffixes: list[_WeightedFeature],
) -> None:
    try:
        raw = (resources.files("imbizo.resources.lid") / "local_features.json").read_text(encoding="utf-8")
    except (FileNotFoundError, ModuleNotFoundError):
        return
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return
    if not isinstance(data, dict):
        return
    for item in data.get("exact", []) or []:
        feature = _feature_from_json(item)
        if feature is None:
            continue
        _append_exact(exact, feature.form, feature)
    for item in data.get("prefixes", []) or []:
        feature = _feature_from_json(item)
        if feature is not None:
            prefixes.append(feature)
    for item in data.get("suffixes", []) or []:
        feature = _feature_from_json(item)
        if feature is not None:
            suffixes.append(feature)


def _add_trigger_features(dictionary_root: Path, exact: dict[str, list[_WeightedFeature]]) -> None:
    for path in sorted((dictionary_root / "triggers").glob("*.yaml")):
        data = _load_yaml(path)
        language_code = str(data.get("language_code", path.stem)).strip()
        candidates = data.get("trigger_candidates", {})
        if not isinstance(candidates, dict):
            continue
        for category, entries in candidates.items():
            if not isinstance(entries, list):
                continue
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                form = _normalize_text(str(entry.get("form", "")))
                if not form:
                    continue
                weight = _trigger_weight(str(category), str(entry.get("trigger_type", "")))
                _append_exact(
                    exact,
                    form,
                    _WeightedFeature(language_code, form, weight, f"trigger_dictionary:{category}:{form}"),
                )


def _add_four_m_features(
    dictionary_root: Path,
    exact: dict[str, list[_WeightedFeature]],
    prefixes: list[_WeightedFeature],
    suffixes: list[_WeightedFeature],
) -> None:
    for path in sorted((dictionary_root / "four_m").glob("*.yaml")):
        data = _load_yaml(path)
        language_code = str(data.get("language_code", path.stem)).strip()
        hints = data.get("four_m_hints", {})
        if not isinstance(hints, dict):
            continue
        for category, entries in hints.items():
            if not isinstance(entries, list):
                continue
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                raw_form = str(entry.get("form", ""))
                form = _normalize_form(raw_form)
                if not form:
                    continue
                weight = 0.28 if category == "content" else 0.14
                feature = _WeightedFeature(language_code, form, weight, f"four_m_hint:{category}:{form}")
                if raw_form.startswith("-"):
                    # Suffixes in starter 4-M dictionaries are analytically useful
                    # for morphology review, but too noisy for token-level LID
                    # (for example Afrikaans -e/-s would overmatch English words).
                    # Packaged LID features add only tightly scoped suffix hints.
                    continue
                if raw_form.endswith("-") and len(form) >= 2:
                    prefixes.append(feature)
                else:
                    _append_exact(exact, form, feature)


def _add_noun_class_features(dictionary_root: Path, prefixes: list[_WeightedFeature]) -> None:
    for path in sorted((dictionary_root / "noun_classes").glob("*.yaml")):
        data = _load_yaml(path)
        language_code = str(data.get("language_code", path.stem)).strip()
        classes = data.get("classes", [])
        if not isinstance(classes, list):
            continue
        for entry in classes:
            if not isinstance(entry, dict):
                continue
            class_number = str(entry.get("class_number", "")).strip()
            verified = bool(entry.get("verified", False))
            weight = 0.16 if verified else 0.08
            for raw_prefix in entry.get("prefixes", []) or []:
                form = _normalize_form(raw_prefix)
                if not form or form in {"n", "ø"}:
                    continue
                prefixes.append(
                    _WeightedFeature(
                        language_code=language_code,
                        form=form,
                        weight=weight,
                        evidence=f"noun_class_prefix:{class_number}:{form}",
                    )
                )


def _trigger_weight(category: str, trigger_type: str) -> float:
    if category == "proper_nouns" or trigger_type == "proper_noun":
        return 0.08
    if category == "discourse_markers" or trigger_type == "discourse_marker":
        return 0.14
    if category in {"domain_specific_borrowings", "cognates"}:
        return 0.18
    return 0.12


def _feature_from_json(item: object) -> _WeightedFeature | None:
    if not isinstance(item, dict):
        return None
    language_code = str(item.get("language_code", "")).strip()
    form = _normalize_form(item.get("form", ""))
    if not language_code or not form:
        return None
    try:
        weight = float(item.get("weight", 0.12))
    except (TypeError, ValueError):
        weight = 0.12
    evidence = str(item.get("evidence", f"packaged_local_feature:{form}"))
    return _WeightedFeature(language_code, form, weight, evidence)


def _prefix_matches(word: str, prefix: str, word_is_known_elsewhere: bool) -> bool:
    if not word.startswith(prefix):
        return False
    if len(prefix) <= 1:
        return False
    if len(prefix) == 2:
        if word_is_known_elsewhere:
            return False
        if prefix in SHORT_PREFIXES_REQUIRING_DICTIONARY_WORD and len(word) < MIN_PREFIXED_TOKEN_LENGTH:
            return False
    return len(word) > len(prefix)


def _normalize_form(value: object) -> str:
    text = str(value).strip().lower()
    if not text or text == "ø":
        return ""
    text = re.sub(r"\([^)]*\)", "", text)
    text = text.replace("-", "")
    return _normalize_text(text)


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower()).strip()


def _words(value: str) -> list[str]:
    return re.findall(r"[a-zA-ZÀ-ÿ']+", value)


def _append_exact(exact: dict[str, list[_WeightedFeature]], form: str, feature: _WeightedFeature) -> None:
    exact.setdefault(form, []).append(feature)


def _to_match(feature: _WeightedFeature, match_kind: str) -> LocalFeatureMatch:
    return LocalFeatureMatch(
        language_code=feature.language_code,
        weight=feature.weight,
        evidence=f"{match_kind}:{feature.evidence}",
    )


def _deduplicate_matches(matches: Iterable[LocalFeatureMatch]) -> list[LocalFeatureMatch]:
    deduplicated: dict[tuple[str, str], LocalFeatureMatch] = {}
    for match in matches:
        key = (match.language_code, match.evidence)
        current = deduplicated.get(key)
        if current is None or match.weight > current.weight:
            deduplicated[key] = match
    return list(deduplicated.values())


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return {}
    return data if isinstance(data, dict) else {}
