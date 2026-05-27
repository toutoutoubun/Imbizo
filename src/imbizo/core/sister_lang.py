"""Sister-language disambiguation for closely related Bantu languages.

This module performs conservative string and context scoring for cases where
local LID produces ties such as isiZulu/isiXhosa or Sesotho/Setswana. The
method is intentionally advisory: South African language labels can be socially
and politically meaningful, so the researcher must accept, reject, or leave a
token ambiguous (Mesthrie, 2002; Mesthrie, 2008).
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
import sqlite3
from pathlib import Path

import yaml

from .annotation import Token


@dataclass(slots=True)
class EvidenceItem:
    """One matched cue used in a sister-language verdict."""

    code: str
    language: str
    weight: float
    description: str
    verified: bool
    note: str | None = None


@dataclass(slots=True)
class RankedLanguage:
    """A candidate language and its advisory score."""

    language: str
    score: float
    evidence_codes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class SisterLangVerdict:
    """Advisory result for one ambiguous token."""

    token_id: str
    best_language: str | None
    confidence: float
    ranked: list[RankedLanguage]
    evidence: list[EvidenceItem]
    ambiguous: bool
    narrative: str


@dataclass(slots=True)
class SisterLangDictionary:
    """Typed representation of a per-pair sister-language YAML dictionary."""

    language_code: str
    language_name: str
    version: str
    source: str
    distinctive_morphemes: list[dict[str, object]]
    distinctive_lexemes: list[dict[str, object]]
    orthographic_features: list[dict[str, object]]
    phonotactic_features: list[dict[str, object]]
    confidence_thresholds: dict[str, object]

    @property
    def languages(self) -> list[str]:
        """Return language codes represented by this dictionary."""

        return [part for part in self.language_code.split("-") if part]


def load_sister_lang_dictionary(path: Path) -> SisterLangDictionary:
    """Load a sister-language YAML dictionary from a local file."""

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    required = ["language_code", "language_name", "version", "source"]
    missing = [key for key in required if not data.get(key)]
    if missing:
        raise ValueError(f"{path} is missing required fields: {', '.join(missing)}")
    return SisterLangDictionary(
        language_code=str(data["language_code"]),
        language_name=str(data["language_name"]),
        version=str(data["version"]),
        source=str(data["source"]),
        distinctive_morphemes=list(data.get("distinctive_morphemes", [])),
        distinctive_lexemes=list(data.get("distinctive_lexemes", [])),
        orthographic_features=list(data.get("orthographic_features", [])),
        phonotactic_features=list(data.get("phonotactic_features", [])),
        confidence_thresholds=dict(data.get("confidence_thresholds", {})),
    )


def disambiguate_sister_languages(
    token: Token,
    utterance_context: list[Token],
    candidate_languages: list[str],
    dictionaries: dict[str, SisterLangDictionary],
) -> SisterLangVerdict:
    """Score sister-language evidence and return a ranked advisory verdict.

    For tokens whose LID returned a tie among sister Bantu languages, this
    function scores evidence from distinctive morphemes, lexemes, orthographic
    features, and immediate utterance context. The approach is justified by
    South African sociolinguistic caution (Mesthrie, 2002, 2008) and by the
    reference grammars cited inside each local dictionary. It is advisory only;
    the researcher accepts or overrides.
    """

    candidates = list(dict.fromkeys(candidate_languages))
    scores = {language: 0.0 for language in candidates}
    evidence: list[EvidenceItem] = []
    text = _clean(token.text_for_matching)

    for dictionary in dictionaries.values():
        if not set(dictionary.languages).intersection(candidates):
            continue
        _score_morphemes(text, dictionary, scores, evidence)
        _score_lexemes(text, dictionary, scores, evidence)
        _score_orthography(text, dictionary, scores, evidence)
        _score_phonotactics(dictionary, scores, evidence)

    _score_context(token, utterance_context, candidates, scores, evidence)

    ranked = [
        RankedLanguage(language=language, score=round(min(score, 1.0), 4), evidence_codes=_codes_for(evidence, language))
        for language, score in sorted(scores.items(), key=lambda item: item[1], reverse=True)
    ]
    if not ranked or ranked[0].score <= 0:
        return SisterLangVerdict(
            token_id=token.id,
            best_language=None,
            confidence=0.0,
            ranked=ranked,
            evidence=evidence,
            ambiguous=True,
            narrative="No distinctive sister-language evidence was found; leave the token ambiguous unless the researcher knows otherwise.",
        )

    best = ranked[0]
    second_score = ranked[1].score if len(ranked) > 1 else 0.0
    threshold = _threshold_for(dictionaries, candidates)
    confidence = round(min(best.score, 1.0), 4)
    ambiguous = confidence < threshold or (confidence - second_score) < 0.15
    best_language = None if ambiguous else best.language
    if ambiguous:
        narrative = (
            f"Evidence for {best.language} is not strong enough to override ambiguity; "
            "manual review is recommended."
        )
    else:
        narrative = (
            f"Evidence tentatively favors {best.language}, but this remains an advisory "
            "suggestion for researcher review."
        )
    return SisterLangVerdict(
        token_id=token.id,
        best_language=best_language,
        confidence=confidence,
        ranked=ranked,
        evidence=evidence,
        ambiguous=ambiguous,
        narrative=narrative,
    )


def persist_sister_lang_verdict(
    conn: sqlite3.Connection,
    token_id: str,
    verdict: SisterLangVerdict,
    source: str = "suggested-accepted",
) -> None:
    """Persist an accepted or overridden sister-language verdict to SQLite."""

    if source not in {"manual", "suggested-accepted", "suggested-overridden", "imported"}:
        raise ValueError("source must be manual, suggested-accepted, suggested-overridden, or imported")
    evidence_codes = ",".join(item.code for item in verdict.evidence)
    language = verdict.best_language
    conn.execute(
        """
        UPDATE tokens
        SET language = COALESCE(?, language),
            language_source = ?,
            sister_lang_confidence = ?,
            sister_lang_evidence = ?
        WHERE id = ?
        """,
        (language, source, verdict.confidence, evidence_codes, token_id),
    )


def _score_morphemes(
    text: str,
    dictionary: SisterLangDictionary,
    scores: dict[str, float],
    evidence: list[EvidenceItem],
) -> None:
    for entry in dictionary.distinctive_morphemes:
        language = str(entry.get("language", ""))
        form = _clean(str(entry.get("form", "")))
        if language in scores and form and text.startswith(form):
            weight = min(0.35, 0.12 + len(form) / 30)
            scores[language] += weight
            evidence.append(
                EvidenceItem(
                    code=f"morph_{form}_{language}",
                    language=language,
                    weight=weight,
                    description=str(entry.get("gloss", "distinctive morpheme")),
                    verified=bool(entry.get("verified", False)),
                    note=str(entry.get("note")) if entry.get("note") else None,
                )
            )


def _score_lexemes(
    text: str,
    dictionary: SisterLangDictionary,
    scores: dict[str, float],
    evidence: list[EvidenceItem],
) -> None:
    for entry in dictionary.distinctive_lexemes:
        language = str(entry.get("language", ""))
        form = _clean(str(entry.get("form", "")))
        if language in scores and form and text == form:
            weight = 0.45 if entry.get("verified") else 0.3
            scores[language] += weight
            evidence.append(
                EvidenceItem(
                    code=f"lex_{form}_{language}",
                    language=language,
                    weight=weight,
                    description=str(entry.get("gloss", "distinctive lexeme")),
                    verified=bool(entry.get("verified", False)),
                    note=str(entry.get("note")) if entry.get("note") else None,
                )
            )


def _score_orthography(
    text: str,
    dictionary: SisterLangDictionary,
    scores: dict[str, float],
    evidence: list[EvidenceItem],
) -> None:
    for entry in dictionary.orthographic_features:
        code = str(entry.get("code", ""))
        languages = [str(item) for item in entry.get("languages", [])]
        matched: list[str] = []
        if code == "xho_nd_initial" and text.startswith(("ndi", "andi")):
            matched = ["xho"]
        elif code == "sot_sh_vs_tsn_tsh":
            if "tsh" in text:
                matched = ["tsn"]
            elif "sh" in text:
                matched = ["sot"]
        elif code == "nso_s_sot_ts_tsn_tsh":
            if "tsh" in text:
                matched = ["tsn"]
            elif "ts" in text:
                matched = ["sot"]
            elif "s" in text:
                matched = ["nso"]
        elif code == "click_letters_c_q_x" and re.search(r"[cqx]", text):
            matched = [language for language in languages if language in scores]
        if not matched:
            continue
        shared = len([language for language in matched if language in scores]) > 1
        weight = 0.08 if shared else 0.2
        for language in matched:
            if language in scores:
                scores[language] += weight
                evidence.append(
                    EvidenceItem(
                        code=f"orth_{code}_{language}",
                        language=language,
                        weight=weight,
                        description=str(entry.get("description", "orthographic feature")),
                        verified=bool(entry.get("verified", False)),
                        note=str(entry.get("note")) if entry.get("note") else None,
                    )
                )


def _score_phonotactics(
    dictionary: SisterLangDictionary,
    scores: dict[str, float],
    evidence: list[EvidenceItem],
) -> None:
    for entry in dictionary.phonotactic_features:
        code = str(entry.get("code", ""))
        if "shared" in code or "caution" in code:
            for language in [str(item) for item in entry.get("languages", []) if str(item) in scores]:
                evidence.append(
                    EvidenceItem(
                        code=f"phonotactic_caution_{language}",
                        language=language,
                        weight=0.0,
                        description=str(entry.get("description", "shared phonotactic caution")),
                        verified=bool(entry.get("verified", False)),
                        note=str(entry.get("note")) if entry.get("note") else None,
                    )
                )


def _score_context(
    token: Token,
    utterance_context: list[Token],
    candidate_languages: list[str],
    scores: dict[str, float],
    evidence: list[EvidenceItem],
) -> None:
    for context_token in utterance_context:
        if context_token.id == token.id or context_token.language not in candidate_languages:
            continue
        distance = abs(context_token.position - token.position) or 1
        weight = max(0.01, 0.08 / distance)
        scores[str(context_token.language)] += weight
        evidence.append(
            EvidenceItem(
                code=f"context_{context_token.id}_{context_token.language}",
                language=str(context_token.language),
                weight=weight,
                description="neighboring manually labelled token",
                verified=False,
                note="Context evidence is weak and should not override form evidence.",
            )
        )


def _threshold_for(dictionaries: dict[str, SisterLangDictionary], candidates: list[str]) -> float:
    thresholds: list[float] = []
    for dictionary in dictionaries.values():
        if set(dictionary.languages).intersection(candidates):
            raw = dictionary.confidence_thresholds.get("ambiguous_below")
            if isinstance(raw, int | float):
                thresholds.append(float(raw))
    return max(thresholds) if thresholds else 0.65


def _codes_for(evidence: list[EvidenceItem], language: str) -> list[str]:
    return [item.code for item in evidence if item.language == language]


def _clean(value: str) -> str:
    return re.sub(r"(^[^\w-]+|[^\w-]+$)", "", value.casefold())
