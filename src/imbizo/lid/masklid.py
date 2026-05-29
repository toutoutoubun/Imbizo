"""MaskLID-style local code-switch detector."""

from __future__ import annotations

from collections import Counter
from typing import Sequence

from imbizo.domain.languages import LanguageTag, find_language_by_code
from imbizo.domain.transcripts import Token, TranscriptSegment
from imbizo.lid.providers import LanguageIdentifier, LanguageScore, LidLayer, LidOptions, LidSuggestionDraft


class MaskLidDetector:
    """Iterative local detector for multilingual segments.

    This is a lightweight MaskLID-style workflow inspired by Kargaran et al.
    (2024): token-level language evidence is aggregated into multilingual
    segment suggestions without training a new model.
    """

    def __init__(self, provider: LanguageIdentifier, languages: Sequence[LanguageTag]) -> None:
        self.provider = provider
        self.languages = list(languages)

    def detect(self, segment: TranscriptSegment, tokens: Sequence[Token], options: LidOptions) -> list[LidSuggestionDraft]:
        """Return code-switch suggestions for a segment and its tokens."""

        token_scores = self.provider.predict([token.token_text for token in tokens], options)
        token_scores = self._apply_segment_context(token_scores, tokens, options)
        winning_codes = [scores[0].language_code for scores in token_scores if scores]
        counts = Counter(winning_codes)
        segment_suggestions: list[LidSuggestionDraft] = []
        for rank, (code, count) in enumerate(counts.most_common(options.max_languages), start=1):
            language = find_language_by_code(self.languages, code)
            if language:
                segment_suggestions.append(
                    LidSuggestionDraft(
                        token_id=None,
                        segment_id=segment.id,
                        language_id=language.id,
                        layer=LidLayer.LAYER3_MASKLID,
                        rank=rank,
                        confidence=count / max(1, len(tokens)),
                        evidence={"token_votes": count, "total_tokens": len(tokens)},
                    )
                )
        token_suggestions: list[LidSuggestionDraft] = []
        for token, scores in zip(tokens, token_scores, strict=False):
            for rank, score in enumerate(scores[: options.max_languages], start=1):
                language = find_language_by_code(self.languages, score.language_code)
                if language and score.confidence >= options.min_confidence:
                    token_suggestions.append(
                        LidSuggestionDraft(
                            token_id=token.id,
                            segment_id=None,
                            language_id=language.id,
                            layer=LidLayer.LAYER1_BASELINE,
                            rank=rank,
                            confidence=score.confidence,
                            evidence=score.evidence,
                        )
                    )
        return segment_suggestions + token_suggestions

    def _apply_segment_context(
        self,
        token_scores: list[list[LanguageScore]],
        tokens: Sequence[Token],
        options: LidOptions,
    ) -> list[list[LanguageScore]]:
        """Use strong local token evidence to rescue low-evidence context tokens.

        This remains advisory. It only fills `und` tokens when a segment has a
        clear local majority from already-detected tokens. The fallback is most
        useful for spreadsheet rows that contain a full utterance but no
        language column: common words vote first, then short function words or
        otherwise unrecognised alphabetic tokens inherit a low-confidence
        segment-context suggestion.
        """

        if len(tokens) < 3:
            return token_scores
        known_top_scores = [
            scores[0]
            for scores in token_scores
            if scores
            and scores[0].language_code != "und"
            and scores[0].confidence >= options.min_confidence
        ]
        if len(known_top_scores) < 2:
            return token_scores
        counts = Counter(score.language_code for score in known_top_scores)
        dominant_code, dominant_count = counts.most_common(1)[0]
        dominance = dominant_count / max(1, len(known_top_scores))
        if dominance < 0.67:
            return token_scores

        context_confidence = min(0.35, 0.24 + (dominance * 0.12))
        smoothed_scores: list[list[LanguageScore]] = []
        for token, scores in zip(tokens, token_scores, strict=False):
            if scores and scores[0].language_code != "und":
                smoothed_scores.append(scores)
                continue
            if not _context_fill_eligible(token.token_text):
                smoothed_scores.append(scores)
                continue
            smoothed_scores.append(
                [
                    LanguageScore(
                        dominant_code,
                        context_confidence,
                        {
                            "method": "segment_context",
                            "dominant_language": dominant_code,
                            "dominant_token_votes": dominant_count,
                            "known_token_votes": len(known_top_scores),
                            "note": "Low-confidence fill from local segment context; researcher review required.",
                        },
                    ),
                    *scores[: max(0, options.max_languages - 1)],
                ]
            )
        return smoothed_scores


def _context_fill_eligible(text: str) -> bool:
    """Return whether an unknown token is safe enough for segment-context fill."""

    token = text.strip()
    if not token:
        return False
    if any(character.isdigit() for character in token):
        return False
    letters = [character for character in token if character.isalpha()]
    if not letters:
        return False
    return len(letters) <= 3 or token.isascii()
