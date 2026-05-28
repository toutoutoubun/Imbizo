"""Build local release artifacts for Imbizo-CS Workbench.

The script intentionally performs no upload. It creates a source distribution,
a wheel, SHA-256 checksums, and a small JSON manifest that can be attached to a
GitHub release or copied into an offline installation bundle.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.11+ always has tomllib.
    import tomli as tomllib  # type: ignore[no-redef]


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"


def main(argv: list[str] | None = None) -> int:
    """Build release artifacts and write checksums."""

    parser = argparse.ArgumentParser(description="Build Imbizo-CS release artifacts locally.")
    parser.add_argument("--out", type=Path, default=DIST, help="Output directory for release artifacts.")
    parser.add_argument(
        "--require-clean",
        action="store_true",
        help="Refuse to build if the git worktree has uncommitted changes.",
    )
    args = parser.parse_args(argv)

    output_dir = args.out.resolve()
    metadata = _project_metadata()
    if args.require_clean and _git_dirty():
        raise SystemExit("Refusing to build release artifacts from a dirty git worktree.")

    output_dir.mkdir(parents=True, exist_ok=True)
    _build_with_setuptools(output_dir)
    artifacts = _artifact_records(output_dir, metadata["version"])
    _write_checksums(output_dir, artifacts)
    manifest_path = output_dir / f"release_manifest_v{metadata['version']}.json"
    manifest = {
        "manifest_version": "1.0",
        "package_name": metadata["name"],
        "version": metadata["version"],
        "generated_on": datetime.now(UTC).isoformat(),
        "source_commit": _git_commit(),
        "source_dirty": _git_dirty(),
        "artifacts": artifacts,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {manifest_path.relative_to(ROOT)}")
    for artifact in artifacts:
        print(f"{artifact['sha256']}  {artifact['path']}")
    return 0


def _project_metadata() -> dict[str, str]:
    """Return package name and version from pyproject.toml."""

    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = data["project"]
    return {"name": str(project["name"]), "version": str(project["version"])}


def _build_with_setuptools(output_dir: Path) -> None:
    """Build sdist and wheel through the configured setuptools backend.

    This avoids a hard runtime dependency on the external `build` package while
    still using the backend declared in `pyproject.toml`.
    """

    previous_cwd = Path.cwd()
    os.chdir(ROOT)
    try:
        import setuptools.build_meta as build_meta

        build_meta.build_sdist(str(output_dir))
        build_meta.build_wheel(str(output_dir))
    finally:
        os.chdir(previous_cwd)


def _artifact_records(output_dir: Path, version: str) -> list[dict[str, Any]]:
    """Return checksum records for the artifacts produced for this version."""

    project_name = _project_metadata()["name"].replace("-", "_")
    candidates = sorted(
        path
        for path in output_dir.iterdir()
        if path.is_file()
        and (
            path.name.endswith(".whl")
            or path.name.endswith(".tar.gz")
        )
        and path.name.startswith(f"{project_name}-{version}")
    )
    if not candidates:
        raise SystemExit(f"No release artifacts found in {output_dir}")
    return [
        {
            "path": path.relative_to(ROOT).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": _sha256(path),
        }
        for path in candidates
    ]


def _write_checksums(output_dir: Path, artifacts: list[dict[str, Any]]) -> None:
    """Write a SHA256SUMS.txt file in the release artifact directory."""

    lines = [f"{record['sha256']}  {Path(record['path']).name}" for record in artifacts]
    (output_dir / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    """Return SHA-256 for a local file."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_commit() -> str | None:
    """Return the current git commit hash, if available."""

    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip()


def _git_dirty() -> bool:
    """Return True if git reports uncommitted changes."""

    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return True
    return bool(result.stdout.strip())


if __name__ == "__main__":
    raise SystemExit(main())
