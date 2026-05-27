"""Export record models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ExportRecord:
    """A local export produced by the researcher."""

    id: str
    export_format: str
    relative_path: str
    options: dict[str, Any] = field(default_factory=dict)
    sha256: str = ""
    created_at: str = ""
