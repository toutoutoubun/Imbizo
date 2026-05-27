import pytest

from imbizo.core.annotation import ConcordLink, Token
from imbizo.core.integration_v2 import (
    DEFAULT_WEIGHTS_V2,
    PhonologicalFeature,
    integration_score_v2,
)

try:
    from hypothesis import given, strategies as st
except Exception:  # pragma: no cover - environment-dependent optional dev dependency
    given = None
    st = None


def test_default_weights_sum_to_one() -> None:
    total = (
        DEFAULT_WEIGHTS_V2.class_prefix
        + DEFAULT_WEIGHTS_V2.concord_links
        + DEFAULT_WEIGHTS_V2.inflection
        + DEFAULT_WEIGHTS_V2.phonology
        + DEFAULT_WEIGHTS_V2.frequency
    )
    assert total == pytest.approx(1.0)


if given is not None and st is not None:

    @given(
        has_prefix=st.booleans(),
        concord_conf=st.floats(min_value=0.0, max_value=1.0),
        frequency=st.integers(min_value=0, max_value=20),
        threshold=st.integers(min_value=1, max_value=20),
        has_phonology=st.booleans(),
    )
    def test_score_is_in_unit_interval(
        has_prefix: bool,
        concord_conf: float,
        frequency: int,
        threshold: int,
        has_phonology: bool,
    ) -> None:
        token = Token(
            id="loan",
            surface="i-laptop",
            nc_class=9 if has_prefix else None,
            nc_prefix="i-" if has_prefix else None,
        )
        links = [ConcordLink("loan", "adj", "AC", concord_conf)] if concord_conf > 0 else []
        features = [
            PhonologicalFeature("p1", "loan", "vowel_epenthesis", "initial_i", "manual")
        ] if has_phonology else []
        result = integration_score_v2(token, links, features, frequency, threshold)
        assert 0.0 <= result.score <= 1.0

    @given(frequency=st.integers(min_value=1, max_value=20), threshold=st.integers(min_value=1, max_value=20))
    def test_removing_evidence_never_increases_score(frequency: int, threshold: int) -> None:
        token = Token(id="loan", surface="i-laptop", nc_class=9, nc_prefix="i-")
        full = integration_score_v2(
            token,
            [ConcordLink("loan", "adj", "AC", 1.0)],
            [PhonologicalFeature("p1", "loan", "vowel_epenthesis", "initial_i", "manual")],
            frequency,
            threshold,
        )
        reduced = integration_score_v2(Token(id="loan", surface="laptop"), [], [], frequency, threshold)
        assert reduced.score <= full.score
else:

    @pytest.mark.skip(reason="hypothesis is not installed in this environment")
    def test_score_is_in_unit_interval() -> None:
        pass

    @pytest.mark.skip(reason="hypothesis is not installed in this environment")
    def test_removing_evidence_never_increases_score() -> None:
        pass
