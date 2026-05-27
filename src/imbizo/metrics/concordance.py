"""KWIC concordance metric."""

from __future__ import annotations

from imbizo.metrics.common import MetricsDataset


def kwic(dataset: MetricsDataset, pattern: str, window: int = 5) -> list[dict[str, str]]:
    """Return keyword-in-context rows for a token pattern."""

    tokens = dataset.tokens
    needle = pattern.lower()
    rows: list[dict[str, str]] = []
    for index, item in enumerate(tokens):
        if needle and needle not in item.token.token_text.lower():
            continue
        left = " ".join(token.token.token_text for token in tokens[max(0, index - window):index])
        right = " ".join(token.token.token_text for token in tokens[index + 1:index + 1 + window])
        rows.append({"left": left, "keyword": item.token.token_text, "right": right, "segment_id": item.segment.id})
    return rows
