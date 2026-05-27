"""Offline runtime registry for resource licence obligations.

The registry reads provenance metadata already present on local disk. It never
contacts the network. The purpose is political as much as technical: reports
and startup warnings should make licence constraints visible instead of hiding
them behind software defaults.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[4]
SCAN_ROOTS = (
    PROJECT_ROOT / "dictionaries" / "imported",
    PROJECT_ROOT / "models",
    PROJECT_ROOT / "corpora",
    PROJECT_ROOT / "processing",
)


@dataclass(frozen=True)
class LicenceClassification:
    """Parsed licence classification for one local resource."""

    spdx_id: str
    tier: int
    fosl_compatible: bool
    combinable_with_agpl: str
    commercial_use_restricted: bool
    sharealike_required: bool
    downstream_obligations: tuple[str, ...]
    redistribution_notice: str

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "LicenceClassification":
        """Create a classification object from YAML metadata."""

        return cls(
            spdx_id=str(data.get("spdx_id", "")),
            tier=int(data.get("tier", 0) or 0),
            fosl_compatible=bool(data.get("fosl_compatible", False)),
            combinable_with_agpl=str(data.get("combinable_with_agpl", "")),
            commercial_use_restricted=bool(data.get("commercial_use_restricted", False)),
            sharealike_required=bool(data.get("sharealike_required", False)),
            downstream_obligations=tuple(str(item) for item in data.get("downstream_obligations", []) or []),
            redistribution_notice=str(data.get("redistribution_notice", "")),
        )


@dataclass(frozen=True)
class ResourceLicenceInfo:
    """Licence metadata for an active imported dictionary or processing resource."""

    resource_id: str
    resource_name: str
    path: Path
    origin_license: str
    classification: LicenceClassification


@dataclass(frozen=True)
class DownstreamLicenceReport:
    """Structured report of licence obligations that may propagate downstream."""

    resources: tuple[ResourceLicenceInfo, ...]
    nc_resources: tuple[ResourceLicenceInfo, ...] = field(default_factory=tuple)
    sharealike_resources: tuple[ResourceLicenceInfo, ...] = field(default_factory=tuple)
    notices: tuple[str, ...] = field(default_factory=tuple)

    @property
    def has_obligations(self) -> bool:
        """Return True when at least one active resource has propagation text."""

        return bool(self.resources)


def list_active_resources() -> list[ResourceLicenceInfo]:
    """Scan local resource indexes and imported YAMLs for licence metadata.

    The scan covers `dictionaries/imported/`, `models/`, `corpora/`, and
    `processing/`. It deliberately uses only local filesystem reads.
    """

    resources: list[ResourceLicenceInfo] = []
    for path in _candidate_yaml_files(SCAN_ROOTS):
        data = _load_yaml_mapping(path)
        source = data.get("source") if isinstance(data, dict) else None
        if not isinstance(source, dict):
            continue
        classification_data = source.get("licence_classification")
        if not isinstance(classification_data, dict):
            continue
        resources.append(
            ResourceLicenceInfo(
                resource_id=str(data.get("resource_id") or data.get("dictionary_kind") or path.stem),
                resource_name=str(source.get("origin_name") or data.get("name") or path.stem),
                path=path,
                origin_license=str(source.get("origin_license") or classification_data.get("spdx_id") or ""),
                classification=LicenceClassification.from_mapping(classification_data),
            )
        )
    return resources


def has_nc_resources() -> bool:
    """True if any active resource is Tier 2 with a NonCommercial restriction."""

    return any(
        info.classification.tier == 2 and info.classification.commercial_use_restricted
        for info in list_active_resources()
    )


def has_sharealike_resources() -> bool:
    """True if any active resource carries a ShareAlike clause."""

    return any(info.classification.sharealike_required for info in list_active_resources())


def downstream_propagation_summary() -> DownstreamLicenceReport:
    """Summarize licence obligations for report rendering and warnings."""

    resources = tuple(list_active_resources())
    nc_resources = tuple(
        info for info in resources if info.classification.tier == 2 and info.classification.commercial_use_restricted
    )
    sharealike_resources = tuple(info for info in resources if info.classification.sharealike_required)
    notices = tuple(
        notice
        for notice in _unique(info.classification.redistribution_notice for info in resources)
        if notice.strip()
    )
    return DownstreamLicenceReport(
        resources=resources,
        nc_resources=nc_resources,
        sharealike_resources=sharealike_resources,
        notices=notices,
    )


def _candidate_yaml_files(roots: Iterable[Path]) -> Iterable[Path]:
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.yaml")):
            if "_provenance" in path.parts:
                continue
            yield path


def _load_yaml_mapping(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return {}
    if isinstance(data, dict):
        return data
    return {}


def _unique(values: Iterable[str]) -> Iterable[str]:
    seen: set[str] = set()
    for value in values:
        if value not in seen:
            seen.add(value)
            yield value
