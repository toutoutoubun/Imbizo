"""Unit tests for the public core.metrics compatibility module."""

from __future__ import annotations

import pytest

from imbizo.core.metrics import burstiness, i_index, m_index, switch_count, switch_density
from imbizo.domain.annotations import Annotation, AnnotationSource
from imbizo.domain.transcripts import SegmentLevel, Token, TranscriptSegment
from imbizo.metrics.common import AnnotatedToken, MetricsDataset


def _dataset(language_ids: list[str]) -> MetricsDataset:
    segment = TranscriptSegment(
        id="seg-1",
        transcript_document_id="doc-1",
        segment_level=SegmentLevel.UTTERANCE,
        sort_order=1,
        text_original="one two three four",
    )
    rows: list[AnnotatedToken] = []
    for index, language_id in enumerate(language_ids, start=1):
        token = Token(id=f"tok-{index}", segment_id=segment.id, sort_order=index, token_text=f"w{index}")
        annotation = Annotation(id=f"ann-{index}", token_id=token.id, source=AnnotationSource.MANUAL, language_id=language_id)
        rows.append(AnnotatedToken(token=token, segment=segment, annotation=annotation))
    return MetricsDataset(tokens=rows)


def test_core_metrics_compute_transparent_code_switching_values() -> None:
    """M-index, I-index, switch density, and burstiness use reproducible formulas."""

    dataset = _dataset(["eng", "zul", "zul", "eng"])

    assert m_index(dataset) == pytest.approx(1.0)
    assert switch_count(dataset) == 2
    assert i_index(dataset) == pytest.approx(2 / 3)
    assert switch_density(dataset, per_tokens=100) == pytest.approx(50.0)
    assert burstiness(dataset) == pytest.approx(-0.5)
