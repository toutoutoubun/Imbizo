"""Tests for v1.0 concord candidate detection and scoring."""

from __future__ import annotations

import pytest

from imbizo.core.concord import ConcordLink, find_concord_candidates, integration_score
from imbizo.domain.transcripts import Token


def _token(identifier: str, text: str, order: int) -> Token:
    return Token(id=identifier, segment_id="u1", sort_order=order, token_text=text)


def test_zulu_fictional_adjectival_concord_candidate() -> None:
    """# fictional test data: confirms pure string matching for entsha."""

    tokens = [
        _token("t1", "Ngithenge", 1),
        _token("t2", "i-laptop", 2),
        _token("t3", "entsha", 3),
        _token("t4", "izolo", 4),
    ]

    candidates = find_concord_candidates(tokens, head_token_index=1, head_class=9, language_code="zul")

    assert any(candidate.token_id == "t3" and candidate.concord_type == "AC" for candidate in candidates)
    assert all(0.0 <= candidate.confidence <= 1.0 for candidate in candidates)


def test_zulu_fictional_confirmed_agreement_chain_scores_high() -> None:
    """# fictional test data: a confirmed link should contribute to integration."""

    stem = _token("t2", "i-laptop", 2)
    links = [
        ConcordLink(
            id="cl1",
            segment_id="u1",
            controller_token_id="t2",
            concord_token_id="t3",
            concord_type="AC",
            controller_nc_class=9,
            expected_form="en-",
            observed_form="entsha",
            agreement_status="confirmed",
            source="manual",
        )
    ]

    assert integration_score(stem, links, project_frequency=5, project_threshold=5) == pytest.approx(1.0)
