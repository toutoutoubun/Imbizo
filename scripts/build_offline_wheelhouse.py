"""Build an offline wheelhouse using pip."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    """Build wheels into a local wheelhouse directory."""

    wheelhouse = Path("wheelhouse")
    wheelhouse.mkdir(exist_ok=True)
    command = [sys.executable, "-m", "pip", "wheel", ".[gui,xlsx,audio,security]", "--wheel-dir", str(wheelhouse)]
    return subprocess.call(command)


if __name__ == "__main__":
    raise SystemExit(main())
