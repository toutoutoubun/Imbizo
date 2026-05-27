"""Tests for offline bootstrap bundle safeguards."""

from __future__ import annotations

from pathlib import Path

import pytest
from click import ClickException

from tools.adapters.utils.provenance import sha256_of
from tools.bootstrap import _verify_bundle_checksums


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
