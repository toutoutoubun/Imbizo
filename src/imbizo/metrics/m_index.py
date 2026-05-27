"""M-index metric."""

from __future__ import annotations

from collections import Counter

from imbizo.metrics.common import MetricsDataset


FORMULA_VERSION = "m_index_v1"


def m_index(dataset: MetricsDataset) -> float:
    """Compute the Multilingual Index (Barnett et al., 2000).

    Formula: M = (1 - sum(p_i ** 2)) * (k / (k - 1)) where p_i is each
    language proportion and k is the number of languages present.
    """

    counts = Counter(item.annotation.language_id for item in dataset.tokens if item.annotation and item.annotation.language_id)
    k = len(counts)
    total = sum(counts.values())
    if k <= 1 or total == 0:
        return 0.0
    proportions = [count / total for count in counts.values()]
    return (1.0 - sum(value * value for value in proportions)) * (k / (k - 1))
