"""Media asset models."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class MediaType(StrEnum):
    """Media classes supported by imports."""

    AUDIO = "audio"
    VIDEO = "video"


@dataclass(slots=True)
class MediaAsset:
    """A copied audio or video file inside the project folder."""

    id: str
    media_type: MediaType
    relative_path: str
    import_batch_id: str | None = None
    original_filename: str = ""
    file_format: str = ""
    mime_type: str = ""
    duration_ms: int | None = None
    sample_rate_hz: int | None = None
    channels: int | None = None
    sha256: str = ""
    notes: str = ""


def is_supported_audio_extension(path: Path) -> bool:
    """Return whether an audio file extension is supported."""

    return path.suffix.lower() in {".wav", ".mp3", ".flac"}


def is_supported_video_extension(path: Path) -> bool:
    """Return whether a video file extension is supported."""

    return path.suffix.lower() in {".mp4", ".mkv"}
