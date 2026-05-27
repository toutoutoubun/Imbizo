"""Unit tests for the public core.annotation compatibility module."""

from __future__ import annotations

from pathlib import Path

from imbizo.core.annotation import AnnotationDraft, AnnotationRepository, AnnotationService, AnnotationStatus
from imbizo.domain.project import ProjectMetadata
from imbizo.services.import_service import ImportService
from imbizo.services.project_service import ProjectService


def test_manual_annotation_overrides_prior_manual_annotation(tmp_path: Path) -> None:
    """A later manual annotation becomes effective while history remains in SQLite."""

    source = tmp_path / "interview.txt"
    source.write_text("hello sawubona\n", encoding="utf-8")
    context = ProjectService().create_project(tmp_path / "project", ProjectMetadata(project_uuid="", title="Annotation Test"))
    imported = ImportService().import_file(context, source)
    assert imported.bundle.document is not None

    service = AnnotationService()
    state = service.load_editor_state(context, imported.bundle.document.id)
    token_id = state.rows[0].token.id
    english = next(language for language in state.languages if language.code == "eng")
    zulu = next(language for language in state.languages if language.code == "zul")

    first = service.save_token_annotation(context, token_id, AnnotationDraft(language_id=english.id))
    second = service.save_token_annotation(context, token_id, AnnotationDraft(language_id=zulu.id, memo="researcher override"))

    repository = AnnotationRepository(context.connection)
    effective = repository.get_effective_annotation_for_token(token_id)
    all_annotations = repository.list_annotations()

    assert effective is not None
    assert effective.id == second.id
    assert effective.language_id == zulu.id
    assert any(annotation.id == first.id and annotation.status == AnnotationStatus.SUPERSEDED for annotation in all_annotations)
