"""Memo pane widget factory."""

from __future__ import annotations

from typing import Any


class MemoPane:
    """Free-text memo editor for selected token or segment."""

    def build(self) -> Any:
        """Build and return a PySide6 widget."""

        from PySide6.QtWidgets import QTextEdit

        editor = QTextEdit()
        editor.setPlaceholderText("Memo")
        return editor
