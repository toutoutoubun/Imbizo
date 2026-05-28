from pathlib import Path
import sqlite3

from imbizo.core.annotation import Token
from imbizo.core.sister_lang import (
    SisterLangDisambiguator,
    disambiguate_sister_languages,
    load_sister_lang_dictionary,
    persist_sister_lang_verdict,
)


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


def test_disambiguator_strong_nguni_morphemes() -> None:
    disambiguator = SisterLangDisambiguator(ROOT / "dictionaries/sister_lang")
    zul = disambiguator.disambiguate(Token(id="z1", surface="ngi-hamba", position=1), [], ["zul", "xho"])
    xho = disambiguator.disambiguate(Token(id="x1", surface="ndi-hamba", position=1), [], ["zul", "xho"])
    assert zul.best_language == "zul"
    assert zul.confidence >= 0.8
    assert xho.best_language == "xho"
    assert xho.confidence >= 0.8


def test_disambiguator_ambiguous_shared_token_low_confidence() -> None:
    disambiguator = SisterLangDisambiguator(ROOT / "dictionaries/sister_lang")
    verdict = disambiguator.disambiguate(Token(id="s1", surface="ke", position=1), [], ["sot", "tsn"])
    assert verdict.best_language is None
    assert verdict.confidence < 0.7


def test_three_way_sotho_tswana_dictionary_uses_v1_schema() -> None:
    dictionary = load_sister_lang_dictionary(ROOT / "dictionaries/sister_lang/nso_vs_sot_vs_tsn.yaml")
    assert dictionary.languages == ["nso", "sot", "tsn"]
    verdict = disambiguate_sister_languages(
        Token(id="n1", surface="lefase", position=1),
        [],
        ["nso", "sot", "tsn"],
        {"nso_vs_sot_vs_tsn": dictionary},
    )
    assert verdict.ranked[0].language == "nso"
    assert verdict.confidence >= 0.7


def test_persist_verdict_handles_v1_5_nullable_columns_without_language_column() -> None:
    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE TABLE tokens (id TEXT PRIMARY KEY, sister_lang_confidence REAL, sister_lang_evidence TEXT)"
    )
    conn.execute("INSERT INTO tokens (id) VALUES ('tok1')")
    dictionary = load_sister_lang_dictionary(ROOT / "dictionaries/sister_lang/zul_vs_xho.yaml")
    verdict = disambiguate_sister_languages(
        Token(id="tok1", surface="ndi-hamba", position=1),
        [],
        ["zul", "xho"],
        {"zul_vs_xho": dictionary},
    )
    persist_sister_lang_verdict(conn, "tok1", verdict)
    row = conn.execute("SELECT sister_lang_confidence, sister_lang_evidence FROM tokens WHERE id = 'tok1'").fetchone()
    assert row[0] == verdict.confidence
    assert "xho" in row[1]
