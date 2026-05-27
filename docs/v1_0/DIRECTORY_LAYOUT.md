# v1.0 Deliverable 2 — Updated Directory Layout

This document describes the planned v1.0 repository layout for the A1
Noun-Class Engine, A2 Concord Agreement Tracker, and B1 4-M Model Annotation
Layer. It is a layout specification only; implementation files are not created
in this deliverable.

## 1. Tree-Style Listing

```text
Imbizo/
|-- pyproject.toml [MOD]
|-- README.md [MOD]
|-- PRINCIPLES.md [MOD]
|-- docs/
|   |-- ARCHITECTURE_OVERVIEW.md [MOD]
|   |-- DATA_MODEL.md [MOD]
|   |-- MODULE_BREAKDOWN.md [MOD]
|   |-- GUI_SPECIFICATIONS.md [MOD]
|   |-- REFERENCES.md [MOD]
|   |-- noun_classes.md [NEW]
|   |-- four_m_model.md [NEW]
|   |-- v1_0/
|       |-- INCREMENT_OVERVIEW.md [MOD]
|       |-- DIRECTORY_LAYOUT.md [NEW]
|-- dictionaries/ [NEW]
|   |-- README.md [NEW]
|   |-- noun_classes/ [NEW]
|   |   |-- zul.yaml [NEW]
|   |   |-- xho.yaml [NEW]
|   |   |-- sot.yaml [NEW]
|   |   |-- tsn.yaml [NEW]
|   |-- concord/ [NEW]
|   |   |-- zul.yaml [NEW]
|   |   |-- xho.yaml [NEW]
|   |   |-- sot.yaml [NEW]
|   |   |-- tsn.yaml [NEW]
|   |-- four_m/ [NEW]
|       |-- eng.yaml [NEW]
|       |-- afr.yaml [NEW]
|       |-- zul.yaml [NEW]
|       |-- xho.yaml [NEW]
|       |-- sot.yaml [NEW]
|       |-- tsn.yaml [NEW]
|-- src/
|   |-- imbizo/
|       |-- core/
|       |   |-- __init__.py [MOD]
|       |   |-- annotation.py [MOD]
|       |   |-- morphology.py [MOD]
|       |   |-- metrics.py [MOD]
|       |   |-- export.py [MOD]
|       |   |-- provenance.py [MOD]
|       |   |-- migrations/ [NEW]
|       |   |   |-- __init__.py [NEW]
|       |   |   |-- v1_0.py [NEW]
|       |   |-- noun_class.py [NEW]
|       |   |-- concord.py [NEW]
|       |   |-- four_m.py [NEW]
|       |-- domain/
|       |   |-- annotations.py [MOD]
|       |   |-- pydantic_models.py [MOD]
|       |-- gui/
|       |   |-- main_window.py [MOD]
|       |   |-- widgets/
|       |       |-- annotation_editor.py [MOD]
|       |       |-- metrics_dashboard.py [MOD]
|       |       |-- project_settings.py [MOD]
|       |-- persistence/
|       |   |-- migrations.py [MOD]
|       |   |-- repositories.py [MOD]
|       |-- plugins/
|       |   |-- api.py [NEW]
|       |   |-- interfaces.py [MOD]
|       |   |-- registry.py [MOD]
|       |   |-- noun_class/ [NEW]
|       |   |   |-- manifest.toml [NEW]
|       |   |   |-- provider.py [NEW]
|       |   |-- concord/ [NEW]
|       |   |   |-- manifest.toml [NEW]
|       |   |   |-- provider.py [NEW]
|       |   |-- four_m/ [NEW]
|       |       |-- manifest.toml [NEW]
|       |       |-- provider.py [NEW]
|       |-- resources/
|           |-- i18n/
|           |   |-- en.json [MOD]
|           |-- templates/
|               |-- report.html.j2 [MOD]
|-- tests/
|   |-- unit/ ... [MVP tests summarized]
|   |-- test_noun_class.py [NEW]
|   |-- test_concord.py [NEW]
|   |-- test_four_m.py [NEW]
|-- packaging/ ... [MVP packaging retained]
|-- scripts/ ... [MVP scripts retained]
|-- examples/ ... [MVP examples retained]
```

## 2. Purpose Annotations

### New Directories

| Path | Purpose |
| --- | --- |
| `docs/v1_0/` | Holds v1.0 increment deliverables separately from the MVP deliverables. |
| `dictionaries/` | Stores canonical shipped dictionary sources before packaging, with no user research data. |
| `dictionaries/noun_classes/` | Stores opt-in noun-class lookup data for supported Bantu languages. |
| `dictionaries/concord/` | Stores opt-in concord pattern lookup data for agreement checking. |
| `dictionaries/four_m/` | Stores opt-in 4-M category hints for languages supported by the MVP. |
| `src/imbizo/core/migrations/` | Stores additive versioned migrations that extend MVP project databases safely. |
| `src/imbizo/plugins/noun_class/` | Contains the bundled local plug-in provider for noun-class suggestions. |
| `src/imbizo/plugins/concord/` | Contains the bundled local plug-in provider for concord agreement suggestions. |
| `src/imbizo/plugins/four_m/` | Contains the bundled local plug-in provider for 4-M morpheme-category suggestions. |

### New Files

| Path | Purpose |
| --- | --- |
| `docs/noun_classes.md` | Explains noun-class annotation fields, dictionary limits, and researcher override practice. |
| `docs/four_m_model.md` | Explains optional 4-M tagging and how it coexists with non-MLF approaches. |
| `docs/v1_0/DIRECTORY_LAYOUT.md` | Defines this v1.0 directory layout. |
| `dictionaries/README.md` | Documents dictionary file format, provenance, semver, verification flags, and edit policy. |
| `dictionaries/noun_classes/zul.yaml` | Provides isiZulu noun-class seed entries, with unverified entries marked `verified: false` and a `note`. |
| `dictionaries/noun_classes/xho.yaml` | Provides isiXhosa noun-class seed entries, with unverified entries marked `verified: false` and a `note`. |
| `dictionaries/noun_classes/sot.yaml` | Provides Sesotho noun-class seed entries, with unverified entries marked `verified: false` and a `note`. |
| `dictionaries/noun_classes/tsn.yaml` | Provides Setswana noun-class seed entries, with unverified entries marked `verified: false` and a `note`. |
| `dictionaries/concord/zul.yaml` | Provides isiZulu concord pattern seed data for opt-in suggestion generation. |
| `dictionaries/concord/xho.yaml` | Provides isiXhosa concord pattern seed data for opt-in suggestion generation. |
| `dictionaries/concord/sot.yaml` | Provides Sesotho concord pattern seed data for opt-in suggestion generation. |
| `dictionaries/concord/tsn.yaml` | Provides Setswana concord pattern seed data for opt-in suggestion generation. |
| `dictionaries/four_m/eng.yaml` | Provides English 4-M hint categories used only as editable local suggestions. |
| `dictionaries/four_m/afr.yaml` | Provides Afrikaans 4-M hint categories used only as editable local suggestions. |
| `dictionaries/four_m/zul.yaml` | Provides isiZulu 4-M hint categories used only as editable local suggestions. |
| `dictionaries/four_m/xho.yaml` | Provides isiXhosa 4-M hint categories used only as editable local suggestions. |
| `dictionaries/four_m/sot.yaml` | Provides Sesotho 4-M hint categories used only as editable local suggestions. |
| `dictionaries/four_m/tsn.yaml` | Provides Setswana 4-M hint categories used only as editable local suggestions. |
| `src/imbizo/core/migrations/__init__.py` | Exposes core migration modules without importing optional feature code at startup. |
| `src/imbizo/core/migrations/v1_0.py` | Adds NULL-able v1.0 tables and columns for A1, A2, and B1 while preserving MVP project data. |
| `src/imbizo/core/noun_class.py` | Provides the public A1 API for noun-class lookups, suggestions, overrides, and provenance hooks. |
| `src/imbizo/core/concord.py` | Provides the public A2 API for concord candidate detection, review status, and metric inputs. |
| `src/imbizo/core/four_m.py` | Provides the public B1 API for optional 4-M morpheme-category annotation. |
| `src/imbizo/plugins/api.py` | Defines stable local plug-in contracts and re-exports backward-compatible interfaces. |
| `src/imbizo/plugins/noun_class/manifest.toml` | Declares the bundled noun-class plug-in for local discovery. |
| `src/imbizo/plugins/noun_class/provider.py` | Connects noun-class dictionary files to the `core.noun_class` suggestion API. |
| `src/imbizo/plugins/concord/manifest.toml` | Declares the bundled concord plug-in for local discovery. |
| `src/imbizo/plugins/concord/provider.py` | Connects concord dictionary files to the `core.concord` suggestion API. |
| `src/imbizo/plugins/four_m/manifest.toml` | Declares the bundled 4-M plug-in for local discovery. |
| `src/imbizo/plugins/four_m/provider.py` | Connects 4-M dictionary files to the `core.four_m` suggestion API. |
| `tests/test_noun_class.py` | Verifies noun-class dictionary loading, unverified-entry handling, and manual override precedence. |
| `tests/test_concord.py` | Verifies concord candidate generation, opt-in behavior, and persistence compatibility. |
| `tests/test_four_m.py` | Verifies optional 4-M tagging, export inclusion, and non-enforcement of a single theory. |

### Modified Files

| Path | Purpose |
| --- | --- |
| `pyproject.toml` | Adds YAML parsing and package-data inclusion for local dictionaries without adding network dependencies. |
| `README.md` | Introduces v1.0 features in researcher-facing language. |
| `PRINCIPLES.md` | Clarifies that A1, A2, and B1 remain auxiliary, opt-in, and manually overridable. |
| `docs/ARCHITECTURE_OVERVIEW.md` | Adds the v1.0 noun-class, concord, and 4-M modules to the architecture description. |
| `docs/DATA_MODEL.md` | Documents additive NULL-able v1.0 schema extensions. |
| `docs/MODULE_BREAKDOWN.md` | Adds public APIs and test strategies for A1, A2, and B1. |
| `docs/GUI_SPECIFICATIONS.md` | Adds UI placement and accessibility behavior for the new opt-in panels. |
| `docs/REFERENCES.md` | Adds references used by the v1.0 linguistic documentation. |
| `src/imbizo/core/annotation.py` | Exposes optional new annotation fields while preserving MVP annotation behavior. |
| `src/imbizo/core/morphology.py` | Connects existing morpheme-split workflows to noun-class, concord, and 4-M suggestions. |
| `src/imbizo/core/metrics.py` | Adds opt-in summary metrics for noun-class and concord review without changing MVP formulas. |
| `src/imbizo/core/export.py` | Adds optional export fields for A1, A2, and B1. |
| `src/imbizo/core/provenance.py` | Adds audit event helpers for suggestions, overrides, dictionary versions, and migration runs. |
| `src/imbizo/domain/annotations.py` | Adds nullable domain fields for noun class, concord relation, and 4-M tags. |
| `src/imbizo/domain/pydantic_models.py` | Extends JSON export models with optional v1.0 objects. |
| `src/imbizo/gui/main_window.py` | Adds menu and settings entry points for opt-in v1.0 panels. |
| `src/imbizo/gui/widgets/annotation_editor.py` | Adds optional columns and side-panel controls for A1, A2, and B1 annotation. |
| `src/imbizo/gui/widgets/metrics_dashboard.py` | Adds optional v1.0 summaries when the project enables them. |
| `src/imbizo/gui/widgets/project_settings.py` | Adds project-level toggles for noun-class, concord, and 4-M features. |
| `src/imbizo/persistence/migrations.py` | Registers the v1.0 migration while keeping MVP migration behavior intact. |
| `src/imbizo/persistence/repositories.py` | Adds repository methods for nullable v1.0 records and dictionary provenance. |
| `src/imbizo/plugins/interfaces.py` | Retains compatibility while delegating stable plug-in contracts to `plugins.api`. |
| `src/imbizo/plugins/registry.py` | Discovers bundled and project-local plug-ins from local manifests only. |
| `src/imbizo/resources/i18n/en.json` | Adds externalized strings for v1.0 controls, warnings, and review states. |
| `src/imbizo/resources/templates/report.html.j2` | Adds optional report sections for reviewed A1, A2, and B1 annotations. |

## 3. Conventions

### Dictionary YAML Versioning

Each YAML dictionary has both `schema_version` and `dictionary_version`.
`schema_version` describes the file shape; `dictionary_version` follows semver.
Patch releases correct spelling, notes, or provenance. Minor releases add
entries or optional fields. Major releases may rename fields or change category
meaning and therefore require a migration note. Breaking dictionary changes
never rewrite project overrides automatically; the app records the old and new
dictionary versions in provenance and asks the researcher before applying a
mapping. Any entry not checked against a cited source or community review must
carry `verified: false` and a plain-language `note`.

### Local Plug-In Discovery

At startup, `plugins.registry` scans only local manifest files bundled with the
application and opt-in project-local manifests. It does not query package
indexes, registries, web services, telemetry endpoints, or update servers.
Providers are imported lazily only after the project enables the corresponding
feature block, so A1/A2/B1 cannot slow down MVP workflows by default.

### Per-Project Dictionary Overrides

Shipped dictionaries are read-only application resources. Researcher edits and
community corrections live inside the project folder:

```text
project/
|-- dictionaries/
|   |-- noun_classes/
|   |-- concord/
|   |-- four_m/
|-- logs/provenance.jsonl
```

Overrides are never stored globally, because dictionary choices are part of the
research record and must travel with the project zip.

### Migration File Naming

Migration files use the target release name: `v1_0.py`, `v1_0_1.py`, and so on.
Each migration must be additive, idempotent, and safe to run against an MVP
database. New columns are NULL-able, new tables are optional, and migrations run
inside SQLite transactions with provenance records for start, success, and
failure.

