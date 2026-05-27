"""Provenance header helpers for imported dictionaries."""

from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping


def build_header(
    dictionary_kind: str,
    language_code: str | None,
    language_pair: list[str] | None,
    source_metadata: Mapping[str, Any],
    raw_sha256: str,
    adapter_path: str,
    adapter_version: str,
    caveats: str,
) -> dict[str, Any]:
    """Build the standard Imbizo-CS imported-dictionary YAML header."""

    retrieved_on = str(source_metadata.get("retrieved_on") or datetime.now(UTC).date().isoformat())
    url = source_metadata.get("url")
    if isinstance(url, list):
        origin_url = str(source_metadata.get("current_url") or url[0])
    else:
        origin_url = str(url or source_metadata.get("origin_url", ""))
    header: dict[str, Any] = {
        "schema_version": "1.0",
        "dictionary_kind": dictionary_kind,
        "content_version": "0.1.0",
        "source": {
            "origin_name": str(source_metadata.get("name") or source_metadata.get("origin_name", "")),
            "origin_url": origin_url,
            "origin_authors": list(source_metadata.get("origin_authors") or []),
            "origin_license": str(source_metadata.get("origin_license") or source_metadata.get("license", "")),
            "origin_version": str(source_metadata.get("origin_version") or f"as of {retrieved_on}"),
            "retrieved_on": retrieved_on,
            "retrieved_sha256": raw_sha256,
            "transformation_tool": adapter_path,
            "transformation_version": adapter_version,
            "transformation_date": datetime.now(UTC).date().isoformat(),
        },
        "review": {
            "last_reviewed_by": "PENDING_HUMAN_REVIEW",
            "last_reviewed_on": None,
            "reviewer_notes": None,
        },
        "caveats": caveats,
    }
    if language_code is not None:
        header["language_code"] = language_code
    if language_pair is not None:
        header["language_pair"] = language_pair
    return header


def sha256_of(path: Path) -> str:
    """Return the SHA-256 hex digest of a local file."""

    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

