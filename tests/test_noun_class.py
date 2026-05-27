"""Tests for v1.0 noun-class dictionary loading and string matching."""

from __future__ import annotations

from imbizo.core.noun_class import load_default_noun_class_dictionary, suggest_class


def test_zulu_fictional_loanword_candidates_include_class_9() -> None:
    """# fictional test data: i-laptop is used only to test dictionary plumbing."""

    dictionary = load_default_noun_class_dictionary("zul")
    suggestions = suggest_class("i-laptop", "i-", "zul")

    assert dictionary.language_code == "zul"
    assert any(suggestion.class_number == 9 for suggestion in suggestions)
    assert all(suggestion.source for suggestion in suggestions)


def test_xhosa_fictional_loanword_candidates_include_class_9() -> None:
    """# fictional test data: i-fax is used only to test dictionary plumbing."""

    suggestions = suggest_class("i-fax", "i-", "xho")

    assert any(suggestion.class_number == 9 for suggestion in suggestions)


def test_zulu_fictional_plural_loanword_prefers_class_6_candidate() -> None:
    """# fictional test data: ama-store is used only to test string matching."""

    suggestions = suggest_class("ama-store", "ama-", "zul")

    assert suggestions
    assert suggestions[0].class_number == 6
    assert suggestions[0].prefix == "ama-"
