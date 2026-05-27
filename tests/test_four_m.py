"""Tests for v1.0 4-M dictionary loading and MLF compatibility checks."""

from __future__ import annotations

from dataclasses import dataclass

from imbizo.core.four_m import check_mlf_compatibility, load_default_four_m_dictionary


@dataclass(slots=True)
class TaggedToken:
    """Small token stand-in with v1.0 4-M fields."""

    id: str
    segment_id: str
    sort_order: int
    token_text: str
    four_m_type: str | None
    language_id: str | None


def test_four_m_dictionary_loads_local_zulu_hints() -> None:
    """The 4-M dictionary is local YAML, not a network-backed resource."""

    dictionary = load_default_four_m_dictionary("zul")

    assert dictionary.language_code == "zul"
    assert dictionary.hints


def test_consistent_fictional_zulu_matrix_utterance() -> None:
    """# fictional test data: all system morphemes point to isiZulu."""

    verdict = check_mlf_compatibility(
        [
            TaggedToken("t1", "u1", 1, "u-", "outsider_late_system", "zul"),
            TaggedToken("t2", "u1", 2, "i-laptop", "content", "eng"),
            TaggedToken("t3", "u1", 3, "en-", "early_system", "zul"),
        ]
    )

    assert verdict.status == "consistent"
    assert verdict.recommended_review is False


def test_consistent_fictional_sesotho_matrix_utterance() -> None:
    """# fictional test data: all system morphemes point to Sesotho."""

    verdict = check_mlf_compatibility(
        [
            TaggedToken("t1", "u2", 1, "o-", "outsider_late_system", "sot"),
            TaggedToken("t2", "u2", 2, "meeting", "content", "eng"),
            TaggedToken("t3", "u2", 3, "ya", "bridge_late_system", "sot"),
        ]
    )

    assert verdict.status == "consistent"


def test_deliberately_mixed_fictional_case_requires_review() -> None:
    """# fictional test data: system morphemes point to more than one language."""

    verdict = check_mlf_compatibility(
        [
            TaggedToken("t1", "u3", 1, "u-", "outsider_late_system", "zul"),
            TaggedToken("t2", "u3", 2, "book", "content", "eng"),
            TaggedToken("t3", "u3", 3, "-s", "early_system", "eng"),
        ]
    )

    assert verdict.status == "mixed"
    assert verdict.recommended_review is True
