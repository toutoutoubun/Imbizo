"""Project creation and open dialogs."""

from __future__ import annotations

from typing import Any


class CreateProjectDialog:
    """Collect local project creation details."""

    def build(self) -> Any:
        """Build and return a PySide6 dialog."""

        from PySide6.QtWidgets import QFileDialog

        return QFileDialog()


class OpenProjectDialog:
    """Collect an existing local project folder."""

    def build(self) -> Any:
        """Build and return a PySide6 dialog."""

        from PySide6.QtWidgets import QFileDialog

        return QFileDialog()
