"""CI compliance checks for imported dictionary and processing-resource YAML files."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import click
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
IMPORTED_ROOT = PROJECT_ROOT / "dictionaries" / "imported"
LICENSES_ROOT = PROJECT_ROOT / "LICENSES"
REPORTS_ROOT = PROJECT_ROOT / "src" / "imbizo" / "resources" / "templates" / "reports"
PARTIAL_INCLUDE = 'partials/licence_propagation.html.j2'

REQUIRED_SOURCE_FIELDS = {
    "origin_name",
    "origin_url",
    "origin_license",
    "origin_version",
    "retrieved_on",
    "retrieved_sha256",
    "transformation_tool",
    "transformation_version",
    "transformation_date",
}

REQUIRED_LICENCE_CLASSIFICATION_FIELDS = {
    "spdx_id",
    "tier",
    "fosl_compatible",
    "combinable_with_agpl",
    "commercial_use_restricted",
    "sharealike_required",
    "downstream_obligations",
    "redistribution_notice",
}

PLACEHOLDER_MARKERS = (
    "REPLACE THIS FILE WITH THE VERBATIM LICENSE TEXT",
    "PLACEHOLDER",
    "TODO",
    "TBD",
)


def main() -> int:
    """Run compliance checks and return a process exit code."""

    failures: list[str] = []
    for path in _resource_yaml_files():
        failures.extend(_check_dictionary(path))
    failures.extend(_check_tier2_acknowledgement())
    failures.extend(_check_report_templates())
    failures.extend(_check_license_index())
    if failures:
        for failure in failures:
            click.echo(failure)
        return 1
    click.echo("Resource compliance checks passed.")
    return 0


def _resource_yaml_files() -> list[Path]:
    roots = [IMPORTED_ROOT, PROJECT_ROOT / "models", PROJECT_ROOT / "corpora", PROJECT_ROOT / "processing"]
    paths: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.yaml")):
            if "_provenance" in path.parts:
                continue
            paths.append(path)
    return paths


def _check_dictionary(path: Path) -> list[str]:
    failures: list[str] = []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        return [f"{path}: YAML root must be a mapping."]

    failures.extend(_check_header(path, data))
    failures.extend(_check_license_file(path, data))
    failures.extend(_check_entries(path, data))
    return failures


def _check_header(path: Path, data: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    for field in ("schema_version", "dictionary_kind", "content_version", "source", "review", "caveats"):
        if field not in data:
            failures.append(f"{path}: missing required top-level field `{field}`.")
    source = data.get("source")
    if not isinstance(source, dict):
        failures.append(f"{path}: `source` must be a mapping.")
    else:
        missing = sorted(field for field in REQUIRED_SOURCE_FIELDS if not source.get(field))
        if missing:
            failures.append(f"{path}: source header missing fields: {', '.join(missing)}.")
        failures.extend(_check_licence_classification(path, source))
    review = data.get("review")
    if not isinstance(review, dict):
        failures.append(f"{path}: `review` must be a mapping.")
    elif "last_reviewed_by" not in review:
        failures.append(f"{path}: review header missing `last_reviewed_by`.")
    return failures


def _check_licence_classification(path: Path, source: Mapping[str, Any]) -> list[str]:
    classification = source.get("licence_classification")
    if not isinstance(classification, dict):
        return [f"{path}: source.licence_classification is required."]
    failures: list[str] = []
    missing = sorted(field for field in REQUIRED_LICENCE_CLASSIFICATION_FIELDS if field not in classification)
    if missing:
        failures.append(f"{path}: licence_classification missing fields: {', '.join(missing)}.")
    if classification.get("tier") in (2, 3) and not str(classification.get("redistribution_notice", "")).strip():
        failures.append(f"{path}: Tier-{classification.get('tier')} resource lacks redistribution_notice.")
    obligations = classification.get("downstream_obligations")
    if not isinstance(obligations, list):
        failures.append(f"{path}: licence_classification.downstream_obligations must be a list.")
    if classification.get("combinable_with_agpl") not in {"combination", "aggregation_only", "none"}:
        failures.append(f"{path}: licence_classification.combinable_with_agpl has an invalid value.")
    return failures


def _check_license_file(path: Path, data: Mapping[str, Any]) -> list[str]:
    source = data.get("source")
    if not isinstance(source, dict):
        return []
    license_name = str(source.get("origin_license", ""))
    if not license_name:
        return [f"{path}: source.origin_license is empty."]
    license_file = _license_file_for(license_name)
    if not license_file.exists():
        return [f"{path}: license file missing for `{license_name}`: {license_file}."]
    text = license_file.read_text(encoding="utf-8", errors="replace")
    if _looks_like_placeholder_license(text):
        return [
            f"{path}: license file {license_file} still contains placeholder text. "
            "Replace it with the verbatim license text before shipping imported dictionaries."
        ]
    return []


def _check_entries(path: Path, data: Mapping[str, Any]) -> list[str]:
    entries = data.get("entries")
    if entries is None and data.get("dictionary_kind") == "processing_resource":
        return []
    if not isinstance(entries, list):
        return [f"{path}: `entries` must be a list."]
    review = data.get("review") if isinstance(data.get("review"), dict) else {}
    reviewer = str(review.get("last_reviewed_by", "PENDING_HUMAN_REVIEW"))
    failures: list[str] = []
    for index, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            failures.append(f"{path}: entry {index} must be a mapping.")
            continue
        verified = entry.get("verified")
        if verified is False:
            continue
        if verified is True and reviewer != "PENDING_HUMAN_REVIEW":
            continue
        failures.append(
            f"{path}: entry {index} must have verified: false, or a human reviewer "
            "must be recorded before verified: true is allowed."
        )
    return failures


def _check_tier2_acknowledgement() -> list[str]:
    tier2_paths: list[Path] = []
    for path in _resource_yaml_files():
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        source = data.get("source") if isinstance(data, dict) else None
        classification = source.get("licence_classification") if isinstance(source, dict) else None
        if isinstance(classification, dict) and classification.get("tier") == 2:
            tier2_paths.append(path)
    if not tier2_paths:
        return []
    ack_path = IMPORTED_ROOT / "_provenance" / "licence_acknowledgement.json"
    if not ack_path.exists():
        return ["Tier-2 resources are present but licence_acknowledgement.json is missing."]
    ack = yaml.safe_load(ack_path.read_text(encoding="utf-8")) or {}
    confirmations = ack.get("environment_confirmations") if isinstance(ack, dict) else None
    if not isinstance(confirmations, dict) or confirmations.get("IMBIZO_NC_ACCEPTED") is not True:
        return ["Tier-2 resources are present but IMBIZO_NC_ACCEPTED was not recorded at installation time."]
    return []


def _check_report_templates() -> list[str]:
    failures: list[str] = []
    required = {
        "loanword_integration.html.j2",
        "mlf_audit.html.j2",
        "trigger_profile.html.j2",
        "mixed_code_profile.html.j2",
        "integration_v2.html.j2",
    }
    for name in sorted(required):
        path = REPORTS_ROOT / name
        if not path.exists():
            failures.append(f"Report template missing: {path}")
            continue
        if PARTIAL_INCLUDE not in path.read_text(encoding="utf-8"):
            failures.append(f"{path}: must include {PARTIAL_INCLUDE}.")
    return failures


def _check_license_index() -> list[str]:
    index_path = LICENSES_ROOT / "INDEX.md"
    if not index_path.exists():
        return ["LICENSES/INDEX.md is missing."]
    text = index_path.read_text(encoding="utf-8")
    failures: list[str] = []
    for needle in ("Software licence", "Resource licences", "AGPLv3", "Tier-1", "Tier-2", "Tier-3"):
        if needle not in text:
            failures.append(f"LICENSES/INDEX.md must mention `{needle}`.")
    referenced = sorted(_referenced_spdx_ids())
    for spdx_id in referenced:
        if spdx_id not in text:
            failures.append(f"LICENSES/INDEX.md does not document referenced licence `{spdx_id}`.")
        license_file = _license_file_for(spdx_id)
        if not license_file.exists():
            failures.append(f"Referenced licence `{spdx_id}` has no licence text file: {license_file}.")
    return failures


def _referenced_spdx_ids() -> set[str]:
    spdx_ids: set[str] = set()
    for path in _resource_yaml_files():
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        source = data.get("source") if isinstance(data, dict) else None
        classification = source.get("licence_classification") if isinstance(source, dict) else None
        if isinstance(classification, dict):
            spdx_ids.add(str(classification.get("spdx_id", "")))
    return {item for item in spdx_ids if item}


def _license_file_for(license_name: str) -> Path:
    folded = license_name.casefold()
    if "nwulite" in folded or "obodo" in folded or "noodl" in folded or "mixed-noodl" in folded:
        return LICENSES_ROOT / "NWULITE-OBODO-1.0.txt"
    if "cc-by-sa-3.0" in folded or "cc by-sa 3.0" in folded or "sharealike 3.0" in folded:
        return LICENSES_ROOT / "CC-BY-SA-3.0.txt"
    if "cc-by-2.5" in folded or "cc by 2.5" in folded or "attribution 2.5" in folded:
        return LICENSES_ROOT / "CC-BY-2.5-SA.txt"
    if "cc-by-nc-4.0" in folded or "cc by-nc 4.0" in folded or "noncommercial 4.0" in folded:
        return LICENSES_ROOT / "CC-BY-NC-4.0.txt"
    if "cc-by-nc-sa" in folded or "cc by-nc-sa" in folded or "noncommercial-sharealike" in folded:
        return LICENSES_ROOT / "CC-BY-NC-SA-2.5-ZA.txt"
    if "cc-by-4.0" in folded or "cc by 4.0" in folded or "attribution 4.0" in folded:
        return LICENSES_ROOT / "CC-BY-4.0.txt"
    if "oer" in folded or "unisa" in folded:
        return LICENSES_ROOT / "OER-UNISA.txt"
    if "public" in folded:
        return LICENSES_ROOT / "PUBLIC-DOMAIN.txt"
    if "apache" in folded:
        return LICENSES_ROOT / "APACHE-2.0.txt"
    if "mit" in folded:
        return LICENSES_ROOT / "MIT.txt"
    return LICENSES_ROOT / f"{license_name}.txt"


def _looks_like_placeholder_license(text: str) -> bool:
    """Return True when a license file is clearly not the real license text."""

    stripped = text.strip()
    if not stripped:
        return True
    folded = stripped.casefold()
    return any(marker.casefold() in folded for marker in PLACEHOLDER_MARKERS)


if __name__ == "__main__":
    raise SystemExit(main())
