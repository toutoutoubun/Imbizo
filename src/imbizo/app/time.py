"""Small time helpers."""

from __future__ import annotations

from datetime import UTC, datetime


def utc_now() -> str:
    """Return the current time as an ISO 8601 UTC string."""

    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
