"""Property tests for the v1.0 integration score."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

hypothesis = pytest.importorskip("hypothesis")
strategies = pytest.importorskip("hypothesis.strategies")

from imbizo.core.concord import ConcordLink, integration_score


@hypothesis.given(
    confirmed=strategies.booleans(),
    has_class=strategies.booleans(),
    reviewed=strategies.booleans(),
    frequency=strategies.integers(min_value=0, max_value=20),
    threshold=strategies.integers(min_value=1, max_value=20),
)
def test_integration_score_is_bounded(
    confirmed: bool,
    has_class: bool,
    reviewed: bool,
    frequency: int,
    threshold: int,
) -> None:
    """Scores are always in [0, 1]."""

    stem = SimpleNamespace(id="stem", nc_class=9 if has_class else None)
    links = [
        ConcordLink(
            id="cl",
            segment_id="u1",
            controller_token_id="stem",
            concord_token_id="adj",
            concord_type="AC",
            observed_form="fictional",
            agreement_status="confirmed" if confirmed else "uncertain",
            source="manual" if reviewed else "suggested-overridden",
            controller_nc_class=9 if has_class else None,
        )
    ]

    score = integration_score(stem, links, frequency, threshold)

    assert 0.0 <= score <= 1.0


@hypothesis.given(
    frequency=strategies.integers(min_value=0, max_value=20),
    threshold=strategies.integers(min_value=1, max_value=20),
)
def test_integration_score_monotonic_when_removing_confirmed_concord(frequency: int, threshold: int) -> None:
    """Removing a confirmed concord criterion never increases the score."""

    stem = SimpleNamespace(id="stem", nc_class=9)
    confirmed_link = ConcordLink(
        id="cl",
        segment_id="u1",
        controller_token_id="stem",
        concord_token_id="adj",
        concord_type="AC",
        observed_form="fictional",
        agreement_status="confirmed",
        source="manual",
        controller_nc_class=9,
    )
    uncertain_link = ConcordLink(
        id="cl",
        segment_id="u1",
        controller_token_id="stem",
        concord_token_id="adj",
        concord_type="AC",
        observed_form="fictional",
        agreement_status="uncertain",
        source="manual",
        controller_nc_class=9,
    )

    assert integration_score(stem, [uncertain_link], frequency, threshold) <= integration_score(
        stem,
        [confirmed_link],
        frequency,
        threshold,
    )
