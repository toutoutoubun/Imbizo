from pathlib import Path

from imbizo.core.annotation import Project, Token
from imbizo.core.interop.chat_clan import to_chat, validate_chat


def _project() -> Project:
    return Project(
        "p1",
        "Fictional Project",
        [
            Token("t1", "sawubona", "u1", 1, "zul", speaker_id="S01", nc_class=1, four_m_type="content"),
            Token("t2", "manager", "u1", 2, "eng", speaker_id="S01", trigger_role="trigger", phon_integration_score=0.4),
        ],
        metadata={"media_filename": "interview.wav", "description": "fictional example"},
    )


def test_chat_file_report_and_losses(tmp_path: Path) -> None:
    report = to_chat(_project(), tmp_path / "sample.cha")
    assert not isinstance(report, str)
    text = report.output_path.read_text(encoding="utf-8")
    assert "@Begin" in text
    assert "@Languages:\teng, zul" in text
    assert "*S01:\t" in text
    assert "%mor:" in text
    assert "%xcom:\tIMBIZO-CS:" in text
    assert report.losses_path.exists()


def test_chat_validator_accepts_export() -> None:
    text = to_chat(_project())
    assert isinstance(text, str)
    report = validate_chat(text)
    assert report.valid
    assert report.documented_losses


def test_chat_file_export_is_ascii_safe_by_default(tmp_path: Path) -> None:
    project = Project("p2", "Unicode Fixture", [Token("t1", "café", "u1", 1, "eng", speaker_id="S01")])
    report = to_chat(project, tmp_path / "unicode.cha")
    assert not isinstance(report, str)
    raw = report.output_path.read_bytes()
    raw.decode("ascii")
    assert b"caf&#233;" in raw
