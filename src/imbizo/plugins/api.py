"""Stable local plug-in registration API for Imbizo-CS Workbench.

Registration is local-file based only. The functions validate YAML dictionary
metadata and store paths in an in-process registry; they do not contact package
indexes, update servers, web APIs, or telemetry services.
"""

from __future__ import annotations

from pathlib import Path

from imbizo.core.concord import load_concord_dictionary
from imbizo.core.four_m import load_four_m_dictionary
from imbizo.core.noun_class import load_noun_class_dictionary


_NOUN_CLASS_DICTIONARIES: dict[str, Path] = {}
_CONCORD_DICTIONARIES: dict[str, Path] = {}
_FOUR_M_DICTIONARIES: dict[str, Path] = {}


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


def _validated_local_path(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"Dictionary file does not exist: {resolved}")
    if not resolved.is_file():
        raise ValueError(f"Dictionary path is not a file: {resolved}")
    if resolved.suffix.lower() not in {".yaml", ".yml"}:
        raise ValueError("Dictionary registrations must point to YAML files.")
    return resolved


def _validate_language_code(expected: str, actual: str) -> None:
    if expected != actual:
        raise ValueError(f"Registered language code `{expected}` does not match YAML language_code `{actual}`.")

