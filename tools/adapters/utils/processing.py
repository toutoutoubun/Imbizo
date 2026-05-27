"""Shared helpers for processing-resource bootstrap adapters."""

from __future__ import annotations

import json
import tarfile
import zipfile
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Mapping

import yaml

from tools.adapters.utils.provenance import build_header, sha256_of


def write_index(
    path: Path,
    *,
    resource_kind: str,
    languages: list[str],
    usable_by: list[str],
    source_metadata: Mapping[str, Any],
    raw_path: Path,
    adapter_path: str,
    adapter_version: str,
    caveats: str,
    extra: Mapping[str, Any] | None = None,
) -> Path:
    """Write a standard processing-resource index YAML."""

    header = build_header(
        dictionary_kind="processing_resource",
        language_code=None,
        language_pair=None,
        source_metadata=source_metadata,
        raw_sha256=sha256_of(raw_path),
        adapter_path=adapter_path,
        adapter_version=adapter_version,
        caveats=caveats,
    )
    payload: dict[str, Any] = {
        **header,
        "resource_kind": resource_kind,
        "languages": languages,
        "usable_by": usable_by,
        "verified": False,
    }
    if extra:
        payload.update(dict(extra))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return path


def write_processing_provenance(
    resource_id: str,
    raw_path: Path,
    outputs: Iterable[Path],
    source_metadata: Mapping[str, Any],
    project_root: Path | None = None,
) -> Path:
    """Write a per-resource processing provenance JSON file."""

    metadata_root = source_metadata.get("project_root")
    root = project_root or (Path(str(metadata_root)) if metadata_root else Path(__file__).resolve().parents[3])
    out_dir = root / "dictionaries" / "imported" / "_provenance" / "processing"
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "resource_id": resource_id,
        "source": _jsonable_mapping(source_metadata),
        "raw_file": str(raw_path),
        "raw_sha256": sha256_of(raw_path),
        "outputs": [str(path) for path in outputs],
        "generated_on": datetime.now(UTC).isoformat(),
    }
    out_path = out_dir / f"{resource_id}.json"
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return out_path


def _jsonable_mapping(mapping: Mapping[str, Any]) -> dict[str, Any]:
    jsonable: dict[str, Any] = {}
    for key, value in mapping.items():
        if isinstance(value, Path):
            jsonable[str(key)] = str(value)
        elif isinstance(value, list):
            jsonable[str(key)] = [str(item) if isinstance(item, Path) else item for item in value]
        else:
            jsonable[str(key)] = value
    return jsonable


def unpack_archive(raw_path: Path, out_dir: Path) -> list[Path]:
    """Extract a zip or tar archive and return extracted file paths."""

    out_dir.mkdir(parents=True, exist_ok=True)
    extracted: list[Path] = []
    if zipfile.is_zipfile(raw_path):
        with zipfile.ZipFile(raw_path) as archive:
            archive.extractall(out_dir)
        extracted = [path for path in out_dir.rglob("*") if path.is_file()]
    elif tarfile.is_tarfile(raw_path):
        with tarfile.open(raw_path) as archive:
            try:
                archive.extractall(out_dir, filter="data")
            except TypeError:  # Python 3.11 compatibility.
                archive.extractall(out_dir)
        extracted = [path for path in out_dir.rglob("*") if path.is_file()]
    else:
        target = out_dir / raw_path.name
        target.write_bytes(raw_path.read_bytes())
        extracted = [target]
    return extracted


def token_count(path: Path) -> int:
    """Count whitespace-separated tokens in a UTF-8 text-like file."""

    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return 0
    return len(text.split())


def conll_inventory(path: Path) -> dict[str, Any]:
    """Summarize CoNLL-style token/tag inventory for an offline corpus file."""

    token_total = 0
    tag_counts: Counter[str] = Counter()
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return {"tokens": 0, "tag_inventory": {}}
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split()
        if len(parts) >= 2:
            token_total += 1
            tag_counts[parts[-1]] += 1
    return {"tokens": token_total, "tag_inventory": dict(sorted(tag_counts.items()))}
