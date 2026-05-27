"""Timeline view widget."""

from __future__ import annotations

from typing import Any


class TimelineViewWidget:
    """ELAN-familiar timeline view."""

    def build(self) -> Any:
        """Build and return a PySide6 widget."""

        from PySide6.QtWidgets import QLabel

        return QLabel("Timeline")
