# Deliverable 4: Module Breakdown

This document defines each planned MVP module's responsibility and public API.
It follows the architecture in [ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md),
the repository plan in [DIRECTORY_LAYOUT.md](DIRECTORY_LAYOUT.md), and the data
contract in [DATA_MODEL.md](DATA_MODEL.md).

The public APIs here are implementation targets for deliverable 6. They are not
expected to be complete forever, but they define the first stable boundaries.

## Public API Rules

- Public functions and classes must have type hints and docstrings.
- Public APIs should accept and return domain dataclasses where practical.
- GUI modules may depend on services; services must not depend on GUI modules.
- Importers and exporters must not show dialogs. They report structured results
  and plain-language errors through service layers.
- Persistence modules own SQLite details. Metrics, importers, exporters, and
  GUI models should not issue raw SQL.
- Optional plugins must be discovered through explicit registries and must not
  be imported during core startup unless enabled.
- No public API may require internet access for core MVP workflows.

## Shared Types

These shared type names should be used across module APIs:

```python
from pathlib import Path
from typing import Any, Protocol, Sequence

from imbizo.domain.annotations import Annotation
from imbizo.domain.languages import LanguageTag
from imbizo.domain.media import MediaAsset
from imbizo.domain.metrics import MetricResult, MetricRun
from imbizo.domain.morphology import MorphemeDictionaryEntry, MorphemeSplit
from imbizo.domain.project import ProjectContext, ProjectMetadata
from imbizo.domain.provenance import ProvenanceRecord
from imbizo.domain.transcripts import Token, TranscriptDocument, TranscriptSegment

Id = str
JsonObject = dict[str, Any]
```

`ProjectContext` is the service-facing handle for an open local project. It
contains the project folder path, database path, project metadata, and derived
standard subdirectories. It must not contain GUI objects.

## Dependency Summary

```text
main -> app, services, gui
gui -> app, services, domain
services -> app, domain, persistence, importers, exporters, lid, morphology, metrics, audio
persistence -> domain
importers -> domain
exporters -> domain
lid -> domain
morphology -> domain
metrics -> domain
audio -> domain
plugins -> domain
resources -> loaded by app/services/gui as data
```

## `src/imbizo/main.py`

Responsibility:

- Provide the executable entry point.
- Initialize local application settings and string resources.
- Create the Qt application and main window.
- Optionally open a project path passed on the command line.
- Return a process exit code.

Public API:

```python
def main(argv: Sequence[str] | None = None) -> int:
    """Launch Imbizo-CS Workbench and return a process exit code."""

def parse_args(argv: Sequence[str]) -> AppLaunchOptions:
    """Parse command-line launch options without performing side effects."""
```

No networking, telemetry, update checks, or account checks may occur here.

## `src/imbizo/app/`

The `app` package contains cross-cutting application helpers that are not
specific to one project, file format, metric, or screen.

### `app/errors.py`

Responsibility:

- Define error classes with user-facing plain-language messages.
- Preserve technical details for local logs without exposing stack traces as
  the default researcher-facing message.

Public API:

```python
class ImbizoError(Exception):
    """Base class for expected application errors."""

class UserFacingError(ImbizoError):
    """An error safe to show directly to a researcher."""

class ProjectError(UserFacingError):
    """A project creation, open, close, or archive error."""

class ImportFailure(UserFacingError):
    """An import failed without modifying the original source file."""

class ExportFailure(UserFacingError):
    """An export failed before producing a valid output file."""

class StorageError(UserFacingError):
    """A local SQLite or project-folder storage error."""

def explain_exception(error: BaseException) -> str:
    """Return a concise plain-language explanation for an exception."""
```

### `app/events.py`

Responsibility:

- Provide lightweight in-process events for UI refreshes and service progress.
- Avoid global mutable state where direct service calls are clearer.

Public API:

```python
class AppEvent:
    """A typed application event with a name and payload."""

class EventBus:
    """In-process publish/subscribe event dispatcher."""

    def subscribe(self, event_name: str, callback: EventCallback) -> Subscription:
        """Subscribe to an event and return a removable subscription."""

    def publish(self, event: AppEvent) -> None:
        """Publish an event to current subscribers."""
```

### `app/jobs.py`

Responsibility:

- Run slow local work away from the GUI thread.
- Provide progress and cancellation primitives for imports, waveform caching,
  LID, metrics, and export.

Public API:

```python
class CancellationToken:
    """Cooperative cancellation flag for local background jobs."""

    def cancel(self) -> None:
        """Request cancellation."""

    def is_cancelled(self) -> bool:
        """Return whether cancellation has been requested."""

class ProgressReporter:
    """Receives progress updates from background jobs."""

    def update(self, message: str, current: int | None = None, total: int | None = None) -> None:
        """Report job progress in researcher-readable terms."""

class JobRunner:
    """Run local jobs and marshal progress back to the caller."""

    def submit(self, name: str, job: JobCallable) -> JobHandle:
        """Submit a job and return a handle for progress and cancellation."""
```

### `app/settings.py`

Responsibility:

- Store app-level preferences that are not research data.
- Keep project data inside the project folder.

Public API:

```python
class AppSettings:
    """Local user preferences such as theme, font size, and recent projects."""

def load_app_settings(settings_path: Path | None = None) -> AppSettings:
    """Load local app settings from disk."""

def save_app_settings(settings: AppSettings, settings_path: Path | None = None) -> None:
    """Save local app settings without writing research data outside a project."""
```

### `app/strings.py`

Responsibility:

- Load externalized UI strings.
- Provide a fallback to English when a translation key is missing.

Public API:

```python
class StringCatalog:
    """Lookup table for localized UI strings."""

    def text(self, key: str, **values: object) -> str:
        """Return localized text for a key."""

def load_string_catalog(locale_code: str, resources_dir: Path) -> StringCatalog:
    """Load UI strings for a locale from bundled resource files."""
```

## `src/imbizo/domain/`

The `domain` package contains pure data models and small validation helpers. It
must not import PySide6, SQLite connection objects, pandas, file parsers, or
network libraries.

### `domain/project.py`

Responsibility:

- Define project metadata and open-project context.
- Define local project paths derived from the project folder.

Public API:

```python
class ProjectMetadata:
    """Human-readable metadata for one local research project."""

class ProjectPaths:
    """Standard local paths inside a project folder."""

    @classmethod
    def from_root(cls, root: Path) -> ProjectPaths:
        """Build standard project paths from a project root."""

class ProjectContext:
    """Service-facing context for an open project."""

def make_project_slug(title: str) -> str:
    """Return a filesystem-friendly project slug."""
```

### `domain/languages.py`

Responsibility:

- Define language tags and default language rows.
- Support user-defined varieties without requiring code changes.

Public API:

```python
class LanguageTag:
    """A project language, special label, or user-defined variety."""

def default_language_tags(now: str) -> list[LanguageTag]:
    """Return default language tags for a new project."""

def find_language_by_code(languages: Sequence[LanguageTag], code: str) -> LanguageTag | None:
    """Find a language tag by code."""

def sort_languages_for_legend(languages: Sequence[LanguageTag]) -> list[LanguageTag]:
    """Return languages in display order for the UI legend."""
```

### `domain/transcripts.py`

Responsibility:

- Define transcript documents, segments, and tokens.
- Preserve original text and optional normalized text separately.

Public API:

```python
class TranscriptDocument:
    """A transcript source or manually created transcript document."""

class TranscriptSegment:
    """A transcript segment at utterance or clause/phrase level."""

class Token:
    """A token belonging to a transcript segment."""

def split_tokens_preserving_offsets(text: str) -> list[TokenDraft]:
    """Split text into token drafts while preserving character offsets."""

def segment_duration_ms(segment: TranscriptSegment) -> int | None:
    """Return segment duration when start and end times are available."""
```

### `domain/annotations.py`

Responsibility:

- Define annotation records, annotation statuses, switch types, and helper
  rules for effective annotation selection.

Public API:

```python
class Annotation:
    """Manual, automatic, or imported linguistic annotation."""

class AnnotationDraft:
    """Editable annotation input before storage assigns an ID."""

def validate_annotation_target(token_id: Id | None, segment_id: Id | None) -> None:
    """Require exactly one token or segment target."""

def choose_effective_annotation(annotations: Sequence[Annotation]) -> Annotation | None:
    """Apply the effective annotation rule for one token or segment."""
```

### `domain/media.py`

Responsibility:

- Define audio and video asset metadata.
- Keep file paths relative to the project folder.

Public API:

```python
class MediaAsset:
    """A copied audio or video file inside the project folder."""

def is_supported_audio_extension(path: Path) -> bool:
    """Return whether an audio file extension is supported."""

def is_supported_video_extension(path: Path) -> bool:
    """Return whether a video file extension is supported."""
```

### `domain/morphology.py`

Responsibility:

- Define editable morphology dictionary entries and token splits.
- Represent suggestions as suggestions, never forced analyses.

Public API:

```python
class MorphemeDictionaryEntry:
    """Editable local morphology dictionary entry."""

class MorphemeSplit:
    """A manual or suggested token-level morpheme segmentation."""

class Morpheme:
    """One morpheme inside a token split."""

def parse_split_text(split_text: str) -> list[str]:
    """Parse researcher-entered split text into morpheme surfaces."""
```

### `domain/metrics.py`

Responsibility:

- Define metric run and result records.
- Keep formulas implemented in `metrics/`, not in domain objects.

Public API:

```python
class MetricRun:
    """One metrics calculation run."""

class MetricResult:
    """One metric value scoped to a project, speaker, scene, segment, or filter."""
```

### `domain/provenance.py`

Responsibility:

- Define auditable provenance records for imports, automatic suggestions,
  manual edits, metrics, exports, and errors.

Public API:

```python
class ProvenanceRecord:
    """Auditable record of imports, auto labels, edits, metrics, and exports."""

def make_provenance_record(event_type: str, actor_type: str, target_id: str = "", **payload: object) -> ProvenanceRecord:
    """Create a provenance record with a generated ID and timestamp."""
```

## `src/imbizo/persistence/`

The `persistence` package is the only package that should know the SQLite schema
in detail. It converts rows to and from domain dataclasses.

### `persistence/connection.py`

Responsibility:

- Open SQLite databases with foreign keys enabled.
- Provide transaction helpers.
- Keep database paths inside the selected project folder.

Public API:

```python
def open_project_database(database_path: Path) -> sqlite3.Connection:
    """Open a project SQLite database with required pragmas."""

def transaction(connection: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    """Run a commit-or-rollback transaction."""
```

### `persistence/migrations.py`

Responsibility:

- Create and migrate project databases.
- Seed default language rows.

Public API:

```python
CURRENT_SCHEMA_VERSION: int

def initialize_database(connection: sqlite3.Connection, metadata: ProjectMetadata) -> None:
    """Create a new project database and seed required rows."""

def migrate_database(connection: sqlite3.Connection) -> None:
    """Apply pending migrations to an existing project database."""

def get_schema_version(connection: sqlite3.Connection) -> int:
    """Return the current project database schema version."""
```

### `persistence/repositories.py`

Responsibility:

- Provide repository classes for structured reads and writes.
- Hide raw SQL from services.
- Preserve manual annotations when applying automatic suggestions.

Public API:

```python
class ProjectRepository:
    """Read and write project metadata and settings."""

    def get_metadata(self) -> ProjectMetadata:
        """Return project metadata."""

    def update_metadata(self, metadata: ProjectMetadata) -> None:
        """Replace project metadata."""

class LanguageRepository:
    """Read and write project language tags."""

    def list_languages(self) -> list[LanguageTag]:
        """Return all project language tags."""

    def save_language(self, language: LanguageTag) -> None:
        """Create or update a language tag."""

class TranscriptRepository:
    """Read and write transcript documents, segments, and tokens."""

    def list_documents(self) -> list[TranscriptDocument]:
        """Return transcript documents."""

    def list_segments(self, document_id: Id) -> list[TranscriptSegment]:
        """Return segments for a transcript document."""

    def list_tokens(self, segment_id: Id) -> list[Token]:
        """Return tokens for one segment."""

    def save_document_bundle(self, document: TranscriptDocument, segments: Sequence[TranscriptSegment], tokens: Sequence[Token]) -> None:
        """Persist one imported transcript bundle."""

class AnnotationRepository:
    """Read and write annotations and tags."""

    def get_effective_annotation_for_token(self, token_id: Id) -> Annotation | None:
        """Return the effective annotation for one token."""

    def save_manual_annotation(self, annotation: Annotation) -> None:
        """Save a manual annotation and supersede older active manual annotations."""

    def save_auto_annotation(self, annotation: Annotation) -> None:
        """Save an automatic annotation without replacing manual work."""

    def bulk_update_annotations(self, annotations: Sequence[Annotation]) -> None:
        """Apply a researcher-approved bulk annotation update."""

class MorphologyRepository:
    """Read and write morphology dictionaries and morpheme splits."""

class LidRepository:
    """Read and write LID runs and suggestions."""

class MetricRepository:
    """Read and write metric runs and results."""

class ProvenanceRepository:
    """Read and write provenance records."""

class ExportRepository:
    """Read and write export records."""
```

## `src/imbizo/services/`

Services coordinate user-level actions. They own transaction boundaries,
plain-language error mapping, and provenance creation. Services return domain
objects or service result dataclasses that GUI models can display.

### `services/project_service.py`

Responsibility:

- Create, open, close, zip-export, and zip-import local projects.
- Ensure project folder structure exists.
- Never store research data outside the project folder except explicit exports.

Public API:

```python
class ProjectService:
    """Coordinate local project lifecycle operations."""

    def create_project(self, root: Path, metadata: ProjectMetadata) -> ProjectContext:
        """Create a project folder, database, and standard subdirectories."""

    def open_project(self, root: Path) -> ProjectContext:
        """Open an existing local project folder."""

    def close_project(self, context: ProjectContext) -> None:
        """Close local resources for an open project."""

    def export_project_zip(self, context: ProjectContext, destination: Path) -> Path:
        """Write a local zip archive containing the project folder contents."""

    def import_project_zip(self, archive_path: Path, destination_root: Path) -> ProjectContext:
        """Import a local project zip into a new project folder."""
```

### `services/import_service.py`

Responsibility:

- Select the right importer for a source file.
- Copy source files into the project folder before parsing.
- Write import batches, transcript records, media records, and provenance.

Public API:

```python
class ImportService:
    """Coordinate safe local imports."""

    def list_supported_formats(self) -> list[str]:
        """Return supported import format names."""

    def import_file(self, context: ProjectContext, source_path: Path, options: ImportOptions) -> ImportResult:
        """Copy and import a source file into a project."""

    def import_many(self, context: ProjectContext, source_paths: Sequence[Path], options: ImportOptions) -> list[ImportResult]:
        """Import multiple files sequentially with individual reports."""
```

### `services/annotation_service.py`

Responsibility:

- Provide the annotation editor data model.
- Save manual token and segment annotations.
- Apply researcher-approved bulk edits.
- Preserve undo/redo data through edit logs.

Public API:

```python
class AnnotationService:
    """Coordinate transcript and annotation editing."""

    def load_editor_state(self, context: ProjectContext, document_id: Id) -> AnnotationEditorState:
        """Load segments, tokens, effective annotations, languages, and tags."""

    def save_token_annotation(self, context: ProjectContext, token_id: Id, draft: AnnotationDraft) -> Annotation:
        """Save a manual annotation for one token."""

    def save_segment_annotation(self, context: ProjectContext, segment_id: Id, draft: AnnotationDraft) -> Annotation:
        """Save a manual annotation for one segment."""

    def reject_auto_annotation(self, context: ProjectContext, annotation_id: Id) -> None:
        """Mark an automatic annotation as rejected."""

    def bulk_edit(self, context: ProjectContext, request: BulkEditRequest) -> BulkEditResult:
        """Apply a researcher-approved bulk edit."""

    def search_annotations(self, context: ProjectContext, query: AnnotationSearchQuery) -> list[AnnotationSearchResult]:
        """Search annotations by language, switch direction, trigger, tag, or text."""
```

### `services/lid_service.py`

Responsibility:

- Run local Layer 1 LID, optional Layer 2 AfroLID rescoring, and Layer 3
  MaskLID-style detection.
- Store suggestions and provenance.
- Keep automatic labels separate from manual decisions.

Public API:

```python
class LidService:
    """Coordinate local language identification workflows."""

    def run_lid_for_document(self, context: ProjectContext, document_id: Id, options: LidOptions) -> LidRun:
        """Run local LID for a transcript document."""

    def suggest_for_segment(self, context: ProjectContext, segment_id: Id, options: LidOptions) -> list[LidSuggestion]:
        """Return local language suggestions for one segment."""

    def accept_suggestion(self, context: ProjectContext, suggestion_id: Id) -> Annotation:
        """Convert a suggestion into an active automatic annotation if no manual annotation blocks it."""
```

### `services/morphology_service.py`

Responsibility:

- Load editable project-local dictionaries.
- Suggest candidate morphemes without forcing segmentation.
- Save manual morpheme splits and history.

Public API:

```python
class MorphologyService:
    """Coordinate morphology suggestions and manual splits."""

    def suggest_splits(self, context: ProjectContext, token_id: Id) -> list[MorphemeSplit]:
        """Return editable morpheme split suggestions for a token."""

    def save_manual_split(self, context: ProjectContext, token_id: Id, split_text: str, notes: str = "") -> MorphemeSplit:
        """Save a researcher-entered morpheme split."""

    def list_dictionary_entries(self, context: ProjectContext, language_id: Id) -> list[MorphemeDictionaryEntry]:
        """Return morphology dictionary entries for one language."""

    def save_dictionary_entry(self, context: ProjectContext, entry: MorphemeDictionaryEntry) -> None:
        """Create or update a project-local dictionary entry."""
```

### `services/metrics_service.py`

Responsibility:

- Compute transparent metrics on demand.
- Store formula version, input filters, input counts, and results.
- Exportable outputs must be reproducible from annotations.

Public API:

```python
class MetricsService:
    """Coordinate local quantitative metrics."""

    def compute_metrics(self, context: ProjectContext, request: MetricsRequest) -> MetricRun:
        """Compute requested metrics and store results."""

    def list_metric_runs(self, context: ProjectContext) -> list[MetricRun]:
        """Return prior metric runs."""

    def get_results(self, context: ProjectContext, metric_run_id: Id) -> list[MetricResult]:
        """Return results for one metric run."""
```

### `services/export_service.py`

Responsibility:

- Produce local exports only.
- Route export requests to format-specific exporters.
- Record export provenance and checksums where practical.

Public API:

```python
class ExportService:
    """Coordinate local project exports."""

    def list_supported_exports(self) -> list[str]:
        """Return supported export format names."""

    def export(self, context: ProjectContext, request: ExportRequest) -> ExportRecord:
        """Write a local export file and record it in project storage."""
```

### `services/provenance_service.py`

Responsibility:

- Write provenance records to SQLite and mirror append-only JSONL logs.
- Provide audit views for automatic decisions and manual overrides.

Public API:

```python
class ProvenanceService:
    """Coordinate provenance recording and audit lookup."""

    def record(self, context: ProjectContext, record: ProvenanceRecord) -> None:
        """Persist a provenance record."""

    def list_for_target(self, context: ProjectContext, target_table: str, target_id: Id) -> list[ProvenanceRecord]:
        """Return provenance records for one target object."""
```

## `src/imbizo/importers/`

Importers parse copied local files. They do not mutate source files and do not
write directly to SQLite. They return domain bundles for `ImportService`.

### `importers/base.py`

Responsibility:

- Define the importer protocol and common result types.

Public API:

```python
class Importer(Protocol):
    """Parser for one or more local import formats."""

    @property
    def name(self) -> str:
        """Return a stable importer name."""

    def can_import(self, path: Path) -> bool:
        """Return whether this importer can parse a copied local file."""

    def import_file(self, path: Path, options: ImportOptions) -> ImportedBundle:
        """Parse a copied local file into domain objects."""

class ImportedBundle:
    """Parsed import output before persistence."""
```

### Format Importers

Responsibilities and public APIs:

| Module | Responsibility | Public API |
| --- | --- | --- |
| `audio.py` | Inspect WAV, MP3, and FLAC files copied into the project. | `AudioImporter` |
| `video.py` | Inspect MP4 and MKV files and prepare audio-track metadata for MVP workflows. | `VideoImporter` |
| `txt.py` | Import plain text transcripts while preserving orthography. | `TxtImporter` |
| `csv_importer.py` | Import CSV/TSV transcript rows. | `CsvTranscriptImporter` |
| `json_importer.py` | Import structured transcript JSON. | `JsonTranscriptImporter` |
| `eaf.py` | Import ELAN EAF annotations and timing tiers. | `EafImporter` |
| `textgrid.py` | Import Praat TextGrid intervals. | `TextGridImporter` |
| `spreadsheet.py` | Import XLSX and ODS spreadsheet transcripts. | `SpreadsheetImporter` |

Each importer class implements the `Importer` protocol. EAF and TextGrid
importers should preserve external references so round-trip export can remain
traceable.

## `src/imbizo/exporters/`

Exporters write local files from domain objects prepared by services. They must
not call network services.

### `exporters/base.py`

Responsibility:

- Define exporter protocol and common request/result types.

Public API:

```python
class Exporter(Protocol):
    """Writer for one local export format."""

    @property
    def format_name(self) -> str:
        """Return a stable export format name."""

    def export(self, package: ExportPackage, destination: Path, options: ExportOptions) -> ExportedFile:
        """Write a local export file."""
```

### Format Exporters

Responsibilities and public APIs:

| Module | Responsibility | Public API |
| --- | --- | --- |
| `csv_exporter.py` | Write annotation and metric CSV files. | `CsvExporter` |
| `xlsx.py` | Write Excel-compatible workbooks. | `XlsxExporter` |
| `json_exporter.py` | Write full project snapshot JSON matching deliverable 3. | `JsonExporter` |
| `eaf.py` | Write ELAN-compatible EAF files. | `EafExporter` |
| `textgrid.py` | Write Praat TextGrid files. | `TextGridExporter` |
| `html.py` | Write self-contained HTML reports with no external resources. | `HtmlExporter` |
| `pdf.py` | Write local PDF print reports through a local renderer. | `PdfExporter` |
| `quotation.py` | Write quotation extracts for qualitative writing. | `QuotationExporter` |

## `src/imbizo/lid/`

The `lid` package implements local language identification as layered,
auditable suggestions.

### `lid/providers.py`

Responsibility:

- Define the provider protocol shared by baseline LID and optional plugins.

Public API:

```python
class LanguageIdentifier(Protocol):
    """Local language identification provider."""

    @property
    def name(self) -> str:
        """Return provider name."""

    @property
    def version(self) -> str:
        """Return provider version or resource version."""

    def predict(self, texts: Sequence[str], options: LidOptions) -> list[list[LanguageScore]]:
        """Return ranked language scores for each input text."""

class LanguageScore:
    """A language code and confidence score from a provider."""
```

### `lid/baseline.py`

Responsibility:

- Wrap the bundled lightweight offline LID model.
- Run chunk-level and token-level predictions.

Public API:

```python
class BaselineLidProvider:
    """CPU-friendly local baseline LID provider."""

    def load(self) -> None:
        """Load local model resources."""

    def predict(self, texts: Sequence[str], options: LidOptions) -> list[list[LanguageScore]]:
        """Predict ranked language labels."""
```

### `lid/afrolid_stub.py`

Responsibility:

- Define a disabled-by-default adapter shape for optional AfroLID.
- Clearly report when optional resources are not installed.

Public API:

```python
class AfroLidProvider:
    """Optional AfroLID adapter; unavailable unless explicitly installed."""

    def is_available(self) -> bool:
        """Return whether optional local resources are installed."""

    def predict(self, texts: Sequence[str], options: LidOptions) -> list[list[LanguageScore]]:
        """Rescore text only when local optional resources are available."""
```

### `lid/masklid.py`

Responsibility:

- Implement MaskLID-style iterative masking over local LID providers.
- Detect two or three languages within a segment when evidence supports it.
- Produce suggestions, not final labels.

Public API:

```python
class MaskLidDetector:
    """Iterative local detector for multilingual segments."""

    def detect(self, segment: TranscriptSegment, tokens: Sequence[Token], options: LidOptions) -> list[LidSuggestionDraft]:
        """Return code-switch suggestions for a segment and its tokens."""
```

### `lid/resources.py`

Responsibility:

- Locate local LID resources.
- Verify checksums where model files are bundled or installed locally.

Public API:

```python
def find_lid_resource(resource_name: str, search_paths: Sequence[Path]) -> Path | None:
    """Find a local LID resource without downloading it."""

def verify_resource_checksum(path: Path, expected_sha256: str) -> bool:
    """Verify a local resource checksum."""
```

## `src/imbizo/morphology/`

This package assists manual morphology work. It does not impose a full analyzer.

### `morphology/dictionaries.py`

Responsibility:

- Load default dictionaries into new projects.
- Read and write editable project-local dictionary entries.

Public API:

```python
def load_default_dictionary(language_code: str, resources_dir: Path) -> list[MorphemeDictionaryEntry]:
    """Load bundled default morphology entries for one language."""

def merge_project_dictionary(defaults: Sequence[MorphemeDictionaryEntry], user_entries: Sequence[MorphemeDictionaryEntry]) -> list[MorphemeDictionaryEntry]:
    """Merge default and user entries without deleting user work."""
```

### `morphology/suggestions.py`

Responsibility:

- Suggest candidate morpheme splits from editable dictionaries.
- Return suggestions with confidence or explanation fields, never forced
  changes to token text.

Public API:

```python
class MorphologySuggester:
    """Dictionary-based local morpheme suggestion engine."""

    def suggest(self, token: Token, entries: Sequence[MorphemeDictionaryEntry]) -> list[MorphemeSplit]:
        """Return editable split suggestions for a token."""
```

## `src/imbizo/metrics/`

Metric modules are pure local calculators. Services provide already-loaded
annotations, tokens, speakers, scenes, and filters.

### Shared Metric Protocol

```python
class MetricCalculator(Protocol):
    """Local metric calculator."""

    @property
    def metric_name(self) -> str:
        """Return stable metric name."""

    @property
    def formula_version(self) -> str:
        """Return formula version used for reproducibility."""

    def compute(self, dataset: MetricsDataset, options: MetricOptions) -> list[MetricResult]:
        """Compute metric results from annotated data."""
```

### Metric Modules

| Module | Responsibility | Public API |
| --- | --- | --- |
| `language_proportion.py` | Language proportions by project, speaker, scene, and custom filters. | `LanguageProportionCalculator` |
| `switch_density.py` | Switch counts and switches per N tokens. | `SwitchDensityCalculator` |
| `m_index.py` | M-index with documented formula inputs. | `MIndexCalculator` |
| `i_index.py` | I-index / switch-point index with documented denominator. | `IIndexCalculator` |
| `burstiness.py` | Goh and Barabasi burstiness from switch intervals. | `BurstinessCalculator` |
| `trigger_tables.py` | Switch-trigger co-occurrence tables. | `TriggerTableCalculator` |
| `concordance.py` | KWIC concordance for tokens and patterns. | `KwicConcordanceCalculator` |

Each metric result must include input counts and enough context to reproduce the
calculation from exported CSV data.

## `src/imbizo/audio/`

The audio package contains local CPU-only media helpers.

### `audio/decoder.py`

Responsibility:

- Decode supported audio formats enough for waveform display and playback.
- Avoid loading more data than necessary for long interviews.

Public API:

```python
class AudioDecoder:
    """Local audio decoder."""

    def inspect(self, path: Path) -> AudioInfo:
        """Return duration, sample rate, and channels."""

    def read_segment(self, path: Path, start_ms: int, end_ms: int) -> AudioBuffer:
        """Read a segment of audio for playback or waveform generation."""
```

### `audio/waveform.py`

Responsibility:

- Create and read rebuildable waveform peak caches.

Public API:

```python
class WaveformCache:
    """Project-local waveform peak cache."""

    def ensure_peaks(self, media: MediaAsset, source_path: Path, cache_dir: Path) -> Path:
        """Create waveform peaks if missing and return the cache path."""

    def load_peaks(self, peaks_path: Path) -> WaveformPeaks:
        """Load cached waveform peaks."""
```

### `audio/playback.py`

Responsibility:

- Provide a thin playback controller for the GUI.
- Keep audio playback local.

Public API:

```python
class PlaybackController:
    """Control local audio playback for selected segments."""

    def play(self, media_path: Path, start_ms: int | None = None, end_ms: int | None = None) -> None:
        """Play a local media segment."""

    def pause(self) -> None:
        """Pause playback."""

    def stop(self) -> None:
        """Stop playback."""
```

## `src/imbizo/gui/`

GUI modules build PySide6 screens and models. They should be thin: user actions
call services, and services return domain objects or view-state dataclasses.

Deliverable 5 will define detailed screen specifications. This section only
defines module boundaries and public construction APIs.

### `gui/main_window.py`

Responsibility:

- Own the top-level window, menu bar, tabs, status area, and project lifecycle
  wiring.

Public API:

```python
class MainWindow(QMainWindow):
    """Top-level Imbizo-CS Workbench window."""

    def open_project(self, project_root: Path) -> None:
        """Open and display a local project."""

    def close_project(self) -> None:
        """Close the current project view."""
```

### `gui/models/`

Responsibilities and public APIs:

| Module | Responsibility | Public API |
| --- | --- | --- |
| `annotation_table_model.py` | Qt table model for token/segment annotations. | `AnnotationTableModel` |
| `language_legend_model.py` | Qt model for language labels and colors. | `LanguageLegendModel` |
| `segment_list_model.py` | Qt model for transcript segment navigation. | `SegmentListModel` |

Models should expose update methods such as `set_editor_state(...)` rather than
reading SQLite directly.

### `gui/widgets/`

Responsibilities and public APIs:

| Module | Responsibility | Public API |
| --- | --- | --- |
| `annotation_editor.py` | Main annotation workbench screen. | `AnnotationEditorWidget` |
| `waveform_view.py` | Waveform display and click-to-play segment interaction. | `WaveformView` |
| `language_legend.py` | Always-visible language color legend. | `LanguageLegendWidget` |
| `memo_pane.py` | Free-text memo editor for selected token or segment. | `MemoPane` |
| `spreadsheet_view.py` | Excel-like annotation grid view. | `SpreadsheetViewWidget` |
| `timeline_view.py` | ELAN-familiar timeline view. | `TimelineViewWidget` |
| `metrics_dashboard.py` | Metric request and result display. | `MetricsDashboardWidget` |
| `project_settings.py` | Project metadata, languages, ethics notes, and settings. | `ProjectSettingsWidget` |

### `gui/dialogs/`

Responsibilities and public APIs:

| Module | Responsibility | Public API |
| --- | --- | --- |
| `error_dialog.py` | Show plain-language errors and optional details. | `show_error(parent, error)` |
| `import_dialog.py` | Collect import options without parsing files. | `ImportDialog` |
| `export_dialog.py` | Collect export format and destination options. | `ExportDialog` |
| `project_dialogs.py` | Create/open/import project dialogs. | `CreateProjectDialog`, `OpenProjectDialog` |

## `src/imbizo/plugins/`

The plugin package defines optional local extension points. The MVP should ship
interfaces and a registry, but no mandatory heavy plugin.

### `plugins/interfaces.py`

Responsibility:

- Define optional extension protocols for ASR, LID, importers, exporters,
  morphology providers, and metrics.

Public API:

```python
class AsrProvider(Protocol):
    """Optional local ASR provider."""

    def transcribe(self, media_path: Path, options: AsrOptions) -> ImportedBundle:
        """Transcribe local media into transcript data."""

class PluginDescriptor:
    """Metadata for one optional local plugin."""
```

### `plugins/registry.py`

Responsibility:

- Register built-in lightweight providers.
- Discover explicitly enabled local plugins.
- Keep unavailable optional plugins visible but inactive when helpful.

Public API:

```python
class PluginRegistry:
    """Registry of local optional extension providers."""

    def register(self, descriptor: PluginDescriptor) -> None:
        """Register a plugin descriptor."""

    def list_plugins(self) -> list[PluginDescriptor]:
        """Return known plugins."""

    def get_provider(self, provider_type: str, name: str) -> object | None:
        """Return an enabled provider by type and name."""
```

## `src/imbizo/resources/`

Resources are data, not Python control flow.

Responsibilities:

- Store UI strings under `resources/i18n/`.
- Store small default morphology dictionaries under `resources/dictionaries/`.
- Store LID resource metadata and checksums under `resources/lid/`.
- Store self-contained report templates under `resources/templates/`.

Public access should happen through loader functions in `app/strings.py`,
`morphology/dictionaries.py`, `lid/resources.py`, and exporters.

## Cross-Module Workflows

### Create Project

```text
gui project dialog
-> ProjectService.create_project
-> ProjectPaths.from_root
-> persistence.initialize_database
-> LanguageRepository saves defaults
-> ProvenanceService records project creation
```

### Import ELAN EAF

```text
ImportDialog
-> ImportService.import_file
-> copy source into project imports/media/transcripts area
-> EafImporter.import_file
-> TranscriptRepository.save_document_bundle
-> AnnotationRepository saves imported annotations
-> ProvenanceService records import report
```

### Run LID Suggestions

```text
AnnotationEditorWidget
-> LidService.run_lid_for_document
-> BaselineLidProvider.predict
-> optional AfroLidProvider only if installed and enabled
-> MaskLidDetector.detect
-> LidRepository saves run and suggestions
-> AnnotationRepository saves auto annotations only where allowed
-> ProvenanceService records auto decisions
```

### Manual Annotation

```text
AnnotationTableModel edit
-> AnnotationService.save_token_annotation
-> AnnotationRepository.save_manual_annotation
-> Edit log records previous and new values
-> ProvenanceService records manual update
-> GUI refreshes effective annotation view
```

### Metrics And Export

```text
MetricsDashboardWidget
-> MetricsService.compute_metrics
-> MetricCalculator.compute
-> MetricRepository saves run and results
-> ExportService.export
-> CsvExporter or XlsxExporter writes local file
-> ProvenanceService records export
```

## Implementation Order For Deliverable 6

The MVP source code should be implemented in this order:

1. Domain dataclasses and enums.
2. Project paths, errors, strings, and settings.
3. SQLite connection, schema creation, and repositories.
4. Project service and import service.
5. TXT, CSV, EAF, TextGrid, and audio importers.
6. Annotation service and editor view state.
7. Baseline LID, MaskLID-style detector, and LID service.
8. Metrics calculators.
9. Export service and CSV, XLSX, JSON, EAF, HTML exporters.
10. PySide6 main window and fully wired annotation editor.

## Non-Goals For This Module Contract

- It does not define full GUI layouts; deliverable 5 does that.
- It does not create source files; deliverable 6 does that.
- It does not add cloud sync, accounts, telemetry, or online model downloads.
- It does not make optional ASR or AfroLID a required dependency.
