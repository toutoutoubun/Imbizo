"""Language labels and defaults."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Sequence


class LanguageCategory(StrEnum):
    """Kinds of language labels available to researchers."""

    LANGUAGE = "language"
    UNKNOWN = "unknown"
    MIXED = "mixed"
    BORROWING = "borrowing"
    PROPER_NOUN = "proper_noun"
    USER_DEFINED = "user_defined"


@dataclass(slots=True)
class LanguageTag:
    """A project language, special label, or user-defined variety."""

    id: str
    code: str
    name: str
    autonym: str = ""
    category: LanguageCategory = LanguageCategory.LANGUAGE
    color_hex: str = "#808080"
    is_expected: bool = False
    is_user_defined: bool = False
    sort_order: int = 0
    notes: str = ""


def default_language_tags() -> list[LanguageTag]:
    """Return default language tags for a new project."""

    return [
        LanguageTag("lang-eng", "eng", "English", "English", color_hex="#2F6BFF", is_expected=True, sort_order=10),
        LanguageTag("lang-afr", "afr", "Afrikaans", "Afrikaans", color_hex="#E07A2F", is_expected=True, sort_order=20),
        LanguageTag("lang-zul", "zul", "isiZulu", "isiZulu", color_hex="#1F9D55", is_expected=True, sort_order=30),
        LanguageTag("lang-xho", "xho", "isiXhosa", "isiXhosa", color_hex="#8E44AD", is_expected=True, sort_order=40),
        LanguageTag("lang-sot", "sot", "Sesotho", "Sesotho", color_hex="#C0392B", is_expected=True, sort_order=50),
        LanguageTag("lang-tsn", "tsn", "Setswana", "Setswana", color_hex="#008B8B", is_expected=True, sort_order=60),
        LanguageTag("lang-und", "und", "Unknown", "Unknown", LanguageCategory.UNKNOWN, "#808080", False, False, 900),
        LanguageTag("lang-mixed", "mixed", "Mixed", "Mixed", LanguageCategory.MIXED, "#6C757D", False, False, 910),
        LanguageTag("lang-borrowing", "borrowing", "Borrowing", "Borrowing", LanguageCategory.BORROWING, "#7A5C00", False, False, 920),
        LanguageTag("lang-proper-noun", "proper_noun", "Proper noun", "Proper noun", LanguageCategory.PROPER_NOUN, "#555555", False, False, 930),
    ]


def find_language_by_code(languages: Sequence[LanguageTag], code: str) -> LanguageTag | None:
    """Find a language tag by code."""

    normalized = code.strip().lower()
    for language in languages:
        if language.code.lower() == normalized:
            return language
    return None


def sort_languages_for_legend(languages: Sequence[LanguageTag]) -> list[LanguageTag]:
    """Return languages in display order for the UI legend."""

    return sorted(languages, key=lambda item: (item.sort_order, item.name.lower()))
