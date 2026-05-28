import sqlite3

import pytest

from imbizo.gui.annotation_editor.highlight_coding import BulkEditCommand, HighlightMode, HighlightToken, _colour_for_token
from imbizo.core.visualisation.palette import LanguagePalette


def test_accessible_name_contains_all_dimensions() -> None:
    token = HighlightToken("t1", "manager", language="eng", four_m_type="content", switch_type="intra_sentential", trigger_role="trigger")
    name = token.accessible_name()
    assert "manager language eng" in name
    assert "4-M content" in name
    assert "trigger trigger" in name


def test_mode_switch_colour_logic() -> None:
    token = HighlightToken("t1", "manager", language="eng", trigger_role="trigger", integration_score=0.8)
    palette = LanguagePalette()
    assert _colour_for_token(token, HighlightMode.LANGUAGE, palette) == palette.colour_for("eng")
    assert _colour_for_token(token, HighlightMode.TRIGGER_ROLE, palette) == "#E69F00"
    assert _colour_for_token(token, HighlightMode.INTEGRATION_SCORE, palette) == "#009E73"


def test_bulk_edit_persists_and_undoes() -> None:
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE tokens (id TEXT PRIMARY KEY, four_m_type TEXT, trigger_role TEXT, mixed_code_variety TEXT, phon_integration_score REAL)")
    conn.execute("CREATE TABLE annotations (id TEXT PRIMARY KEY, token_id TEXT, source TEXT, status TEXT, language_id TEXT, switch_type TEXT, memo TEXT, created_at TEXT, updated_at TEXT)")
    conn.execute("INSERT INTO tokens (id) VALUES ('t1')")
    command = BulkEditCommand(conn, ["t1"], {"trigger_role": "trigger"})
    command.apply()
    assert conn.execute("SELECT trigger_role FROM tokens WHERE id='t1'").fetchone()[0] == "trigger"
    command.undo()
    assert conn.execute("SELECT trigger_role FROM tokens WHERE id='t1'").fetchone()[0] is None


def test_qt_editor_builds_when_pyside_available() -> None:
    pytest.importorskip("PySide6")
    from imbizo.gui.annotation_editor.highlight_coding import HighlightCodingEditor

    editor = HighlightCodingEditor()
    editor.set_tokens([HighlightToken("t1", "hello", language="eng")])
    widget = editor.build()
    assert widget is not None
