"""Stable local plug-in registration API for Imbizo-CS Workbench.

Registration is local-file based only. The functions validate YAML dictionary
metadata and store paths in an in-process registry; they do not contact package
indexes, update servers, web APIs, or telemetry services.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from imbizo.core.concord import load_concord_dictionary
from imbizo.core.four_m import load_four_m_dictionary
from imbizo.core.noun_class import load_noun_class_dictionary


_NOUN_CLASS_DICTIONARIES: dict[str, Path] = {}
_CONCORD_DICTIONARIES: dict[str, Path] = {}
_FOUR_M_DICTIONARIES: dict[str, Path] = {}
_SISTER_LANG_DICTIONARIES: dict[str, Path] = {}
_TRIGGER_DICTIONARIES: dict[str, Path] = {}
_MIXED_CODE_DICTIONARIES: dict[str, Path] = {}
_PHONOLOGY_DICTIONARIES: dict[str, Path] = {}


def register_noun_class_dictionary(language_code: str, path: Path) -> None:
    """Register a local noun-class YAML dictionary for one language.

    The YAML is loaded immediately to verify required metadata, including the
    `source` field. No network calls are made.
    """

    dictionary = load_noun_class_dictionary(_validated_local_path(path))
    _validate_language_code(language_code, dictionary.language_code)
    _NOUN_CLASS_DICTIONARIES[language_code] = path.expanduser().resolve()


def register_concord_dictionary(language_code: str, path: Path) -> None:
    """Register a local concord YAML dictionary for one language.

    The YAML is loaded immediately to verify required metadata, including the
    `source` field. No network calls are made.
    """

    dictionary = load_concord_dictionary(_validated_local_path(path))
    _validate_language_code(language_code, dictionary.language_code)
    _CONCORD_DICTIONARIES[language_code] = path.expanduser().resolve()


def register_four_m_dictionary(language_code: str, path: Path) -> None:
    """Register a local 4-M YAML dictionary for one language.

    The YAML is loaded immediately to verify required metadata, including the
    `source` field. No network calls are made.
    """

    dictionary = load_four_m_dictionary(_validated_local_path(path))
    _validate_language_code(language_code, dictionary.language_code)
    _FOUR_M_DICTIONARIES[language_code] = path.expanduser().resolve()


def get_registered_noun_class_dictionary(language_code: str) -> Path | None:
    """Return a registered local noun-class dictionary path, if present."""

    return _NOUN_CLASS_DICTIONARIES.get(language_code)


def get_registered_concord_dictionary(language_code: str) -> Path | None:
    """Return a registered local concord dictionary path, if present."""

    return _CONCORD_DICTIONARIES.get(language_code)


def get_registered_four_m_dictionary(language_code: str) -> Path | None:
    """Return a registered local 4-M dictionary path, if present."""

    return _FOUR_M_DICTIONARIES.get(language_code)


def register_sister_lang_dictionary(pair_code: str, path: Path) -> None:
    """Register a local sister-language disambiguation dictionary.

    Registration validates only local YAML metadata and never initiates network
    calls. The dictionary remains advisory and project overridable.
    """

    _SISTER_LANG_DICTIONARIES[pair_code] = _validated_yaml_metadata(
        _validated_local_path(path),
        required_fields=["source", "language_code"],
    )


def register_trigger_dictionary(language_code: str, path: Path) -> None:
    """Register a local Clyne-style trigger dictionary."""

    _TRIGGER_DICTIONARIES[language_code] = _validated_yaml_metadata(
        _validated_local_path(path),
        required_fields=["source", "language_code"],
    )


def register_mixed_code_dictionary(variety_code: str, path: Path) -> None:
    """Register a local mixed-code variety profile."""

    _MIXED_CODE_DICTIONARIES[variety_code] = _validated_yaml_metadata(
        _validated_local_path(path),
        required_fields=["source", "variety_code", "caveats"],
    )


def register_phonology_dictionary(language_code: str, path: Path) -> None:
    """Register a local phonology dictionary for Integration Score v2."""

    _PHONOLOGY_DICTIONARIES[language_code] = _validated_yaml_metadata(
        _validated_local_path(path),
        required_fields=["source", "language_code"],
    )


def get_registered_sister_lang_dictionary(pair_code: str) -> Path | None:
    """Return a registered sister-language dictionary path, if present."""

    return _SISTER_LANG_DICTIONARIES.get(pair_code)


def get_registered_trigger_dictionary(language_code: str) -> Path | None:
    """Return a registered trigger dictionary path, if present."""

    return _TRIGGER_DICTIONARIES.get(language_code)


def get_registered_mixed_code_dictionary(variety_code: str) -> Path | None:
    """Return a registered mixed-code profile path, if present."""

    return _MIXED_CODE_DICTIONARIES.get(variety_code)


def get_registered_phonology_dictionary(language_code: str) -> Path | None:
    """Return a registered phonology dictionary path, if present."""

    return _PHONOLOGY_DICTIONARIES.get(language_code)


def _validated_local_path(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"Dictionary file does not exist: {resolved}")
    if not resolved.is_file():
        raise ValueError(f"Dictionary path is not a file: {resolved}")
    if resolved.suffix.lower() not in {".yaml", ".yml"}:
        raise ValueError("Dictionary registrations must point to YAML files.")
    return resolved


def _validated_yaml_metadata(path: Path, required_fields: list[str]) -> Path:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    missing = [field for field in required_fields if not data.get(field)]
    if missing:
        raise ValueError(f"{path} is missing required fields: {', '.join(missing)}")
    return path


def _validate_language_code(expected: str, actual: str) -> None:
    if expected != actual:
        raise ValueError(f"Registered language code `{expected}` does not match YAML language_code `{actual}`.")
