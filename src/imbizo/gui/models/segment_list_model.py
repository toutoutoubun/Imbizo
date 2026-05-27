"""Segment list model data adapter."""

from __future__ import annotations

from dataclasses import dataclass, field

from imbizo.domain.transcripts import TranscriptSegment


@dataclass(slots=True)
class SegmentListModel:
    """Data holder for transcript segment navigation."""

    segments: list[TranscriptSegment] = field(default_factory=list)

    def set_segments(self, segments: list[TranscriptSegment]) -> None:
        """Replace segment list."""

        self.segments = list(segments)
