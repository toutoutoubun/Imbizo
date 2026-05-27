"""Create an air-gap dictionary bootstrap bundle.

This is one of the only two files allowed to import urllib.request. It runs on
a connected machine and packages raw downloads, checksums, and license files.
"""

from __future__ import annotations

import json
import shutil
import urllib.request
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping

import click
import yaml

from tools.adapters.utils.provenance import sha256_of

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@click.command()
@click.option("--manifest", "manifest_path", type=click.Path(path_type=Path), default=PROJECT_ROOT / "bootstrap" / "sources.yaml")
@click.option("--out", "out_path", type=click.Path(path_type=Path), default=PROJECT_ROOT / "bootstrap_bundle.zip")
def main(manifest_path: Path, out_path: Path) -> None:
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
        _verify_online_license_metadata(source)
        raw_files = _download_source(source, bundle_root / "raw")
        for raw_file in raw_files:
            checksum = sha256_of(raw_file)
            checksum_lines.append(f"{checksum}  raw/{raw_file.name}")
        license_file = _license_file_for(str(source.get("license", "")))
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
        try:
            urllib.request.urlretrieve(url, path)
        except Exception as exc:
            raise click.ClickException(f"Failed to download {url}: {exc}") from exc
        paths.append(path)
        click.echo(f"Downloaded {source['id']} -> {path.name}")
    return paths


def _verify_online_license_metadata(source: Mapping[str, Any]) -> None:
    markers = [str(marker) for marker in source.get("license_markers", [])]
    if not markers:
        return
    probe_url = str(source.get("license_probe_url") or source.get("url"))
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


def _safe_raw_name(source_id: str, index: int, url: str) -> str:
    suffix = Path(url.split("?", 1)[0]).suffix or ".raw"
    return f"{source_id}_{index:02d}{suffix}"


def _license_file_for(license_name: str) -> Path:
    folded = license_name.casefold()
    if "nwulite" in folded:
        return PROJECT_ROOT / "LICENSES" / "NWULITE-OBODO-1.0.txt"
    if "cc-by-nc-sa" in folded or "cc by-nc-sa" in folded:
        return PROJECT_ROOT / "LICENSES" / "CC-BY-NC-SA-2.5-ZA.txt"
    if "cc-by-4.0" in folded or "cc by 4.0" in folded:
        return PROJECT_ROOT / "LICENSES" / "CC-BY-4.0.txt"
    if "oer" in folded or "unisa" in folded:
        return PROJECT_ROOT / "LICENSES" / "OER-UNISA.txt"
    if "public" in folded:
        return PROJECT_ROOT / "LICENSES" / "PUBLIC-DOMAIN.txt"
    return PROJECT_ROOT / "LICENSES" / f"{license_name}.txt"


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
