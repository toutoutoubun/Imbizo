"""Project-local morphology dictionaries and manual morpheme splits."""

from __future__ import annotations

from imbizo.domain.morphology import Morpheme, MorphemeDictionaryEntry, MorphemeSplit, parse_split_text
from imbizo.morphology.suggestions import MorphologySuggester
from imbizo.services.morphology_service import MorphologyService

__all__ = [
    "Morpheme",
    "MorphemeDictionaryEntry",
    "MorphemeService",
    "MorphemeSplit",
    "MorphologyService",
    "MorphologySuggester",
    "parse_split_text",
]

MorphemeService = MorphologyService
