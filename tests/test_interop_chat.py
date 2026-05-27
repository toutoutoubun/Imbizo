from imbizo.core.annotation import Project, Token
from imbizo.core.interop.chat_clan import to_chat, validate_chat


def test_chat_export_validates_offline() -> None:
    project = Project("p1", "Fictional Project", [Token(id="t1", surface="hello", utterance_id="u1", language="eng", speaker_id="S01")])
    text = to_chat(project)
    report = validate_chat(text)
    assert report.valid
    assert "%ximb:" in text


def test_chat_validator_catches_missing_markers() -> None:
    report = validate_chat("*SP01:\thello .\n")
    assert not report.valid
