"""MaskLID-style local code-switch detector."""

from __future__ import annotations

from collections import Counter
from typing import Sequence

from imbizo.domain.languages import LanguageTag, find_language_by_code
from imbizo.domain.transcripts import Token, TranscriptSegment
from imbizo.lid.providers import LanguageIdentifier, LidLayer, LidOptions, LidSuggestionDraft


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
