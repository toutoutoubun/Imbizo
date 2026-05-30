"""Local LID service."""

from __future__ import annotations

import json
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path

from imbizo.app.time import utc_now
from imbizo.domain.annotations import Annotation, AnnotationSource, choose_effective_annotation
from imbizo.domain.metrics import JobStatus
from imbizo.domain.project import ProjectContext
from imbizo.domain.provenance import make_provenance_record
from imbizo.lid.baseline import BaselineLidProvider
from imbizo.lid.coarse_groups import (
    annotate_suggestions_with_candidate_scores,
    apply_coarse_group_gate,
    coarse_gate_allows_auto_apply,
    coarse_gate_reason,
)
from imbizo.lid.masklid import MaskLidDetector
from imbizo.lid.providers import LidLayer, LidOptions, LidProgress, LidSuggestionDraft
from imbizo.persistence.repositories import AnnotationRepository, LanguageRepository, TranscriptRepository
from imbizo.services.provenance_service import ProvenanceService


@dataclass(slots=True)
class LidRunReport:
    """Summary of one local LID run for GUI feedback and tests."""

    run_id: str
    suggestions_count: int
    segment_suggestions_count: int
    token_suggestions_count: int
    auto_annotations_count: int
    skipped_unknown_count: int
    preserved_manual_count: int
    provider_method: str
    provider_message: str
    coarse_group_gate_enabled: bool = False
    coarse_group_gated_count: int = 0
    coarse_group_low_confidence_count: int = 0
    coarse_group_ambiguous_count: int = 0


class LidService:
    """Coordinate local language identification workflows."""

    def __init__(self) -> None:
        self.provider = BaselineLidProvider()

    def run_lid_for_document(self, context: ProjectContext, document_id: str, options: LidOptions | None = None) -> str:
        """Run local LID for a transcript document and return the run ID."""

        return self.run_lid_for_document_report(context, document_id, options).run_id

    def run_lid_for_document_report(
        self,
        context: ProjectContext,
        document_id: str,
        options: LidOptions | None = None,
    ) -> LidRunReport:
        """Run local LID and return a researcher-readable execution report."""

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
                json.dumps(_lid_parameters(options), ensure_ascii=False),
                JobStatus.RUNNING.value,
                now,
                None,
            ),
        )
        try:
            self._progress(options, 2, "Preparing local LID")
            transcript_repo = TranscriptRepository(context.connection)
            languages = LanguageRepository(context.connection).list_languages()
            language_codes_by_id = {language.id: language.code for language in languages}
            if hasattr(self.provider, "configure_search_roots"):
                self.provider.configure_search_roots(_model_search_roots(context))
            detector = MaskLidDetector(self.provider, languages)
            segments = transcript_repo.list_segments(document_id)
            token_batches = [(segment, transcript_repo.list_tokens(segment.id)) for segment in segments]
            total_batches = max(1, len(token_batches))
            suggestions: list[LidSuggestionDraft] = []
            for index, (segment, tokens) in enumerate(token_batches, start=1):
                self._progress(options, 5 + int((index - 1) / total_batches * 55), f"Detecting languages in segment {index}/{len(token_batches)}")
                suggestions.extend(detector.detect(segment, tokens, options))
            if options.use_coarse_group_gate:
                suggestions = [
                    apply_coarse_group_gate(suggestion, options)
                    for suggestion in annotate_suggestions_with_candidate_scores(suggestions, language_codes_by_id)
                ]

            self._progress(options, 62, f"Saving {len(suggestions)} LID suggestions")
            for index, suggestion in enumerate(suggestions, start=1):
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
                if index % 100 == 0:
                    self._progress(options, 62 + int(index / max(1, len(suggestions)) * 18), f"Saved {index}/{len(suggestions)} LID suggestions")

            token_suggestions = [suggestion for suggestion in suggestions if suggestion.token_id]
            top_token_suggestions = [suggestion for suggestion in token_suggestions if suggestion.token_id and suggestion.rank == 1]
            annotation_repo = AnnotationRepository(context.connection)
            annotations_by_token = annotation_repo.list_annotations_for_tokens([str(suggestion.token_id) for suggestion in top_token_suggestions])
            auto_annotations: list[Annotation] = []
            skipped_unknown_count = 0
            preserved_manual_count = 0
            coarse_group_gated_count = 0
            coarse_group_low_confidence_count = 0
            coarse_group_ambiguous_count = 0
            for suggestion in top_token_suggestions:
                if not suggestion.token_id:
                    continue
                language_code = language_codes_by_id.get(suggestion.language_id or "", "")
                if language_code == "und":
                    skipped_unknown_count += 1
                    continue
                existing = choose_effective_annotation(annotations_by_token.get(suggestion.token_id, []))
                if existing is not None and existing.source == AnnotationSource.MANUAL:
                    preserved_manual_count += 1
                    continue
                if not coarse_gate_allows_auto_apply(suggestion):
                    coarse_group_gated_count += 1
                    reason = coarse_gate_reason(suggestion)
                    if reason == "low_group_confidence":
                        coarse_group_low_confidence_count += 1
                    elif reason == "closely_related_language_group":
                        coarse_group_ambiguous_count += 1
                    continue
                auto_annotations.append(
                    Annotation(
                        id=str(uuid.uuid4()),
                        token_id=suggestion.token_id,
                        source=AnnotationSource.AUTO,
                        language_id=suggestion.language_id,
                        auto_confidence=suggestion.confidence,
                        created_by=self.provider.name,
                    )
                )

            self._progress(options, 84, f"Applying {len(auto_annotations)} useful auto labels")
            annotation_repo.save_auto_annotations(auto_annotations, commit=False)
            finished_at = utc_now()
            context.connection.execute(
                """
                UPDATE lid_runs
                SET status = ?, finished_at = ?, error_message = ''
                WHERE id = ?
                """,
                (JobStatus.COMPLETED.value, finished_at, run_id),
            )
            context.connection.commit()
            ProvenanceService().record(
                context,
                make_provenance_record(
                    "auto_label",
                    "lid_layer",
                    target_id=run_id,
                    suggestions=len(suggestions),
                    auto_annotations=len(auto_annotations),
                    skipped_unknown=skipped_unknown_count,
                    preserved_manual=preserved_manual_count,
                    coarse_group_gate_enabled=options.use_coarse_group_gate,
                    coarse_group_gated_count=coarse_group_gated_count,
                    coarse_group_low_confidence_count=coarse_group_low_confidence_count,
                    coarse_group_ambiguous_count=coarse_group_ambiguous_count,
                ),
            )
            self._progress(options, 100, "Local LID complete")
            return LidRunReport(
                run_id=run_id,
                suggestions_count=len(suggestions),
                segment_suggestions_count=len([suggestion for suggestion in suggestions if suggestion.segment_id]),
                token_suggestions_count=len(token_suggestions),
                auto_annotations_count=len(auto_annotations),
                skipped_unknown_count=skipped_unknown_count,
                preserved_manual_count=preserved_manual_count,
                provider_method=getattr(self.provider, "active_method", self.provider.name),
                provider_message=getattr(self.provider, "load_error", ""),
                coarse_group_gate_enabled=options.use_coarse_group_gate,
                coarse_group_gated_count=coarse_group_gated_count,
                coarse_group_low_confidence_count=coarse_group_low_confidence_count,
                coarse_group_ambiguous_count=coarse_group_ambiguous_count,
            )
        except Exception as exc:
            context.connection.rollback()
            context.connection.execute(
                """
                INSERT OR REPLACE INTO lid_runs (
                    id, provider_name, provider_version, layer, parameters_json,
                    status, started_at, finished_at, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    self.provider.name,
                    self.provider.version,
                    LidLayer.LAYER3_MASKLID.value,
                    json.dumps(_lid_parameters(options), ensure_ascii=False),
                    JobStatus.FAILED.value,
                    now,
                    utc_now(),
                    str(exc),
                ),
            )
            context.connection.commit()
            self._progress(options, 100, "Local LID failed")
            raise

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
        languages = LanguageRepository(context.connection).list_languages()
        suggestions = MaskLidDetector(self.provider, languages).detect(
            segment_obj,
            transcript_repo.list_tokens(segment_id),
            options,
        )
        if not options.use_coarse_group_gate:
            return suggestions
        language_codes_by_id = {language.id: language.code for language in languages}
        return [
            apply_coarse_group_gate(suggestion, options)
            for suggestion in annotate_suggestions_with_candidate_scores(suggestions, language_codes_by_id)
        ]

    def _progress(self, options: LidOptions, current: int, message: str) -> None:
        if options.progress_callback is not None:
            options.progress_callback(LidProgress(current=max(0, min(100, current)), total=100, message=message))


def _model_search_roots(context: ProjectContext) -> list[Path]:
    """Return local roots where optional fastText LID resources may live."""

    roots = [context.paths.root, context.paths.root.parent, Path.cwd()]
    executable = Path(sys.executable).resolve()
    roots.extend(executable.parents[:4])
    seen: set[Path] = set()
    unique: list[Path] = []
    for root in roots:
        if root not in seen:
            seen.add(root)
            unique.append(root)
    return unique


def _lid_parameters(options: LidOptions) -> dict[str, object]:
    """Return the persisted local LID parameter payload."""

    return {
        "max_languages": options.max_languages,
        "min_confidence": options.min_confidence,
        "use_coarse_group_gate": options.use_coarse_group_gate,
    }
