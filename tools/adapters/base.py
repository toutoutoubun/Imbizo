"""Base interface for dictionary bootstrap adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Mapping


class SourceAdapter(ABC):
    """Base class for dictionary source adapters.

    Implementations MUST:
    1. Read the verified, already-downloaded file at raw_path.
    2. Write one or more YAML files under output_dirs/.
    3. Include the standard provenance header in every output file.
    4. Mark all auto-converted entries `verified: false`.
    5. Never make network calls. Network access is the bootstrap CLI's
       responsibility, not the adapter's.
    """

    adapter_version: str = "0.1.0"

    @abstractmethod
    def convert(
        self,
        raw_path: Path,
        output_dirs: list[Path],
        source_metadata: Mapping[str, Any],
    ) -> list[Path]:
        """Return the list of output YAML files that were written."""

