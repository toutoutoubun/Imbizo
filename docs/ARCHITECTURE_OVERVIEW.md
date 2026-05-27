# Deliverable 1: Architecture Overview

This document defines the high-level architecture for Imbizo-CS Workbench. It is
the baseline for later deliverables and should be read together with
[PRINCIPLES.md](../PRINCIPLES.md).

Imbizo-CS Workbench is a local desktop application for humanities researchers
working with multilingual South African interview data. The architecture is
designed around four fixed commitments:

1. Core work must run offline.
2. Research data must remain inside a local project folder.
3. Automated analysis must produce editable suggestions, not final authority.
4. The application must remain practical on CPU-only, low-memory laptops.

## Architectural Style

The MVP should use a layered desktop architecture:

- A PySide6 presentation layer for researcher-facing screens.
- Application services that coordinate project actions, imports, annotation,
  local language identification, metrics, and export.
- Domain models that describe projects, media files, transcript segments,
  tokens, annotations, languages, metrics, and provenance records.
- Persistence repositories backed by one SQLite database per project plus plain
  files for media, transcripts, dictionaries, exports, and logs.
- Local processing engines for waveform preparation, file parsing, LID,
  MaskLID-style code-switch detection, morphology suggestions, and metrics.
- Explicit plugin boundaries for future local ASR, AfroLID, additional
  languages, and morphology tools.

The GUI must depend on services, not directly on SQLite tables or parser
implementations. Services may depend on repositories and processing engines.
Processing engines should be mostly UI-independent so they can be tested without
opening a desktop window.

## ASCII Diagram

```text
+--------------------------------------------------------------------------+
| Researcher                                                               |
| Humanities workflow: listen, read, annotate, question, revise, export     |
+-----------------------------------+--------------------------------------+
                                    |
                                    v
+--------------------------------------------------------------------------+
| PySide6 Desktop UI                                                       |
|                                                                          |
| Main window                                                              |
| Annotation editor | Spreadsheet view | Timeline view | Metrics dashboard |
| Project settings | Import/export dialogs | Plain-language errors         |
|                                                                          |
| Responsibilities:                                                        |
| - Show raw media, transcripts, annotations, memos, provenance             |
| - Keep automatic labels visually distinct from researcher decisions       |
| - Support keyboard navigation, scalable fonts, high-contrast theme        |
+-----------------------------------+--------------------------------------+
                                    |
                                    | commands, events, view models
                                    v
+--------------------------------------------------------------------------+
| Application Services                                                     |
|                                                                          |
| ProjectService      - create, open, close, zip, import zip                |
| ImportService       - copy source files, parse supported formats          |
| AnnotationService   - edit segments, tokens, labels, memos, tags          |
| LidService          - run local LID and code-switch detection             |
| MorphologyService   - suggest editable morpheme candidates                |
| MetricsService      - compute transparent quantitative metrics            |
| ExportService       - write local CSV, XLSX, JSON, EAF, TextGrid, HTML    |
| ProvenanceService   - log automatic decisions and manual overrides        |
+----------------------+-------------------+-------------------------------+
                       |                   |
                       | domain objects    | background jobs
                       v                   v
+--------------------------------+   +-------------------------------------+
| Domain Model                   |   | Local Processing Engines             |
|                                |   |                                     |
| ProjectMetadata                |   | Audio decoding and waveform cache    |
| Participant, Speaker, Scene    |   | TXT/CSV/JSON/EAF/TextGrid parsers    |
| MediaAsset                     |   | Layer 1 lightweight LID              |
| TranscriptSegment              |   | Layer 2 optional AfroLID adapter     |
| Token                          |   | Layer 3 MaskLID-style detection      |
| Annotation                     |   | Morphology dictionary lookup          |
| LanguageTag                    |   | M-index, I-index, burstiness, KWIC    |
| MorphemeSplit                  |   | HTML/PDF report rendering             |
| ProvenanceRecord               |   |                                     |
+----------------------+---------+   +----------------+--------------------+
                       |                              |
                       | repository APIs             | local files only
                       v                              v
+--------------------------------------------------------------------------+
| Project Folder Boundary                                                  |
|                                                                          |
| project.sqlite        - canonical relational project database             |
| media/                - copied audio/video files                          |
| transcripts/          - imported plain transcript files and snapshots     |
| dictionaries/         - project-local morphology and language resources   |
| exports/              - user-created export files                         |
| logs/provenance.jsonl - append-only readable provenance log               |
| cache/                - waveform peaks and other rebuildable local caches |
|                                                                          |
| Rule: imports copy source files into this boundary and never modify the   |
| original source path.                                                     |
+--------------------------------------------------------------------------+
                                    |
                                    v
+--------------------------------------------------------------------------+
| Local Machine                                                             |
|                                                                          |
| No telemetry | No required account | No required API key | No cloud sync  |
| Optional plugins must be explicit, local, removable, and non-essential.   |
+--------------------------------------------------------------------------+
```

## Core Runtime Flow

1. The researcher creates or opens a project folder.
2. The application opens the project's SQLite database and verifies the plain
   file subdirectories.
3. Imports copy external source files into the project folder, then parse them
   into transcript segments, tokens, media assets, and initial metadata.
4. The annotation editor loads segments and tokens through application services.
5. Optional automatic analysis writes suggested labels with provenance:
   layer name, model/resource version, confidence, timestamp, and target item.
6. The researcher accepts, edits, replaces, or rejects suggestions. Manual edits
   are stored as authoritative annotation records and also logged.
7. Metrics are computed on demand from current annotations. Formula details and
   input counts must be available in the UI and in exports.
8. Exports write local files only. Exporters read from repositories and project
   files; they do not call external services.

## Data Sovereignty Boundary

The project folder is the sovereignty boundary. All user research material,
project configuration, annotations, dictionaries, logs, caches, and exports live
inside that folder unless the researcher explicitly chooses an export target.

Core code must not:

- Upload data.
- Perform telemetry.
- Require an account.
- Require a subscription or license server.
- Require an internet connection to launch, annotate, compute metrics, or
  export.

Future plugins may use resources that the researcher installs separately, but
the core application must continue to work when every optional plugin is absent.

## Authority Model

The architecture separates automatic suggestions from researcher decisions.

- Automatic labels are stored with `source = "auto"` and provenance.
- Manual labels are stored with `source = "manual"` and override automatic
  suggestions for analysis and export.
- Rejected or superseded automatic labels remain auditable.
- No automatic process should silently overwrite a manual annotation.
- Metrics should use the current effective annotation set and expose which
  records were included.

This keeps the Matrix Language Frame, trigger coding, morphology assistance, and
code-switch detection useful without turning them into black-box conclusions.

## Local Processing Strategy

Heavy or long-running work should run outside the GUI thread by using Qt worker
threads or a small local job abstraction. The first MVP should keep jobs simple:

- Import parsing jobs.
- Waveform peak generation jobs.
- LID and MaskLID-style jobs.
- Metrics calculation jobs.
- Export jobs.

Each job should report progress, support cancellation where practical, and
return plain-language errors to the UI. Failed jobs must leave existing project
data intact.

## Performance Commitments

The architecture should protect low-resource hardware by default:

- Load large media files lazily.
- Store waveform peak caches instead of redrawing from full audio every time.
- Stream imports where practical.
- Keep LID batch sizes small and configurable.
- Avoid bundled large neural models in the MVP.
- Make optional high-memory plugins opt-in and clearly labelled.
- Keep startup work minimal so the app can launch quickly before opening a
  large project.

## Extensibility Boundaries

The first extension points should be interfaces, not mandatory dependencies:

- `AsrProvider` for future local ASR such as Whisper.cpp or Vosk.
- `LanguageIdentifier` for the baseline model and optional AfroLID rescoring.
- `Importer` for new file types.
- `Exporter` for new research outputs.
- `MorphologyProvider` for future analyzers or richer dictionaries.
- `MetricCalculator` for additional quantitative measures.

Every extension must preserve offline operation unless the researcher knowingly
chooses a plugin action that requires downloading an external resource.

## What This Deliverable Does Not Define

This document does not yet define the full repository directory layout, SQLite
schema, JSON export schema, module APIs, or GUI wireframes. Those are covered by
deliverables 2 through 5. This architecture only fixes the system shape and the
boundaries that future implementation must respect.
