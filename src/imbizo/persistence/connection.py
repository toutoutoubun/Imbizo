"""SQLite connection helpers."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


def open_project_database(database_path: Path) -> sqlite3.Connection:
    """Open a project SQLite database with required pragmas."""

    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    return connection


@contextmanager
def transaction(connection: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    """Run a commit-or-rollback transaction."""

    try:
        yield connection
    except Exception:
        connection.rollback()
        raise
    else:
        connection.commit()
