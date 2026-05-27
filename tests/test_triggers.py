from pathlib import Path
import sqlite3

from imbizo.core.annotation import Token
from imbizo.core.triggers import TriggerLink, find_trigger_candidates, load_trigger_dictionary, persist_trigger_link


ROOT = Path(__file__).resolve().parents[1]


def test_proper_noun_trigger_before_switch() -> None:
    load_trigger_dictionary(ROOT / "dictionaries/triggers/eng.yaml")
    tokens = [
        Token(id="t1", surface="Johannesburg", position=0, language="eng"),
        Token(id="t2", surface="ngithe", position=1, language="zul"),
    ]
    candidates = find_trigger_candidates(tokens, switch_index=1, window_left=1)
    assert candidates
    assert candidates[0].head_token_id == "t1"
    assert candidates[0].triggered_token_id == "t2"
    assert candidates[0].trigger_type == "proper_noun"


def test_borrowing_trigger_persistence() -> None:
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE tokens (id TEXT PRIMARY KEY, trigger_role TEXT)")
    conn.execute(
        "CREATE TABLE trigger_links (head_token_id TEXT, triggered_token_id TEXT, trigger_type TEXT, confidence REAL, source TEXT, note TEXT, created_at TEXT, PRIMARY KEY (head_token_id, triggered_token_id, trigger_type))"
    )
    conn.executemany("INSERT INTO tokens (id) VALUES (?)", [("t1",), ("t2",)])
    persist_trigger_link(conn, TriggerLink("t1", "t2", "borrowing", 0.7, "manual"))
    assert conn.execute("SELECT trigger_role FROM tokens WHERE id='t1'").fetchone()[0] == "trigger"
    assert conn.execute("SELECT COUNT(*) FROM trigger_links").fetchone()[0] == 1
