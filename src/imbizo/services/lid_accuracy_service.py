"""Local LID acceptance summaries.

The dashboard metric answers a practical review question: for every final
language label in a project, how many labels are still accepted automatic LID
labels, and how many came from manual/imported human evidence?

This avoids a misleading "accuracy" denominator made only from corrected or
imported labels. Manual/imported annotations remain authoritative, but tokens
that were auto-labelled and never corrected now count as accepted auto labels.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from imbizo.domain.project import ProjectContext


AccuracyScope = Literal["token", "span"]


@dataclass(slots=True)
class LidAccuracyRow:
    """One language-specific Local LID acceptance row."""

    scope: AccuracyScope
    language_id: str
    language_code: str
    language_name: str
    final_label_count: int
    accepted_auto_count: int
    reviewed_label_count: int
    manual_label_count: int
    imported_label_count: int
    basis: str

    @property
    def auto_acceptance_rate(self) -> float | None:
        """Return accepted automatic labels divided by final labels."""

        if self.final_label_count == 0:
            return None
        return self.accepted_auto_count / self.final_label_count

    @property
    def manual_intervention_rate(self) -> float | None:
        """Return manual/imported labels divided by final labels."""

        if self.final_label_count == 0:
            return None
        return self.reviewed_label_count / self.final_label_count


class LidAccuracyService:
    """Compute final-label Local LID acceptance for token/span outputs."""

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
                JOIN tokens tok ON tok.id = effective.token_id
                JOIN segments seg ON seg.id = tok.segment_id
                WHERE seg.transcript_document_id = ?
            """
            parameters = (document_id,)
        rows = context.connection.execute(
            f"""
            WITH effective AS (
                SELECT token_id, language_id, source
                FROM (
                    SELECT
                        token_id,
                        language_id,
                        source,
                        ROW_NUMBER() OVER (
                            PARTITION BY token_id
                            ORDER BY
                                CASE source WHEN 'manual' THEN 1 WHEN 'imported' THEN 2 WHEN 'auto' THEN 3 ELSE 4 END,
                                updated_at DESC
                        ) AS rn
                    FROM annotations
                    WHERE status = 'active'
                      AND token_id IS NOT NULL
                      AND language_id IS NOT NULL
                      AND source IN ('manual', 'imported', 'auto')
                )
                WHERE rn = 1
            ),
            gold AS (
                SELECT effective.*
                FROM effective
                {document_filter}
            )
            SELECT
                lang.id AS language_id,
                lang.code AS language_code,
                lang.name AS language_name,
                COUNT(*) AS final_label_count,
                SUM(CASE WHEN gold.source = 'auto' THEN 1 ELSE 0 END) AS accepted_auto_count,
                SUM(CASE WHEN gold.source IN ('manual', 'imported') THEN 1 ELSE 0 END) AS reviewed_label_count,
                SUM(CASE WHEN gold.source = 'manual' THEN 1 ELSE 0 END) AS manual_label_count,
                SUM(CASE WHEN gold.source = 'imported' THEN 1 ELSE 0 END) AS imported_label_count
            FROM gold
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
                basis=(
                    "Final effective token labels grouped by source. "
                    "Auto accepted means the active effective label is still automatic; "
                    "manual/imported means a researcher or imported file supplied the final label."
                ),
            )
            for row in rows
        ]

    def _span_accuracy(self, context: ProjectContext, document_id: str | None) -> list[LidAccuracyRow]:
        document_filter = ""
        parameters: tuple[str, ...] = ()
        if document_id:
            document_filter = """
                JOIN segments seg ON seg.id = effective.segment_id
                WHERE seg.transcript_document_id = ?
            """
            parameters = (document_id,)
        rows = context.connection.execute(
            f"""
            WITH reviewed AS (
                SELECT segment_id, language_id, source
                FROM (
                    SELECT
                        segment_id,
                        language_id,
                        source,
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
                SELECT segment_id, language_id, 'auto' AS source
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
            effective AS (
                SELECT segment_id, language_id, source FROM reviewed
                UNION ALL
                SELECT top_suggestions.segment_id, top_suggestions.language_id, top_suggestions.source
                FROM top_suggestions
                LEFT JOIN reviewed ON reviewed.segment_id = top_suggestions.segment_id
                WHERE reviewed.segment_id IS NULL
            ),
            gold AS (
                SELECT effective.*
                FROM effective
                {document_filter}
            )
            SELECT
                lang.id AS language_id,
                lang.code AS language_code,
                lang.name AS language_name,
                COUNT(*) AS final_label_count,
                SUM(CASE WHEN gold.source = 'auto' THEN 1 ELSE 0 END) AS accepted_auto_count,
                SUM(CASE WHEN gold.source IN ('manual', 'imported') THEN 1 ELSE 0 END) AS reviewed_label_count,
                SUM(CASE WHEN gold.source = 'manual' THEN 1 ELSE 0 END) AS manual_label_count,
                SUM(CASE WHEN gold.source = 'imported' THEN 1 ELSE 0 END) AS imported_label_count
            FROM gold
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
                basis=(
                    "Final effective span labels grouped by source. "
                    "Reviewed span labels override Local LID suggestions; unreviewed segments use the latest rank-1 suggestion."
                ),
            )
            for row in rows
        ]


def _row_from_sql(*, scope: AccuracyScope, row, basis: str) -> LidAccuracyRow:
    final_label_count = int(row["final_label_count"] or 0)
    accepted_auto_count = int(row["accepted_auto_count"] or 0)
    reviewed_label_count = int(row["reviewed_label_count"] or 0)
    manual_label_count = int(row["manual_label_count"] or 0)
    imported_label_count = int(row["imported_label_count"] or 0)
    return LidAccuracyRow(
        scope=scope,
        language_id=str(row["language_id"]),
        language_code=str(row["language_code"]),
        language_name=str(row["language_name"]),
        final_label_count=final_label_count,
        accepted_auto_count=accepted_auto_count,
        reviewed_label_count=reviewed_label_count,
        manual_label_count=manual_label_count,
        imported_label_count=imported_label_count,
        basis=basis,
    )
