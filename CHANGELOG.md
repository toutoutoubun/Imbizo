# Changelog

## 1.5.0

- Adds sister-language disambiguation, triggered-switching profiles,
  mixed-code variety mode, phonological integration scoring, LIDES/CHAT export,
  and community-review workflows.
- Adds dictionary and processing-resource bootstrap tooling with licence-tier
  metadata, offline bundles, provenance records, and compliance checks.
- Adds release packaging checks, local build artifacts, SHA-256 manifests, and
  maintainer documentation for air-gapped distribution.

## 1.0.0

- Adds optional noun-class, concord, and 4-M annotation support.
- Adds local YAML dictionaries:
  - `dictionaries/noun_classes/{zul,xho,sot,tsn}.yaml` version `0.1.0`
  - `dictionaries/concord/{zul,xho,sot,tsn}.yaml` version `0.1.0`
  - `dictionaries/four_m/{eng,afr,zul,xho,sot,tsn}.yaml` version `0.1.0`
- Adds `imbizo-cs migrate` and `imbizo-cs restore` for offline project
  upgrades and rollback.

## 0.1.0

- Initial offline-first MVP implementation.
- Local project folders with SQLite storage.
- Transcript import, manual annotation, local LID suggestions, metrics, and
  local export workflows.
