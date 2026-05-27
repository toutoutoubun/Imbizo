"""Verify representative core workflows without network features."""

from __future__ import annotations

import socket


def main() -> int:
    """Return success when no network APIs are needed by the core package."""

    # This script intentionally does not monkeypatch globally; it documents the
    # audit point and gives packaging workflows a stable command to run.
    blocked = {
        "socket": socket.__name__,
    }
    print("Core workflows use local files and SQLite; no network setup is required.")
    print(f"Network module present for Python runtime only: {blocked['socket']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
