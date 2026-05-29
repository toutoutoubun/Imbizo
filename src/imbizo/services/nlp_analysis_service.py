"""End-to-end local NLP analysis pipeline.

This service is the local orchestration layer for Imbizo-CS Workbench. It
connects already-offline components: Local LID, code-switching metrics,
advisory noun-class hints, Clyne-style trigger candidates, and optional
mixed-code lexical evidence. Automatic outputs remain advisory and
overridable, consistent with the project's humanities-led posture.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
from typing import Any, Literal
import uuid

from imbizo import __version__
from imbizo.app.time import utc_now
from imbizo.core.annotation import Token as AdvisoryToken
from imbizo.core.mixed_code import detect_mixed_code_spans, load_mixed_code_dictionary
from imbizo.core.noun_class import suggest_class
from imbizo.core.triggers import find_trigger_candidates, load_trigger_dictionaries
from imbizo.domain.annotations import choose_effective_annotation
from imbizo.domain.project import ProjectContext
from imbizo.domain.provenance import make_provenance_record
from imbizo.domain.transcripts import Token, TranscriptSegment
from imbizo.lid.providers import LidOptions, LidProgress
from imbizo.persistence.repositories import AnnotationRepository, LanguageRepository, TranscriptRepository
from imbizo.services.lid_service import LidRunReport, LidService
from imbizo.services.metrics_service import MetricsRequest, MetricsService
from imbizo.services.provenance_service import ProvenanceService


ProgressCallback = Callable[[str, int, int], None]
StageStatus = Literal["completed", "skipped", "failed"]


@dataclass(slots=True)
class NlpAnalysisOptions:
    """Options for one local NLP pipeline run.

    Every option is local and advisory. The pipeline never calls the network,
    never uploads project data, and never overwrites manual annotations.
    """

    document_id: str | None = None
    run_lid: bool = True
    run_metrics: bool = True
    run_switch_profile: bool = True
    run_noun_class_hints: bool = True
    run_trigger_detection: bool = True
    run_mixed_code: bool = False
    mixed_code_varieties: tuple[str, ...] = ("tsotsitaal", "iscamtho", "kaaps", "sabela")
    lid_min_confidence: float = 0.25


@dataclass(slots=True)
class NlpAnalysisStageReport:
    """Structured summary of one pipeline stage."""

    name: str
    status: StageStatus
    message: str
    counts: dict[str, Any] = field(default_factory=dict)
    started_at: str = ""
    finished_at: str = ""


@dataclass(slots=True)
class NlpAnalysisReport:
    """Structured report for one reproducible local NLP analysis run."""

    id: str
    project_title: str
    imbizo_version: str
    document_id: str | None
    started_at: str
    finished_at: str
    options: dict[str, Any]
    stages: list[NlpAnalysisStageReport]
    metrics_run_id: str | None = None
    report_path: str = ""
    provenance_event_id: str = ""
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable representation."""

        data = asdict(self)
        data["stages"] = [asdict(stage) for stage in self.stages]
        return data


@dataclass(slots=True)
class _TokenRow:
    token: Token
    segment: TranscriptSegment
    language_code: str | None


class NlpAnalysisService:
    """Run the fully local NLP analysis workflow.

    The pipeline is deliberately conservative: it aggregates evidence from
    local tools and dictionaries, stores a report and a provenance event, and
    leaves interpretation to the researcher. Named concepts are implemented as
    advisory lenses: Local LID (Joulin et al., 2017 when fastText resources are
    installed), Clyne-style triggering (Clyne, 1967, 2003), noun-class prefix
    hints from local dictionaries, and code-switching metrics.
    """

    def __init__(
        self,
        lid_service: LidService | None = None,
        metrics_service: MetricsService | None = None,
    ) -> None:
        self.lid_service = lid_service or LidService()
        self.metrics_service = metrics_service or MetricsService()

    def run(
        self,
        context: ProjectContext,
        options: NlpAnalysisOptions | None = None,
        progress_callback: ProgressCallback | None = None,
    ) -> NlpAnalysisReport:
        """Run the local analysis pipeline and persist a JSON report."""

        options = options or NlpAnalysisOptions()
        run_id = str(uuid.uuid4())
        started_at = utc_now()
        stages: list[NlpAnalysisStageReport] = []
        warnings: list[str] = []

        self._progress(progress_callback, "Preparing local NLP analysis", 0, 100)
        documents = self._documents(context, options.document_id)
        if not documents:
            raise ValueError("No transcript document is available for local NLP analysis.")

        if options.run_lid:
            stages.append(self._run_lid_stage(context, documents, options, progress_callback))
        else:
            stages.append(self._skipped_stage("local_lid", "Local LID was disabled for this run."))

        rows = self._build_token_rows(context, options.document_id)
        if not rows:
            raise ValueError("The selected document has no token rows. Import or repair the transcript first.")

        if options.run_switch_profile:
            stages.append(self._run_switch_stage(rows))
        else:
            stages.append(self._skipped_stage("switch_profile", "Switch profiling was disabled for this run."))

        if options.run_noun_class_hints:
            stages.append(self._run_noun_class_stage(rows, warnings))
        else:
            stages.append(self._skipped_stage("noun_class_hints", "Noun-class hints were disabled for this run."))

        if options.run_trigger_detection:
            stages.append(self._run_trigger_stage(context, rows, warnings))
        else:
            stages.append(self._skipped_stage("trigger_candidates", "Trigger detection was disabled for this run."))

        if options.run_mixed_code:
            stages.append(self._run_mixed_code_stage(context, rows, options, warnings))
        else:
            stages.append(
                self._skipped_stage(
                    "mixed_code_candidates",
                    "Mixed-code variety mode is opt-in and was not enabled for this run.",
                )
            )

        metrics_run_id: str | None = None
        if options.run_metrics:
            metrics_stage, metrics_run_id = self._run_metrics_stage(context, options)
            stages.append(metrics_stage)
        else:
            stages.append(self._skipped_stage("metrics", "Metric computation was disabled for this run."))

        finished_at = utc_now()
        report = NlpAnalysisReport(
            id=run_id,
            project_title=context.metadata.title,
            imbizo_version=__version__,
            document_id=options.document_id,
            started_at=started_at,
            finished_at=finished_at,
            options=asdict(options),
            stages=stages,
            metrics_run_id=metrics_run_id,
            warnings=warnings,
        )
        report_path = self._write_report(context, report)
        report.report_path = str(report_path)
        provenance = make_provenance_record(
            "local_nlp_analysis",
            "local_pipeline",
            target_id=run_id,
            report_path=str(report_path.relative_to(context.paths.root)),
            metrics_run_id=metrics_run_id,
            stages=[asdict(stage) for stage in stages],
            warnings=warnings,
        )
        ProvenanceService().record(context, provenance)
        report.provenance_event_id = provenance.id
        report_path.write_text(json.dumps(report.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
        self._progress(progress_callback, "Local NLP analysis complete", 100, 100)
        return report

    def _run_lid_stage(
        self,
        context: ProjectContext,
        documents: list[str],
        options: NlpAnalysisOptions,
        progress_callback: ProgressCallback | None,
    ) -> NlpAnalysisStageReport:
        started = utc_now()
        reports: list[LidRunReport] = []

        def lid_progress(update: LidProgress) -> None:
            self._progress(progress_callback, f"Local LID: {update.message}", update.current, update.total)

        for document_id in documents:
            reports.append(
                self.lid_service.run_lid_for_document_report(
                    context,
                    document_id,
                    LidOptions(min_confidence=options.lid_min_confidence, progress_callback=lid_progress),
                )
            )
        provider_methods = sorted({report.provider_method for report in reports})
        provider_messages = [report.provider_message for report in reports if report.provider_message]
        return NlpAnalysisStageReport(
            name="local_lid",
            status="completed",
            message="Local language identification completed. Manual labels were preserved.",
            counts={
                "documents": len(documents),
                "suggestions": sum(report.suggestions_count for report in reports),
                "auto_annotations": sum(report.auto_annotations_count for report in reports),
                "preserved_manual": sum(report.preserved_manual_count for report in reports),
                "skipped_unknown": sum(report.skipped_unknown_count for report in reports),
                "provider_methods": provider_methods,
                "provider_messages": provider_messages,
            },
            started_at=started,
            finished_at=utc_now(),
        )

    def _run_switch_stage(self, rows: list[_TokenRow]) -> NlpAnalysisStageReport:
        started = utc_now()
        switch_points = []
        switch_type_counts: Counter[str] = Counter()
        previous: _TokenRow | None = None
        for row in rows:
            if previous is None:
                previous = row
                continue
            if not previous.language_code or not row.language_code or previous.language_code == row.language_code:
                previous = row
                continue
            switch_type = "intra_sentential" if previous.segment.id == row.segment.id else "inter_sentential"
            switch_type_counts[switch_type] += 1
            if len(switch_points) < 50:
                switch_points.append(
                    {
                        "from_token_id": previous.token.id,
                        "to_token_id": row.token.id,
                        "from_language": previous.language_code,
                        "to_language": row.language_code,
                        "switch_type": switch_type,
                    }
                )
            previous = row
        return NlpAnalysisStageReport(
            name="switch_profile",
            status="completed",
            message="Adjacent language transitions were profiled as advisory switch points.",
            counts={
                "token_rows": len(rows),
                "switch_count": sum(switch_type_counts.values()),
                "switch_type_counts": dict(switch_type_counts),
                "sample_switch_points": switch_points,
            },
            started_at=started,
            finished_at=utc_now(),
        )

    def _run_noun_class_stage(self, rows: list[_TokenRow], warnings: list[str]) -> NlpAnalysisStageReport:
        started = utc_now()
        bantu_codes = {"zul", "xho", "sot", "tsn"}
        checked = 0
        with_suggestions = 0
        top_classes: Counter[str] = Counter()
        missing_dictionaries: set[str] = set()
        samples: list[dict[str, Any]] = []
        for row in rows:
            if row.language_code not in bantu_codes:
                continue
            checked += 1
            try:
                suggestions = suggest_class(row.token.token_text, "", row.language_code)
            except FileNotFoundError:
                missing_dictionaries.add(row.language_code)
                continue
            if not suggestions:
                continue
            top = suggestions[0]
            with_suggestions += 1
            top_classes[str(top.class_label)] += 1
            if len(samples) < 50:
                samples.append(
                    {
                        "token_id": row.token.id,
                        "surface": row.token.token_text,
                        "language": row.language_code,
                        "class_label": top.class_label,
                        "class_number": top.class_number,
                        "prefix": top.prefix,
                        "verified": top.verified,
                    }
                )
        if missing_dictionaries:
            warnings.append(f"Missing noun-class dictionaries for: {', '.join(sorted(missing_dictionaries))}")
        return NlpAnalysisStageReport(
            name="noun_class_hints",
            status="completed",
            message="Noun-class prefix hints were generated as review suggestions only.",
            counts={
                "tokens_checked": checked,
                "tokens_with_suggestions": with_suggestions,
                "top_class_counts": dict(top_classes),
                "sample_suggestions": samples,
            },
            started_at=started,
            finished_at=utc_now(),
        )

    def _run_trigger_stage(
        self,
        context: ProjectContext,
        rows: list[_TokenRow],
        warnings: list[str],
    ) -> NlpAnalysisStageReport:
        started = utc_now()
        loaded = self._load_trigger_roots(context, warnings)
        by_segment: dict[str, list[_TokenRow]] = defaultdict(list)
        for row in rows:
            by_segment[row.segment.id].append(row)
        candidate_count = 0
        samples: list[dict[str, Any]] = []
        for segment_rows in by_segment.values():
            advisory_tokens = self._advisory_tokens(segment_rows)
            for index in range(1, len(advisory_tokens)):
                if advisory_tokens[index - 1].language == advisory_tokens[index].language:
                    continue
                for candidate in find_trigger_candidates(advisory_tokens, index, window_left=2):
                    candidate_count += 1
                    if len(samples) < 50:
                        samples.append(asdict(candidate))
        return NlpAnalysisStageReport(
            name="trigger_candidates",
            status="completed",
            message="Clyne-style trigger candidates were detected as contextual prompts, not causal explanations.",
            counts={"dictionaries_loaded": loaded, "candidates": candidate_count, "sample_candidates": samples},
            started_at=started,
            finished_at=utc_now(),
        )

    def _run_mixed_code_stage(
        self,
        context: ProjectContext,
        rows: list[_TokenRow],
        options: NlpAnalysisOptions,
        warnings: list[str],
    ) -> NlpAnalysisStageReport:
        started = utc_now()
        dictionaries = self._load_mixed_code_dictionaries(context, options.mixed_code_varieties, warnings)
        by_segment: dict[str, list[_TokenRow]] = defaultdict(list)
        for row in rows:
            by_segment[row.segment.id].append(row)
        candidate_count = 0
        samples: list[dict[str, Any]] = []
        for dictionary in dictionaries.values():
            for segment_rows in by_segment.values():
                candidates = detect_mixed_code_spans(self._advisory_tokens(segment_rows), dictionary.variety_code, dictionary)
                candidate_count += len(candidates)
                for candidate in candidates:
                    if len(samples) < 50:
                        samples.append(asdict(candidate))
        return NlpAnalysisStageReport(
            name="mixed_code_candidates",
            status="completed",
            message="Mixed-code lexical evidence was detected without declaring speaker or text identity.",
            counts={"dictionaries_loaded": len(dictionaries), "candidates": candidate_count, "sample_candidates": samples},
            started_at=started,
            finished_at=utc_now(),
        )

    def _run_metrics_stage(
        self,
        context: ProjectContext,
        options: NlpAnalysisOptions,
    ) -> tuple[NlpAnalysisStageReport, str]:
        started = utc_now()
        run = self.metrics_service.compute_metrics(context, MetricsRequest(document_id=options.document_id))
        results = self.metrics_service.get_results(context, run.id)
        return (
            NlpAnalysisStageReport(
                name="metrics",
                status="completed",
                message="Code-switching metrics were computed locally and stored in SQLite.",
                counts={"metric_run_id": run.id, "metric_count": len(results), "input_count": max((r.input_count for r in results), default=0)},
                started_at=started,
                finished_at=utc_now(),
            ),
            run.id,
        )

    def _build_token_rows(self, context: ProjectContext, document_id: str | None) -> list[_TokenRow]:
        transcript_repo = TranscriptRepository(context.connection)
        annotation_repo = AnnotationRepository(context.connection)
        languages = LanguageRepository(context.connection).list_languages()
        code_by_id = {language.id: language.code for language in languages}
        documents = self._documents(context, document_id)
        segments = [segment for doc_id in documents for segment in transcript_repo.list_segments(doc_id)]
        segments_by_id = {segment.id: segment for segment in segments}
        tokens = [token for doc_id in documents for token in transcript_repo.list_all_tokens(doc_id)]
        annotations_by_token = annotation_repo.list_annotations_for_tokens([token.id for token in tokens])
        rows: list[_TokenRow] = []
        for token in tokens:
            annotation = choose_effective_annotation(annotations_by_token.get(token.id, []))
            language_code = code_by_id.get(annotation.language_id) if annotation and annotation.language_id else None
            segment = segments_by_id.get(token.segment_id)
            if segment is not None:
                rows.append(_TokenRow(token=token, segment=segment, language_code=language_code))
        return rows

    def _documents(self, context: ProjectContext, document_id: str | None) -> list[str]:
        transcript_repo = TranscriptRepository(context.connection)
        documents = transcript_repo.list_documents()
        if document_id is None:
            return [document.id for document in documents]
        return [document.id for document in documents if document.id == document_id]

    def _write_report(self, context: ProjectContext, report: NlpAnalysisReport) -> Path:
        report_dir = context.paths.logs / "analysis"
        report_dir.mkdir(parents=True, exist_ok=True)
        path = report_dir / f"local_nlp_analysis_{report.id}.json"
        path.write_text(json.dumps(report.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
        return path

    def _load_trigger_roots(self, context: ProjectContext, warnings: list[str]) -> int:
        loaded = 0
        for root in self._dictionary_roots(context):
            trigger_dir = root / "triggers"
            if not trigger_dir.exists():
                continue
            loaded += len(load_trigger_dictionaries(trigger_dir))
        if loaded == 0:
            warnings.append("No trigger dictionaries were found; trigger detection produced no candidates.")
        return loaded

    def _load_mixed_code_dictionaries(
        self,
        context: ProjectContext,
        varieties: tuple[str, ...],
        warnings: list[str],
    ) -> dict[str, Any]:
        loaded: dict[str, Any] = {}
        for root in self._dictionary_roots(context):
            mixed_dir = root / "mixed_code"
            if not mixed_dir.exists():
                continue
            for variety in varieties:
                path = mixed_dir / f"{variety}.yaml"
                if path.exists() and variety not in loaded:
                    loaded[variety] = load_mixed_code_dictionary(path)
        if not loaded:
            warnings.append("No mixed-code dictionaries were found; mixed-code mode produced no candidates.")
        return loaded

    def _dictionary_roots(self, context: ProjectContext) -> list[Path]:
        candidates = [
            context.paths.dictionaries,
            Path.cwd() / "dictionaries",
            Path(__file__).resolve().parents[3] / "dictionaries",
        ]
        roots: list[Path] = []
        seen: set[Path] = set()
        for candidate in candidates:
            resolved = candidate.resolve()
            if resolved not in seen and resolved.exists():
                roots.append(resolved)
                seen.add(resolved)
        return roots

    def _advisory_tokens(self, rows: list[_TokenRow]) -> list[AdvisoryToken]:
        return [
            AdvisoryToken(
                id=row.token.id,
                surface=row.token.token_text,
                utterance_id=row.segment.id,
                position=row.token.sort_order,
                language=row.language_code,
                normalized=row.token.normalized_text,
            )
            for row in rows
        ]

    def _skipped_stage(self, name: str, message: str) -> NlpAnalysisStageReport:
        now = utc_now()
        return NlpAnalysisStageReport(name=name, status="skipped", message=message, started_at=now, finished_at=now)

    def _progress(self, callback: ProgressCallback | None, message: str, current: int, total: int) -> None:
        if callback is not None:
            callback(message, current, total)
