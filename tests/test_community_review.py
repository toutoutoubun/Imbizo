from pathlib import Path

from imbizo.core.annotation import Project, Token
from imbizo.core.community.review import export_review_packet, import_review_packet, validate_review_packet


def test_signature_verification(tmp_path: Path) -> None:
    project = Project("p1", "Fictional Project", [Token(id="t1", surface="hello")], project_path=str(tmp_path / "project"))
    packet = export_review_packet(project, ["dictionary_entry"], "Reviewer", tmp_path / "review.zip")
    report = validate_review_packet(packet)
    assert report.valid
    assert report.signature_hash


def test_import_review_packet_dry_run_pending(tmp_path: Path) -> None:
    project_path = tmp_path / "project"
    project_path.mkdir()
    project = Project("p1", "Fictional Project", [Token(id="t1", surface="hello")], project_path=str(project_path))
    packet = export_review_packet(project, ["dictionary_entry"], "Reviewer", tmp_path / "review.zip")
    result = import_review_packet(project, packet, auto_apply=False)
    assert result.pending_count == 1
    assert result.applied_count == 0
    assert not (project_path / "logs" / "provenance.jsonl").exists()


def test_import_review_packet_auto_apply_writes_provenance(tmp_path: Path) -> None:
    project_path = tmp_path / "project"
    project_path.mkdir()
    project = Project("p1", "Fictional Project", [Token(id="t1", surface="hello")], project_path=str(project_path))
    packet = export_review_packet(project, ["dictionary_entry"], "Reviewer", tmp_path / "review.zip")
    result = import_review_packet(project, packet, auto_apply=True)
    assert result.applied_count == 1
    assert result.provenance_event_written
    assert (project_path / "logs" / "provenance.jsonl").exists()
