"""CI compliance checks for imported dictionary YAML files."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import click
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
IMPORTED_ROOT = PROJECT_ROOT / "dictionaries" / "imported"
LICENSES_ROOT = PROJECT_ROOT / "LICENSES"

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

PLACEHOLDER_MARKERS = (
    "REPLACE THIS FILE WITH THE VERBATIM LICENSE TEXT",
    "PLACEHOLDER",
    "TODO",
    "TBD",
)


def main() -> int:
    """Run compliance checks and return a process exit code."""

    failures: list[str] = []
    for path in sorted(IMPORTED_ROOT.rglob("*.yaml")):
        if "_provenance" in path.parts:
            continue
        failures.extend(_check_dictionary(path))
    if failures:
        for failure in failures:
            click.echo(failure)
        return 1
    click.echo("Dictionary compliance checks passed.")
    return 0


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
    for field in ("schema_version", "dictionary_kind", "content_version", "source", "review", "caveats", "entries"):
        if field not in data:
            failures.append(f"{path}: missing required top-level field `{field}`.")
    source = data.get("source")
    if not isinstance(source, dict):
        failures.append(f"{path}: `source` must be a mapping.")
    else:
        missing = sorted(field for field in REQUIRED_SOURCE_FIELDS if not source.get(field))
        if missing:
            failures.append(f"{path}: source header missing fields: {', '.join(missing)}.")
    review = data.get("review")
    if not isinstance(review, dict):
        failures.append(f"{path}: `review` must be a mapping.")
    elif "last_reviewed_by" not in review:
        failures.append(f"{path}: review header missing `last_reviewed_by`.")
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


def _license_file_for(license_name: str) -> Path:
    folded = license_name.casefold()
    if "nwulite" in folded or "obodo" in folded:
        return LICENSES_ROOT / "NWULITE-OBODO-1.0.txt"
    if "cc-by-nc-sa" in folded or "cc by-nc-sa" in folded or "noncommercial-sharealike" in folded:
        return LICENSES_ROOT / "CC-BY-NC-SA-2.5-ZA.txt"
    if "cc-by-4.0" in folded or "cc by 4.0" in folded or "attribution 4.0" in folded:
        return LICENSES_ROOT / "CC-BY-4.0.txt"
    if "oer" in folded or "unisa" in folded:
        return LICENSES_ROOT / "OER-UNISA.txt"
    if "public" in folded:
        return LICENSES_ROOT / "PUBLIC-DOMAIN.txt"
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
