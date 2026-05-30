"""Reviewed Local LID accuracy summaries.

Accuracy here means agreement with researcher-reviewed labels. The service
never treats auto labels as ground truth: manual and imported annotations form
the denominator, and active automatic labels or segment suggestions are compared
against that reviewed evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from imbizo.domain.project import ProjectContext


AccuracyScope = Literal["token", "span"]


@dataclass(slots=True)
class LidAccuracyRow:
    """One language-specific Local LID accuracy row."""

    scope: AccuracyScope
    language_id: str
    language_code: str
    language_name: str
    reviewed_count: int
    auto_labelled_count: int
    correct_count: int
    incorrect_count: int
    missing_count: int
    basis: str

    @property
    def accuracy(self) -> float | None:
        """Return correct auto labels divided by all reviewed items."""

        if self.reviewed_count == 0:
            return None
        return self.correct_count / self.reviewed_count


class LidAccuracyService:
    """Compute reviewed token/span accuracy for local LID outputs."""

    def compute(self, context: ProjectContext, document_id: str | None = None) -> list[LidAccuracyRow]:
        """Return token and span accuracy rows for one project or document."""

        return [
            *self._token_accuracy(context, document_id),
            *self._span_accuracy(context, document_id),
        ]

    def _token_accuracy(self, context: ProjectContext, document_id: str | None) -> list[LidAccuracyRow]:
        document_filter = ""
        parameters: tuple[str, ...] = ()
        if document_id:
            document_filter = """
                JOIN tokens tok ON tok.id = gold.token_id
                JOIN segments seg ON seg.id = tok.segment_id
                WHERE seg.transcript_document_id = ?
            """
            parameters = (document_id,)
        rows = context.connection.execute(
            f"""
            WITH reviewed AS (
                SELECT token_id, language_id
                FROM (
                    SELECT
                        token_id,
                        language_id,
                        ROW_NUMBER() OVER (
                            PARTITION BY token_id
                            ORDER BY
                                CASE source WHEN 'manual' THEN 1 WHEN 'imported' THEN 2 ELSE 3 END,
                                updated_at DESC
                        ) AS rn
                    FROM annotations
                    WHERE status = 'active'
                      AND token_id IS NOT NULL
                      AND language_id IS NOT NULL
                      AND source IN ('manual', 'imported')
                )
                WHERE rn = 1
            ),
            auto_labels AS (
                SELECT token_id, language_id
                FROM (
                    SELECT
                        token_id,
                        language_id,
                        ROW_NUMBER() OVER (
                            PARTITION BY token_id
                            ORDER BY updated_at DESC
                        ) AS rn
                    FROM annotations
                    WHERE status = 'active'
                      AND token_id IS NOT NULL
                      AND language_id IS NOT NULL
                      AND source = 'auto'
                )
                WHERE rn = 1
            ),
            gold AS (
                SELECT reviewed.*
                FROM reviewed
                {document_filter}
            )
            SELECT
                lang.id AS language_id,
                lang.code AS language_code,
                lang.name AS language_name,
                COUNT(*) AS reviewed_count,
                SUM(CASE WHEN auto_labels.language_id IS NOT NULL THEN 1 ELSE 0 END) AS auto_labelled_count,
                SUM(CASE WHEN auto_labels.language_id = gold.language_id THEN 1 ELSE 0 END) AS correct_count
            FROM gold
            LEFT JOIN auto_labels ON auto_labels.token_id = gold.token_id
            JOIN languages lang ON lang.id = gold.language_id
            GROUP BY lang.id, lang.code, lang.name
            ORDER BY lang.sort_order, lang.name
            """,
            parameters,
        ).fetchall()
        return [
            _row_from_sql(
                scope="token",
                row=row,
                basis="Reviewed manual/imported token labels compared with active auto token labels.",
            )
            for row in rows
        ]

    def _span_accuracy(self, context: ProjectContext, document_id: str | None) -> list[LidAccuracyRow]:
        document_filter = ""
        parameters: tuple[str, ...] = ()
        if document_id:
            document_filter = """
                JOIN segments seg ON seg.id = gold.segment_id
                WHERE seg.transcript_document_id = ?
            """
            parameters = (document_id,)
        rows = context.connection.execute(
            f"""
            WITH reviewed AS (
                SELECT segment_id, language_id
                FROM (
                    SELECT
                        segment_id,
                        language_id,
                        ROW_NUMBER() OVER (
                            PARTITION BY segment_id
                            ORDER BY
                                CASE source WHEN 'manual' THEN 1 WHEN 'imported' THEN 2 ELSE 3 END,
                                updated_at DESC
                        ) AS rn
                    FROM annotations
                    WHERE status = 'active'
                      AND segment_id IS NOT NULL
                      AND language_id IS NOT NULL
                      AND source IN ('manual', 'imported')
                )
                WHERE rn = 1
            ),
            top_suggestions AS (
                SELECT segment_id, language_id
                FROM (
                    SELECT
                        lid_suggestions.segment_id,
                        lid_suggestions.language_id,
                        ROW_NUMBER() OVER (
                            PARTITION BY lid_suggestions.segment_id
                            ORDER BY lid_suggestions.created_at DESC
                        ) AS rn
                    FROM lid_suggestions
                    JOIN lid_runs ON lid_runs.id = lid_suggestions.lid_run_id
                    WHERE lid_suggestions.segment_id IS NOT NULL
                      AND lid_suggestions.language_id IS NOT NULL
                      AND lid_suggestions.rank = 1
                      AND lid_runs.status = 'completed'
                )
                WHERE rn = 1
            ),
            gold AS (
                SELECT reviewed.*
                FROM reviewed
                {document_filter}
            )
            SELECT
                lang.id AS language_id,
                lang.code AS language_code,
                lang.name AS language_name,
                COUNT(*) AS reviewed_count,
                SUM(CASE WHEN top_suggestions.language_id IS NOT NULL THEN 1 ELSE 0 END) AS auto_labelled_count,
                SUM(CASE WHEN top_suggestions.language_id = gold.language_id THEN 1 ELSE 0 END) AS correct_count
            FROM gold
            LEFT JOIN top_suggestions ON top_suggestions.segment_id = gold.segment_id
            JOIN languages lang ON lang.id = gold.language_id
            GROUP BY lang.id, lang.code, lang.name
            ORDER BY lang.sort_order, lang.name
            """,
            parameters,
        ).fetchall()
        return [
            _row_from_sql(
                scope="span",
                row=row,
                basis="Reviewed manual/imported span labels compared with latest rank-1 Local LID span suggestions.",
            )
            for row in rows
        ]


def _row_from_sql(*, scope: AccuracyScope, row, basis: str) -> LidAccuracyRow:
    reviewed_count = int(row["reviewed_count"] or 0)
    auto_labelled_count = int(row["auto_labelled_count"] or 0)
    correct_count = int(row["correct_count"] or 0)
    incorrect_count = max(0, auto_labelled_count - correct_count)
    missing_count = max(0, reviewed_count - auto_labelled_count)
    return LidAccuracyRow(
        scope=scope,
        language_id=str(row["language_id"]),
        language_code=str(row["language_code"]),
        language_name=str(row["language_name"]),
        reviewed_count=reviewed_count,
        auto_labelled_count=auto_labelled_count,
        correct_count=correct_count,
        incorrect_count=incorrect_count,
        missing_count=missing_count,
        basis=basis,
    )
