from imbizo.core.annotation import Project, Token
from imbizo.core.interop.lides import to_lides, validate_lides


def test_lides_export_validates_and_documents_loss() -> None:
    project = Project("p1", "Fictional Project", [Token(id="t1", surface="hello", utterance_id="u1", language="eng")])
    text = to_lides(project)
    report = validate_lides(text)
    assert report.valid
    assert report.documented_losses


def test_lides_validator_catches_malformed_text() -> None:
    report = validate_lides("not lides\n")
    assert not report.valid
