"""Audio metadata importer."""

from __future__ import annotations

import uuid
import wave
from pathlib import Path

from imbizo.domain.media import MediaAsset, MediaType
from imbizo.importers.base import ImportedBundle, ImportOptions


class AudioImporter:
    """Import audio metadata for WAV, MP3, and FLAC files."""

    name = "audio"

    def can_import(self, path: Path) -> bool:
        """Return whether this importer can parse a copied local file."""

        return path.suffix.lower() in {".wav", ".mp3", ".flac"}

    def import_file(self, path: Path, options: ImportOptions) -> ImportedBundle:
        """Inspect audio metadata without modifying the file."""

        sample_rate = None
        channels = None
        duration_ms = None
        if path.suffix.lower() == ".wav":
            with wave.open(str(path), "rb") as handle:
                sample_rate = handle.getframerate()
                channels = handle.getnchannels()
                duration_ms = int(handle.getnframes() / sample_rate * 1000) if sample_rate else None
        media = MediaAsset(
            id=str(uuid.uuid4()),
            media_type=MediaType.AUDIO,
            relative_path=str(path),
            original_filename=path.name,
            file_format=path.suffix.lower().lstrip("."),
            duration_ms=duration_ms,
            sample_rate_hz=sample_rate,
            channels=channels,
        )
        return ImportedBundle(media_assets=[media], report={"media_assets": 1})
