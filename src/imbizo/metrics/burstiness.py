"""Burstiness metric."""

from __future__ import annotations

import statistics

from imbizo.metrics.common import MetricsDataset


FORMULA_VERSION = "burstiness_v1"


def switch_intervals(dataset: MetricsDataset) -> list[int]:
    """Return token intervals between language switches."""

    intervals: list[int] = []
    previous_language: str | None = None
    since_last = 0
    for item in dataset.tokens:
        language_id = item.annotation.language_id if item.annotation else None
        if not language_id:
            continue
        if previous_language is not None:
            since_last += 1
            if language_id != previous_language:
                intervals.append(since_last)
                since_last = 0
        previous_language = language_id
    return intervals


def burstiness(dataset: MetricsDataset) -> float:
    """Compute Goh and Barabasi burstiness from switch intervals (Goh & Barabasi, 2008).

    Formula: B = (sigma - mu) / (sigma + mu), where mu is the mean interval and
    sigma is the standard deviation of intervals between switches.
    """

    intervals = switch_intervals(dataset)
    if len(intervals) < 2:
        return 0.0
    mean = statistics.mean(intervals)
    stdev = statistics.pstdev(intervals)
    if mean + stdev == 0:
        return 0.0
    return (stdev - mean) / (stdev + mean)
