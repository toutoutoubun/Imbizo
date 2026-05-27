# Changelog

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
