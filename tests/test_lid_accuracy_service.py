"""Tests for reviewed Local LID accuracy summaries."""

from __future__ import annotations

import uuid
from pathlib import Path

from imbizo.app.time import utc_now
from imbizo.domain.annotations import Annotation, AnnotationSource
from imbizo.domain.metrics import JobStatus
from imbizo.domain.project import ProjectMetadata
from imbizo.lid.providers import LidLayer
from imbizo.persistence.repositories import AnnotationRepository, LanguageRepository, TranscriptRepository
from imbizo.services.import_service import ImportService
from imbizo.services.lid_accuracy_service import LidAccuracyService
from imbizo.services.project_service import ProjectService


def _context_with_labels(tmp_path: Path):
    source = tmp_path / "sample.txt"
    source.write_text("hello sawubona\n", encoding="utf-8")
    context = ProjectService().create_project(tmp_path / "project", ProjectMetadata(project_uuid="", title="Accuracy Test"))
    imported = ImportService().import_file(context, source)
    assert imported.bundle.document is not None
    languages = {language.code: language for language in LanguageRepository(context.connection).list_languages()}
    tokens = TranscriptRepository(context.connection).list_all_tokens(imported.bundle.document.id)
    segments = TranscriptRepository(context.connection).list_segments(imported.bundle.document.id)
    assert len(tokens) == 2
    assert len(segments) == 1
    return context, imported.bundle.document, tokens, segments[0], languages


def test_token_accuracy_compares_auto_labels_with_reviewed_gold(tmp_path: Path) -> None:
    """Accuracy is computed against manual/imported labels, never auto alone."""

    context, _document, tokens, _segment, languages = _context_with_labels(tmp_path)
    now = utc_now()
    repo = AnnotationRepository(context.connection)
    repo.save_imported_annotations(
        [
            Annotation(id=str(uuid.uuid4()), token_id=tokens[0].id, source=AnnotationSource.IMPORTED, language_id=languages["eng"].id, created_at=now, updated_at=now),
            Annotation(id=str(uuid.uuid4()), token_id=tokens[1].id, source=AnnotationSource.IMPORTED, language_id=languages["zul"].id, created_at=now, updated_at=now),
        ]
    )
    repo.save_auto_annotations(
        [
            Annotation(id=str(uuid.uuid4()), token_id=tokens[0].id, source=AnnotationSource.AUTO, language_id=languages["eng"].id, created_at=now, updated_at=now),
            Annotation(id=str(uuid.uuid4()), token_id=tokens[1].id, source=AnnotationSource.AUTO, language_id=languages["eng"].id, created_at=now, updated_at=now),
        ]
    )

    rows = LidAccuracyService().compute(context)
    token_rows = {row.language_code: row for row in rows if row.scope == "token"}

    assert token_rows["eng"].reviewed_count == 1
    assert token_rows["eng"].correct_count == 1
    assert token_rows["eng"].accuracy == 1.0
    assert token_rows["zul"].reviewed_count == 1
    assert token_rows["zul"].correct_count == 0
    assert token_rows["zul"].incorrect_count == 1
    assert token_rows["zul"].accuracy == 0.0


def test_span_accuracy_compares_latest_rank_one_suggestion_with_reviewed_span(tmp_path: Path) -> None:
    """Span rows compare reviewed segment labels with latest rank-1 suggestions."""

    context, _document, _tokens, segment, languages = _context_with_labels(tmp_path)
    now = utc_now()
    AnnotationRepository(context.connection).save_imported_annotations(
        [
            Annotation(id=str(uuid.uuid4()), segment_id=segment.id, source=AnnotationSource.IMPORTED, language_id=languages["zul"].id, created_at=now, updated_at=now),
        ]
    )
    run_id = str(uuid.uuid4())
    context.connection.execute(
        """
        INSERT INTO lid_runs (
            id, provider_name, provider_version, layer, parameters_json,
            status, started_at, finished_at, error_message
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            "fixture",
            "0.1",
            LidLayer.LAYER3_MASKLID.value,
            "{}",
            JobStatus.COMPLETED.value,
            now,
            now,
            "",
        ),
    )
    context.connection.execute(
        """
        INSERT INTO lid_suggestions (
            id, lid_run_id, token_id, segment_id, language_id, layer,
            rank, confidence, evidence_json, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            str(uuid.uuid4()),
            run_id,
            None,
            segment.id,
            languages["eng"].id,
            LidLayer.LAYER3_MASKLID.value,
            1,
            0.8,
            "{}",
            now,
        ),
    )
    context.connection.commit()

    rows = LidAccuracyService().compute(context)
    span_rows = {row.language_code: row for row in rows if row.scope == "span"}

    assert span_rows["zul"].reviewed_count == 1
    assert span_rows["zul"].auto_labelled_count == 1
    assert span_rows["zul"].correct_count == 0
    assert span_rows["zul"].accuracy == 0.0
