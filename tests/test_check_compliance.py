"""Tests for dictionary compliance safeguards."""

from __future__ import annotations

from tools.check_compliance import _looks_like_placeholder_license


def test_placeholder_license_text_is_detected() -> None:
    """Placeholder license files must not pass release compliance."""

    assert _looks_like_placeholder_license(
        "CC-BY-4.0\n\nREPLACE THIS FILE WITH THE VERBATIM LICENSE TEXT FROM <url>\n"
    )
    assert _looks_like_placeholder_license("PLACEHOLDER")
    assert _looks_like_placeholder_license("")


def test_non_placeholder_license_text_is_not_flagged() -> None:
    """Ordinary license-like text is not rejected by the placeholder guard."""

    assert not _looks_like_placeholder_license(
        "Sample License\nPermission is granted to copy this text subject to attribution."
    )
