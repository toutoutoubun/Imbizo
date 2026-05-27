"""Create a transferable offline installation bundle on a connected machine."""

from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path


FASTTEXT_LID_URL = "https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.ftz"


def main() -> int:
    """Download wheels and optional local model files into one bundle folder."""

    parser = argparse.ArgumentParser()
    parser.add_argument("bundle_dir", type=Path, help="Directory to create for USB transfer.")
    parser.add_argument("--include-fasttext-lid", action="store_true", help="Download fastText lid.176.ftz into the bundle.")
    args = parser.parse_args()

    bundle = args.bundle_dir
    wheelhouse = bundle / "wheelhouse"
    models = bundle / "models"
    bundle.mkdir(parents=True, exist_ok=True)
    wheelhouse.mkdir(exist_ok=True)
    models.mkdir(exist_ok=True)

    subprocess.check_call([sys.executable, "-m", "pip", "wheel", ".[gui,xlsx,security,reports]", "--wheel-dir", str(wheelhouse)])
    shutil.copy2("INSTALL_OFFLINE.md", bundle / "INSTALL_OFFLINE.md")
    shutil.copy2("CITATION.cff", bundle / "CITATION.cff")
    shutil.copy2("CHANGELOG.md", bundle / "CHANGELOG.md")
    shutil.copytree("dictionaries", bundle / "dictionaries", dirs_exist_ok=True)

    if args.include_fasttext_lid:
        target = models / "lid.176.ftz"
        print(f"Downloading {FASTTEXT_LID_URL} -> {target}")
        urllib.request.urlretrieve(FASTTEXT_LID_URL, target)

    _write_checksums(bundle)
    print(f"Offline bundle created at {bundle}")
    return 0


def _write_checksums(bundle: Path) -> None:
    """Write SHA-256 checksums for every regular file in the bundle."""

    lines: list[str] = []
    for path in sorted(item for item in bundle.rglob("*") if item.is_file()):
        if path.name == "SHA256SUMS.txt":
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{digest}  {path.relative_to(bundle).as_posix()}")
    (bundle / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
