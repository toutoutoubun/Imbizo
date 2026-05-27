"""Provenance models."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from imbizo.app.time import utc_now


@dataclass(slots=True)
class ProvenanceRecord:
    """Auditable record of imports, auto labels, edits, metrics, and exports."""

    id: str
    event_type: str
    actor_type: str
    actor_name: str = ""
    target_table: str = ""
    target_id: str = ""
    related_table: str = ""
    related_id: str = ""
    tool_name: str = ""
    tool_version: str = ""
    confidence: float | None = None
    message: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""


def make_provenance_record(event_type: str, actor_type: str, target_id: str = "", **payload: object) -> ProvenanceRecord:
    """Create a provenance record with a generated ID and timestamp."""

    return ProvenanceRecord(
        id=str(uuid.uuid4()),
        event_type=event_type,
        actor_type=actor_type,
        target_id=target_id,
        payload=dict(payload),
        created_at=utc_now(),
    )
