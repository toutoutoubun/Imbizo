"""Project settings widget."""

from __future__ import annotations

from typing import Any


class ProjectSettingsWidget:
    """Project metadata, languages, ethics notes, and settings."""

    def build(self) -> Any:
        """Build and return a PySide6 widget."""

        from PySide6.QtWidgets import QFormLayout, QLineEdit, QWidget

        root = QWidget()
        layout = QFormLayout(root)
        layout.addRow("Project title", QLineEdit())
        layout.addRow("Researcher", QLineEdit())
        layout.addRow("Location", QLineEdit())
        return root
