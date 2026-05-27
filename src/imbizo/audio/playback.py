"""Local playback controller."""

from __future__ import annotations

from pathlib import Path


class PlaybackController:
    """Control local audio playback for selected segments."""

    def __init__(self) -> None:
        self.current_media_path: Path | None = None
        self.start_ms: int | None = None
        self.end_ms: int | None = None
        self.is_playing = False

    def play(self, media_path: Path, start_ms: int | None = None, end_ms: int | None = None) -> None:
        """Play a local media segment."""
        self.current_media_path = media_path
        self.start_ms = start_ms
        self.end_ms = end_ms
        self.is_playing = True

    def pause(self) -> None:
        """Pause playback."""
        self.is_playing = False

    def stop(self) -> None:
        """Stop playback."""
        self.is_playing = False
        self.current_media_path = None
        self.start_ms = None
        self.end_ms = None
