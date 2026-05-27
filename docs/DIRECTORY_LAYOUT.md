# Deliverable 2: Directory Layout

This document defines the planned repository layout for Imbizo-CS Workbench and
the local project-folder layout created for each research project. It follows
the boundaries established in
[ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md) and the design constraints
in [PRINCIPLES.md](../PRINCIPLES.md).

## Repository Layout

```text
Imbizo/
|-- PRINCIPLES.md
|-- README.md
|-- INSTALL_OFFLINE.md
|-- pyproject.toml
|-- requirements.txt
|-- requirements-offline.txt
|-- LICENSE
|-- CHANGELOG.md
|
|-- docs/
|   |-- ARCHITECTURE_OVERVIEW.md
|   |-- DIRECTORY_LAYOUT.md
|   |-- DATA_MODEL.md
|   |-- MODULE_BREAKDOWN.md
|   |-- GUI_SPECIFICATIONS.md
|   |-- ROADMAP_PLUGINS.md
|   |-- formulas/
|   |   |-- m_index.md
|   |   |-- i_index.md
|   |   |-- burstiness.md
|   |   |-- switch_density.md
|   |-- accessibility/
|   |   |-- keyboard_navigation.md
|   |   |-- high_contrast_theme.md
|   |-- offline_verification/
|       |-- network_audit.md
|       |-- dependency_inventory.md
|
|-- src/
|   |-- imbizo/
|       |-- __init__.py
|       |-- main.py
|       |
|       |-- app/
|       |   |-- __init__.py
|       |   |-- errors.py
|       |   |-- events.py
|       |   |-- jobs.py
|       |   |-- settings.py
|       |   |-- strings.py
|       |
|       |-- domain/
|       |   |-- __init__.py
|       |   |-- annotations.py
|       |   |-- languages.py
|       |   |-- media.py
|       |   |-- metrics.py
|       |   |-- morphology.py
|       |   |-- project.py
|       |   |-- provenance.py
|       |   |-- transcripts.py
|       |
|       |-- services/
|       |   |-- __init__.py
|       |   |-- annotation_service.py
|       |   |-- export_service.py
|       |   |-- import_service.py
|       |   |-- lid_service.py
|       |   |-- metrics_service.py
|       |   |-- morphology_service.py
|       |   |-- project_service.py
|       |   |-- provenance_service.py
|       |
|       |-- persistence/
|       |   |-- __init__.py
|       |   |-- connection.py
|       |   |-- migrations.py
|       |   |-- repositories.py
|       |   |-- schema.sql
|       |
|       |-- importers/
|       |   |-- __init__.py
|       |   |-- base.py
|       |   |-- audio.py
|       |   |-- csv_importer.py
|       |   |-- eaf.py
|       |   |-- json_importer.py
|       |   |-- spreadsheet.py
|       |   |-- textgrid.py
|       |   |-- txt.py
|       |   |-- video.py
|       |
|       |-- exporters/
|       |   |-- __init__.py
|       |   |-- base.py
|       |   |-- csv_exporter.py
|       |   |-- eaf.py
|       |   |-- html.py
|       |   |-- json_exporter.py
|       |   |-- pdf.py
|       |   |-- quotation.py
|       |   |-- textgrid.py
|       |   |-- xlsx.py
|       |
|       |-- lid/
|       |   |-- __init__.py
|       |   |-- baseline.py
|       |   |-- masklid.py
|       |   |-- providers.py
|       |   |-- afrolid_stub.py
|       |   |-- resources.py
|       |
|       |-- morphology/
|       |   |-- __init__.py
|       |   |-- dictionaries.py
|       |   |-- suggestions.py
|       |
|       |-- metrics/
|       |   |-- __init__.py
|       |   |-- burstiness.py
|       |   |-- concordance.py
|       |   |-- i_index.py
|       |   |-- language_proportion.py
|       |   |-- m_index.py
|       |   |-- switch_density.py
|       |   |-- trigger_tables.py
|       |
|       |-- audio/
|       |   |-- __init__.py
|       |   |-- decoder.py
|       |   |-- playback.py
|       |   |-- waveform.py
|       |
|       |-- gui/
|       |   |-- __init__.py
|       |   |-- main_window.py
|       |   |-- models/
|       |   |   |-- annotation_table_model.py
|       |   |   |-- language_legend_model.py
|       |   |   |-- segment_list_model.py
|       |   |-- widgets/
|       |   |   |-- annotation_editor.py
|       |   |   |-- language_legend.py
|       |   |   |-- memo_pane.py
|       |   |   |-- metrics_dashboard.py
|       |   |   |-- project_settings.py
|       |   |   |-- spreadsheet_view.py
|       |   |   |-- timeline_view.py
|       |   |   |-- waveform_view.py
|       |   |-- dialogs/
|       |       |-- error_dialog.py
|       |       |-- export_dialog.py
|       |       |-- import_dialog.py
|       |       |-- project_dialogs.py
|       |
|       |-- plugins/
|       |   |-- __init__.py
|       |   |-- interfaces.py
|       |   |-- registry.py
|       |
|       |-- resources/
|           |-- i18n/
|           |   |-- en.json
|           |   |-- af.json
|           |   |-- zu.json
|           |   |-- xh.json
|           |   |-- st.json
|           |   |-- tn.json
|           |-- dictionaries/
|           |   |-- isizulu_morphemes.json
|           |   |-- isixhosa_morphemes.json
|           |   |-- sesotho_morphemes.json
|           |   |-- setswana_morphemes.json
|           |-- lid/
|           |   |-- README.md
|           |   |-- checksums.txt
|           |-- templates/
|               |-- report.html.j2
|               |-- report.css
|
|-- tests/
|   |-- conftest.py
|   |-- fixtures/
|   |   |-- eaf/
|   |   |-- textgrid/
|   |   |-- transcripts/
|   |   |-- projects/
|   |-- unit/
|   |   |-- test_annotations.py
|   |   |-- test_importers.py
|   |   |-- test_lid.py
|   |   |-- test_metrics.py
|   |   |-- test_project_service.py
|   |-- integration/
|   |   |-- test_eaf_roundtrip.py
|   |   |-- test_project_reopen.py
|   |   |-- test_exports.py
|   |-- gui/
|       |-- test_annotation_editor_model.py
|
|-- scripts/
|   |-- build_offline_wheelhouse.py
|   |-- package_linux.py
|   |-- package_windows.py
|   |-- verify_no_network.py
|   |-- verify_offline_install.py
|
|-- packaging/
|   |-- pyinstaller/
|   |   |-- imbizo-linux.spec
|   |   |-- imbizo-windows.spec
|   |-- linux/
|   |   |-- README.md
|   |-- windows/
|       |-- README.md
|
|-- third_party/
|   |-- licenses/
|   |-- notices/
|
|-- examples/
|   |-- README.md
|   |-- demo_project_minimal/
|       |-- README.md
|
|-- tools/
    |-- dev/
        |-- format_check.py
        |-- sample_project_builder.py
```

## Top-Level Files

- `PRINCIPLES.md` records the non-negotiable design philosophy.
- `README.md` will be written for humanities researchers, not only developers.
- `INSTALL_OFFLINE.md` will describe installation with no internet connection.
- `pyproject.toml` will define package metadata, tooling, and test settings.
- `requirements.txt` will support normal development installs.
- `requirements-offline.txt` will pin the dependency set used for offline
  packaging.
- `LICENSE`, `CHANGELOG.md`, `third_party/licenses/`, and
  `third_party/notices/` keep licensing visible and auditable.

## Documentation

The `docs/` directory contains deliverables and user-facing technical
explanations. Formula documents are separated because metric definitions must be
transparent in the app and reproducible from exports. Offline verification docs
record how maintainers confirm that core workflows make no network calls.

Documentation should avoid promising cloud features. Any future optional plugin
with network behavior must be documented as opt-in and outside the core MVP.

## Source Package

The Python package lives under `src/imbizo/`. This keeps import behavior
predictable and avoids accidentally importing files from the repository root.

The package is divided by architectural role:

- `app/` contains cross-cutting application concerns such as jobs, settings,
  events, user-facing strings, and plain-language errors.
- `domain/` contains the core typed objects used by services, persistence,
  metrics, importers, exporters, and GUI models.
- `services/` coordinates user-level actions and owns transaction boundaries.
- `persistence/` owns SQLite connections, migrations, schema creation, and
  repository implementations.
- `importers/` parses external file formats after source files have been copied
  into the local project folder.
- `exporters/` writes local output files without external services.
- `lid/` contains local language identification providers and the
  MaskLID-style code-switch detection workflow.
- `morphology/` contains editable dictionary loading and suggestion logic. It
  must not become a forced analyzer in the MVP.
- `metrics/` contains transparent formula implementations.
- `audio/` contains decoding, playback coordination, and waveform cache logic.
- `gui/` contains PySide6 windows, widgets, table models, and dialogs.
- `plugins/` defines interfaces and a registry for optional local plugins.
- `resources/` stores bundled strings, templates, small dictionaries, and LID
  resource metadata.

## Dependency Direction

The intended dependency direction is:

```text
gui -> services -> domain
gui -> app
services -> persistence
services -> importers
services -> exporters
services -> lid
services -> morphology
services -> metrics
importers -> domain
exporters -> domain
persistence -> domain
metrics -> domain
lid -> domain
morphology -> domain
audio -> domain
plugins -> domain
```

Avoid dependencies in the opposite direction:

- `domain/` must not import `gui/`, `persistence/`, or PySide6.
- `persistence/` must not call GUI code.
- `importers/` and `exporters/` must not show dialogs.
- `metrics/` must not read directly from SQLite; services provide the data.
- Optional plugins must not be required by core startup.

## Test Layout

Tests are grouped by risk and runtime cost:

- `tests/unit/` covers pure functions, domain rules, import parsing, LID
  wrappers, metrics, and service behavior with temporary project folders.
- `tests/integration/` covers project creation, reopen, import/export
  round-trips, and SQLite persistence.
- `tests/gui/` covers Qt models and widget behavior that can be tested without
  manual interaction.
- `tests/fixtures/` stores small, non-sensitive sample files. No private
  research data belongs in the repository.

The test suite must remain runnable offline.

## Packaging and Offline Installation

The `scripts/` and `packaging/` directories support offline-first distribution:

- `build_offline_wheelhouse.py` collects pinned open-source Python wheels for
  a specific release.
- `verify_offline_install.py` tests installation from local files only.
- `verify_no_network.py` runs representative core workflows while blocking or
  monitoring network calls.
- PyInstaller specs live under `packaging/pyinstaller/`.

Generated installers, wheelhouses, build artifacts, and local virtual
environments should not be committed to the repository. They belong in release
artifacts or local build directories.

## Resource Policy

Bundled resources must be small enough for low-resource offline installation.

- UI strings live in `src/imbizo/resources/i18n/`.
- Default morphology dictionaries live in `src/imbizo/resources/dictionaries/`.
- Report templates live in `src/imbizo/resources/templates/`.
- LID model metadata lives in `src/imbizo/resources/lid/`.

Large optional models, including AfroLID or future ASR models, must not be
placed in the core source tree. They should be installed through explicit local
plugin/resource workflows and remain removable.

## Runtime Project Folder Layout

Each researcher project is a normal local folder. The app owns files inside that
folder only after the researcher creates or opens it.

```text
My_Interview_Project/
|-- project.sqlite
|-- project.json
|-- README_PROJECT.txt
|
|-- media/
|   |-- audio/
|   |-- video/
|   |-- extracted_audio/
|
|-- transcripts/
|   |-- source/
|   |-- normalized/
|   |-- snapshots/
|
|-- annotations/
|   |-- exports_for_review/
|
|-- dictionaries/
|   |-- morphology/
|   |-- language_tags.json
|
|-- imports/
|   |-- original_copies/
|   |-- import_reports/
|
|-- exports/
|   |-- csv/
|   |-- xlsx/
|   |-- json/
|   |-- elan/
|   |-- praat/
|   |-- html/
|   |-- pdf/
|   |-- quotations/
|
|-- logs/
|   |-- provenance.jsonl
|   |-- errors.jsonl
|
|-- cache/
    |-- waveform_peaks/
    |-- lid/
    |-- thumbnails/
```

## Runtime Folder Rules

- `project.sqlite` is the canonical database for structured project state.
- `project.json` is a human-readable metadata snapshot and recovery aid.
- `media/` stores copies of imported audio and video. Source files outside the
  project folder must never be modified.
- `transcripts/source/` stores imported transcript copies.
- `transcripts/normalized/` stores optional normalized views that never replace
  originals.
- `dictionaries/` stores project-local editable language tags and morphology
  dictionaries.
- `imports/original_copies/` records copied source files when preserving the
  original import package helps auditability.
- `exports/` stores researcher-created local export files.
- `logs/provenance.jsonl` stores append-only automatic decisions and manual
  overrides in a readable format.
- `cache/` stores rebuildable files. Deleting `cache/` must not delete research
  data.

## Files Not To Store

The repository and project folders should avoid:

- User account tokens.
- API keys.
- Cloud configuration required for core features.
- Telemetry logs.
- Private research data in repository fixtures.
- Large optional model weights in the core package.
- Generated build artifacts committed as source.

## Naming Conventions

- Python modules use lowercase snake case.
- Public classes use `PascalCase`.
- Public functions and methods use `snake_case`.
- Runtime project subdirectories use lowercase snake case.
- Export files should include a project slug and timestamp when created by the
  app.
- User-facing labels must come from externalized string resources, not hardcoded
  widget text.

## Future Deliverable Boundaries

This document names planned modules and files but does not define their public
APIs or implementation details. Those belong to later deliverables:

- Deliverable 3 defines SQLite, JSON, and Python data models.
- Deliverable 4 defines module responsibilities and public APIs.
- Deliverable 5 defines GUI screen specifications.
- Deliverable 6 creates the MVP source code.
