"""Provenance service."""

from __future__ import annotations

import json

from imbizo.domain.project import ProjectContext
from imbizo.domain.provenance import ProvenanceRecord
from imbizo.persistence.repositories import ProvenanceRepository


class ProvenanceService:
    """Coordinate provenance recording and audit lookup."""

    def record(self, context: ProjectContext, record: ProvenanceRecord) -> None:
        """Persist a provenance record."""

        ProvenanceRepository(context.connection).save(record)
        log_path = context.paths.logs / "provenance.jsonl"
        payload = {
            "id": record.id,
            "event_type": record.event_type,
            "actor_type": record.actor_type,
            "target_table": record.target_table,
            "target_id": record.target_id,
            "tool_name": record.tool_name,
            "message": record.message,
            "payload": record.payload,
            "created_at": record.created_at,
        }
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def list_for_target(self, context: ProjectContext, target_table: str, target_id: str) -> list[ProvenanceRecord]:
        """Return provenance records for one target object."""

        return ProvenanceRepository(context.connection).list_for_target(target_table, target_id)
