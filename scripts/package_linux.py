"""Package Linux standalone build with PyInstaller."""

from __future__ import annotations

import subprocess
import sys


def main() -> int:
    """Run PyInstaller for the Linux spec."""

    return subprocess.call([sys.executable, "-m", "PyInstaller", "packaging/pyinstaller/imbizo-linux.spec"])


if __name__ == "__main__":
    raise SystemExit(main())
