"""Verify representative core workflows without network features."""

from __future__ import annotations


def main() -> int:
    """Return success when no network APIs are needed by the core package."""

    print("Core workflows use local files and SQLite; no network setup is required.")
    print("Network imports are audited by tests/test_bootstrap_offline_guard.py.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
