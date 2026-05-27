"""Local LID service."""

from __future__ import annotations

import json
import uuid

from imbizo.app.time import utc_now
from imbizo.domain.annotations import Annotation, AnnotationSource
from imbizo.domain.metrics import JobStatus
from imbizo.domain.project import ProjectContext
from imbizo.domain.provenance import make_provenance_record
from imbizo.lid.baseline import BaselineLidProvider
from imbizo.lid.masklid import MaskLidDetector
from imbizo.lid.providers import LidLayer, LidOptions, LidSuggestionDraft
from imbizo.persistence.repositories import AnnotationRepository, LanguageRepository, TranscriptRepository
from imbizo.services.provenance_service import ProvenanceService


class LidService:
    """Coordinate local language identification workflows."""

    def __init__(self) -> None:
        self.provider = BaselineLidProvider()

    def run_lid_for_document(self, context: ProjectContext, document_id: str, options: LidOptions | None = None) -> str:
        """Run local LID for a transcript document and return the run ID."""

        options = options or LidOptions()
        run_id = str(uuid.uuid4())
        now = utc_now()
        context.connection.execute(
            """
            INSERT INTO lid_runs (
                id, provider_name, provider_version, layer, parameters_json,
                status, started_at, finished_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                self.provider.name,
                self.provider.version,
                LidLayer.LAYER3_MASKLID.value,
                json.dumps({"max_languages": options.max_languages, "min_confidence": options.min_confidence}),
                JobStatus.COMPLETED.value,
                now,
                utc_now(),
            ),
        )
        transcript_repo = TranscriptRepository(context.connection)
        languages = LanguageRepository(context.connection).list_languages()
        detector = MaskLidDetector(self.provider, languages)
        suggestions: list[LidSuggestionDraft] = []
        for segment in transcript_repo.list_segments(document_id):
            tokens = transcript_repo.list_tokens(segment.id)
            suggestions.extend(detector.detect(segment, tokens, options))
        for suggestion in suggestions:
            suggestion_id = str(uuid.uuid4())
            context.connection.execute(
                """
                INSERT INTO lid_suggestions (
                    id, lid_run_id, token_id, segment_id, language_id, layer,
                    rank, confidence, evidence_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    suggestion_id,
                    run_id,
                    suggestion.token_id,
                    suggestion.segment_id,
                    suggestion.language_id,
                    suggestion.layer.value,
                    suggestion.rank,
                    suggestion.confidence,
                    json.dumps(suggestion.evidence, ensure_ascii=False),
                    utc_now(),
                ),
            )
            if suggestion.token_id and suggestion.rank == 1:
                existing_manual = AnnotationRepository(context.connection).get_effective_annotation_for_token(suggestion.token_id)
                if existing_manual is None or existing_manual.source != AnnotationSource.MANUAL:
                    AnnotationRepository(context.connection).save_auto_annotation(
                        Annotation(
                            id=str(uuid.uuid4()),
                            token_id=suggestion.token_id,
                            source=AnnotationSource.AUTO,
                            language_id=suggestion.language_id,
                            auto_confidence=suggestion.confidence,
                            created_by=self.provider.name,
                        )
                    )
        context.connection.commit()
        ProvenanceService().record(
            context,
            make_provenance_record("auto_label", "lid_layer", target_id=run_id, suggestions=len(suggestions)),
        )
        return run_id

    def suggest_for_segment(self, context: ProjectContext, segment_id: str, options: LidOptions | None = None) -> list[LidSuggestionDraft]:
        """Return local language suggestions for one segment."""

        options = options or LidOptions()
        transcript_repo = TranscriptRepository(context.connection)
        segment = context.connection.execute("SELECT * FROM segments WHERE id = ?", (segment_id,)).fetchone()
        if segment is None:
            return []
        from imbizo.domain.transcripts import SegmentLevel, TranscriptSegment

        segment_obj = TranscriptSegment(
            id=segment["id"],
            transcript_document_id=segment["transcript_document_id"],
            segment_level=SegmentLevel(segment["segment_level"]),
            sort_order=int(segment["sort_order"]),
            text_original=segment["text_original"],
            start_ms=segment["start_ms"],
            end_ms=segment["end_ms"],
        )
        return MaskLidDetector(self.provider, LanguageRepository(context.connection).list_languages()).detect(
            segment_obj,
            transcript_repo.list_tokens(segment_id),
            options,
        )
