"""Metric result models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class JobStatus(StrEnum):
    """Shared status for background work."""

    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(slots=True)
class MetricRun:
    """One metrics calculation run."""

    id: str
    formula_version: str
    status: JobStatus
    run_name: str = ""
    input_filter: dict[str, Any] = field(default_factory=dict)
    started_at: str = ""
    finished_at: str | None = None
    error_message: str = ""


@dataclass(slots=True)
class MetricResult:
    """One metric value scoped to a project, speaker, scene, segment, or filter."""

    id: str
    metric_run_id: str
    metric_name: str
    scope_type: str
    value: Any
    scope_id: str = ""
    input_count: int = 0
    created_at: str = ""
