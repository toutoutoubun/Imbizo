"""Import dialog."""

from __future__ import annotations

from typing import Any


class ImportDialog:
    """Collect import options without parsing files."""

    def build(self) -> Any:
        """Build and return a PySide6 dialog."""

        from PySide6.QtWidgets import QFileDialog

        return QFileDialog()
