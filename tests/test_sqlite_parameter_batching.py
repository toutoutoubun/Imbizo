"""Regression tests for SQLite parameter batching on large projects."""

from __future__ import annotations

from pathlib import Path

from imbizo.domain.project import ProjectMetadata
from imbizo.persistence.repositories import AnnotationRepository, TranscriptRepository
from imbizo.services.import_service import ImportService
from imbizo.services.project_service import ProjectService


def test_annotation_lookup_batches_large_token_lists(tmp_path: Path) -> None:
    """Large documents must not exceed SQLite's host-parameter limit."""

    context = ProjectService().create_project(
        tmp_path / "project",
        ProjectMetadata(project_uuid="", title="Batching Test"),
    )
    token_ids = [f"tok-{index:05d}" for index in range(40_000)]

    grouped = AnnotationRepository(context.connection).list_annotations_for_tokens(token_ids)

    assert len(grouped) == len(token_ids)
    assert grouped["tok-00000"] == []
    assert grouped["tok-39999"] == []


def test_clear_document_content_batches_large_token_deletes(tmp_path: Path) -> None:
    """Repair cleanup must also batch token deletes for large imports."""

    source = tmp_path / "large.txt"
    source.write_text(" ".join(f"token{index}" for index in range(40_000)), encoding="utf-8")
    context = ProjectService().create_project(
        tmp_path / "project",
        ProjectMetadata(project_uuid="", title="Large Delete Test"),
    )
    imported = ImportService().import_file(context, source)
    assert imported.bundle.document is not None

    TranscriptRepository(context.connection).clear_document_content(imported.bundle.document.id)

    token_count = TranscriptRepository(context.connection).count_tokens_for_document(imported.bundle.document.id)
    assert token_count == 0
