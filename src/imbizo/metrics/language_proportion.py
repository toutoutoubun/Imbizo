"""Language proportion metric."""

from __future__ import annotations

from collections import Counter

from imbizo.metrics.common import MetricsDataset


def language_proportions(dataset: MetricsDataset) -> dict[str, float]:
    """Compute language proportions from effective token annotations."""

    counts = Counter(item.annotation.language_id for item in dataset.tokens if item.annotation and item.annotation.language_id)
    total = sum(counts.values())
    if total == 0:
        return {}
    return {language_id: count / total for language_id, count in counts.items()}
