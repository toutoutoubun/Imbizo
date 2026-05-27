from pathlib import Path

from imbizo.core.annotation import Token
from imbizo.core.mixed_code import detect_mixed_code_spans, load_mixed_code_dictionary


ROOT = Path(__file__).resolve().parents[1]


def test_clearly_tsotsitaal_span_returns_candidate() -> None:
    dictionary = load_mixed_code_dictionary(ROOT / "dictionaries/mixed_code/tsotsitaal.yaml")
    tokens = [
        Token(id="t1", surface="heita", position=0),
        Token(id="t2", surface="kasi", position=1),
        Token(id="t3", surface="dladla", position=2),
    ]
    candidates = detect_mixed_code_spans(tokens, "tsotsitaal", dictionary, threshold=0.4)
    assert candidates
    assert candidates[0].confidence > 0.4
    assert "does not identify a speaker" in candidates[0].warning


def test_ambiguous_span_with_one_marker_does_not_over_fire() -> None:
    dictionary = load_mixed_code_dictionary(ROOT / "dictionaries/mixed_code/tsotsitaal.yaml")
    tokens = [
        Token(id="t1", surface="heita", position=0),
        Token(id="t2", surface="ordinary", position=1),
        Token(id="t3", surface="words", position=2),
    ]
    assert detect_mixed_code_spans(tokens, "tsotsitaal", dictionary, threshold=0.4) == []


def test_non_tsotsitaal_span_returns_empty() -> None:
    dictionary = load_mixed_code_dictionary(ROOT / "dictionaries/mixed_code/tsotsitaal.yaml")
    tokens = [Token(id="t1", surface="plain", position=0), Token(id="t2", surface="interview", position=1)]
    assert detect_mixed_code_spans(tokens, "tsotsitaal", dictionary, threshold=0.4) == []
