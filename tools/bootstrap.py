"""Dictionary bootstrap CLI for Imbizo-CS Workbench.

This is the central CLI allowed to import urllib.request. Runtime application
modules must never perform dictionary or processing-resource downloads.
"""

from __future__ import annotations

import hashlib
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
@click.option(
    "--include-nc-data",
    is_flag=True,
    default=False,
    help=(
        "Opt in to download Tier-2 (NonCommercial or aggregation-only) resources such as MasakhaPOS, "
        "MasakhaNER, and fastText lid.176. Requires IMBIZO_NC_ACCEPTED=1. "
        "See PRINCIPLES.md, Part IV: Licence philosophy."
    ),
)
@click.option(
    "--include-community",
    is_flag=True,
    default=False,
    help=(
        "Opt in to Tier-3 community-governed resources. Requires IMBIZO_COMMUNITY_ACCEPTED=1. "
        "These are normally shared through offline community-review packets."
    ),
)
@click.option("--include-asr", is_flag=True, default=False, help="Include strictly opt-in whisper.cpp ASR resources.")
def main(
    manifest_path: Path,
    offline: bool,
    bundle_path: Path | None,
    skip_license_pending: bool,
    dry_run: bool,
    only_source: str | None,
    include_nc_data: bool,
    include_community: bool,
    include_asr: bool,
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
    _print_tier_summary(sources, include_nc_data, include_community, include_asr)
    _enforce_selected_tier_confirmations(sources, include_nc_data, include_community)

    bundle_extract_dir: Path | None = None
    if bundle_path is not None:
        bundle_extract_dir = _extract_bundle(bundle_path)

    summaries: list[dict[str, Any]] = []
    for source in sources:
        summary = _process_source(
            source,
            offline,
            bundle_extract_dir,
            skip_license_pending,
            dry_run,
            include_asr,
            include_nc_data,
            include_community,
        )
        summaries.append(summary)
        click.echo(
            f"{summary['id']}: {summary['status']} | license={summary['license']} | "
            f"outputs={summary['output_count']} | size={summary['total_size']}"
        )
    if not dry_run:
        _write_licence_acknowledgement(sources, summaries, include_nc_data, include_community, include_asr)
    _print_summary(summaries)


def _load_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise click.ClickException(f"Manifest not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict) or not isinstance(data.get("sources"), list):
        raise click.ClickException(f"Manifest {path} must contain a sources list.")
    return data


def _classification(source: Mapping[str, Any]) -> Mapping[str, Any]:
    classification = source.get("licence_classification")
    if isinstance(classification, Mapping):
        return classification
    return {}


def _source_tier(source: Mapping[str, Any]) -> int:
    try:
        return int(_classification(source).get("tier", 1))
    except (TypeError, ValueError):
        return 1


def _tier_gate_status(source: Mapping[str, Any], include_nc_data: bool, include_community: bool) -> str | None:
    tier = _source_tier(source)
    if tier == 2 and not include_nc_data:
        return "skipped-tier2-opt-in-required"
    if tier == 3 and not include_community:
        return "skipped-tier3-community-required"
    return None


def _print_tier_summary(
    sources: list[Mapping[str, Any]],
    include_nc_data: bool,
    include_community: bool,
    include_asr: bool,
) -> None:
    counts = {1: 0, 2: 0, 3: 0}
    for source in sources:
        counts[_source_tier(source)] = counts.get(_source_tier(source), 0) + 1
    click.echo("Bootstrap distribution tiers")
    click.echo(f"Tier 1 Core sources visible: {counts.get(1, 0)}")
    click.echo(f"Tier 2 Optional-NC sources visible: {counts.get(2, 0)} | requested={include_nc_data}")
    click.echo(f"Tier 3 Community sources visible: {counts.get(3, 0)} | requested={include_community}")
    click.echo(f"Optional ASR requested: {include_asr}")
    click.echo(f"IMBIZO_NC_ACCEPTED present: {os.environ.get('IMBIZO_NC_ACCEPTED') == '1'}")
    click.echo(f"IMBIZO_COMMUNITY_ACCEPTED present: {os.environ.get('IMBIZO_COMMUNITY_ACCEPTED') == '1'}")


def _enforce_selected_tier_confirmations(
    sources: list[Mapping[str, Any]],
    include_nc_data: bool,
    include_community: bool,
) -> None:
    if include_nc_data and os.environ.get("IMBIZO_NC_ACCEPTED") != "1":
        _echo_tier_notices(sources, tier=2)
        raise click.ClickException("Tier-2 resources require IMBIZO_NC_ACCEPTED=1 before bootstrap proceeds.")
    if include_community and os.environ.get("IMBIZO_COMMUNITY_ACCEPTED") != "1":
        _echo_tier_notices(sources, tier=3)
        raise click.ClickException("Tier-3 resources require IMBIZO_COMMUNITY_ACCEPTED=1 before bootstrap proceeds.")


def _echo_tier_notices(sources: list[Mapping[str, Any]], tier: int) -> None:
    click.echo(f"\nTier-{tier} redistribution notices")
    for source in sources:
        if _source_tier(source) != tier:
            continue
        notice = str(_classification(source).get("redistribution_notice", "")).strip()
        if notice:
            click.echo(f"\n[{source.get('id')}] {notice}")


def _process_source(
    source: Mapping[str, Any],
    offline: bool,
    bundle_extract_dir: Path | None,
    skip_license_pending: bool,
    dry_run: bool,
    include_asr: bool,
    include_nc_data: bool,
    include_community: bool,
) -> dict[str, Any]:
    source_id = str(source["id"])
    license_name = str(source.get("license", ""))
    tier_status = _tier_gate_status(source, include_nc_data, include_community)
    if tier_status is not None:
        return _summary(source_id, tier_status, license_name, [], 0)
    if source.get("opt_in_flag") == "include_asr" and not include_asr:
        return _summary(source_id, "skipped-asr-opt-in-required", license_name, [], 0)
    if source.get("license_check_required") and not _license_approved(source_id):
        if skip_license_pending:
            return _summary(source_id, "skipped-license-pending", license_name, [], 0)
        return _summary(source_id, "skipped-needs-license-approval", license_name, [], 0)

    for license_file in _license_files_for_source(source):
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
        metadata["include_asr"] = include_asr
        metadata["include_nc_data"] = include_nc_data
        metadata["include_community"] = include_community
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
            download_url(url, raw_path)
            paths.append(raw_path)
    return paths


def download_url(url: str, raw_path: Path) -> None:
    """Download a URL to disk using the one bootstrap-approved network path."""

    try:
        urllib.request.urlretrieve(url, raw_path)
    except Exception as exc:
        raise click.ClickException(f"Failed to download {url}: {exc}") from exc


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


def _license_files_for_source(source: Mapping[str, Any]) -> list[Path]:
    if source.get("license_resolution") == "per_file_metadata":
        return [
            PROJECT_ROOT / "LICENSES" / "CC-BY-4.0.txt",
            PROJECT_ROOT / "LICENSES" / "OER-UNISA.txt",
            PROJECT_ROOT / "LICENSES" / "CC-BY-NC-4.0.txt",
        ]
    return [_license_file_for(str(source.get("license", "")))]


def _license_file_for(license_name: str) -> Path:
    folded = license_name.casefold()
    if "nwulite" in folded or "noodl" in folded or "obodo" in folded or "mixed-noodl" in folded:
        return PROJECT_ROOT / "LICENSES" / "NWULITE-OBODO-1.0.txt"
    if "cc-by-sa-3.0" in folded or "cc by-sa 3.0" in folded or "sharealike 3.0" in folded:
        return PROJECT_ROOT / "LICENSES" / "CC-BY-SA-3.0.txt"
    if "cc-by-2.5" in folded or "cc by 2.5" in folded or "attribution 2.5" in folded:
        return PROJECT_ROOT / "LICENSES" / "CC-BY-2.5-SA.txt"
    if "cc-by-nc-4.0" in folded or "cc by-nc 4.0" in folded or "noncommercial 4.0" in folded:
        return PROJECT_ROOT / "LICENSES" / "CC-BY-NC-4.0.txt"
    if "cc-by-nc-sa" in folded or "cc by-nc-sa" in folded or "cc-by-nc-sa 2.5" in folded:
        return PROJECT_ROOT / "LICENSES" / "CC-BY-NC-SA-2.5-ZA.txt"
    if "cc-by-4.0" in folded or "cc by 4.0" in folded:
        return PROJECT_ROOT / "LICENSES" / "CC-BY-4.0.txt"
    if "oer" in folded or "unisa" in folded:
        return PROJECT_ROOT / "LICENSES" / "OER-UNISA.txt"
    if "public" in folded:
        return PROJECT_ROOT / "LICENSES" / "PUBLIC-DOMAIN.txt"
    if "apache" in folded:
        return PROJECT_ROOT / "LICENSES" / "APACHE-2.0.txt"
    if "mit" in folded:
        return PROJECT_ROOT / "LICENSES" / "MIT.txt"
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
    target_dir = PROVENANCE_DIR / "processing" if source.get("resource_kind") in {"model", "corpus", "dataset", "toolkit"} else PROVENANCE_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "source_id": source_id,
        "source": dict(source),
        "raw_files": [{"path": str(path), "sha256": sha256_of(path)} for path in raw_paths],
        "outputs": [str(path) for path in output_files],
        "generated_on": datetime.now(UTC).isoformat(),
    }
    (target_dir / f"{source_id}.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _write_licence_acknowledgement(
    sources: list[Mapping[str, Any]],
    summaries: list[Mapping[str, Any]],
    include_nc_data: bool,
    include_community: bool,
    include_asr: bool,
) -> None:
    converted_ids = {str(row["id"]) for row in summaries if row.get("status") == "converted"}
    if not converted_ids:
        return
    installed_sources = [source for source in sources if str(source.get("id")) in converted_ids]
    installed_tiers = sorted({_source_tier(source) for source in installed_sources})
    notices = [
        str(_classification(source).get("redistribution_notice", "")).strip()
        for source in installed_sources
        if str(_classification(source).get("redistribution_notice", "")).strip()
    ]
    notice_digest = hashlib.sha256("\n\n".join(notices).encode("utf-8")).hexdigest()
    payload = {
        "timestamp": datetime.now(UTC).isoformat(),
        "installed_tiers": installed_tiers,
        "installed_source_ids": sorted(converted_ids),
        "requested_flags": {
            "include_nc_data": include_nc_data,
            "include_community": include_community,
            "include_asr": include_asr,
        },
        "environment_confirmations": {
            "IMBIZO_NC_ACCEPTED": os.environ.get("IMBIZO_NC_ACCEPTED") == "1",
            "IMBIZO_COMMUNITY_ACCEPTED": os.environ.get("IMBIZO_COMMUNITY_ACCEPTED") == "1",
            "IMBIZO_ASR_ACCEPTED": os.environ.get("IMBIZO_ASR_ACCEPTED") == "1",
        },
        "redistribution_notice_sha256": notice_digest,
    }
    PROVENANCE_DIR.mkdir(parents=True, exist_ok=True)
    (PROVENANCE_DIR / "licence_acknowledgement.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )


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
