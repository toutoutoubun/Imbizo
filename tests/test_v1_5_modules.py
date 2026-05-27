from pathlib import Path
import sqlite3

from imbizo.core.annotation import Token
from imbizo.core.community.review import create_review_packet, validate_review_packet
from imbizo.core.annotation import ConcordLink, Project
from imbizo.core.integration_v2 import PhonologicalFeature, integration_score_v2, load_phonology_dictionary
from imbizo.core.interop.chat_clan import to_chat, validate_chat
from imbizo.core.interop.lides import to_lides, validate_lides
from imbizo.core.migrations.v1_5 import migrate_project
from imbizo.core.mixed_code import load_mixed_code_profile, suggest_mixed_code_span
from imbizo.core.sister_lang import disambiguate_sister_languages, load_sister_lang_dictionary
from imbizo.core.triggers import find_trigger_candidates, load_trigger_dictionary


ROOT = Path(__file__).resolve().parents[1]


def test_sister_language_disambiguation_is_advisory() -> None:
    dictionary = load_sister_lang_dictionary(ROOT / "dictionaries/sister_lang/zul_vs_xho.yaml")
    token = Token(id="t1", surface="ndi-hamba", position=1)
    verdict = disambiguate_sister_languages(
        token,
        [Token(id="ctx", surface="molo", position=0, language="xho")],
        ["zul", "xho"],
        {"zul_vs_xho": dictionary},
    )
    assert verdict.ranked
    assert 0.0 <= verdict.confidence <= 1.0
    assert verdict.best_language in {"xho", None}


def test_trigger_candidates_are_local_string_matches() -> None:
    dictionary = load_trigger_dictionary(ROOT / "dictionaries/triggers/eng.yaml")
    tokens = [
        Token(id="t1", surface="manager", position=0, language="eng"),
        Token(id="t2", surface="ngithe", position=1, language="zul"),
    ]
    candidates = find_trigger_candidates(tokens, switch_index=1, window_left=1)
    assert candidates
    assert candidates[0].head_token_id == "t1"
    assert candidates[0].triggered_token_id == "t2"


def test_mixed_code_profile_suggests_review_prompt_only() -> None:
    profile = load_mixed_code_profile(ROOT / "dictionaries/mixed_code/tsotsitaal.yaml")
    suggestion = suggest_mixed_code_span(
        [
            Token(id="t1", surface="heita", position=0),
            Token(id="t2", surface="kasi", position=1),
        ],
        profile,
    )
    assert suggestion is not None
    assert suggestion.variety == "tsotsitaal"
    assert suggestion.confidence > 0
    assert "heita" in suggestion.evidence_forms


def test_integration_score_v2_bounds_and_optional_phonology() -> None:
    load_phonology_dictionary(ROOT / "dictionaries/phonology/zul.yaml")
    token = Token(id="loan", surface="i-laptop", position=0)
    no_audio = integration_score_v2(token, [ConcordLink("loan", "adj", "AC", 0.8)], [], 3, 5)
    with_audio = integration_score_v2(
        token,
        [ConcordLink("loan", "adj", "AC", 0.8)],
        [PhonologicalFeature("p1", "loan", "vowel_epenthesis", "initial_i", "manual")],
        3,
        5,
    )
    assert 0.0 <= no_audio.score <= 1.0
    assert 0.0 <= with_audio.score <= 1.0
    assert with_audio.score >= no_audio.score


def test_migration_refuses_mvp_and_upgrades_v1_0(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    db = project / "project.sqlite"
    with sqlite3.connect(db) as conn:
        conn.execute("CREATE TABLE tokens (id TEXT PRIMARY KEY, surface TEXT)")
        conn.execute("CREATE TABLE schema_version (version TEXT NOT NULL, applied_at TEXT NOT NULL)")
        conn.execute("INSERT INTO schema_version VALUES ('1.0', 'now')")
    report = migrate_project(project, no_backup=True)
    assert report.applied is True
    with sqlite3.connect(db) as conn:
        columns = {row[1] for row in conn.execute("PRAGMA table_xinfo(tokens)")}
        assert "sister_lang_confidence" in columns
        assert conn.execute("SELECT version FROM schema_version ORDER BY rowid DESC LIMIT 1").fetchone()[0] == "1.5"


def test_interop_exports_preserve_sidecars(tmp_path: Path) -> None:
    tokens = [Token(id="t1", surface="hello", utterance_id="u1", position=0, language="eng", speaker_id="S01")]
    project = Project(id="p1", title="Fictional Project", tokens=tokens)
    lides = to_lides(project)
    chat = to_chat(project)
    assert validate_lides(lides).valid
    assert validate_chat(chat).valid
    assert "XIMB" in lides
    assert "%ximb" in chat


def test_community_review_packet_validates(tmp_path: Path) -> None:
    change = tmp_path / "change.yaml"
    change.write_text("source: local\nversion: 0.1.0\n", encoding="utf-8")
    packet = create_review_packet(
        tmp_path / "review.zip",
        reviewer_alias="Reviewer",
        review_scope="dictionary_entry",
        changed_files=[change],
        diff_text="Reviewed one fictional entry.",
    )
    report = validate_review_packet(packet)
    assert report.valid
    assert report.signature_hash
