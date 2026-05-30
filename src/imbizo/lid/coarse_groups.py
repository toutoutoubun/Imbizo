"""Conservative coarse language-group gate for local LID suggestions.

The gate does not replace the baseline provider, MaskLID-style detector, or
the sister-language disambiguator. It only adds auditable evidence to LID
suggestions and, when explicitly enabled, can prevent risky auto-annotation
while still saving the underlying suggestion for researcher review.
"""

from __future__ import annotations

import re
from collections import defaultdict
from enum import StrEnum
from typing import Any, Literal, Mapping, Sequence

from imbizo.lid.providers import LanguageScore, LidOptions, LidSuggestionDraft


GroupConfidence = Literal["high", "medium", "low"]


class LanguageGroup(StrEnum):
    """Coarse South African language groups used for conservative LID gating."""

    GERMANIC = "Germanic"
    NGUNI = "Nguni"
    SOTHO_TSWANA = "Sotho-Tswana"
    VENDA = "Venda"
    TSONGA = "Tsonga"
    SPECIAL = "special"
    UNASSIGNED = "unassigned"


_NORMALIZED_LANGUAGE_ALIASES: dict[str, str] = {
    "english": "eng",
    "eng": "eng",
    "en": "eng",
    "afrikaans": "afr",
    "afr": "afr",
    "af": "afr",
    "isizulu": "zul",
    "zulu": "zul",
    "zul": "zul",
    "zu": "zul",
    "isixhosa": "xho",
    "xhosa": "xho",
    "xho": "xho",
    "xh": "xho",
    "isindebele": "nbl",
    "ndebele": "nbl",
    "nbl": "nbl",
    "nr": "nbl",
    "siswati": "ssw",
    "swati": "ssw",
    "ssw": "ssw",
    "ss": "ssw",
    "sepedi": "nso",
    "northernsotho": "nso",
    "northern_sotho": "nso",
    "nso": "nso",
    "sesotho": "sot",
    "southernsotho": "sot",
    "southern_sotho": "sot",
    "sot": "sot",
    "st": "sot",
    "setswana": "tsn",
    "tswana": "tsn",
    "tsn": "tsn",
    "tn": "tsn",
    "tshivenda": "ven",
    "venda": "ven",
    "ven": "ven",
    "ve": "ven",
    "xitsonga": "tso",
    "tsonga": "tso",
    "tso": "tso",
    "ts": "tso",
    "unknown": "und",
    "und": "und",
    "unk": "und",
    "mixed": "mixed",
    "borrowing": "borrowing",
    "propernoun": "proper_noun",
    "proper_noun": "proper_noun",
    "unassigned": "unassigned",
}

_LANGUAGE_TO_GROUP: dict[str, LanguageGroup] = {
    "eng": LanguageGroup.GERMANIC,
    "afr": LanguageGroup.GERMANIC,
    "zul": LanguageGroup.NGUNI,
    "xho": LanguageGroup.NGUNI,
    "nbl": LanguageGroup.NGUNI,
    "ssw": LanguageGroup.NGUNI,
    "nso": LanguageGroup.SOTHO_TSWANA,
    "sot": LanguageGroup.SOTHO_TSWANA,
    "tsn": LanguageGroup.SOTHO_TSWANA,
    "ven": LanguageGroup.VENDA,
    "tso": LanguageGroup.TSONGA,
    "und": LanguageGroup.SPECIAL,
    "mixed": LanguageGroup.SPECIAL,
    "borrowing": LanguageGroup.SPECIAL,
    "proper_noun": LanguageGroup.SPECIAL,
    "unassigned": LanguageGroup.SPECIAL,
}

_BANTU_GROUPS = {
    LanguageGroup.NGUNI.value,
    LanguageGroup.SOTHO_TSWANA.value,
    LanguageGroup.VENDA.value,
    LanguageGroup.TSONGA.value,
}
_CLOSELY_RELATED_GROUPS = {LanguageGroup.NGUNI.value, LanguageGroup.SOTHO_TSWANA.value}


def normalize_language_label(label: str) -> str | None:
    """Normalize a language label, ISO 639-3 code, or common alias.

    Returns ``None`` for empty labels or labels not covered by the deliberately
    small South African language map. This is transparent rather than clever:
    unsupported labels should remain visible for researcher review.
    """

    cleaned = _normalization_key(label)
    if not cleaned:
        return None
    return _NORMALIZED_LANGUAGE_ALIASES.get(cleaned)


def language_to_group(label_or_code: str) -> str:
    """Return the coarse language group for a label or code."""

    code = normalize_language_label(label_or_code)
    if code is None:
        return LanguageGroup.UNASSIGNED.value
    return _LANGUAGE_TO_GROUP.get(code, LanguageGroup.UNASSIGNED).value


def aggregate_group_scores(scores: Sequence[LanguageScore]) -> dict[str, float]:
    """Aggregate language-level confidence scores into coarse groups."""

    totals: dict[str, float] = defaultdict(float)
    for score in scores:
        group = language_to_group(score.language_code)
        if group == LanguageGroup.UNASSIGNED.value:
            continue
        totals[group] += max(0.0, float(score.confidence))
    return dict(sorted(totals.items(), key=lambda item: item[1], reverse=True))


def assess_group_confidence(group_scores: Mapping[str, float]) -> GroupConfidence:
    """Classify confidence in the top coarse group as high, medium, or low."""

    ordered = sorted(group_scores.items(), key=lambda item: item[1], reverse=True)
    if not ordered:
        return "low"
    top_score = ordered[0][1]
    next_score = ordered[1][1] if len(ordered) > 1 else 0.0
    margin = top_score - next_score
    if top_score >= 0.67 and margin >= 0.20:
        return "high"
    if top_score >= 0.45 and margin >= 0.12:
        return "medium"
    return "low"


def apply_coarse_group_gate(draft: LidSuggestionDraft, options: LidOptions) -> LidSuggestionDraft:
    """Add coarse-group gate evidence to a LID suggestion when enabled.

    When ``options.use_coarse_group_gate`` is false this function is a strict
    no-op and returns the input draft unchanged. When enabled, it annotates
    ``draft.evidence`` with a ``coarse_group_gate`` block. The original scores,
    language ID, confidence, and rank are not changed.
    """

    if not options.use_coarse_group_gate:
        return draft

    candidate_scores = _candidate_scores_from_evidence(draft)
    group_scores = aggregate_group_scores(candidate_scores)
    ordered_groups = sorted(group_scores.items(), key=lambda item: item[1], reverse=True)
    top_group = ordered_groups[0][0] if ordered_groups else LanguageGroup.UNASSIGNED.value
    group_confidence = assess_group_confidence(group_scores)
    warnings: list[str] = []
    auto_apply_allowed = True
    reason = "ok"

    if group_confidence == "low":
        auto_apply_allowed = False
        reason = "low_group_confidence"
        warnings.append("Coarse language group confidence is low; exact label should be reviewed manually.")

    language_scores = _language_scores_by_code(candidate_scores)
    if top_group in _CLOSELY_RELATED_GROUPS and _has_close_language_ambiguity(top_group, language_scores):
        auto_apply_allowed = False
        reason = "closely_related_language_group"
        warnings.append(f"{top_group} languages are closely related; exact language label should be reviewed manually.")

    if _has_germanic_bantu_boundary_warning(ordered_groups):
        warnings.append(
            "Germanic and Bantu evidence are close; review for borrowing, proper-noun, or mixed-language context."
        )

    gate_evidence = {
        "algorithm": "coarse_language_group_gate",
        "version": "0.1.0",
        "top_group": top_group,
        "group_confidence": group_confidence,
        "group_scores": [{"group": group, "score": round(score, 4)} for group, score in ordered_groups],
        "warnings": warnings,
        "auto_apply_allowed": auto_apply_allowed,
        "reason": reason,
    }
    draft.evidence = {**draft.evidence, "coarse_group_gate": gate_evidence}
    return draft


def coarse_gate_allows_auto_apply(draft: LidSuggestionDraft) -> bool:
    """Return whether gate evidence permits auto-annotation for this suggestion."""

    gate = draft.evidence.get("coarse_group_gate")
    if not isinstance(gate, Mapping):
        return True
    return gate.get("auto_apply_allowed") is not False


def coarse_gate_reason(draft: LidSuggestionDraft) -> str:
    """Return the gate reason for reporting, if present."""

    gate = draft.evidence.get("coarse_group_gate")
    if not isinstance(gate, Mapping):
        return ""
    reason = gate.get("reason")
    return str(reason) if reason is not None else ""


def _normalization_key(label: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", label.strip().lower()).strip("_").replace("__", "_")


def _candidate_scores_from_evidence(draft: LidSuggestionDraft) -> list[LanguageScore]:
    raw_scores = draft.evidence.get("candidate_scores")
    scores: list[LanguageScore] = []
    if isinstance(raw_scores, Sequence) and not isinstance(raw_scores, (str, bytes)):
        for item in raw_scores:
            if not isinstance(item, Mapping):
                continue
            code = item.get("language_code")
            confidence = item.get("confidence")
            if not isinstance(code, str) or not isinstance(confidence, (int, float)):
                continue
            scores.append(LanguageScore(code, float(confidence)))
    if scores:
        return scores

    code = draft.evidence.get("language_code")
    if isinstance(code, str) and isinstance(draft.confidence, (int, float)):
        return [LanguageScore(code, float(draft.confidence))]
    return []


def _language_scores_by_code(scores: Sequence[LanguageScore]) -> dict[str, float]:
    totals: dict[str, float] = defaultdict(float)
    for score in scores:
        code = normalize_language_label(score.language_code)
        if code is None:
            continue
        totals[code] += max(0.0, float(score.confidence))
    return dict(totals)


def _has_close_language_ambiguity(top_group: str, language_scores: Mapping[str, float]) -> bool:
    relevant = [
        (code, score)
        for code, score in language_scores.items()
        if _LANGUAGE_TO_GROUP.get(code, LanguageGroup.UNASSIGNED).value == top_group
    ]
    if len(relevant) < 2:
        return False
    ordered = sorted(relevant, key=lambda item: item[1], reverse=True)
    return ordered[0][1] - ordered[1][1] < 0.20


def _has_germanic_bantu_boundary_warning(ordered_groups: Sequence[tuple[str, float]]) -> bool:
    if len(ordered_groups) < 2:
        return False
    top_group, top_score = ordered_groups[0]
    next_group, next_score = ordered_groups[1]
    crosses_boundary = (
        top_group == LanguageGroup.GERMANIC.value
        and next_group in _BANTU_GROUPS
        or next_group == LanguageGroup.GERMANIC.value
        and top_group in _BANTU_GROUPS
    )
    return crosses_boundary and abs(top_score - next_score) < 0.15


def annotate_suggestions_with_candidate_scores(
    suggestions: Sequence[LidSuggestionDraft],
    language_codes_by_id: Mapping[str, str],
) -> list[LidSuggestionDraft]:
    """Attach peer candidate scores per token/segment target for gate evidence."""

    grouped: dict[tuple[str, str], list[LidSuggestionDraft]] = defaultdict(list)
    for suggestion in suggestions:
        target = _suggestion_target_key(suggestion)
        if target is not None:
            grouped[target].append(suggestion)

    annotated: list[LidSuggestionDraft] = []
    for suggestion in suggestions:
        target = _suggestion_target_key(suggestion)
        peers = grouped.get(target, []) if target is not None else [suggestion]
        candidate_scores = _candidate_score_dicts(peers, language_codes_by_id)
        language_code = language_codes_by_id.get(suggestion.language_id or "")
        if language_code:
            suggestion.evidence = {
                **suggestion.evidence,
                "language_code": language_code,
                "candidate_scores": candidate_scores,
            }
        annotated.append(suggestion)
    return annotated


def _suggestion_target_key(suggestion: LidSuggestionDraft) -> tuple[str, str] | None:
    if suggestion.token_id:
        return ("token", suggestion.token_id)
    if suggestion.segment_id:
        return ("segment", suggestion.segment_id)
    return None


def _candidate_score_dicts(
    suggestions: Sequence[LidSuggestionDraft],
    language_codes_by_id: Mapping[str, str],
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for suggestion in sorted(suggestions, key=lambda item: item.rank):
        language_code = language_codes_by_id.get(suggestion.language_id or "")
        if not language_code:
            continue
        candidates.append(
            {
                "language_code": language_code,
                "confidence": float(suggestion.confidence or 0.0),
                "rank": suggestion.rank,
            }
        )
    return candidates
