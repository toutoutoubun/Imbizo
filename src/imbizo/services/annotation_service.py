"""Annotation editing service."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from imbizo.app.time import utc_now
from imbizo.domain.annotations import Annotation, AnnotationDraft, AnnotationSource, choose_effective_annotation
from imbizo.domain.languages import LanguageTag
from imbizo.domain.project import ProjectContext
from imbizo.domain.provenance import make_provenance_record
from imbizo.domain.transcripts import Token, TranscriptDocument, TranscriptSegment
from imbizo.persistence.repositories import AnnotationRepository, LanguageRepository, TranscriptRepository
from imbizo.services.provenance_service import ProvenanceService


@dataclass(slots=True)
class AnnotationRow:
    """One row in the annotation editor."""

    segment: TranscriptSegment
    token: Token
    annotation: Annotation | None


@dataclass(slots=True)
class AnnotationEditorState:
    """Data needed by the annotation editor."""

    document: TranscriptDocument
    segments: list[TranscriptSegment]
    rows: list[AnnotationRow]
    languages: list[LanguageTag]


class AnnotationService:
    """Coordinate transcript and annotation editing."""

    def load_editor_state(self, context: ProjectContext, document_id: str) -> AnnotationEditorState:
        """Load segments, tokens, effective annotations, languages, and tags."""

        transcript_repo = TranscriptRepository(context.connection)
        documents = {document.id: document for document in transcript_repo.list_documents()}
        document = documents[document_id]
        segments = transcript_repo.list_segments(document_id)
        segments_by_id = {segment.id: segment for segment in segments}
        annotation_repo = AnnotationRepository(context.connection)
        tokens = transcript_repo.list_all_tokens(document_id)
        annotations_by_token = annotation_repo.list_annotations_for_tokens([token.id for token in tokens])
        rows = [
            AnnotationRow(
                segment=segments_by_id[token.segment_id],
                token=token,
                annotation=choose_effective_annotation(annotations_by_token.get(token.id, [])),
            )
            for token in tokens
            if token.segment_id in segments_by_id
        ]
        languages = LanguageRepository(context.connection).list_languages()
        return AnnotationEditorState(document=document, segments=segments, rows=rows, languages=languages)

    def save_token_annotation(self, context: ProjectContext, token_id: str, draft: AnnotationDraft) -> Annotation:
        """Save a manual annotation for one token."""

        now = utc_now()
        annotation = Annotation(
            id=str(uuid.uuid4()),
            token_id=token_id,
            source=AnnotationSource.MANUAL,
            language_id=draft.language_id,
            matrix_language_id=draft.matrix_language_id,
            embedded_language_id=draft.embedded_language_id,
            switch_type=draft.switch_type,
            linguistic_status=draft.linguistic_status,
            trigger_text=draft.trigger_text,
            direction_from_language_id=draft.direction_from_language_id,
            direction_to_language_id=draft.direction_to_language_id,
            researcher_confidence=draft.researcher_confidence,
            memo=draft.memo,
            created_by="researcher",
            created_at=now,
            updated_at=now,
        )
        AnnotationRepository(context.connection).save_manual_annotation(annotation)
        ProvenanceService().record(
            context,
            make_provenance_record(
                "manual_create",
                "researcher",
                target_id=annotation.id,
                token_id=token_id,
                language_id=draft.language_id,
            ),
        )
        return annotation

    def save_segment_annotation(self, context: ProjectContext, segment_id: str, draft: AnnotationDraft) -> Annotation:
        """Save a manual annotation for one segment."""

        now = utc_now()
        annotation = Annotation(
            id=str(uuid.uuid4()),
            segment_id=segment_id,
            source=AnnotationSource.MANUAL,
            language_id=draft.language_id,
            matrix_language_id=draft.matrix_language_id,
            embedded_language_id=draft.embedded_language_id,
            switch_type=draft.switch_type,
            linguistic_status=draft.linguistic_status,
            trigger_text=draft.trigger_text,
            direction_from_language_id=draft.direction_from_language_id,
            direction_to_language_id=draft.direction_to_language_id,
            researcher_confidence=draft.researcher_confidence,
            memo=draft.memo,
            created_by="researcher",
            created_at=now,
            updated_at=now,
        )
        AnnotationRepository(context.connection).save_manual_annotation(annotation)
        return annotation

    def reject_auto_annotation(self, context: ProjectContext, annotation_id: str) -> None:
        """Mark an automatic annotation as rejected."""

        AnnotationRepository(context.connection).reject_annotation(annotation_id)
        ProvenanceService().record(context, make_provenance_record("manual_reject", "researcher", target_id=annotation_id))

    def search_annotations(self, context: ProjectContext, text: str = "") -> list[AnnotationRow]:
        """Search annotations by token text for the MVP."""

        transcript_repo = TranscriptRepository(context.connection)
        annotation_repo = AnnotationRepository(context.connection)
        rows: list[AnnotationRow] = []
        needle = text.lower()
        for document in transcript_repo.list_documents():
            for segment in transcript_repo.list_segments(document.id):
                for token in transcript_repo.list_tokens(segment.id):
                    if not needle or needle in token.token_text.lower():
                        rows.append(AnnotationRow(segment, token, annotation_repo.get_effective_annotation_for_token(token.id)))
        return rows
