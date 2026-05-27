"""Project-local morphology dictionaries and corpus loaders."""

from __future__ import annotations

from imbizo.domain.morphology import Morpheme, MorphemeDictionaryEntry, MorphemeSplit, parse_split_text
from imbizo.morphology.suggestions import MorphologySuggester
from imbizo.services.morphology_service import MorphologyService

from .annotated_corpus_loader import MorphAnnotatedCorpus, load_morph_corpus

__all__ = [
    "Morpheme",
    "MorphemeDictionaryEntry",
    "MorphemeService",
    "MorphemeSplit",
    "MorphAnnotatedCorpus",
    "MorphologyService",
    "MorphologySuggester",
    "load_morph_corpus",
    "parse_split_text",
]

MorphemeService = MorphologyService
