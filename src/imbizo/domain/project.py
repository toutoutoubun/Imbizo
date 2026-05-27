"""Project metadata and paths."""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path


Id = str


@dataclass(slots=True)
class ProjectMetadata:
    """Human-readable metadata for one local research project."""

    project_uuid: Id
    title: str
    subtitle: str = ""
    researcher: str = ""
    institution: str = ""
    location: str = ""
    project_date: str = ""
    participants_summary: str = ""
    expected_languages_summary: str = ""
    ethics_notes: str = ""
    irb_rec_reference: str = ""
    care_acknowledgement: str = ""
    consent_status: str = ""
    data_sharing_constraints: str = ""
    app_version: str = ""
    schema_version: int = 1
    created_at: str = ""
    updated_at: str = ""


@dataclass(slots=True)
class ProjectPaths:
    """Standard local paths inside a project folder."""

    root: Path
    database: Path
    project_json: Path
    media_audio: Path
    media_video: Path
    extracted_audio: Path
    transcripts_source: Path
    transcripts_normalized: Path
    transcripts_snapshots: Path
    dictionaries: Path
    morphology_dictionaries: Path
    imports_original: Path
    import_reports: Path
    exports: Path
    logs: Path
    cache: Path
    waveform_cache: Path

    @classmethod
    def from_root(cls, root: Path) -> "ProjectPaths":
        """Build standard project paths from a project root."""

        root = root.expanduser().resolve()
        return cls(
            root=root,
            database=root / "project.sqlite",
            project_json=root / "project.json",
            media_audio=root / "media" / "audio",
            media_video=root / "media" / "video",
            extracted_audio=root / "media" / "extracted_audio",
            transcripts_source=root / "transcripts" / "source",
            transcripts_normalized=root / "transcripts" / "normalized",
            transcripts_snapshots=root / "transcripts" / "snapshots",
            dictionaries=root / "dictionaries",
            morphology_dictionaries=root / "dictionaries" / "morphology",
            imports_original=root / "imports" / "original_copies",
            import_reports=root / "imports" / "import_reports",
            exports=root / "exports",
            logs=root / "logs",
            cache=root / "cache",
            waveform_cache=root / "cache" / "waveform_peaks",
        )

    def ensure_all(self) -> None:
        """Create all standard project directories."""

        for path in (
            self.root,
            self.media_audio,
            self.media_video,
            self.extracted_audio,
            self.transcripts_source,
            self.transcripts_normalized,
            self.transcripts_snapshots,
            self.dictionaries,
            self.morphology_dictionaries,
            self.imports_original,
            self.import_reports,
            self.exports / "csv",
            self.exports / "xlsx",
            self.exports / "json",
            self.exports / "elan",
            self.exports / "praat",
            self.exports / "html",
            self.exports / "pdf",
            self.exports / "quotations",
            self.logs,
            self.cache,
            self.waveform_cache,
        ):
            path.mkdir(parents=True, exist_ok=True)


@dataclass(slots=True)
class ProjectContext:
    """Service-facing context for an open project."""

    paths: ProjectPaths
    metadata: ProjectMetadata
    connection: sqlite3.Connection


def make_project_slug(title: str) -> str:
    """Return a filesystem-friendly project slug."""

    slug = re.sub(r"[^A-Za-z0-9]+", "_", title.strip()).strip("_").lower()
    return slug or "imbizo_project"
