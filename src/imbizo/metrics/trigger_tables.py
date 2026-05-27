"""Switch-trigger co-occurrence tables."""

from __future__ import annotations

from collections import Counter

from imbizo.metrics.common import MetricsDataset


def trigger_cooccurrence(dataset: MetricsDataset) -> dict[str, int]:
    """Count trigger text co-occurrences with switch annotations."""

    counts: Counter[str] = Counter()
    for item in dataset.tokens:
        annotation = item.annotation
        if annotation and annotation.trigger_text:
            key = f"{annotation.direction_from_language_id or ''}->{annotation.direction_to_language_id or ''}:{annotation.trigger_text}"
            counts[key] += 1
    return dict(counts)
