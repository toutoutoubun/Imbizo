"""Morphology assistance service."""

from __future__ import annotations

import uuid

from imbizo.app.time import utc_now
from imbizo.domain.morphology import Morpheme, MorphemeDictionaryEntry, MorphemeSplit, parse_split_text
from imbizo.domain.project import ProjectContext
from imbizo.morphology.suggestions import MorphologySuggester


class MorphologyService:
    """Coordinate morphology suggestions and manual splits."""

    def suggest_splits(self, context: ProjectContext, token_id: str) -> list[MorphemeSplit]:
        """Return editable morpheme split suggestions for a token."""

        row = context.connection.execute("SELECT * FROM tokens WHERE id = ?", (token_id,)).fetchone()
        if row is None:
            return []
        from imbizo.domain.transcripts import Token

        token = Token(
            id=row["id"],
            segment_id=row["segment_id"],
            sort_order=int(row["sort_order"]),
            token_text=row["token_text"],
            normalized_text=row["normalized_text"],
            char_start=row["char_start"],
            char_end=row["char_end"],
            external_ref=row["external_ref"],
        )
        entries = self.list_dictionary_entries(context)
        return MorphologySuggester().suggest(token, entries)

    def save_manual_split(self, context: ProjectContext, token_id: str, split_text: str, notes: str = "") -> MorphemeSplit:
        """Save a researcher-entered morpheme split."""

        now = utc_now()
        split = MorphemeSplit(
            id=str(uuid.uuid4()),
            token_id=token_id,
            source="manual",
            status="active",
            split_text=split_text,
            notes=notes,
            created_at=now,
            updated_at=now,
        )
        context.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS morpheme_splits (
                id TEXT PRIMARY KEY,
                token_id TEXT NOT NULL,
                source TEXT NOT NULL,
                status TEXT NOT NULL,
                split_text TEXT NOT NULL,
                notes TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        context.connection.execute(
            """
            INSERT INTO morpheme_splits (
                id, token_id, source, status, split_text, notes, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (split.id, split.token_id, split.source, split.status, split.split_text, split.notes, split.created_at, split.updated_at),
        )
        context.connection.commit()
        return split

    def list_dictionary_entries(self, context: ProjectContext, language_id: str | None = None) -> list[MorphemeDictionaryEntry]:
        """Return morphology dictionary entries."""

        context.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS morpheme_dictionary_entries (
                id TEXT PRIMARY KEY,
                language_id TEXT NOT NULL,
                surface TEXT NOT NULL,
                category TEXT NOT NULL,
                gloss TEXT NOT NULL DEFAULT '',
                notes TEXT NOT NULL DEFAULT '',
                source TEXT NOT NULL DEFAULT 'user',
                is_active INTEGER NOT NULL DEFAULT 1
            )
            """
        )
        if language_id:
            rows = context.connection.execute(
                "SELECT * FROM morpheme_dictionary_entries WHERE language_id = ? AND is_active = 1 ORDER BY surface",
                (language_id,),
            ).fetchall()
        else:
            rows = context.connection.execute(
                "SELECT * FROM morpheme_dictionary_entries WHERE is_active = 1 ORDER BY surface"
            ).fetchall()
        return [
            MorphemeDictionaryEntry(
                id=row["id"],
                language_id=row["language_id"],
                surface=row["surface"],
                category=row["category"],
                gloss=row["gloss"],
                notes=row["notes"],
                source=row["source"],
                is_active=bool(row["is_active"]),
            )
            for row in rows
        ]

    def save_dictionary_entry(self, context: ProjectContext, entry: MorphemeDictionaryEntry) -> None:
        """Create or update a project-local dictionary entry."""

        self.list_dictionary_entries(context)
        context.connection.execute(
            """
            INSERT OR REPLACE INTO morpheme_dictionary_entries (
                id, language_id, surface, category, gloss, notes, source, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (entry.id, entry.language_id, entry.surface, entry.category, entry.gloss, entry.notes, entry.source, int(entry.is_active)),
        )
        context.connection.commit()
