"""Participants, speakers, and scenes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class Participant:
    """A research participant or described person in the project."""

    id: str
    participant_code: str
    display_name: str = ""
    role: str = ""
    demographics: dict[str, Any] = field(default_factory=dict)
    consent_status: str = ""
    notes: str = ""


@dataclass(slots=True)
class Speaker:
    """A speaker label used in transcript segments."""

    id: str
    label: str
    participant_id: str | None = None
    display_name: str = ""
    notes: str = ""


@dataclass(slots=True)
class Scene:
    """A scene, interview section, or analytical time span."""

    id: str
    name: str
    description: str = ""
    start_ms: int | None = None
    end_ms: int | None = None
    sort_order: int = 0
    notes: str = ""
