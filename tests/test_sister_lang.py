from pathlib import Path

from imbizo.core.annotation import Token
from imbizo.core.sister_lang import disambiguate_sister_languages, load_sister_lang_dictionary


ROOT = Path(__file__).resolve().parents[1]


def test_zul_xho_ambiguous_token_gets_ranked_verdict() -> None:
    dictionary = load_sister_lang_dictionary(ROOT / "dictionaries/sister_lang/zul_vs_xho.yaml")
    token = Token(id="tok1", surface="ndi-hamba", position=1)
    verdict = disambiguate_sister_languages(
        token,
        [Token(id="ctx1", surface="molo", position=0, language="xho")],
        ["zul", "xho"],
        {"zul_vs_xho": dictionary},
    )
    assert verdict.ranked
    assert 0.0 <= verdict.confidence <= 1.0
    assert verdict.best_language in {"xho", None}
    assert "advisory" in verdict.narrative or "manual review" in verdict.narrative


def test_sot_tsn_shared_token_remains_conservative() -> None:
    dictionary = load_sister_lang_dictionary(ROOT / "dictionaries/sister_lang/sot_vs_tsn.yaml")
    token = Token(id="tok2", surface="ke", position=1)
    verdict = disambiguate_sister_languages(token, [], ["sot", "tsn"], {"sot_vs_tsn": dictionary})
    assert verdict.best_language is None
    assert verdict.ambiguous is True
