"""CPU-only audio inspection helpers."""

from __future__ import annotations

import wave
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class AudioInfo:
    """Basic audio metadata."""

    duration_ms: int | None
    sample_rate_hz: int | None
    channels: int | None


class AudioDecoder:
    """Local audio decoder."""

    def inspect(self, path: Path) -> AudioInfo:
        """Return duration, sample rate, and channels."""

        if path.suffix.lower() != ".wav":
            return AudioInfo(duration_ms=None, sample_rate_hz=None, channels=None)
        with wave.open(str(path), "rb") as handle:
            sample_rate = handle.getframerate()
            channels = handle.getnchannels()
            duration_ms = int(handle.getnframes() / sample_rate * 1000) if sample_rate else None
        return AudioInfo(duration_ms=duration_ms, sample_rate_hz=sample_rate, channels=channels)
