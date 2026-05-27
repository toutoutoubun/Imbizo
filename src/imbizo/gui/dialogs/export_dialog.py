"""Export dialog."""

from __future__ import annotations

from typing import Any


class ExportDialog:
    """Collect export format and destination options."""

    def build(self) -> Any:
        """Build and return a PySide6 dialog."""

        from PySide6.QtWidgets import QFileDialog

        return QFileDialog()
