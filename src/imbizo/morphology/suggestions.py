"""Dictionary-based morphology suggestions."""

from __future__ import annotations

import uuid
from typing import Sequence

from imbizo.domain.morphology import Morpheme, MorphemeDictionaryEntry, MorphemeSplit
from imbizo.domain.transcripts import Token


class MorphologySuggester:
    """Dictionary-based local morpheme suggestion engine."""

    def suggest(self, token: Token, entries: Sequence[MorphemeDictionaryEntry]) -> list[MorphemeSplit]:
        """Return editable split suggestions for a token."""

        active = [entry for entry in entries if entry.is_active and token.token_text.lower().startswith(entry.surface.lower())]
        suggestions: list[MorphemeSplit] = []
        for entry in active[:5]:
            split_id = str(uuid.uuid4())
            split_text = f"{entry.surface}+{token.token_text[len(entry.surface):]}" if len(entry.surface) < len(token.token_text) else entry.surface
            suggestions.append(
                MorphemeSplit(
                    id=split_id,
                    token_id=token.id,
                    source="suggestion",
                    status="active",
                    split_text=split_text,
                    morphemes=[
                        Morpheme(
                            id=str(uuid.uuid4()),
                            split_id=split_id,
                            sort_order=1,
                            surface=entry.surface,
                            gloss=entry.gloss,
                            category=entry.category,
                            language_id=entry.language_id,
                            dictionary_entry_id=entry.id,
                        )
                    ],
                )
            )
        return suggestions
