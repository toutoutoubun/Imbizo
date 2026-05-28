"""Tests for offline bootstrap bundle safeguards."""

from __future__ import annotations

from pathlib import Path

import pytest
from click import ClickException

from tools.adapters.utils.provenance import sha256_of
from tools.bootstrap import _license_files_for_source, _verify_bundle_checksums, _verify_source_license_files


def test_verify_bundle_checksums_accepts_matching_files(tmp_path: Path) -> None:
    """A bundle checksum file must validate every listed raw artifact."""

    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    raw_file = raw_dir / "source.json"
    raw_file.write_text('{"ok": true}', encoding="utf-8")
    (tmp_path / "checksums.sha256").write_text(f"{sha256_of(raw_file)}  raw/source.json\n", encoding="utf-8")

    _verify_bundle_checksums(tmp_path)


def test_verify_bundle_checksums_rejects_mismatches(tmp_path: Path) -> None:
    """Offline reconstruction refuses corrupted bundle content."""

    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    (raw_dir / "source.json").write_text('{"ok": false}', encoding="utf-8")
    (tmp_path / "checksums.sha256").write_text(f"{'0' * 64}  raw/source.json\n", encoding="utf-8")

    with pytest.raises(ClickException, match="checksum verification failed"):
        _verify_bundle_checksums(tmp_path)


def test_source_license_files_reject_placeholders(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Bootstrap and bundle creation must not ship placeholder licence files."""

    licenses = tmp_path / "LICENSES"
    licenses.mkdir()
    (licenses / "CC-BY-4.0.txt").write_text(
        "CC-BY-4.0\n\nREPLACE THIS FILE WITH THE VERBATIM LICENSE TEXT FROM <url>\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("tools.bootstrap._license_files_for", lambda _: [licenses / "CC-BY-4.0.txt"])

    with pytest.raises(ClickException, match="still a placeholder"):
        _verify_source_license_files({"id": "fixture", "license": "CC-BY-4.0"})


def test_source_license_files_include_mixed_resource_licences() -> None:
    """Mixed manifests copy every required resource licence into bundles."""

    mafoko = _license_files_for_source(
        {"license": "Nwulite Obodo Open Data License 1.0 OR CC-BY-NC-SA 2.5 ZA"}
    )
    za_lex = _license_files_for_source({"license": "Apache-2.0 / MIT"})

    assert {path.name for path in mafoko} == {"NWULITE-OBODO-1.0.txt", "CC-BY-NC-SA-2.5-ZA.txt"}
    assert {path.name for path in za_lex} == {"APACHE-2.0.txt", "MIT.txt"}
