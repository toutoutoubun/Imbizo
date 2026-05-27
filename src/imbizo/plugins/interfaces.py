"""Plugin protocol definitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol


@dataclass(slots=True)
class AsrOptions:
    """Options for optional local ASR plugins."""

    language_hints: list[str] = field(default_factory=list)


@dataclass(slots=True)
class PluginDescriptor:
    """Metadata for one optional local plugin."""

    name: str
    provider_type: str
    version: str
    enabled: bool = False
    local_only: bool = True
    description: str = ""
    provider: object | None = None


class AsrProvider(Protocol):
    """Optional local ASR provider."""

    def transcribe(self, media_path: Path, options: AsrOptions) -> Any:
        """Transcribe local media into transcript data."""
