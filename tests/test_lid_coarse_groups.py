"""Tests for the conservative coarse language-group LID gate."""

from __future__ import annotations

from imbizo.lid.coarse_groups import (
    aggregate_group_scores,
    apply_coarse_group_gate,
    assess_group_confidence,
    language_to_group,
    normalize_language_label,
)
from imbizo.lid.providers import LanguageScore, LidLayer, LidOptions, LidSuggestionDraft


def _draft(*scores: tuple[str, float]) -> LidSuggestionDraft:
    return LidSuggestionDraft(
        token_id="tok-1",
        segment_id=None,
        language_id="lang-zul",
        layer=LidLayer.LAYER1_BASELINE,
        rank=1,
        confidence=scores[0][1],
        evidence={
            "language_code": scores[0][0],
            "candidate_scores": [
                {"language_code": code, "confidence": confidence, "rank": index}
                for index, (code, confidence) in enumerate(scores, start=1)
            ],
        },
    )


def test_normalize_language_label_handles_common_aliases() -> None:
    """Common names and ISO aliases normalize to stable ISO 639-3 codes."""

    assert normalize_language_label("English") == "eng"
    assert normalize_language_label("en") == "eng"
    assert normalize_language_label("isiZulu") == "zul"
    assert normalize_language_label("Zulu") == "zul"
    assert normalize_language_label("Northern Sotho") == "nso"
    assert normalize_language_label("proper noun") == "proper_noun"
    assert normalize_language_label("not-in-map") is None


def test_language_to_group_maps_south_african_language_groups() -> None:
    """Languages map to the conservative coarse groups used by the gate."""

    assert language_to_group("eng") == "Germanic"
    assert language_to_group("Afrikaans") == "Germanic"
    assert language_to_group("xho") == "Nguni"
    assert language_to_group("Siswati") == "Nguni"
    assert language_to_group("Sesotho") == "Sotho-Tswana"
    assert language_to_group("tn") == "Sotho-Tswana"
    assert language_to_group("Tshivenda") == "Venda"
    assert language_to_group("Tsonga") == "Tsonga"
    assert language_to_group("und") == "special"
    assert language_to_group("unmapped") == "unassigned"


def test_aggregate_group_scores_and_confidence() -> None:
    """Language confidence scores aggregate without changing source scores."""

    scores = [
        LanguageScore("zul", 0.39),
        LanguageScore("xho", 0.31),
        LanguageScore("eng", 0.20),
        LanguageScore("afr", 0.05),
    ]

    grouped = aggregate_group_scores(scores)

    assert grouped["Nguni"] == 0.70
    assert grouped["Germanic"] == 0.25
    assert assess_group_confidence(grouped) == "high"


def test_low_group_confidence_blocks_auto_apply_when_gate_enabled() -> None:
    """Low coarse-group confidence blocks auto labels but preserves evidence."""

    gated = apply_coarse_group_gate(_draft(("zul", 0.34), ("eng", 0.31), ("sot", 0.29)), LidOptions(use_coarse_group_gate=True))

    evidence = gated.evidence["coarse_group_gate"]
    assert evidence["group_confidence"] == "low"
    assert evidence["auto_apply_allowed"] is False
    assert evidence["reason"] == "low_group_confidence"


def test_nguni_language_ambiguity_blocks_auto_apply_when_gate_enabled() -> None:
    """Close isiZulu/isiXhosa evidence is saved as ambiguity, not auto-applied."""

    gated = apply_coarse_group_gate(_draft(("zul", 0.52), ("xho", 0.48)), LidOptions(use_coarse_group_gate=True))

    evidence = gated.evidence["coarse_group_gate"]
    assert evidence["top_group"] == "Nguni"
    assert evidence["auto_apply_allowed"] is False
    assert evidence["reason"] == "closely_related_language_group"
    assert "closely related" in evidence["warnings"][0]


def test_sotho_tswana_language_ambiguity_blocks_auto_apply_when_gate_enabled() -> None:
    """Close Sesotho/Setswana/Sepedi evidence is treated conservatively."""

    gated = apply_coarse_group_gate(_draft(("sot", 0.45), ("tsn", 0.38), ("nso", 0.14)), LidOptions(use_coarse_group_gate=True))

    evidence = gated.evidence["coarse_group_gate"]
    assert evidence["top_group"] == "Sotho-Tswana"
    assert evidence["auto_apply_allowed"] is False
    assert evidence["reason"] == "closely_related_language_group"


def test_gate_off_is_noop() -> None:
    """The new feature is default-off and preserves existing evidence exactly."""

    original = _draft(("zul", 0.52), ("xho", 0.48))
    before = dict(original.evidence)

    returned = apply_coarse_group_gate(original, LidOptions())

    assert returned is original
    assert returned.evidence == before
    assert "coarse_group_gate" not in returned.evidence
