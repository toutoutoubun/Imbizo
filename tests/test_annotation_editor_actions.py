"""Regression tests for annotation editor action buttons."""

from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from imbizo.domain.project import ProjectMetadata
from imbizo.services.annotation_service import AnnotationService
from imbizo.services.import_service import ImportService
from imbizo.services.lid_service import LidService
from imbizo.services.project_service import ProjectService


def _qt_app() -> Any:
    """Return a QApplication configured for headless tests."""

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    qt_widgets: Any = pytest.importorskip("PySide6.QtWidgets")
    return qt_widgets.QApplication.instance() or qt_widgets.QApplication([])


def _context(tmp_path: Path) -> Any:
    """Create a small project context for GUI action tests."""

    return ProjectService().create_project(
        tmp_path / "project",
        ProjectMetadata(project_uuid="", title="Annotation Actions Test"),
    )


def test_import_file_button_imports_selected_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Clicking Import File must call the import path and refresh visible rows."""

    app = _qt_app()
    qt_widgets: Any = pytest.importorskip("PySide6.QtWidgets")
    from imbizo.gui.widgets.annotation_editor import AnnotationEditorWidget

    source = tmp_path / "interview.txt"
    source.write_text("hello friend\n", encoding="utf-8")
    context = _context(tmp_path)
    editor = AnnotationEditorWidget(context, AnnotationService(), LidService())
    editor.build()

    monkeypatch.setattr(qt_widgets.QFileDialog, "getOpenFileName", lambda *args, **kwargs: (str(source), ""))
    monkeypatch.setattr(qt_widgets.QMessageBox, "information", lambda *args, **kwargs: None)
    monkeypatch.setattr(qt_widgets.QMessageBox, "critical", lambda *args, **kwargs: None)

    assert editor.import_file_button is not None
    editor.import_file_button.click()
    app.processEvents()

    assert editor.table is not None
    assert editor.table.rowCount() == 2
    assert editor.status_label is not None
    assert "Imported" in editor.status_label.text()


def test_run_lid_button_invokes_local_lid_runner(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Clicking Run Local LID must invoke the local LID progress runner."""

    app = _qt_app()
    qt_widgets: Any = pytest.importorskip("PySide6.QtWidgets")
    import imbizo.gui.widgets.annotation_editor as annotation_editor
    from imbizo.gui.widgets.annotation_editor import AnnotationEditorWidget

    source = tmp_path / "interview.txt"
    source.write_text("hello friend\n", encoding="utf-8")
    context = _context(tmp_path)
    imported = ImportService().import_file(context, source)
    assert imported.bundle.document is not None
    editor = AnnotationEditorWidget(context, AnnotationService(), LidService())
    editor.build()

    calls: list[str] = []

    def fake_run_lid_with_progress(parent: Any, context_arg: Any, document_id: str, lid_service: Any, **kwargs: Any) -> Any:
        calls.append(document_id)
        calls.append(str(kwargs["options"].use_coarse_group_gate))
        return SimpleNamespace(
            suggestions_count=2,
            auto_annotations_count=2,
            skipped_unknown_count=0,
            preserved_manual_count=0,
            provider_method="test provider",
            provider_message=None,
            coarse_group_gate_enabled=kwargs["options"].use_coarse_group_gate,
            coarse_group_gated_count=0,
            coarse_group_ambiguous_count=0,
            coarse_group_low_confidence_count=0,
        )

    monkeypatch.setattr(annotation_editor, "run_lid_with_progress", fake_run_lid_with_progress)
    monkeypatch.setattr(qt_widgets.QMessageBox, "information", lambda *args, **kwargs: None)
    monkeypatch.setattr(qt_widgets.QMessageBox, "critical", lambda *args, **kwargs: None)

    assert editor.run_lid_button is not None
    assert editor.coarse_group_gate_checkbox is not None
    editor.coarse_group_gate_checkbox.setChecked(True)
    editor.run_lid_button.click()
    app.processEvents()

    assert calls == [imported.bundle.document.id, "True"]
    assert editor.status_label is not None
    assert editor.status_label.text().startswith("Local LID complete:")
