"""Metrics dashboard widget."""

from __future__ import annotations

from typing import Any


class MetricsDashboardWidget:
    """Metric request and result display."""

    def build(self) -> Any:
        """Build and return a PySide6 widget."""

        from PySide6.QtWidgets import QTableWidget

        table = QTableWidget(0, 4)
        table.setHorizontalHeaderLabels(["Metric", "Scope", "Value", "Inputs"])
        return table
