"""Tests for Local LID acceptance summaries."""

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
    source.write_text("hello sawubona friend\n", encoding="utf-8")
    context = ProjectService().create_project(tmp_path / "project", ProjectMetadata(project_uuid="", title="Accuracy Test"))
    imported = ImportService().import_file(context, source)
    assert imported.bundle.document is not None
    languages = {language.code: language for language in LanguageRepository(context.connection).list_languages()}
    tokens = TranscriptRepository(context.connection).list_all_tokens(imported.bundle.document.id)
    segments = TranscriptRepository(context.connection).list_segments(imported.bundle.document.id)
    assert len(tokens) == 3
    assert len(segments) == 1
    return context, imported.bundle.document, tokens, segments[0], languages


def test_token_acceptance_counts_final_auto_and_reviewed_labels(tmp_path: Path) -> None:
    """Final labels include accepted auto labels plus manual/imported labels."""

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
            Annotation(id=str(uuid.uuid4()), token_id=tokens[2].id, source=AnnotationSource.AUTO, language_id=languages["eng"].id, created_at=now, updated_at=now),
        ]
    )

    rows = LidAccuracyService().compute(context)
    token_rows = {row.language_code: row for row in rows if row.scope == "token"}

    assert token_rows["eng"].final_label_count == 2
    assert token_rows["eng"].accepted_auto_count == 1
    assert token_rows["eng"].reviewed_label_count == 1
    assert token_rows["eng"].auto_acceptance_rate == 0.5
    assert token_rows["eng"].manual_intervention_rate == 0.5
    assert token_rows["zul"].final_label_count == 1
    assert token_rows["zul"].accepted_auto_count == 0
    assert token_rows["zul"].reviewed_label_count == 1
    assert token_rows["zul"].manual_intervention_rate == 1.0


def test_span_acceptance_reviewed_span_overrides_latest_rank_one_suggestion(tmp_path: Path) -> None:
    """Reviewed span labels override rank-1 suggestions in final-label counts."""

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

    assert span_rows["zul"].final_label_count == 1
    assert span_rows["zul"].accepted_auto_count == 0
    assert span_rows["zul"].reviewed_label_count == 1
    assert span_rows["zul"].manual_intervention_rate == 1.0
    assert "eng" not in span_rows
