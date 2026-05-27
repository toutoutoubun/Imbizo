"""Language legend model data adapter."""

from __future__ import annotations

from dataclasses import dataclass, field

from imbizo.domain.languages import LanguageTag, sort_languages_for_legend


@dataclass(slots=True)
class LanguageLegendModel:
    """Data holder for language labels and colors."""

    languages: list[LanguageTag] = field(default_factory=list)

    def set_languages(self, languages: list[LanguageTag]) -> None:
        """Replace languages in legend display order."""

        self.languages = sort_languages_for_legend(languages)
