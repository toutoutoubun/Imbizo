"""Dictionary bootstrap CLI for Imbizo-CS Workbench.

This is one of the only two files allowed to import urllib.request. The
runtime application must never perform dictionary downloads.
"""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import urllib.request
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping

import click
import yaml

from tools.adapters.base import SourceAdapter
from tools.adapters.utils.provenance import sha256_of

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "downloads" / "raw"
PROVENANCE_DIR = PROJECT_ROOT / "dictionaries" / "imported" / "_provenance"


@click.command()
@click.option("--manifest", "manifest_path", type=click.Path(path_type=Path), default=PROJECT_ROOT / "bootstrap" / "sources.yaml")
@click.option("--offline", is_flag=True, default=False, help="Require --from-bundle and avoid all network access.")
@click.option("--from-bundle", "bundle_path", type=click.Path(path_type=Path), default=None)
@click.option("--skip-license-pending", is_flag=True, default=False, help="Skip sources requiring explicit license approval.")
@click.option("--dry-run", is_flag=True, default=False, help="Verify checksums and licenses without writing outputs.")
@click.option("--only", "only_source", default=None, help="Run a single source id.")
def main(
    manifest_path: Path,
    offline: bool,
    bundle_path: Path | None,
    skip_license_pending: bool,
    dry_run: bool,
    only_source: str | None,
) -> None:
    """Fetch or unpack verified sources and convert them to internal YAML."""

    if offline and bundle_path is None:
        raise click.ClickException("--offline requires --from-bundle.")
    manifest = _load_manifest(manifest_path)
    sources = manifest.get("sources", [])
    if only_source:
        sources = [source for source in sources if source.get("id") == only_source]
        if not sources:
            raise click.ClickException(f"No source with id `{only_source}` appears in {manifest_path}.")

    bundle_extract_dir: Path | None = None
    if bundle_path is not None:
        bundle_extract_dir = _extract_bundle(bundle_path)

    summaries: list[dict[str, Any]] = []
    for source in sources:
        summary = _process_source(source, offline, bundle_extract_dir, skip_license_pending, dry_run)
        summaries.append(summary)
        click.echo(
            f"{summary['id']}: {summary['status']} | license={summary['license']} | "
            f"outputs={summary['output_count']} | size={summary['total_size']}"
        )
    _print_summary(summaries)


def _load_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise click.ClickException(f"Manifest not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict) or not isinstance(data.get("sources"), list):
        raise click.ClickException(f"Manifest {path} must contain a sources list.")
    return data


def _process_source(
    source: Mapping[str, Any],
    offline: bool,
    bundle_extract_dir: Path | None,
    skip_license_pending: bool,
    dry_run: bool,
) -> dict[str, Any]:
    source_id = str(source["id"])
    license_name = str(source.get("license", ""))
    if source.get("license_check_required") and not _license_approved(source_id):
        if skip_license_pending:
            return _summary(source_id, "skipped-license-pending", license_name, [], 0)
        return _summary(source_id, "skipped-needs-license-approval", license_name, [], 0)

    license_file = _license_file_for(license_name)
    if not license_file.exists():
        raise click.ClickException(f"License file missing for {source_id}: {license_file}")
    if not offline:
        _verify_online_license_metadata(source)

    raw_paths = _materialize_raw_files(source, offline, bundle_extract_dir)
    expected_sha = source.get("expected_sha256")
    output_files: list[Path] = []
    total_size = 0
    for raw_path in raw_paths:
        actual_sha = sha256_of(raw_path)
        if expected_sha and actual_sha != expected_sha:
            raise click.ClickException(f"Checksum mismatch for {raw_path}: expected {expected_sha}, got {actual_sha}")
        total_size += raw_path.stat().st_size
        if dry_run:
            continue
        adapter = _load_adapter(PROJECT_ROOT / str(source["adapter"]))
        metadata = dict(source)
        metadata["retrieved_on"] = datetime.now(UTC).date().isoformat()
        metadata["retrieved_sha256"] = actual_sha
        metadata["current_url"] = raw_path.name
        output_dirs = [PROJECT_ROOT / str(path) for path in source.get("output_dirs", [])]
        output_files.extend(adapter.convert(raw_path, output_dirs, metadata))

    if not dry_run:
        _write_source_provenance(source_id, source, raw_paths, output_files)
    status = "dry-run-ok" if dry_run else "converted"
    return _summary(source_id, status, license_name, output_files, total_size)


def _materialize_raw_files(source: Mapping[str, Any], offline: bool, bundle_extract_dir: Path | None) -> list[Path]:
    urls = source.get("url")
    url_list = urls if isinstance(urls, list) else [urls]
    paths: list[Path] = []
    for index, url in enumerate(url_list, start=1):
        if not isinstance(url, str):
            raise click.ClickException(f"Source {source.get('id')} has an invalid URL entry.")
        file_name = _safe_raw_name(str(source["id"]), index, url)
        if offline:
            if bundle_extract_dir is None:
                raise click.ClickException("Offline mode requires an extracted bundle.")
            bundle_raw = bundle_extract_dir / "raw" / file_name
            if not bundle_raw.exists():
                raise click.ClickException(f"Bundle does not contain raw source file: {bundle_raw}")
            paths.append(bundle_raw)
        else:
            RAW_DIR.mkdir(parents=True, exist_ok=True)
            raw_path = RAW_DIR / file_name
            urllib.request.urlretrieve(url, raw_path)
            paths.append(raw_path)
    return paths


def _verify_online_license_metadata(source: Mapping[str, Any]) -> None:
    markers = [str(marker) for marker in source.get("license_markers", [])]
    if not markers:
        return
    probe_url = str(source.get("license_probe_url") or source.get("url"))
    if not probe_url or probe_url.startswith("["):
        raise click.ClickException(f"Source {source.get('id')} requires a license probe URL.")
    try:
        with urllib.request.urlopen(probe_url, timeout=30) as response:
            page = response.read().decode("utf-8", errors="replace")
    except Exception as exc:
        raise click.ClickException(f"Could not verify online license metadata for {source.get('id')}: {exc}") from exc
    folded = page.casefold()
    if not any(marker.casefold() in folded for marker in markers):
        raise click.ClickException(
            f"Could not confirm required license metadata for {source.get('id')} at {probe_url}. "
            f"Expected one of: {', '.join(markers)}"
        )


def _extract_bundle(bundle_path: Path) -> Path:
    if not bundle_path.exists():
        raise click.ClickException(f"Bundle not found: {bundle_path}")
    extract_dir = PROJECT_ROOT / "downloads" / "bundle_extract"
    if extract_dir.exists():
        shutil.rmtree(extract_dir)
    extract_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(bundle_path, "r") as archive:
        archive.extractall(extract_dir)
    _verify_bundle_checksums(extract_dir)
    return extract_dir


def _verify_bundle_checksums(extract_dir: Path) -> None:
    checksum_file = extract_dir / "checksums.sha256"
    if not checksum_file.exists():
        raise click.ClickException(f"Offline bundle is missing checksums.sha256: {checksum_file}")
    failures: list[str] = []
    for line in checksum_file.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        expected, _, relative_path = line.partition("  ")
        if not expected or not relative_path:
            failures.append(f"Malformed checksum line: {line}")
            continue
        path = extract_dir / relative_path
        if not path.exists():
            failures.append(f"Bundle checksum target missing: {relative_path}")
            continue
        actual = sha256_of(path)
        if actual != expected:
            failures.append(f"Checksum mismatch for {relative_path}: expected {expected}, got {actual}")
    if failures:
        raise click.ClickException("Offline bundle checksum verification failed:\n" + "\n".join(failures))


def _safe_raw_name(source_id: str, index: int, url: str) -> str:
    suffix = Path(url.split("?", 1)[0]).suffix or ".raw"
    return f"{source_id}_{index:02d}{suffix}"


def _license_approved(source_id: str) -> bool:
    approved = {
        item.strip()
        for item in os.environ.get("IMBIZO_LICENSE_APPROVED", "").split(",")
        if item.strip()
    }
    return source_id in approved


def _license_file_for(license_name: str) -> Path:
    folded = license_name.casefold()
    if "nwulite" in folded:
        return PROJECT_ROOT / "LICENSES" / "NWULITE-OBODO-1.0.txt"
    if "cc-by-nc-sa" in folded or "cc by-nc-sa" in folded or "cc-by-nc-sa 2.5" in folded:
        return PROJECT_ROOT / "LICENSES" / "CC-BY-NC-SA-2.5-ZA.txt"
    if "cc-by-4.0" in folded or "cc by 4.0" in folded:
        return PROJECT_ROOT / "LICENSES" / "CC-BY-4.0.txt"
    if "oer" in folded or "unisa" in folded:
        return PROJECT_ROOT / "LICENSES" / "OER-UNISA.txt"
    if "public" in folded:
        return PROJECT_ROOT / "LICENSES" / "PUBLIC-DOMAIN.txt"
    return PROJECT_ROOT / "LICENSES" / f"{license_name}.txt"


def _load_adapter(path: Path) -> SourceAdapter:
    if not path.exists():
        raise click.ClickException(f"Adapter file not found: {path}")
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise click.ClickException(f"Cannot load adapter: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    adapter_cls = getattr(module, "Adapter", None)
    if adapter_cls is None:
        raise click.ClickException(f"Adapter file {path} does not expose Adapter.")
    adapter = adapter_cls()
    if not isinstance(adapter, SourceAdapter):
        raise click.ClickException(f"Adapter {path} is not a SourceAdapter.")
    return adapter


def _write_source_provenance(source_id: str, source: Mapping[str, Any], raw_paths: list[Path], output_files: list[Path]) -> None:
    PROVENANCE_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "source_id": source_id,
        "source": dict(source),
        "raw_files": [{"path": str(path), "sha256": sha256_of(path)} for path in raw_paths],
        "outputs": [str(path) for path in output_files],
        "generated_on": datetime.now(UTC).isoformat(),
    }
    (PROVENANCE_DIR / f"{source_id}.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _summary(source_id: str, status: str, license_name: str, outputs: list[Path], total_size: int) -> dict[str, Any]:
    return {
        "id": source_id,
        "status": status,
        "license": license_name,
        "output_count": len(outputs),
        "total_size": total_size,
    }


def _print_summary(summaries: list[Mapping[str, Any]]) -> None:
    click.echo("\nSummary")
    click.echo("source_id\tstatus\tlicense\toutputs\tsize_bytes")
    for row in summaries:
        click.echo(f"{row['id']}\t{row['status']}\t{row['license']}\t{row['output_count']}\t{row['total_size']}")


if __name__ == "__main__":
    main()
