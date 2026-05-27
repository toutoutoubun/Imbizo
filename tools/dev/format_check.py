"""Development formatting check command."""

from __future__ import annotations


def main() -> int:
    """Return success for repositories without a configured formatter."""

    print("No formatter configured yet.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
