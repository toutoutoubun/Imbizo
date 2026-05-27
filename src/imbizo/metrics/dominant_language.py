"""Dominant language metric."""

from __future__ import annotations

from collections import Counter, defaultdict

from imbizo.metrics.common import MetricsDataset


def dominant_language_by_segment(dataset: MetricsDataset) -> dict[str, str]:
    """Return dominant effective language per segment."""

    counts: dict[str, Counter[str]] = defaultdict(Counter)
    for item in dataset.tokens:
        if item.annotation and item.annotation.language_id:
            counts[item.segment.id][item.annotation.language_id] += 1
    return {
        segment_id: counter.most_common(1)[0][0]
        for segment_id, counter in counts.items()
        if counter
    }
