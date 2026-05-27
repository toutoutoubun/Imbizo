# Deliverable 5: GUI Screen Specifications

This document defines the MVP GUI screens for Imbizo-CS Workbench. It follows
the architecture, data model, and module API contracts in:

- [ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md)
- [DIRECTORY_LAYOUT.md](DIRECTORY_LAYOUT.md)
- [DATA_MODEL.md](DATA_MODEL.md)
- [MODULE_BREAKDOWN.md](MODULE_BREAKDOWN.md)

The GUI is a PySide6 desktop interface for humanities researchers. It must feel
like a careful research workbench: dense enough for serious annotation, calm
enough for long interview sessions, and explicit about every automatic
suggestion.

## GUI Principles

- The researcher is the authority. Automatic labels are suggestions and must be
  visibly marked as automatic until accepted or overridden.
- The first working screen after opening a project is the annotation editor, not
  a landing page.
- Raw data stays visible. The interface must not hide original transcript text,
  timing, or imported annotations behind summary-only views.
- The app must be usable with keyboard navigation, scalable fonts, and a
  high-contrast theme.
- UI strings must come from `resources/i18n/*.json`.
- Long-running tasks must show progress and allow cancellation when practical.
- Errors must be shown in plain language with optional technical details.
- No screen may require a network connection, account, API key, or telemetry.

## Information Architecture

The MVP uses one main window with five primary work areas:

1. Annotation editor.
2. Spreadsheet view.
3. Timeline view.
4. Metrics dashboard.
5. Project settings.

The main window also provides project commands, import/export commands, undo and
redo, a project status area, and a language legend.

```text
+--------------------------------------------------------------------------+
| Menu bar: Project | Import | Export | Edit | View | Tools | Help          |
+--------------------------------------------------------------------------+
| Toolbar: New Open Save Import Export Undo Redo Run LID Metrics            |
+-------------------+------------------------------------------------------+
| Project navigator | Tab bar: Annotation | Spreadsheet | Timeline |        |
|                   |          Metrics | Project Settings                  |
| Documents         +------------------------------------------------------+
| Scenes            | Active tab content                                    |
| Speakers          |                                                      |
| Filters           |                                                      |
|                   |                                                      |
+-------------------+------------------------------------------------------+
| Language legend: color swatches, labels, auto/manual marker sample         |
+--------------------------------------------------------------------------+
| Status bar: project path | autosave state | job progress | offline state   |
+--------------------------------------------------------------------------+
```

## Shared UI Components

### Project Navigator

Location:

- Left dock in the main window.

Purpose:

- Let the researcher switch transcript documents, scenes, speakers, and saved
  filters.

Content:

- Document list.
- Scene list.
- Speaker list.
- Saved searches and filters.

Behavior:

- Selecting a document refreshes all primary tabs.
- Selecting a scene or speaker applies a filter to the active tab.
- The navigator can be collapsed to give more room to the annotation editor.

Service calls:

- `AnnotationService.load_editor_state(...)`
- `MetricsService.compute_metrics(...)` when a metrics tab filter changes.

### Language Legend

Location:

- Always visible at the bottom of the main window.

Purpose:

- Keep language color coding understandable without hiding data.

Content:

- Color swatch for each language.
- Language name and short code.
- Special labels: unknown, mixed, borrowing, proper noun.
- Auto marker sample and manual marker sample.

Behavior:

- Clicking a language applies a temporary filter in the active view.
- Right-click opens language edit actions if the project settings screen allows
  editing.
- Colors update immediately after project settings changes.

Service calls:

- `LanguageRepository.list_languages()` through screen services.
- `ProjectSettingsWidget` saves edits through project/settings services.

### Status Bar

Location:

- Bottom edge below the language legend.

Purpose:

- Give constant feedback about local state.

Content:

- Open project path.
- Autosave state: saved, saving, failed.
- Background job progress.
- Offline state indicator.
- Current selection summary.

Behavior:

- Clicking a failed autosave message opens the error dialog.
- Clicking a job progress message opens a small job details panel.

### Error Dialog

Purpose:

- Show plain-language errors with optional technical detail.

Required fields:

- Short message.
- What the app was trying to do.
- What happened.
- Suggested next step.
- Technical details disclosure area.

Behavior:

- Never shows only a traceback.
- For import errors, confirms that the original source file was not modified.
- For export errors, identifies whether a partial output file was removed or
  retained.

## Main Window Specification

Module:

- `src/imbizo/gui/main_window.py`

Class:

- `MainWindow`

Primary services:

- `ProjectService`
- `ImportService`
- `ExportService`
- `AnnotationService`
- `LidService`
- `MetricsService`
- `ProvenanceService`

### Main Window Layout

```text
+--------------------------------------------------------------------------+
| Menu bar                                                                  |
+--------------------------------------------------------------------------+
| Main toolbar                                                              |
+---------------------+----------------------------------------------------+
| Left dock            | Primary stacked tab area                           |
|                      |                                                    |
| Project navigator    | +----------------------------------------------+   |
|                      | | Tab bar                                      |   |
| Documents            | +----------------------------------------------+   |
| Scenes               | | Active screen                                 |   |
| Speakers             | |                                              |   |
| Saved filters        | |                                              |   |
|                      | |                                              |   |
+---------------------+----------------------------------------------------+
| Language legend                                                           |
+--------------------------------------------------------------------------+
| Status bar                                                                |
+--------------------------------------------------------------------------+
```

### Menus

Project menu:

- New Project
- Open Project
- Close Project
- Export Project as Zip
- Import Project from Zip
- Recent Projects
- Exit

Import menu:

- Import Audio
- Import Video
- Import Transcript
- Import ELAN EAF
- Import Praat TextGrid
- Import Spreadsheet

Export menu:

- Export CSV
- Export XLSX
- Export JSON Snapshot
- Export ELAN EAF
- Export Praat TextGrid
- Export HTML Report
- Export PDF Report
- Export Quotations

Edit menu:

- Undo
- Redo
- Find
- Find and Replace
- Bulk Edit
- Edit Selected Annotation

View menu:

- Annotation Editor
- Spreadsheet View
- Timeline View
- Metrics Dashboard
- Project Settings
- Increase Font Size
- Decrease Font Size
- High Contrast Theme

Tools menu:

- Run Local LID
- Rebuild Waveform Cache
- Manage Morphology Dictionaries
- View Provenance Log
- Verify Offline Mode

Help menu:

- User Guide
- Metric Formulas
- About Imbizo-CS Workbench

### Toolbar

Toolbar actions should use icons plus accessible names:

- New project.
- Open project.
- Save current edits.
- Import.
- Export.
- Undo.
- Redo.
- Play or pause.
- Run local LID.
- Compute metrics.

The toolbar must not include cloud, account, sync, or login actions.

### Empty State

When no project is open:

- Show a compact local project chooser.
- Actions: New Project, Open Project, Import Project from Zip.
- Show recent local projects if available.
- Do not show marketing content or cloud setup prompts.

### Main Window State

Required states:

- No project open.
- Project open, no transcript documents.
- Project open with selected transcript document.
- Background job running.
- Storage or autosave error.
- Read-only recovery mode if a project cannot be written safely.

### Main Window Keyboard Behavior

Minimum shortcuts:

- `Ctrl+N`: new project.
- `Ctrl+O`: open project.
- `Ctrl+S`: save current edits.
- `Ctrl+I`: import.
- `Ctrl+E`: export.
- `Ctrl+F`: find.
- `Ctrl+Z`: undo.
- `Ctrl+Y`: redo.
- `Ctrl+Plus`: increase font size.
- `Ctrl+Minus`: decrease font size.
- `Space`: play or pause media when focus is in annotation work area.

Shortcuts must be configurable later, but hardcoded defaults are acceptable for
the MVP.

## Annotation Editor Specification

Module:

- `src/imbizo/gui/widgets/annotation_editor.py`

Class:

- `AnnotationEditorWidget`

Purpose:

- Main working screen for token-level and segment-level annotation.
- Shows waveform, transcript, annotation grid, memo pane, and language legend
  context in one view.

Primary services:

- `AnnotationService`
- `LidService`
- `MorphologyService`
- `ProvenanceService`
- `audio.PlaybackController`
- `audio.WaveformCache`

### Annotation Editor Layout

Desktop layout:

```text
+--------------------------------------------------------------------------+
| Document selector | Scene filter | Speaker filter | Search | Run LID      |
+--------------------------------------------------------------------------+
| Waveform view with segment boundaries and playhead                         |
+--------------------------+--------------------------+--------------------+
| Transcript pane          | Annotation grid          | Memo/provenance     |
|                          |                          |                    |
| Utterance list           | Token rows               | Selected item      |
| Clause/phrase children   | Language                 | memo               |
| Active token highlight   | ML / EL                  | tags               |
| Original text visible    | Switch type              | morphemes          |
| Optional normalized text | Status                   | provenance         |
+--------------------------+--------------------------+--------------------+
| Filter bar: language | switch type | trigger | confidence | tags          |
+--------------------------------------------------------------------------+
```

Responsive behavior:

- On narrow screens, memo/provenance becomes a right-side collapsible drawer.
- The waveform remains above transcript and grid.
- The annotation grid must keep horizontal scrolling instead of truncating
  researcher data.

### Waveform View

Required elements:

- CPU-generated waveform peaks.
- Segment boundary markers.
- Current playhead.
- Selected segment highlight.
- Time ruler in minutes and seconds.
- Play, pause, stop controls.

Behavior:

- Clicking a segment boundary selects the corresponding transcript segment.
- Double-clicking a segment plays from `start_ms` to `end_ms`.
- Dragging the playhead changes playback position.
- If no audio is linked, show a compact local message that transcript editing
  is still available.

Service calls:

- `WaveformCache.ensure_peaks(...)`
- `WaveformCache.load_peaks(...)`
- `PlaybackController.play(...)`
- `PlaybackController.pause()`
- `PlaybackController.stop()`

### Transcript Pane

Required elements:

- Utterance-level segment list.
- Optional clause/phrase children nested under utterances.
- Original transcript text.
- Optional normalized text toggle.
- Speaker label.
- Time range.
- Current token highlight.

Behavior:

- Selecting a segment loads its tokens in the annotation grid.
- Editing transcript text preserves original text unless the researcher is
  explicitly editing the original transcript field.
- Normalized text is visually distinct and never replaces original text.
- Non-standard orthography, repetitions, hesitations, and code-mixed forms must
  remain editable as written.

### Annotation Grid

Required columns:

1. Token order.
2. Token text.
3. Normalized token.
4. Language label.
5. Source marker.
6. Matrix Language.
7. Embedded Language.
8. Switch type.
9. Linguistic status.
10. Direction.
11. Trigger word or phrase.
12. Researcher confidence.
13. Tags.
14. Morpheme split.

Column behavior:

- Token text is editable only when the researcher is editing transcript content.
- Language cells use a color swatch plus text.
- Source marker must distinguish manual, imported, and auto.
- Auto labels are visually lighter and include an accept or override action.
- Confidence uses a 1 to 5 selector for researcher confidence.
- Morpheme split opens an inline editor or side pane.

Allowed controls:

- Language: combo box from project language list plus special labels.
- ML and EL: combo boxes from language list.
- Switch type: combo box with intra-sentential, inter-sentential,
  extra-sentential.
- Linguistic status: combo box with borrowing, insertion, alternation.
- Direction: two language selectors or computed display when both languages are
  present.
- Trigger: text field.
- Confidence: stepper or combo box 1 through 5.
- Tags: tag picker with project tags.

Autosave:

- Cell edits save through `AnnotationService`.
- Save success updates the status bar.
- Save failure leaves the edited cell visibly unsaved and opens an error option.

Undo and redo:

- Every manual annotation edit creates edit-log data.
- Undo restores the prior annotation state.
- Redo reapplies the annotation state.

### Auto Suggestion Treatment

Automatic suggestions must:

- Be marked with `auto`.
- Show the assigning layer when available: Layer 1 baseline, Layer 2 AfroLID,
  or Layer 3 MaskLID.
- Show confidence when available.
- Offer Accept, Override, and Reject actions.
- Never overwrite an active manual annotation.

Acceptance behavior:

- Accept converts the suggestion into an effective annotation only if no active
  manual annotation blocks it.
- Override creates a manual annotation.
- Reject marks the suggestion or auto annotation as rejected and records
  provenance.

### Memo And Provenance Pane

Required sections:

- Selected item summary.
- Free-text memo.
- Tags.
- Morpheme suggestions and manual split history.
- Provenance timeline.

Behavior:

- The memo autosaves after a short idle delay or when focus leaves the editor.
- Provenance timeline is read-only.
- Morpheme suggestions can be copied into a manual split field but are never
  applied silently.

### Annotation Editor Filters

Filter controls:

- Language.
- Source: manual, imported, auto.
- Switch type.
- Linguistic status.
- Direction.
- Trigger text.
- Speaker.
- Scene.
- Confidence range.
- Tag.
- Free-text search.

Filter results:

- Filtering affects the transcript pane and annotation grid.
- The waveform should still show segment positions, with non-matching segments
  subdued rather than removed when practical.

### Annotation Editor Empty States

No document:

- Show local import and manual transcript creation actions.

Document has no tokens:

- Offer tokenization action and manual token entry.

No linked media:

- Hide playback controls that cannot operate, but keep transcript and grid
  fully usable.

LID resources unavailable:

- Show that manual annotation is available.
- Optional LID plugin setup must be separate from core annotation.

## Spreadsheet View Specification

Module:

- `src/imbizo/gui/widgets/spreadsheet_view.py`

Class:

- `SpreadsheetViewWidget`

Purpose:

- Provide an Excel-like view for researchers who prefer tabular workflows.
- Support fast filtering, copying, bulk editing, and export-minded review.

Primary services:

- `AnnotationService`
- `ExportService`
- `ProvenanceService`

### Spreadsheet Layout

```text
+--------------------------------------------------------------------------+
| Toolbar: Search | Filter | Bulk Edit | Copy Rows | Export Visible Rows    |
+--------------------------------------------------------------------------+
| Row group sidebar | Spreadsheet grid                                      |
|                   |                                                       |
| Documents         | Segment ID | Speaker | Time | Token | Language | ...  |
| Scenes            |                                                       |
| Speakers          |                                                       |
+-------------------+-------------------------------------------------------+
| Selection summary | visible rows | changed rows | autosave state          |
+--------------------------------------------------------------------------+
```

### Required Columns

- Document.
- Scene.
- Speaker.
- Segment order.
- Segment start time.
- Segment end time.
- Segment text.
- Token order.
- Token text.
- Normalized token.
- Language label.
- Source marker.
- Matrix Language.
- Embedded Language.
- Switch type.
- Linguistic status.
- Direction.
- Trigger word or phrase.
- Researcher confidence.
- Tags.
- Memo excerpt.

### Spreadsheet Interactions

Selection:

- Single cell.
- Row.
- Multi-row.
- Column.
- Range selection with keyboard.

Editing:

- Direct cell editing for annotation fields.
- Paste from clipboard for compatible columns.
- Find and replace on selected fields.
- Bulk edit dialog for selected rows.

Sorting and filtering:

- Sort by document, speaker, scene, time, language, switch type, trigger, or
  confidence.
- Filter controls mirror annotation editor filters.

Copy and export:

- Copy selected rows as TSV to clipboard.
- Export visible rows to CSV or XLSX through `ExportService`.

Safety:

- Bulk edits require a confirmation summary showing affected row count and
  fields.
- Manual edits supersede auto annotations, never the reverse.
- The app must preserve an undo path for bulk changes.

## Timeline View Specification

Module:

- `src/imbizo/gui/widgets/timeline_view.py`

Class:

- `TimelineViewWidget`

Purpose:

- Provide an ELAN-familiar timeline for segment timing, speaker turns, language
  spans, and code-switch events.

Primary services:

- `AnnotationService`
- `audio.PlaybackController`
- `audio.WaveformCache`

### Timeline Layout

```text
+--------------------------------------------------------------------------+
| Transport: Play | Pause | Stop | Time | Zoom | Fit | Speaker filter       |
+--------------------------------------------------------------------------+
| Time ruler                                                                |
+--------------------------------------------------------------------------+
| Waveform lane                                                             |
+--------------------------------------------------------------------------+
| Speaker lanes                                                             |
| Speaker A: [utterance span] [utterance span]                              |
| Speaker B:       [utterance span] [utterance span]                        |
+--------------------------------------------------------------------------+
| Language lanes                                                            |
| English:   [token/span]       [token/span]                                |
| isiZulu:         [token/span]       [token/span]                          |
| Mixed:                  [span]                                            |
+--------------------------------------------------------------------------+
| Selected segment transcript and annotation summary                         |
+--------------------------------------------------------------------------+
```

### Timeline Elements

- Time ruler.
- Waveform lane.
- Speaker lanes.
- Segment blocks.
- Token or phrase language spans.
- Switch markers.
- Trigger markers.
- Playhead.

Behavior:

- Clicking a segment block selects it across all tabs.
- Double-clicking a block plays the associated media interval.
- Dragging segment boundaries edits timing only after confirmation.
- Zoom controls support detailed token review and full-interview overview.
- Switch markers use direction indicators and language colors.

Editing:

- MVP editing is limited to selecting segments, editing timing, and opening the
  selected item in the annotation editor.
- Full drag-to-segment editing can be post-MVP if necessary.

Accessibility:

- Timeline information must also be available in list/table form.
- Keyboard users can move by previous/next segment and previous/next switch.

## Metrics Dashboard Specification

Module:

- `src/imbizo/gui/widgets/metrics_dashboard.py`

Class:

- `MetricsDashboardWidget`

Purpose:

- Compute and display transparent offline quantitative metrics from current
  annotations.

Primary services:

- `MetricsService`
- `ExportService`
- `AnnotationService`

### Metrics Dashboard Layout

```text
+--------------------------------------------------------------------------+
| Metric selector | Scope selector | Filters | Compute | Export             |
+--------------------------------------------------------------------------+
| Formula panel                         | Result summary                    |
|                                       |                                   |
| Metric name                           | Tables                            |
| Formula version                       | Small charts                      |
| Inputs used                           | Warnings                          |
| Reproducibility notes                 |                                   |
+---------------------------------------+-----------------------------------+
| Detailed results table                                                    |
+--------------------------------------------------------------------------+
| Prior metric runs                                                         |
+--------------------------------------------------------------------------+
```

### Supported Metrics

MVP metric choices:

- Language proportion.
- Switch count.
- Switch density.
- Dominant language per utterance.
- M-index.
- I-index.
- Burstiness.
- Switch-trigger co-occurrence table.
- KWIC concordance.

### Metric Controls

Scope selector:

- Whole project.
- Speaker.
- Scene.
- Transcript document.
- Current filter.

Filters:

- Language.
- Speaker.
- Scene.
- Time range.
- Tag.
- Manual-only annotations.
- Include imported annotations.
- Include accepted auto annotations.

Compute action:

- Runs through `MetricsService.compute_metrics(...)`.
- Shows progress for large projects.
- Stores `MetricRun` and `MetricResult` records.

Formula panel:

- Shows formula name.
- Shows formula version.
- Shows numerator and denominator definitions.
- Shows which annotation sources are included.
- Shows input counts.
- Links to local formula documentation files.

Result display:

- Tables are primary.
- Simple local charts are allowed if they do not hide exact values.
- Charts must have text/table equivalents.

Export:

- CSV and XLSX for metric tables.
- HTML report can include selected metric tables.
- Exported files must be reproducible from visible result tables.

Warnings:

- Show when no manual annotations are present.
- Show when effective annotations include auto suggestions.
- Show when a metric has too few tokens or switches to be meaningful.

## Project Settings Specification

Module:

- `src/imbizo/gui/widgets/project_settings.py`

Class:

- `ProjectSettingsWidget`

Purpose:

- Edit project metadata, expected languages, user-defined language tags,
  participants, ethics notes, accessibility preferences, and optional plugin
  state.

Primary services:

- `ProjectService`
- `AnnotationService`
- `MorphologyService`
- `ProvenanceService`

### Project Settings Layout

```text
+--------------------------------------------------------------------------+
| Settings navigation                                                       |
| Project details | Languages | Participants | Ethics | Dictionaries | UI   |
+-------------------+------------------------------------------------------+
| Section list       | Settings form                                        |
|                   |                                                      |
|                   | Field groups, tables, and local validation messages   |
+-------------------+------------------------------------------------------+
| Apply | Revert | Save status                                             |
+--------------------------------------------------------------------------+
```

### Project Details Section

Fields:

- Project title.
- Subtitle.
- Researcher.
- Location.
- Project date.
- Participants summary.
- Expected languages summary.
- Notes.

Behavior:

- Saves to `project_metadata`.
- Updates window title and project status display.
- Shows validation errors beside fields.

### Languages Section

Fields and tables:

- Language code.
- Name.
- Autonym.
- Category.
- Color.
- Expected language flag.
- User-defined flag.
- Notes.

Required actions:

- Add language.
- Edit language.
- Disable or hide language from active lists when safe.
- Change color.
- Restore default special labels if missing.

Rules:

- Mandatory supported languages are present by default.
- User-defined tags such as Tsotsitaal, Iscamtho, and Kaaps are allowed.
- Special labels unknown, mixed, borrowing, and proper noun must remain
  available.
- Deleting a language used by annotations should be blocked or converted into a
  safe inactive state.

### Participants Section

Fields:

- Participant code.
- Display name.
- Role.
- Consent status.
- Demographic notes as structured local fields where configured.
- General notes.

Behavior:

- Participants can be linked to speaker labels.
- Speaker labels remain usable even when participant metadata is incomplete.

### Ethics Section

Fields:

- Ethics notes.
- Consent notes.
- Data handling notes.
- Local anonymization notes.

Behavior:

- All fields are stored locally.
- The app must not provide cloud backup prompts here.
- Exports can optionally include or exclude ethics notes.

### Dictionaries Section

Purpose:

- Edit project-local morphology dictionaries.

Fields:

- Language.
- Surface form.
- Category.
- Gloss.
- Source.
- Active flag.
- Notes.

Behavior:

- Default entries can be copied into the project.
- User entries are preserved during updates.
- Suggestions in annotation screens refresh after dictionary edits.

### UI And Accessibility Section

Fields:

- Font size.
- Theme: default or high contrast.
- Row height.
- Reduce animation.
- Autosave delay.
- Locale.

Behavior:

- Font size changes apply immediately.
- High contrast applies immediately.
- Locale changes may require restart in the MVP.

### Optional Plugins Section

Purpose:

- Show optional plugin state without making plugins required.

Rows:

- Local ASR providers.
- Optional AfroLID provider.
- Additional language resources.
- Morphology providers.

Required labels:

- Not installed.
- Installed locally.
- Enabled.
- Disabled.
- Requires local resource.

Rules:

- No automatic downloads in MVP.
- Enabling a plugin requires explicit researcher action.
- Core annotation and export workflows must remain available with all plugins
  disabled.

## Dialog Specifications

### Create Project Dialog

Fields:

- Project folder.
- Title.
- Researcher.
- Location.
- Project date.
- Expected languages.
- Ethics notes.

Behavior:

- Shows the folder that will contain `project.sqlite`.
- Validates write access before creation.
- Creates a local folder only after confirmation.

### Import Dialog

Fields:

- Source file path.
- Detected format.
- Copy destination preview.
- Link to existing media or transcript document.
- Import options relevant to the detected format.

Behavior:

- Confirms source files will be copied and not modified.
- Shows an import report after completion.
- Offers to open the imported document in the annotation editor.

### Export Dialog

Fields:

- Export format.
- Destination path.
- Scope.
- Include manual annotations.
- Include imported annotations.
- Include accepted auto annotations.
- Include memos.
- Include ethics notes.

Behavior:

- Warns if exporting auto annotations.
- Writes only local files.
- Opens the export folder after success only if the OS action is available and
  safe.

### Bulk Edit Dialog

Fields:

- Selected row count.
- Field to change.
- New value.
- Optional filter preview.
- Confirmation summary.

Behavior:

- Requires explicit confirmation.
- Creates undo data.
- Records provenance.

## Visual Design Specification

Overall style:

- Quiet, dense, research-focused desktop tool.
- Avoid marketing-style hero areas.
- Avoid decorative imagery.
- Prefer clear tables, split panes, toolbars, and dockable panels.

Color:

- Language colors must be distinct enough for quick scanning.
- Color must never be the only signal; labels and source markers are required.
- High-contrast theme must preserve language differentiation.

Typography:

- Use system fonts by default.
- Font size must be scalable.
- Avoid viewport-based font scaling.
- Table text must not overlap controls.

Spacing:

- Compact, consistent spacing suitable for long annotation sessions.
- Table row height configurable.
- Split pane sizes persist in app settings.

## Accessibility Specification

Keyboard:

- All primary actions reachable by keyboard.
- Tab order follows visual order.
- Tables support arrow-key navigation.
- Combo boxes open with keyboard.
- Segment navigation supports previous and next shortcuts.

Screen readers:

- Controls have accessible names from localized strings.
- Source markers must be readable as text, not color alone.
- Timeline data has table/list equivalents.

Contrast:

- High-contrast theme available from the View menu and settings.
- Selection, focus, and error states must pass high-contrast review.

Scalable text:

- UI remains usable when font size is increased.
- Panels scroll when needed rather than clipping text.

## State And Persistence Rules

Autosave:

- Annotation edits autosave to SQLite.
- Memos autosave after idle delay.
- Project settings save after Apply or explicit Save.
- Autosave failures must be visible and recoverable.

View state:

- Last active tab.
- Split pane sizes.
- Visible columns.
- Column widths.
- Filters.
- Font size.
- Theme.

Research data:

- View preferences may live in app settings.
- Project-specific filters and language colors live in the project folder.
- Research content must not be stored in app-level settings outside the project.

## Service Wiring Summary

| Screen | Primary service calls |
| --- | --- |
| Main window | `ProjectService.create_project`, `open_project`, `close_project`, `export_project_zip`, `import_project_zip` |
| Annotation editor | `AnnotationService.load_editor_state`, `save_token_annotation`, `save_segment_annotation`, `search_annotations` |
| Annotation editor auto labels | `LidService.run_lid_for_document`, `accept_suggestion`, `AnnotationService.reject_auto_annotation` |
| Annotation editor morphology | `MorphologyService.suggest_splits`, `save_manual_split` |
| Spreadsheet view | `AnnotationService.search_annotations`, `bulk_edit`, `ExportService.export` |
| Timeline view | `AnnotationService.load_editor_state`, `PlaybackController.play` |
| Metrics dashboard | `MetricsService.compute_metrics`, `get_results`, `ExportService.export` |
| Project settings | `ProjectService` metadata updates, language repository updates, `MorphologyService.save_dictionary_entry` |

## MVP Acceptance Checklist

- A researcher can create or open a local project from the main window.
- A researcher can import a transcript or EAF and land in the annotation editor.
- The annotation editor shows waveform, transcript, annotation grid, memo pane,
  and language legend together when media is available.
- Token-level annotations can be edited manually and autosaved.
- Automatic labels are visibly marked as auto and can be accepted, overridden,
  or rejected.
- Spreadsheet view supports filtering, editing, copying, and bulk edit.
- Timeline view supports selecting and playing segments in an ELAN-familiar
  arrangement.
- Metrics dashboard computes and displays M-index, I-index, and burstiness with
  transparent formula context.
- Project settings can edit metadata, languages, participants, ethics notes,
  dictionaries, and accessibility preferences.
- All core screens work offline and make no network calls.

## Non-Goals For MVP GUI

- Cloud sync UI.
- Account creation or login UI.
- Commercial LLM features.
- Automatic translation as a default screen.
- Bundled high-end ASR workflow.
- Required internet downloads for language models.
- Hidden black-box interpretation of code-switching meaning.
