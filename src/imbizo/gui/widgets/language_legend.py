"""Language legend widget factory."""

from __future__ import annotations

from typing import Any, Sequence

from imbizo.domain.languages import LanguageTag


class LanguageLegendWidget:
    """Always-visible language color legend."""

    def __init__(self, languages: Sequence[LanguageTag]) -> None:
        self.languages = list(languages)

    def build(self) -> Any:
        """Build and return a PySide6 widget."""

        from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

        root = QWidget()
        layout = QHBoxLayout(root)
        for language in self.languages:
            label = QLabel(f"{language.name} ({language.code})")
            label.setStyleSheet(f"border-left: 16px solid {language.color_hex}; padding-left: 4px;")
            layout.addWidget(label)
        return root
