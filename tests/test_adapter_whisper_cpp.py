"""Tests for optional whisper.cpp adapter."""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.adapters.whisper_cpp import WhisperCppAdapter


def test_whisper_cpp_refuses_without_explicit_opt_in(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """whisper.cpp cannot be installed without both opt-in gates."""

    raw = tmp_path / "whisper.tar"
    raw.write_text("fixture", encoding="utf-8")
    monkeypatch.delenv("IMBIZO_ASR_ACCEPTED", raising=False)
    with pytest.raises(ValueError, match="opt-in"):
        WhisperCppAdapter().convert(raw, [tmp_path / "processing" / "whisper_cpp"], {"id": "whisper_cpp_optional"})
    with pytest.raises(ValueError, match="IMBIZO_ASR_ACCEPTED"):
        WhisperCppAdapter().convert(raw, [tmp_path / "processing" / "whisper_cpp"], {"id": "whisper_cpp_optional", "include_asr": True})
