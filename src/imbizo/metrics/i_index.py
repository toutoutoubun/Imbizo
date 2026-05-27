"""I-index metric."""

from __future__ import annotations

from imbizo.metrics.common import MetricsDataset
from imbizo.metrics.switch_density import switch_count


FORMULA_VERSION = "i_index_v1"


def i_index(dataset: MetricsDataset) -> float:
    """Compute the Integration / switch-point Index (Guzman et al., 2017).

    Formula: I = observed switch points / possible adjacent annotated token
    boundaries. The denominator is annotated token count minus one.
    """

    annotated_count = len([item for item in dataset.tokens if item.annotation and item.annotation.language_id])
    if annotated_count <= 1:
        return 0.0
    return switch_count(dataset) / (annotated_count - 1)
