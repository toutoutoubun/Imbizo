"""Metrics service."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Sequence

from imbizo.app.time import utc_now
from imbizo.domain.metrics import JobStatus, MetricResult, MetricRun
from imbizo.domain.project import ProjectContext
from imbizo.metrics.burstiness import burstiness
from imbizo.metrics.common import AnnotatedToken, MetricsDataset
from imbizo.metrics.concordance import kwic
from imbizo.metrics.dominant_language import dominant_language_by_segment
from imbizo.metrics.i_index import i_index
from imbizo.metrics.language_proportion import language_proportions
from imbizo.metrics.m_index import m_index
from imbizo.metrics.switch_density import switch_count, switch_density
from imbizo.metrics.trigger_tables import trigger_cooccurrence
from imbizo.persistence.repositories import AnnotationRepository, MetricRepository, TranscriptRepository


@dataclass(slots=True)
class MetricsRequest:
    """Metrics to compute."""

    metric_names: Sequence[str] = field(default_factory=lambda: [
        "language_proportion",
        "switch_count",
        "switch_density",
        "dominant_language",
        "m_index",
        "i_index",
        "burstiness",
        "trigger_cooccurrence",
        "kwic",
    ])
    document_id: str | None = None
    kwic_pattern: str = ""


class MetricsService:
    """Coordinate local quantitative metrics."""

    def compute_metrics(self, context: ProjectContext, request: MetricsRequest | None = None) -> MetricRun:
        """Compute requested metrics and store results."""

        request = request or MetricsRequest()
        run = MetricRun(
            id=str(uuid.uuid4()),
            formula_version="mvp_formulas_v1",
            status=JobStatus.COMPLETED,
            run_name="MVP metric run",
            input_filter={"document_id": request.document_id},
            started_at=utc_now(),
            finished_at=utc_now(),
        )
        dataset = self._build_dataset(context, request.document_id)
        results: list[MetricResult] = []
        values = {
            "language_proportion": language_proportions(dataset),
            "switch_count": switch_count(dataset),
            "switch_density": switch_density(dataset),
            "dominant_language": dominant_language_by_segment(dataset),
            "m_index": m_index(dataset),
            "i_index": i_index(dataset),
            "burstiness": burstiness(dataset),
            "trigger_cooccurrence": trigger_cooccurrence(dataset),
            "kwic": kwic(dataset, request.kwic_pattern) if request.kwic_pattern else [],
        }
        for name in request.metric_names:
            if name in values:
                results.append(
                    MetricResult(
                        id=str(uuid.uuid4()),
                        metric_run_id=run.id,
                        metric_name=name,
                        scope_type="project",
                        value=values[name],
                        input_count=len(dataset.tokens),
                        created_at=utc_now(),
                    )
                )
        repo = MetricRepository(context.connection)
        repo.save_run(run)
        repo.save_results(results)
        return run

    def get_results(self, context: ProjectContext, metric_run_id: str) -> list[MetricResult]:
        """Return results for one metric run."""

        return MetricRepository(context.connection).get_results(metric_run_id)

    def _build_dataset(self, context: ProjectContext, document_id: str | None = None) -> MetricsDataset:
        transcript_repo = TranscriptRepository(context.connection)
        annotation_repo = AnnotationRepository(context.connection)
        rows: list[AnnotatedToken] = []
        documents = transcript_repo.list_documents()
        for document in documents:
            if document_id and document.id != document_id:
                continue
            for segment in transcript_repo.list_segments(document.id):
                for token in transcript_repo.list_tokens(segment.id):
                    rows.append(AnnotatedToken(token=token, segment=segment, annotation=annotation_repo.get_effective_annotation_for_token(token.id)))
        return MetricsDataset(tokens=rows)
