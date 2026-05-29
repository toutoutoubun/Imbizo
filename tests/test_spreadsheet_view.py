"""Regression tests for the spreadsheet annotation tab."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest

from imbizo.domain.project import ProjectMetadata
from imbizo.services.import_service import ImportService
from imbizo.services.project_service import ProjectService


def test_spreadsheet_view_loads_imported_tokens(tmp_path: Path) -> None:
    """The Spreadsheet tab must show project rows instead of an empty shell."""

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    qt_widgets: Any = pytest.importorskip("PySide6.QtWidgets")

    from imbizo.gui.widgets.spreadsheet_view import SpreadsheetViewWidget

    app = qt_widgets.QApplication.instance() or qt_widgets.QApplication([])
    source = tmp_path / "interview.txt"
    source.write_text("I went home\nngiyabonga friend\n", encoding="utf-8")
    context = ProjectService().create_project(tmp_path / "project", ProjectMetadata(project_uuid="", title="Sheet Test"))
    imported = ImportService().import_file(context, source)
    assert imported.bundle.document is not None

    view = SpreadsheetViewWidget(context)
    widget = view.build()

    assert widget is not None
    assert view.table is not None
    assert view.table.rowCount() == 5
    assert view.table.item(0, 3).text() == "I"
    assert view.status_label is not None
    assert view.status_label.text() == "5 token rows"
    app.quit()


def test_spreadsheet_view_persists_memo_edits(tmp_path: Path) -> None:
    """Editing the Memo cell creates a manual annotation for that token."""

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    qt_widgets: Any = pytest.importorskip("PySide6.QtWidgets")

    from imbizo.gui.widgets.spreadsheet_view import SpreadsheetViewWidget

    app = qt_widgets.QApplication.instance() or qt_widgets.QApplication([])
    source = tmp_path / "interview.txt"
    source.write_text("hello\n", encoding="utf-8")
    context = ProjectService().create_project(tmp_path / "project", ProjectMetadata(project_uuid="", title="Sheet Edit Test"))
    ImportService().import_file(context, source)

    view = SpreadsheetViewWidget(context)
    view.build()
    assert view.table is not None
    view.table.item(0, 9).setText("checked in spreadsheet")
    view._cell_changed(0, 9)

    row = context.connection.execute("SELECT memo, source FROM annotations").fetchone()
    assert row is not None
    assert row["memo"] == "checked in spreadsheet"
    assert row["source"] == "manual"
    app.quit()
