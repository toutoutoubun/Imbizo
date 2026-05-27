"""Switch count and density metrics."""

from __future__ import annotations

from imbizo.metrics.common import MetricsDataset


def switch_count(dataset: MetricsDataset) -> int:
    """Count adjacent effective language changes."""

    count = 0
    previous: str | None = None
    for item in dataset.tokens:
        language_id = item.annotation.language_id if item.annotation else None
        if previous and language_id and language_id != previous:
            count += 1
        if language_id:
            previous = language_id
    return count


def switch_density(dataset: MetricsDataset, per_tokens: int = 100) -> float:
    """Compute switches per N annotated tokens."""

    annotated = [item for item in dataset.tokens if item.annotation and item.annotation.language_id]
    if not annotated:
        return 0.0
    return switch_count(dataset) / len(annotated) * per_tokens
