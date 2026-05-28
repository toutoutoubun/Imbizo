"""Create an air-gap dictionary bootstrap bundle.

Network access is delegated to :mod:`tools.bootstrap` so the project has one
auditable download path for bootstrap resources.
"""

from __future__ import annotations

import json
import os
import shutil
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping

import click
import yaml

from tools.adapters.utils.provenance import sha256_of
from tools.bootstrap import (
    _license_files_for_source,
    _source_tier,
    _verify_source_license_files,
    _verify_online_license_metadata,
    download_url,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@click.command()
@click.option("--manifest", "manifest_path", type=click.Path(path_type=Path), default=PROJECT_ROOT / "bootstrap" / "sources.yaml")
@click.option("--out", "out_path", type=click.Path(path_type=Path), default=PROJECT_ROOT / "bootstrap_bundle.zip")
@click.option("--include-nc-data", is_flag=True, default=False, help="Include Tier-2 resources after IMBIZO_NC_ACCEPTED=1.")
@click.option("--include-community", is_flag=True, default=False, help="Include Tier-3 resources after IMBIZO_COMMUNITY_ACCEPTED=1.")
@click.option("--include-asr", is_flag=True, default=False, help="Include strictly opt-in whisper.cpp ASR resources.")
def main(manifest_path: Path, out_path: Path, include_nc_data: bool, include_community: bool, include_asr: bool) -> None:
    """Download shippable sources and pack an offline bootstrap zip."""

    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    bundle_root = PROJECT_ROOT / "downloads" / "bundle_build"
    if bundle_root.exists():
        shutil.rmtree(bundle_root)
    (bundle_root / "raw").mkdir(parents=True, exist_ok=True)
    (bundle_root / "LICENSES").mkdir(parents=True, exist_ok=True)

    entries: list[dict[str, Any]] = []
    checksum_lines: list[str] = []
    for source in manifest.get("sources", []):
        if source.get("bundle_status") != "shippable":
            click.echo(f"Skipping {source.get('id')}: not shippable")
            continue
        tier = _source_tier(source)
        if tier == 2 and not include_nc_data:
            click.echo(f"Skipping {source.get('id')}: Tier-2 opt-in not requested")
            continue
        if tier == 2 and os.environ.get("IMBIZO_NC_ACCEPTED") != "1":
            raise click.ClickException("Tier-2 bundle creation requires IMBIZO_NC_ACCEPTED=1.")
        if tier == 3 and not include_community:
            click.echo(f"Skipping {source.get('id')}: Tier-3 community opt-in not requested")
            continue
        if tier == 3 and os.environ.get("IMBIZO_COMMUNITY_ACCEPTED") != "1":
            raise click.ClickException("Tier-3 bundle creation requires IMBIZO_COMMUNITY_ACCEPTED=1.")
        if source.get("opt_in_flag") == "include_asr" and not include_asr:
            click.echo(f"Skipping {source.get('id')}: ASR opt-in not requested")
            continue
        _verify_source_license_files(source)
        _verify_online_license_metadata(source)
        raw_files = _download_source(source, bundle_root / "raw")
        for raw_file in raw_files:
            checksum = sha256_of(raw_file)
            checksum_lines.append(f"{checksum}  raw/{raw_file.name}")
        for license_file in _license_files_for_source(source):
            if not license_file.exists():
                raise click.ClickException(f"License file missing: {license_file}")
            shutil.copy2(license_file, bundle_root / "LICENSES" / license_file.name)
        entries.append(
            {
                "id": source["id"],
                "name": source.get("name"),
                "license": source.get("license"),
                "raw_files": [f"raw/{path.name}" for path in raw_files],
                "retrieved_on": datetime.now(UTC).isoformat(),
            }
        )

    (bundle_root / "checksums.sha256").write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")
    (bundle_root / "manifest.json").write_text(json.dumps({"sources": entries}, indent=2, ensure_ascii=False), encoding="utf-8")
    (bundle_root / "README_BUNDLE.md").write_text(_bundle_readme(), encoding="utf-8")

    if out_path.exists():
        out_path.unlink()
    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in bundle_root.rglob("*"):
            if path.is_file():
                archive.write(path, path.relative_to(bundle_root))
    click.echo(f"Wrote {out_path}")
    click.echo("On the offline machine run: python tools/bootstrap.py --offline --from-bundle <this zip>")


def _download_source(source: Mapping[str, Any], raw_dir: Path) -> list[Path]:
    urls = source.get("url")
    url_list = urls if isinstance(urls, list) else [urls]
    paths: list[Path] = []
    for index, url in enumerate(url_list, start=1):
        if not isinstance(url, str):
            raise click.ClickException(f"Invalid URL for source {source.get('id')}")
        path = raw_dir / _safe_raw_name(str(source["id"]), index, url)
        download_url(url, path)
        paths.append(path)
        click.echo(f"Downloaded {source['id']} -> {path.name}")
    return paths


def _safe_raw_name(source_id: str, index: int, url: str) -> str:
    suffix = Path(url.split("?", 1)[0]).suffix or ".raw"
    return f"{source_id}_{index:02d}{suffix}"


def _bundle_readme() -> str:
    return """# Imbizo-CS Dictionary Bootstrap Bundle

This zip is for transferring audited dictionary source files to an offline
machine by USB or other local media.

1. Copy the zip to the offline machine.
2. Verify `checksums.sha256` after extraction if desired.
3. Run `python tools/bootstrap.py --offline --from-bundle <bundle.zip>`.

The bundle contains raw source files, checksums, and license files. It does not
contact the internet during offline reconstruction.
"""


if __name__ == "__main__":
    main()
