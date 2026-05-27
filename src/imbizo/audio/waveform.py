"""Rebuildable waveform peak caches."""

from __future__ import annotations

import json
import wave
from dataclasses import dataclass
from pathlib import Path

from imbizo.domain.media import MediaAsset


@dataclass(slots=True)
class WaveformPeaks:
    """Downsampled waveform peak data."""

    peaks: list[float]


class WaveformCache:
    """Project-local waveform peak cache."""

    def ensure_peaks(self, media: MediaAsset, source_path: Path, cache_dir: Path) -> Path:
        """Create waveform peaks if missing and return the cache path."""

        cache_dir.mkdir(parents=True, exist_ok=True)
        target = cache_dir / f"{media.id}.json"
        if target.exists():
            return target
        peaks: list[float] = []
        if source_path.suffix.lower() == ".wav":
            with wave.open(str(source_path), "rb") as handle:
                frames = handle.readframes(handle.getnframes())
                sample_width = handle.getsampwidth()
                if sample_width == 2:
                    import array

                    samples = array.array("h")
                    samples.frombytes(frames)
                    step = max(1, len(samples) // 1000)
                    for index in range(0, len(samples), step):
                        window = samples[index:index + step]
                        peaks.append(max(abs(value) for value in window) / 32768 if window else 0.0)
        target.write_text(json.dumps({"peaks": peaks}), encoding="utf-8")
        return target

    def load_peaks(self, peaks_path: Path) -> WaveformPeaks:
        """Load cached waveform peaks."""

        data = json.loads(peaks_path.read_text(encoding="utf-8"))
        return WaveformPeaks(peaks=[float(value) for value in data.get("peaks", [])])
