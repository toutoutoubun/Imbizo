from pathlib import Path

from imbizo.core.annotation import Project, Token
from imbizo.core.interop.lides import parse_lides, to_lides, validate_lides


def _project() -> Project:
    return Project(
        "p1",
        "Fictional isiZulu-English interview",
        [
            Token("t1", "ngi", "u1", 1, "zul", speaker_id="S01", nc_class=1, four_m_type="early_system"),
            Token("t2", "laptop", "u1", 2, "eng", speaker_id="S01", trigger_role="trigger"),
        ],
    )


def test_lides_file_report_and_losses(tmp_path: Path) -> None:
    report = to_lides(_project(), tmp_path / "sample.lides")
    assert not isinstance(report, str)
    assert report.output_path.exists()
    assert report.losses_path.exists()
    text = report.output_path.read_text(encoding="utf-8")
    assert "LIDES VERSION: 1.0" in text
    assert "PROJECT-LANGUAGES: eng, zul" in text
    assert "TOK\tt1" in text
    assert "PRINCIPLES.md Part II" in report.losses_path.read_text(encoding="utf-8")


def test_lides_validator_and_parse_round_trip() -> None:
    text = to_lides(_project())
    assert isinstance(text, str)
    validation = validate_lides(text)
    assert validation.valid
    rows = parse_lides(text)
    assert rows[0]["token_id"] == "t1"
    assert rows[0]["language"] == "zul"
