"""Spreadsheet-style annotation view."""

from __future__ import annotations

from typing import Any


class SpreadsheetViewWidget:
    """Excel-like annotation grid view."""

    def build(self) -> Any:
        """Build and return a PySide6 widget."""

        from PySide6.QtWidgets import QTableWidget

        table = QTableWidget(0, 8)
        table.setHorizontalHeaderLabels(["Document", "Speaker", "Time", "Token", "Language", "Switch", "Trigger", "Memo"])
        return table
