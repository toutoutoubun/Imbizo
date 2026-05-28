"""Regression tests for the welcome-screen import choices."""

from __future__ import annotations

from typing import Any

import pytest


def test_welcome_distinguishes_project_folder_from_data_file() -> None:
    """The welcome screen must not make researchers use Open Project for XML/CSV."""

    qt_widgets: Any = pytest.importorskip("PySide6.QtWidgets")

    from imbizo.gui.main_window import MainWindow

    app = qt_widgets.QApplication.instance() or qt_widgets.QApplication([])
    window = MainWindow().build()
    buttons = {button.text() for button in window.findChildren(qt_widgets.QPushButton)}

    assert "Open Project Folder" in buttons
    assert "Import Data File" in buttons
    assert "Import Project ZIP" in buttons
    assert "Open Project" not in buttons
    app.quit()
