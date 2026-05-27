"""Video metadata importer."""

from __future__ import annotations

import uuid
from pathlib import Path

from imbizo.domain.media import MediaAsset, MediaType
from imbizo.importers.base import ImportedBundle, ImportOptions


class VideoImporter:
    """Import basic video metadata for MP4 and MKV files."""

    name = "video"

    def can_import(self, path: Path) -> bool:
        """Return whether this importer can parse a copied local file."""

        return path.suffix.lower() in {".mp4", ".mkv"}

    def import_file(self, path: Path, options: ImportOptions) -> ImportedBundle:
        """Register video files for future audio-track workflows."""

        media = MediaAsset(
            id=str(uuid.uuid4()),
            media_type=MediaType.VIDEO,
            relative_path=str(path),
            original_filename=path.name,
            file_format=path.suffix.lower().lstrip("."),
        )
        return ImportedBundle(media_assets=[media], report={"media_assets": 1, "note": "Audio-track extraction is not bundled in the MVP."})
