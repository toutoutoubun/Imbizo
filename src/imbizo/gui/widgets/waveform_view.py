"""Waveform view widget factory."""

from __future__ import annotations

from typing import Any


class WaveformView:
    """Waveform display and click-to-play segment interaction."""

    def build(self) -> Any:
        """Build and return a PySide6 widget."""

        from PySide6.QtWidgets import QLabel

        return QLabel("Waveform")
