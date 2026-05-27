# v1.5 Deliverable 2 - Updated Directory Layout

This document describes the planned v1.5 repository layout for C1 Sister
Language Disambiguator, C2 Triggered Switching Detector, C3 Mixed-Code Variety
Mode, D1 Borrowing Integration Score v2, D2 Comparable Subcorpus Exporter, and
D3 Community Review Workflow. It is a layout specification only; implementation
files are not created in this deliverable.

## 1. Tree-Style Listing

```text
Imbizo/
|-- pyproject.toml [MOD]
|-- README.md [MOD]
|-- PRINCIPLES.md [MOD]
|-- INSTALL_OFFLINE.md [MOD]
|-- CHANGELOG.md [MOD]
|-- docs/
|   |-- REFERENCES.md [MOD]
|   |-- ROADMAP_PLUGINS.md [MOD]
|   |-- sister_languages.md [NEW]
|   |-- triggers.md [NEW]
|   |-- mixed_codes.md [NEW]
|   |-- phonological_integration.md [NEW]
|   |-- interop_lides_chat.md [NEW]
|   |-- community_review.md [NEW]
|   |-- v1_5/ [NEW]
|   |   |-- INCREMENT_OVERVIEW.md [NEW]
|   |   |-- DIRECTORY_LAYOUT.md [NEW]
|   |-- MVP and v1.0 docs retained unchanged unless listed above
|-- dictionaries/ [MOD]
|   |-- README.md [MOD]
|   |-- noun_classes/ ... [v1.0 retained]
|   |-- concord/ ... [v1.0 retained]
|   |-- four_m/ ... [v1.0 retained]
|   |-- sister_lang/ [NEW]
|   |   |-- zul_vs_xho.yaml [NEW]
|   |   |-- sot_vs_tsn.yaml [NEW]
|   |   |-- nso_vs_sot_vs_tsn.yaml [NEW]
|   |-- triggers/ [NEW]
|   |   |-- eng.yaml [NEW]
|   |   |-- afr.yaml [NEW]
|   |   |-- zul.yaml [NEW]
|   |   |-- xho.yaml [NEW]
|   |   |-- sot.yaml [NEW]
|   |   |-- tsn.yaml [NEW]
|   |-- mixed_code/ [NEW]
|   |   |-- tsotsitaal.yaml [NEW]
|   |   |-- iscamtho.yaml [NEW]
|   |   |-- kaaps.yaml [NEW]
|   |   |-- sabela.yaml [NEW]
|   |-- phonology/ [NEW]
|       |-- zul.yaml [NEW]
|       |-- xho.yaml [NEW]
|       |-- sot.yaml [NEW]
|       |-- tsn.yaml [NEW]
|       |-- afr.yaml [NEW]
|-- src/
|   |-- imbizo/
|       |-- __init__.py [MOD]
|       |-- cli.py [MOD]
|       |-- core/
|       |   |-- __init__.py [MOD]
|       |   |-- annotation.py [MOD]
|       |   |-- metrics.py [MOD]
|       |   |-- provenance.py [MOD]
|       |   |-- noun_class.py [MOD]
|       |   |-- concord.py [MOD]
|       |   |-- four_m.py [MOD]
|       |   |-- migrations/
|       |   |   |-- __init__.py [MOD]
|       |   |   |-- v1_0.py [v1.0 retained]
|       |   |   |-- v1_5.py [NEW]
|       |   |-- sister_lang.py [NEW]
|       |   |-- triggers.py [NEW]
|       |   |-- mixed_code.py [NEW]
|       |   |-- integration_v2.py [NEW]
|       |   |-- interop/ [NEW]
|       |   |   |-- __init__.py [NEW]
|       |   |   |-- lides.py [NEW]
|       |   |   |-- chat_clan.py [NEW]
|       |   |-- community/ [NEW]
|       |       |-- __init__.py [NEW]
|       |       |-- review.py [NEW]
|       |-- gui/
|       |   |-- main_window.py [MOD]
|       |   |-- widgets/
|       |       |-- annotation_editor.py [MOD]
|       |       |-- metrics_dashboard.py [MOD]
|       |       |-- project_settings.py [MOD]
|       |-- plugins/
|       |   |-- api.py [MOD]
|       |   |-- registry.py [MOD]
|       |   |-- sister_lang/ [NEW]
|       |   |   |-- manifest.toml [NEW]
|       |   |   |-- provider.py [NEW]
|       |   |-- triggers/ [NEW]
|       |   |   |-- manifest.toml [NEW]
|       |   |   |-- provider.py [NEW]
|       |   |-- mixed_code/ [NEW]
|       |   |   |-- manifest.toml [NEW]
|       |   |   |-- provider.py [NEW]
|       |   |-- phonology/ [NEW]
|       |       |-- manifest.toml [NEW]
|       |       |-- provider.py [NEW]
|       |-- resources/
|           |-- i18n/
|           |   |-- en.json [MOD]
|           |-- templates/
|               |-- reports/ [MOD]
|                   |-- comparable_subcorpus.html.j2 [NEW]
|                   |-- community_review_packet.html.j2 [NEW]
|-- tests/
|   |-- MVP and v1.0 tests retained
|   |-- test_sister_lang.py [NEW]
|   |-- test_triggers.py [NEW]
|   |-- test_mixed_code.py [NEW]
|   |-- test_integration_v2.py [NEW]
|   |-- test_interop_lides.py [NEW]
|   |-- test_interop_chat.py [NEW]
|   |-- test_community_review.py [NEW]
|-- scripts/
|   |-- create_offline_bundle.py [MOD]
|   |-- verify_review_packet.py [NEW]
|-- packaging/ ... [MVP and v1.0 packaging retained]
|-- examples/ ... [MVP and v1.0 examples retained]
```

## 2. Purpose Annotations

### New Directories

| Path | Purpose |
| --- | --- |
| `docs/v1_5/` | Holds v1.5 increment deliverables separately from MVP and v1.0 documentation. |
| `dictionaries/sister_lang/` | Stores per-pair local evidence dictionaries for closely related language disambiguation. |
| `dictionaries/triggers/` | Stores local trigger-candidate dictionaries used by the Clyne-style triggered switching detector. |
| `dictionaries/mixed_code/` | Stores variety profiles for named mixed-code practices such as Tsotsitaal, Iscamtho, Kaaps, and Sabela. |
| `dictionaries/phonology/` | Stores optional phonological and tonal evidence tables for Borrowing Integration Score v2. |
| `src/imbizo/core/interop/` | Contains standards-oriented exporters that translate Imbizo annotations into comparable corpus formats. |
| `src/imbizo/core/community/` | Contains offline review-packet creation, validation, and import logic for community dictionary review. |
| `src/imbizo/plugins/sister_lang/` | Contains the bundled local provider for sister-language dictionary registration and lookup. |
| `src/imbizo/plugins/triggers/` | Contains the bundled local provider for trigger dictionary registration and candidate generation. |
| `src/imbizo/plugins/mixed_code/` | Contains the bundled local provider for mixed-code variety profiles and opt-in project settings. |
| `src/imbizo/plugins/phonology/` | Contains the bundled local provider for phonology dictionaries used by integration scoring. |

### New Files

| Path | Purpose |
| --- | --- |
| `docs/sister_languages.md` | Explains why sister-language disambiguation is uncertain, advisory, and manually overridable. |
| `docs/triggers.md` | Explains triggered-switching analysis, candidate status, and researcher confirmation workflow. |
| `docs/mixed_codes.md` | Explains mixed-code variety mode and why named varieties should not be flattened into simple CS pairs. |
| `docs/phonological_integration.md` | Explains optional phonological and tonal evidence for borrowing integration without requiring audio expertise. |
| `docs/interop_lides_chat.md` | Documents LIDES and CHAT/CLAN export behavior, sidecar files, and known representational limits. |
| `docs/community_review.md` | Documents offline dictionary review packets, reviewer scope, and project-local acceptance policy. |
| `docs/v1_5/INCREMENT_OVERVIEW.md` | Provides the v1.5 plain-language overview, architecture diagram, and risk register. |
| `docs/v1_5/DIRECTORY_LAYOUT.md` | Defines this v1.5 directory layout. |
| `dictionaries/sister_lang/zul_vs_xho.yaml` | Provides local, evidence-based cues for isiZulu versus isiXhosa disambiguation, with uncertain entries marked `verified: false`. |
| `dictionaries/sister_lang/sot_vs_tsn.yaml` | Provides local, evidence-based cues for Sesotho versus Setswana disambiguation, with uncertainty preserved. |
| `dictionaries/sister_lang/nso_vs_sot_vs_tsn.yaml` | Provides optional three-way cues for Sepedi, Sesotho, and Setswana where a project enables post-MVP language coverage. |
| `dictionaries/triggers/eng.yaml` | Lists English trigger candidates and cross-references relevant language, POS, and optional noun-class contexts. |
| `dictionaries/triggers/afr.yaml` | Lists Afrikaans trigger candidates and cross-references relevant language, POS, and optional noun-class contexts. |
| `dictionaries/triggers/zul.yaml` | Lists isiZulu trigger candidates, including optional links to v1.0 noun-class and concord evidence. |
| `dictionaries/triggers/xho.yaml` | Lists isiXhosa trigger candidates, including optional links to v1.0 noun-class and concord evidence. |
| `dictionaries/triggers/sot.yaml` | Lists Sesotho trigger candidates, including optional links to v1.0 noun-class and concord evidence. |
| `dictionaries/triggers/tsn.yaml` | Lists Setswana trigger candidates, including optional links to v1.0 noun-class and concord evidence. |
| `dictionaries/mixed_code/tsotsitaal.yaml` | Defines a project-local Tsotsitaal profile structure with labels, notes, and non-prescriptive evidence categories. |
| `dictionaries/mixed_code/iscamtho.yaml` | Defines a project-local Iscamtho profile structure with community-review status and override notes. |
| `dictionaries/mixed_code/kaaps.yaml` | Defines a project-local Kaaps profile structure for mixed-code annotation without forcing standard Afrikaans assumptions. |
| `dictionaries/mixed_code/sabela.yaml` | Defines a project-local Sabela profile structure with explicit uncertainty and local review fields. |
| `dictionaries/phonology/zul.yaml` | Provides optional isiZulu phonological and tonal adaptation cues for integration scoring, with confidence metadata. |
| `dictionaries/phonology/xho.yaml` | Provides optional isiXhosa phonological and tonal adaptation cues for integration scoring, with confidence metadata. |
| `dictionaries/phonology/sot.yaml` | Provides optional Sesotho phonological and tonal adaptation cues for integration scoring, with confidence metadata. |
| `dictionaries/phonology/tsn.yaml` | Provides optional Setswana phonological and tonal adaptation cues for integration scoring, with confidence metadata. |
| `dictionaries/phonology/afr.yaml` | Provides optional Afrikaans phonological adaptation cues for mixed Afrikaans-host or Afrikaans-source analyses. |
| `src/imbizo/core/migrations/v1_5.py` | Adds NULL-able v1.5 schema extensions while preserving MVP and v1.0 project data. |
| `src/imbizo/core/sister_lang.py` | Provides the C1 public API for loading per-pair dictionaries, producing ranked evidence, and preserving ambiguity. |
| `src/imbizo/core/triggers.py` | Provides the C2 public API for local rule-based trigger candidate detection and review persistence. |
| `src/imbizo/core/mixed_code.py` | Provides the C3 public API for opt-in mixed-code variety profiles and span-level annotation behavior. |
| `src/imbizo/core/integration_v2.py` | Provides the D1 public API for transparent, configurable integration scoring with optional phonological evidence. |
| `src/imbizo/core/interop/__init__.py` | Exposes interop exporters without importing optional exporter dependencies at startup. |
| `src/imbizo/core/interop/lides.py` | Exports comparable subcorpora to a LIDES-oriented representation with Imbizo sidecar metadata. |
| `src/imbizo/core/interop/chat_clan.py` | Exports comparable subcorpora to CHAT/CLAN-compatible transcript files with Imbizo sidecar metadata. |
| `src/imbizo/core/community/__init__.py` | Exposes community-review helpers while keeping review workflows optional. |
| `src/imbizo/core/community/review.py` | Creates, validates, and imports offline review packets for dictionaries and variety profiles. |
| `src/imbizo/plugins/sister_lang/manifest.toml` | Declares the bundled sister-language plug-in for local-only discovery. |
| `src/imbizo/plugins/sister_lang/provider.py` | Connects sister-language dictionaries to `core.sister_lang`. |
| `src/imbizo/plugins/triggers/manifest.toml` | Declares the bundled triggered-switching plug-in for local-only discovery. |
| `src/imbizo/plugins/triggers/provider.py` | Connects trigger dictionaries to `core.triggers`. |
| `src/imbizo/plugins/mixed_code/manifest.toml` | Declares the bundled mixed-code variety plug-in for local-only discovery. |
| `src/imbizo/plugins/mixed_code/provider.py` | Connects mixed-code profiles to `core.mixed_code`. |
| `src/imbizo/plugins/phonology/manifest.toml` | Declares the bundled phonology plug-in for local-only discovery. |
| `src/imbizo/plugins/phonology/provider.py` | Connects phonology dictionaries to `core.integration_v2`. |
| `src/imbizo/resources/templates/reports/comparable_subcorpus.html.j2` | Renders a local report summarizing what was exported to LIDES or CHAT/CLAN. |
| `src/imbizo/resources/templates/reports/community_review_packet.html.j2` | Renders a human-readable offline review packet diff for community reviewers. |
| `tests/test_sister_lang.py` | Verifies dictionary loading, ambiguity preservation, and no forced language assignment. |
| `tests/test_triggers.py` | Verifies trigger candidate detection, false-positive controls, and provenance-ready review states. |
| `tests/test_mixed_code.py` | Verifies mixed-code profile loading and non-prescriptive variety-mode behavior. |
| `tests/test_integration_v2.py` | Verifies score bounds, optional-evidence behavior, and monotonicity under configurable weights. |
| `tests/test_interop_lides.py` | Verifies LIDES-oriented export structure and Imbizo sidecar preservation. |
| `tests/test_interop_chat.py` | Verifies CHAT/CLAN export structure and preservation of timestamps, speakers, and sidecar metadata. |
| `tests/test_community_review.py` | Verifies review-packet manifest validation, human-readable diff generation, and safe import behavior. |
| `scripts/verify_review_packet.py` | Checks an offline review packet manifest, hashes, and local signature before import. |

### Modified Files

| Path | Purpose |
| --- | --- |
| `pyproject.toml` | Adds package-data inclusion for v1.5 dictionaries and optional test dependencies without adding network behavior. |
| `README.md` | Adds a researcher-facing v1.5 section with sister-language, trigger, mixed-code, interop, and review workflows. |
| `PRINCIPLES.md` | Clarifies that mixed-code varieties and sister-language uncertainty must not be forced into one theoretical mould. |
| `INSTALL_OFFLINE.md` | Adds v1.5 offline upgrade and review-packet transfer instructions. |
| `CHANGELOG.md` | Records v1.5 additions and dictionary version snapshots. |
| `docs/REFERENCES.md` | Adds v1.5 references for triggered switching, mixed-code varieties, LIDES, and CHAT/CLAN. |
| `docs/ROADMAP_PLUGINS.md` | Updates post-v1.5 optional plug-in priorities without making any network-dependent feature core. |
| `dictionaries/README.md` | Adds v1.5 dictionary schemas, confidence fields, and community-review package rules. |
| `src/imbizo/__init__.py` | Updates the application version while preserving compatibility with earlier project schemas. |
| `src/imbizo/cli.py` | Adds v1.5 migration and review-packet commands while retaining v1.0 migrate/restore behavior. |
| `src/imbizo/core/annotation.py` | Adds nullable v1.5 annotation accessors for ambiguity, triggers, mixed-code spans, and integration v2 evidence. |
| `src/imbizo/core/metrics.py` | Adds opt-in summaries for trigger candidates, ambiguity rates, mixed-code spans, and integration v2 distributions. |
| `src/imbizo/core/provenance.py` | Adds audit event helpers for v1.5 suggestions, review packets, and interop exports. |
| `src/imbizo/core/noun_class.py` | Exposes noun-class data to trigger dictionaries without changing v1.0 semantics. |
| `src/imbizo/core/concord.py` | Exposes reviewed concord links to Integration Score v2 without changing v1.0 persistence. |
| `src/imbizo/core/four_m.py` | Allows mixed-code mode to mark MLF checks as advisory or not applicable. |
| `src/imbizo/gui/main_window.py` | Adds menu entry points for v1.5 opt-in workflows. |
| `src/imbizo/gui/widgets/annotation_editor.py` | Adds optional UI affordances for ambiguity, triggers, mixed-code spans, and phonological evidence. |
| `src/imbizo/gui/widgets/metrics_dashboard.py` | Adds optional v1.5 tabs for ambiguity, trigger, integration v2, and interop summaries. |
| `src/imbizo/gui/widgets/project_settings.py` | Adds project-level opt-in toggles for v1.5 feature blocks. |
| `src/imbizo/plugins/api.py` | Extends the local plug-in contract for sister-language, trigger, mixed-code, and phonology dictionaries. |
| `src/imbizo/plugins/registry.py` | Continues local-only discovery and adds v1.5 manifest types. |
| `src/imbizo/resources/i18n/en.json` | Adds externalized strings for v1.5 controls, warnings, and review states. |
| `scripts/create_offline_bundle.py` | Includes v1.5 dictionaries, docs, review scripts, and checksums in offline bundles. |

## 3. Conventions

### Sister-Language Dictionary Scope

Sister-language disambiguation dictionaries are scoped per comparison set, not
per individual language. A file such as `zul_vs_xho.yaml` stores evidence that
helps distinguish isiZulu from isiXhosa, while `nso_vs_sot_vs_tsn.yaml` stores
three-way evidence only for projects that opt into Sepedi-related analysis.
Each entry records the compared languages, the evidence type, the surface cue,
the confidence level, `verified`, and `note`. Ambiguous evidence is valid data;
the dictionary may explicitly say that a cue is shared rather than decisive.

### Trigger Dictionaries and v1.0 Cross-References

Trigger dictionaries are language-scoped because trigger candidates are often
searched relative to the token's language, lemma, POS, discourse function, or
neighboring context. They may cross-reference v1.0 noun-class and concord
dictionaries by stable identifiers, for example `noun_class_ref:
zul:class_9` or `concord_ref: zul:AC:9`. These references are advisory joins,
not hard dependencies: if noun-class dictionaries are disabled, trigger
detection still runs with the evidence available.

### Mixed-Code Variety Dictionaries

Mixed-code variety dictionaries are profile files rather than monolingual
lexicons. They can contain variety names, aliases, geographic or community
notes, common source-language pools, locally reviewed forms, caution notes,
and recommended UI warnings. They do not define a single "correct" grammar and
they must not replace project-local ethnographic memos. Standard-language
fields such as ISO language code may be plural, absent, or marked as
`not_applicable` where a named variety is not reducible to one source language.

### Phonology Dictionary Confidence

Phonology dictionaries declare the transcription basis for each block:
`ipa`, `orthographic`, `broad_phonetic`, `tone_marked`, `tone_unmarked`, or
`unknown`. Each cue carries a confidence level and a `requires_audio` flag.
When a project has only text transcripts, phonological evidence is reported as
unavailable rather than negative. Tone-related fields must state whether tone
was actually transcribed, inferred from orthography, or left unassessed.

### Community-Review Patch Packages

Community-review patches are zip files containing:

```text
review_packet.zip
|-- manifest.toml
|-- SIGNATURE.txt
|-- DIFF.md
|-- changes/
|   |-- dictionaries/...
|-- hashes/
|   |-- SHA256SUMS.txt
```

`manifest.toml` records the packet id, reviewer-supplied name or pseudonym,
review scope, source project version, dictionary versions, and consent to share
the patch. `SIGNATURE.txt` is a local detached signature or plain attestation,
depending on the reviewer's tooling. `DIFF.md` is a human-readable summary so a
researcher can inspect the change before import. Import never applies a patch
globally; it stages changes inside the current project until the researcher
accepts them.

### Plug-In Discovery

Plug-in discovery rules are unchanged from MVP and v1.0. The application scans
only bundled local manifests and project-local manifests. It does not contact
package indexes, plug-in registries, update servers, model hubs, telemetry
endpoints, or web APIs. Providers are imported lazily after a project enables
the relevant feature block, preserving low-resource startup behavior.
