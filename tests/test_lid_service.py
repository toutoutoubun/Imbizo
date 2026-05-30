"""Tests for local LID service behaviour."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Sequence

from imbizo.domain.annotations import AnnotationDraft
from imbizo.domain.project import ProjectMetadata
from imbizo.lid.baseline import BaselineLidProvider
from imbizo.lid.providers import LanguageScore, LidOptions, LidProgress
from imbizo.services.annotation_service import AnnotationService
from imbizo.services.import_service import ImportService
from imbizo.services.lid_service import LidService
from imbizo.services.project_service import ProjectService


def _context_with_document(tmp_path: Path, text: str):
    source = tmp_path / "sample.txt"
    source.write_text(text, encoding="utf-8")
    context = ProjectService().create_project(tmp_path / "project", ProjectMetadata(project_uuid="", title="LID Test"))
    imported = ImportService().import_file(context, source)
    assert imported.bundle.document is not None
    return context, imported.bundle.document


def test_local_lid_applies_useful_labels_without_auto_unknown(tmp_path: Path) -> None:
    """Useful local labels are applied, while low-evidence Unknown stays advisory."""

    context, document = _context_with_document(tmp_path, "I went to the market 123\nngiyabonga friend\n")
    updates: list[LidProgress] = []

    report = LidService().run_lid_for_document_report(
        context,
        document.id,
        LidOptions(progress_callback=updates.append),
    )

    assert report.suggestions_count > 0
    assert report.auto_annotations_count >= 2
    assert report.skipped_unknown_count >= 1
    assert updates
    assert updates[-1].message == "Local LID complete"

    rows = context.connection.execute(
        """
        SELECT languages.code FROM annotations
        JOIN languages ON languages.id = annotations.language_id
        WHERE annotations.source = 'auto'
        """
    ).fetchall()
    auto_codes = {row["code"] for row in rows}
    assert "eng" in auto_codes
    assert "zul" in auto_codes
    assert "und" not in auto_codes


def test_local_lid_preserves_manual_labels(tmp_path: Path) -> None:
    """Manual annotations remain the effective annotation after Local LID."""

    context, document = _context_with_document(tmp_path, "I and the\n")
    annotation_service = AnnotationService()
    state = annotation_service.load_editor_state(context, document.id)
    first_token = state.rows[0].token
    xhosa = next(language for language in state.languages if language.code == "xho")
    manual = annotation_service.save_token_annotation(context, first_token.id, AnnotationDraft(language_id=xhosa.id, memo="manual check"))

    report = LidService().run_lid_for_document_report(context, document.id)

    assert report.preserved_manual_count >= 1
    auto_rows = context.connection.execute(
        "SELECT * FROM annotations WHERE token_id = ? AND source = 'auto'",
        (first_token.id,),
    ).fetchall()
    assert auto_rows == []
    state_after = annotation_service.load_editor_state(context, document.id)
    first_after = next(row for row in state_after.rows if row.token.id == first_token.id)
    assert first_after.annotation is not None
    assert first_after.annotation.id == manual.id


def test_local_lid_discovers_project_fasttext_model_and_maps_codes(tmp_path: Path, monkeypatch) -> None:
    """A local lid.176 model in project/models/lid is used without env vars."""

    class FakeFastTextModel:
        def predict(self, text: str, k: int) -> tuple[list[str], list[float]]:
            return ["__label__zu", "__label__en"][:k], [0.91, 0.05][:k]

    monkeypatch.setitem(sys.modules, "fasttext", SimpleNamespace(load_model=lambda path: FakeFastTextModel()))
    context, document = _context_with_document(tmp_path, "sawubona friend\n")
    model_dir = context.paths.root / "models" / "lid"
    model_dir.mkdir(parents=True)
    (model_dir / "lid.176.ftz").write_bytes(b"fake model")

    report = LidService().run_lid_for_document_report(context, document.id)

    assert report.provider_method == "fastText lid.176"
    rows = context.connection.execute(
        """
        SELECT languages.code FROM annotations
        JOIN languages ON languages.id = annotations.language_id
        WHERE annotations.source = 'auto'
        """
    ).fetchall()
    assert {row["code"] for row in rows} == {"zul"}


def test_baseline_lid_without_env_uses_heuristic_not_cwd(monkeypatch) -> None:
    """Unset model config must not treat the current directory as a model."""

    monkeypatch.delenv("IMBIZO_FASTTEXT_LID_MODEL", raising=False)
    provider = BaselineLidProvider()
    prediction = provider.predict(["hello"], LidOptions(max_languages=1))[0][0]

    assert prediction.language_code == "eng"
    assert prediction.evidence["method"] == "heuristic"


def test_heuristic_lid_handles_common_contractions_and_sesotho_markers(monkeypatch) -> None:
    """The no-model fallback should cover common transcript tokens."""

    monkeypatch.delenv("IMBIZO_FASTTEXT_LID_MODEL", raising=False)
    provider = BaselineLidProvider()

    predictions = provider.predict(
        ["I'm", "you're", "awake", "got", "questions", "ao", "tsalanang"],
        LidOptions(max_languages=1),
    )

    assert [scores[0].language_code for scores in predictions[:5]] == ["eng", "eng", "eng", "eng", "eng"]
    assert [scores[0].language_code for scores in predictions[5:]] == ["sot", "sot"]


def test_local_lid_labels_no_language_sentence_rows_with_context(tmp_path: Path) -> None:
    """Spreadsheet-style rows without language labels still receive useful LID."""

    context, document = _context_with_document(
        tmp_path,
        "I'm so glad you're awake I've got the best news ever\n"
        "my sources say she is alive\n",
    )

    report = LidService().run_lid_for_document_report(context, document.id)

    assert report.provider_method == "heuristic"
    assert report.auto_annotations_count >= 10
    rows = context.connection.execute(
        """
        SELECT tokens.token_text, languages.code FROM annotations
        JOIN tokens ON tokens.id = annotations.token_id
        JOIN languages ON languages.id = annotations.language_id
        WHERE annotations.source = 'auto'
        ORDER BY tokens.rowid
        """
    ).fetchall()
    auto_codes = {row["token_text"]: row["code"] for row in rows}
    assert auto_codes["I'm"] == "eng"
    assert auto_codes["you're"] == "eng"
    assert auto_codes["awake"] == "eng"
    assert auto_codes["sources"] == "eng"


def test_heuristic_lid_uses_packaged_dictionary_and_morphology_features(monkeypatch) -> None:
    """Packaged local dictionaries enrich the no-model fallback offline."""

    monkeypatch.delenv("IMBIZO_FASTTEXT_LID_MODEL", raising=False)
    provider = BaselineLidProvider()

    predictions = provider.predict(
        ["isikole", "isikolo", "motho", "sekolo", "ngifunda", "ndifunda", "walking"],
        LidOptions(max_languages=1),
    )

    assert predictions[0][0].language_code == "zul"
    assert predictions[1][0].language_code == "xho"
    assert predictions[2][0].language_code in {"sot", "tsn"}
    assert predictions[3][0].language_code in {"sot", "tsn"}
    assert predictions[4][0].language_code == "zul"
    assert predictions[5][0].language_code == "xho"
    assert predictions[6][0].language_code == "eng"
    assert any(
        str(item).startswith(("exact:packaged_", "prefix:packaged_", "suffix:packaged_"))
        for item in predictions[0][0].evidence["matched_evidence"]
    )


def test_heuristic_lid_uses_project_local_dictionary_override(tmp_path: Path, monkeypatch) -> None:
    """Project dictionaries can add local LID evidence without network access."""

    monkeypatch.delenv("IMBIZO_FASTTEXT_LID_MODEL", raising=False)
    dictionary = tmp_path / "dictionaries" / "triggers"
    dictionary.mkdir(parents=True)
    (dictionary / "sot.yaml").write_text(
        """
language_code: sot
language_name: Sesotho trigger candidates
trigger_candidates:
  domain_specific_borrowings:
    - form: "kgotso"
      trigger_type: "borrowing"
      verified: false
""",
        encoding="utf-8",
    )
    provider = BaselineLidProvider(search_roots=[tmp_path])

    prediction = provider.predict(["kgotso"], LidOptions(max_languages=1))[0][0]

    assert prediction.language_code == "sot"
    assert "exact:trigger_dictionary:domain_specific_borrowings:kgotso" in prediction.evidence["matched_evidence"]


class AmbiguousNguniProvider:
    """Small deterministic provider for coarse group gate regression tests."""

    @property
    def name(self) -> str:
        return "test-ambiguous-nguni"

    @property
    def version(self) -> str:
        return "0.1"

    def predict(self, texts: Sequence[str], options: LidOptions) -> list[list[LanguageScore]]:
        return [
            [
                LanguageScore("zul", 0.52, {"method": "fixture"}),
                LanguageScore("xho", 0.48, {"method": "fixture"}),
            ][: options.max_languages]
            for _text in texts
        ]


def test_coarse_group_gate_saves_suggestions_but_blocks_auto_annotation(tmp_path: Path) -> None:
    """Gated suggestions remain auditable while risky auto labels are withheld."""

    context, document = _context_with_document(tmp_path, "sawubona mhlobo\n")
    service = LidService()
    service.provider = AmbiguousNguniProvider()

    report = service.run_lid_for_document_report(context, document.id, LidOptions(max_languages=2, use_coarse_group_gate=True))

    assert report.coarse_group_gate_enabled is True
    assert report.coarse_group_gated_count >= 2
    assert report.coarse_group_ambiguous_count >= 2
    assert report.auto_annotations_count == 0
    suggestion_rows = context.connection.execute(
        "SELECT evidence_json FROM lid_suggestions WHERE token_id IS NOT NULL AND rank = 1 ORDER BY created_at"
    ).fetchall()
    assert suggestion_rows
    for row in suggestion_rows:
        evidence = json.loads(row["evidence_json"])
        gate = evidence["coarse_group_gate"]
        assert gate["top_group"] == "Nguni"
        assert gate["auto_apply_allowed"] is False
        assert gate["reason"] == "closely_related_language_group"

    annotation_rows = context.connection.execute("SELECT * FROM annotations WHERE source = 'auto'").fetchall()
    assert annotation_rows == []
    provenance_rows = context.connection.execute(
        "SELECT payload_json FROM provenance_records WHERE event_type = 'auto_label' ORDER BY created_at DESC LIMIT 1"
    ).fetchall()
    assert provenance_rows
    payload = json.loads(provenance_rows[0]["payload_json"])
    assert payload["coarse_group_gate_enabled"] is True
    assert payload["coarse_group_gated_count"] >= 2


def test_coarse_group_gate_off_preserves_existing_auto_annotation_behaviour(tmp_path: Path) -> None:
    """Default-off gate leaves existing Local LID auto-annotation semantics alone."""

    context, document = _context_with_document(tmp_path, "sawubona mhlobo\n")
    service = LidService()
    service.provider = AmbiguousNguniProvider()

    report = service.run_lid_for_document_report(context, document.id, LidOptions(max_languages=2))

    assert report.coarse_group_gate_enabled is False
    assert report.coarse_group_gated_count == 0
    assert report.auto_annotations_count >= 2
    suggestion_rows = context.connection.execute("SELECT evidence_json FROM lid_suggestions WHERE token_id IS NOT NULL").fetchall()
    assert suggestion_rows
    assert all("coarse_group_gate" not in json.loads(row["evidence_json"]) for row in suggestion_rows)


def test_coarse_group_gate_does_not_override_manual_annotation(tmp_path: Path) -> None:
    """Manual annotations stay authoritative even when gate evidence is present."""

    context, document = _context_with_document(tmp_path, "sawubona mhlobo\n")
    annotation_service = AnnotationService()
    state = annotation_service.load_editor_state(context, document.id)
    first_token = state.rows[0].token
    english = next(language for language in state.languages if language.code == "eng")
    manual = annotation_service.save_token_annotation(context, first_token.id, AnnotationDraft(language_id=english.id, memo="manual"))
    service = LidService()
    service.provider = AmbiguousNguniProvider()

    report = service.run_lid_for_document_report(context, document.id, LidOptions(max_languages=2, use_coarse_group_gate=True))

    assert report.preserved_manual_count >= 1
    state_after = annotation_service.load_editor_state(context, document.id)
    first_after = next(row for row in state_after.rows if row.token.id == first_token.id)
    assert first_after.annotation is not None
    assert first_after.annotation.id == manual.id
