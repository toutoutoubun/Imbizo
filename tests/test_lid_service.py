"""Tests for local LID service behaviour."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

from imbizo.domain.annotations import AnnotationDraft
from imbizo.domain.project import ProjectMetadata
from imbizo.lid.baseline import BaselineLidProvider
from imbizo.lid.providers import LidOptions, LidProgress
from imbizo.services.annotation_service import AnnotationService
from imbizo.services.import_service import ImportService
from imbizo.services.lid_service import LidService
from imbizo.services.project_service import ProjectService


def _context_with_document(tmp_path: Path, text: str):
    source = tmp_path / "sample.txt"
    source.write_text(text, encoding="utf-8")
    context = ProjectService().create_project(tmp_path / "project", ProjectMetadata(project_uuid="", title="LID Test"))
    imported = ImportService().import_file(context, source)
    assert imported.bundle.document is not None
    return context, imported.bundle.document


def test_local_lid_applies_useful_labels_without_auto_unknown(tmp_path: Path) -> None:
    """Useful local labels are applied, while low-evidence Unknown stays advisory."""

    context, document = _context_with_document(tmp_path, "I went to the market 123\nngiyabonga friend\n")
    updates: list[LidProgress] = []

    report = LidService().run_lid_for_document_report(
        context,
        document.id,
        LidOptions(progress_callback=updates.append),
    )

    assert report.suggestions_count > 0
    assert report.auto_annotations_count >= 2
    assert report.skipped_unknown_count >= 1
    assert updates
    assert updates[-1].message == "Local LID complete"

    rows = context.connection.execute(
        """
        SELECT languages.code FROM annotations
        JOIN languages ON languages.id = annotations.language_id
        WHERE annotations.source = 'auto'
        """
    ).fetchall()
    auto_codes = {row["code"] for row in rows}
    assert "eng" in auto_codes
    assert "zul" in auto_codes
    assert "und" not in auto_codes


def test_local_lid_preserves_manual_labels(tmp_path: Path) -> None:
    """Manual annotations remain the effective annotation after Local LID."""

    context, document = _context_with_document(tmp_path, "I and the\n")
    annotation_service = AnnotationService()
    state = annotation_service.load_editor_state(context, document.id)
    first_token = state.rows[0].token
    xhosa = next(language for language in state.languages if language.code == "xho")
    manual = annotation_service.save_token_annotation(context, first_token.id, AnnotationDraft(language_id=xhosa.id, memo="manual check"))

    report = LidService().run_lid_for_document_report(context, document.id)

    assert report.preserved_manual_count >= 1
    auto_rows = context.connection.execute(
        "SELECT * FROM annotations WHERE token_id = ? AND source = 'auto'",
        (first_token.id,),
    ).fetchall()
    assert auto_rows == []
    state_after = annotation_service.load_editor_state(context, document.id)
    first_after = next(row for row in state_after.rows if row.token.id == first_token.id)
    assert first_after.annotation is not None
    assert first_after.annotation.id == manual.id


def test_local_lid_discovers_project_fasttext_model_and_maps_codes(tmp_path: Path, monkeypatch) -> None:
    """A local lid.176 model in project/models/lid is used without env vars."""

    class FakeFastTextModel:
        def predict(self, text: str, k: int) -> tuple[list[str], list[float]]:
            return ["__label__zu", "__label__en"][:k], [0.91, 0.05][:k]

    monkeypatch.setitem(sys.modules, "fasttext", SimpleNamespace(load_model=lambda path: FakeFastTextModel()))
    context, document = _context_with_document(tmp_path, "sawubona friend\n")
    model_dir = context.paths.root / "models" / "lid"
    model_dir.mkdir(parents=True)
    (model_dir / "lid.176.ftz").write_bytes(b"fake model")

    report = LidService().run_lid_for_document_report(context, document.id)

    assert report.provider_method == "fastText lid.176"
    rows = context.connection.execute(
        """
        SELECT languages.code FROM annotations
        JOIN languages ON languages.id = annotations.language_id
        WHERE annotations.source = 'auto'
        """
    ).fetchall()
    assert {row["code"] for row in rows} == {"zul"}


def test_baseline_lid_without_env_uses_heuristic_not_cwd(monkeypatch) -> None:
    """Unset model config must not treat the current directory as a model."""

    monkeypatch.delenv("IMBIZO_FASTTEXT_LID_MODEL", raising=False)
    provider = BaselineLidProvider()
    prediction = provider.predict(["hello"], LidOptions(max_languages=1))[0][0]

    assert prediction.language_code == "eng"
    assert prediction.evidence["method"] == "heuristic"
