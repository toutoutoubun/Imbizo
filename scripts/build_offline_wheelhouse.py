"""Build an offline wheelhouse using pip."""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    """Build wheels into a local wheelhouse directory."""

    parser = argparse.ArgumentParser(description="Build an Imbizo-CS offline wheelhouse.")
    parser.add_argument("--out", type=Path, default=Path("wheelhouse"), help="Wheelhouse output directory.")
    parser.add_argument(
        "--extras",
        default="gui,xlsx,audio,security,reports",
        help="Comma-separated optional dependency groups to include.",
    )
    args = parser.parse_args(argv)

    wheelhouse = args.out
    wheelhouse.mkdir(exist_ok=True)
    command = [sys.executable, "-m", "pip", "wheel", f".[{args.extras}]", "--wheel-dir", str(wheelhouse)]
    result = subprocess.call(command)
    if result == 0:
        _write_checksums(wheelhouse)
    return result


def _write_checksums(wheelhouse: Path) -> None:
    """Write SHA-256 checksums for wheels in the wheelhouse."""

    lines: list[str] = []
    for path in sorted(wheelhouse.glob("*.whl")):
        lines.append(f"{_sha256(path)}  {path.name}")
    (wheelhouse / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    """Return SHA-256 for a local file."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
