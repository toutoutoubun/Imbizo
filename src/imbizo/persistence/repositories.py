"""Repository classes over the local SQLite database."""

from __future__ import annotations

import json
import sqlite3
from typing import Any, Sequence

from imbizo.app.time import utc_now
from imbizo.domain.annotations import (
    Annotation,
    AnnotationSource,
    AnnotationStatus,
    LinguisticStatus,
    SwitchType,
    Tag,
)
from imbizo.domain.exports import ExportRecord
from imbizo.domain.languages import LanguageCategory, LanguageTag
from imbizo.domain.media import MediaAsset, MediaType
from imbizo.domain.metrics import JobStatus, MetricResult, MetricRun
from imbizo.domain.people import Participant, Scene, Speaker
from imbizo.domain.project import ProjectMetadata
from imbizo.domain.provenance import ProvenanceRecord
from imbizo.domain.transcripts import SegmentLevel, SourceFormat, Token, TranscriptDocument, TranscriptSegment


def _enum_value(value: Any) -> Any:
    return getattr(value, "value", value)


class ProjectRepository:
    """Read and write project metadata."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def get_metadata(self) -> ProjectMetadata:
        """Return project metadata."""

        row = self.connection.execute("SELECT * FROM project_metadata WHERE id = 1").fetchone()
        if row is None:
            raise RuntimeError("Project metadata is missing.")
        return ProjectMetadata(
            project_uuid=row["project_uuid"],
            title=row["title"],
            subtitle=row["subtitle"],
            researcher=row["researcher"],
            institution=row["institution"] if "institution" in row.keys() else "",
            location=row["location"],
            project_date=row["project_date"],
            participants_summary=row["participants_summary"],
            expected_languages_summary=row["expected_languages_summary"],
            ethics_notes=row["ethics_notes"],
            irb_rec_reference=row["irb_rec_reference"] if "irb_rec_reference" in row.keys() else "",
            care_acknowledgement=row["care_acknowledgement"] if "care_acknowledgement" in row.keys() else "",
            consent_status=row["consent_status"] if "consent_status" in row.keys() else "",
            data_sharing_constraints=row["data_sharing_constraints"] if "data_sharing_constraints" in row.keys() else "",
            app_version=row["app_version"],
            schema_version=int(row["schema_version"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def update_metadata(self, metadata: ProjectMetadata) -> None:
        """Replace project metadata."""

        metadata.updated_at = utc_now()
        self.connection.execute(
            """
            UPDATE project_metadata
            SET title = ?, subtitle = ?, researcher = ?, location = ?,
                institution = ?, project_date = ?, participants_summary = ?,
                expected_languages_summary = ?, ethics_notes = ?,
                irb_rec_reference = ?, care_acknowledgement = ?,
                consent_status = ?, data_sharing_constraints = ?,
                app_version = ?, schema_version = ?, updated_at = ?
            WHERE id = 1
            """,
            (
                metadata.title,
                metadata.subtitle,
                metadata.researcher,
                metadata.location,
                metadata.institution,
                metadata.project_date,
                metadata.participants_summary,
                metadata.expected_languages_summary,
                metadata.ethics_notes,
                metadata.irb_rec_reference,
                metadata.care_acknowledgement,
                metadata.consent_status,
                metadata.data_sharing_constraints,
                metadata.app_version,
                metadata.schema_version,
                metadata.updated_at,
            ),
        )
        self.connection.commit()


class LanguageRepository:
    """Read and write project language tags."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def list_languages(self) -> list[LanguageTag]:
        """Return all project language tags."""

        rows = self.connection.execute("SELECT * FROM languages ORDER BY sort_order, name").fetchall()
        return [
            LanguageTag(
                id=row["id"],
                code=row["code"],
                name=row["name"],
                autonym=row["autonym"],
                category=LanguageCategory(row["category"]),
                color_hex=row["color_hex"],
                is_expected=bool(row["is_expected"]),
                is_user_defined=bool(row["is_user_defined"]),
                sort_order=int(row["sort_order"]),
                notes=row["notes"],
            )
            for row in rows
        ]

    def save_language(self, language: LanguageTag) -> None:
        """Create or update a language tag."""

        self.connection.execute(
            """
            INSERT INTO languages (
                id, code, name, autonym, category, color_hex,
                is_expected, is_user_defined, sort_order, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                code = excluded.code,
                name = excluded.name,
                autonym = excluded.autonym,
                category = excluded.category,
                color_hex = excluded.color_hex,
                is_expected = excluded.is_expected,
                is_user_defined = excluded.is_user_defined,
                sort_order = excluded.sort_order,
                notes = excluded.notes
            """,
            (
                language.id,
                language.code,
                language.name,
                language.autonym,
                language.category.value,
                language.color_hex,
                int(language.is_expected),
                int(language.is_user_defined),
                language.sort_order,
                language.notes,
            ),
        )
        self.connection.commit()


class PeopleRepository:
    """Read and write participants, speakers, and scenes."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def save_participant(self, participant: Participant) -> None:
        """Create or update a participant."""

        now = utc_now()
        self.connection.execute(
            """
            INSERT INTO participants (
                id, participant_code, display_name, role, demographics_json,
                consent_status, notes, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                participant_code = excluded.participant_code,
                display_name = excluded.display_name,
                role = excluded.role,
                demographics_json = excluded.demographics_json,
                consent_status = excluded.consent_status,
                notes = excluded.notes,
                updated_at = excluded.updated_at
            """,
            (
                participant.id,
                participant.participant_code,
                participant.display_name,
                participant.role,
                json.dumps(participant.demographics, ensure_ascii=False),
                participant.consent_status,
                participant.notes,
                now,
                now,
            ),
        )
        self.connection.commit()

    def list_participants(self) -> list[Participant]:
        """Return project participants."""

        rows = self.connection.execute("SELECT * FROM participants ORDER BY participant_code").fetchall()
        return [
            Participant(
                id=row["id"],
                participant_code=row["participant_code"],
                display_name=row["display_name"],
                role=row["role"],
                demographics=json.loads(row["demographics_json"]),
                consent_status=row["consent_status"],
                notes=row["notes"],
            )
            for row in rows
        ]

    def save_speaker(self, speaker: Speaker) -> None:
        """Create or update a speaker."""

        now = utc_now()
        self.connection.execute(
            """
            INSERT INTO speakers (
                id, participant_id, label, display_name, notes, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                participant_id = excluded.participant_id,
                label = excluded.label,
                display_name = excluded.display_name,
                notes = excluded.notes,
                updated_at = excluded.updated_at
            """,
            (speaker.id, speaker.participant_id, speaker.label, speaker.display_name, speaker.notes, now, now),
        )
        self.connection.commit()

    def list_speakers(self) -> list[Speaker]:
        """Return speaker labels."""

        rows = self.connection.execute("SELECT * FROM speakers ORDER BY label").fetchall()
        return [
            Speaker(
                id=row["id"],
                participant_id=row["participant_id"],
                label=row["label"],
                display_name=row["display_name"],
                notes=row["notes"],
            )
            for row in rows
        ]

    def save_scene(self, scene: Scene) -> None:
        """Create or update a scene."""

        now = utc_now()
        self.connection.execute(
            """
            INSERT INTO scenes (
                id, name, description, start_ms, end_ms, sort_order, notes,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                description = excluded.description,
                start_ms = excluded.start_ms,
                end_ms = excluded.end_ms,
                sort_order = excluded.sort_order,
                notes = excluded.notes,
                updated_at = excluded.updated_at
            """,
            (scene.id, scene.name, scene.description, scene.start_ms, scene.end_ms, scene.sort_order, scene.notes, now, now),
        )
        self.connection.commit()

    def list_scenes(self) -> list[Scene]:
        """Return scenes."""

        rows = self.connection.execute("SELECT * FROM scenes ORDER BY sort_order, name").fetchall()
        return [
            Scene(
                id=row["id"],
                name=row["name"],
                description=row["description"],
                start_ms=row["start_ms"],
                end_ms=row["end_ms"],
                sort_order=int(row["sort_order"]),
                notes=row["notes"],
            )
            for row in rows
        ]


class TagRepository:
    """Read and write tags."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def save_tag(self, tag: Tag) -> None:
        """Create or update a tag."""

        now = utc_now()
        self.connection.execute(
            """
            INSERT INTO tags (id, name, color_hex, description, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                color_hex = excluded.color_hex,
                description = excluded.description,
                updated_at = excluded.updated_at
            """,
            (tag.id, tag.name, tag.color_hex, tag.description, now, now),
        )
        self.connection.commit()

    def list_tags(self) -> list[Tag]:
        """Return project tags."""

        rows = self.connection.execute("SELECT * FROM tags ORDER BY name").fetchall()
        return [Tag(id=row["id"], name=row["name"], color_hex=row["color_hex"], description=row["description"]) for row in rows]


class TranscriptRepository:
    """Read and write transcript documents, segments, and tokens."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def list_documents(self) -> list[TranscriptDocument]:
        """Return transcript documents."""

        rows = self.connection.execute("SELECT * FROM transcript_documents ORDER BY name").fetchall()
        return [self._document_from_row(row) for row in rows]

    def list_segments(self, document_id: str) -> list[TranscriptSegment]:
        """Return segments for a transcript document."""

        rows = self.connection.execute(
            "SELECT * FROM segments WHERE transcript_document_id = ? ORDER BY sort_order",
            (document_id,),
        ).fetchall()
        return [self._segment_from_row(row) for row in rows]

    def list_tokens(self, segment_id: str) -> list[Token]:
        """Return tokens for one segment."""

        rows = self.connection.execute(
            "SELECT * FROM tokens WHERE segment_id = ? ORDER BY sort_order",
            (segment_id,),
        ).fetchall()
        return [self._token_from_row(row) for row in rows]

    def list_all_tokens(self, document_id: str | None = None) -> list[Token]:
        """Return tokens, optionally limited to one document."""

        if document_id:
            rows = self.connection.execute(
                """
                SELECT tokens.* FROM tokens
                JOIN segments ON segments.id = tokens.segment_id
                WHERE segments.transcript_document_id = ?
                ORDER BY segments.sort_order, tokens.sort_order
                """,
                (document_id,),
            ).fetchall()
        else:
            rows = self.connection.execute(
                """
                SELECT tokens.* FROM tokens
                JOIN segments ON segments.id = tokens.segment_id
                ORDER BY segments.sort_order, tokens.sort_order
                """
            ).fetchall()
        return [self._token_from_row(row) for row in rows]

    def save_document_bundle(
        self,
        document: TranscriptDocument,
        segments: Sequence[TranscriptSegment],
        tokens: Sequence[Token],
    ) -> None:
        """Persist one imported transcript bundle."""

        self.connection.execute(
            """
            INSERT OR REPLACE INTO transcript_documents (
                id, import_batch_id, media_asset_id, name, source_format,
                relative_path, original_filename, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                document.id,
                document.import_batch_id,
                document.media_asset_id,
                document.name,
                document.source_format.value,
                document.relative_path,
                document.original_filename,
                document.notes,
            ),
        )
        for segment in segments:
            self.connection.execute(
                """
                INSERT OR REPLACE INTO segments (
                    id, transcript_document_id, media_asset_id, parent_segment_id,
                    speaker_id, scene_id, segment_level, sort_order, start_ms,
                    end_ms, text_original, text_normalized, external_ref, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    segment.id,
                    segment.transcript_document_id,
                    segment.media_asset_id,
                    segment.parent_segment_id,
                    segment.speaker_id,
                    segment.scene_id,
                    segment.segment_level.value,
                    segment.sort_order,
                    segment.start_ms,
                    segment.end_ms,
                    segment.text_original,
                    segment.text_normalized,
                    segment.external_ref,
                    segment.notes,
                ),
            )
        for token in tokens:
            self.connection.execute(
                """
                INSERT OR REPLACE INTO tokens (
                    id, segment_id, sort_order, token_text, normalized_text,
                    char_start, char_end, external_ref
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    token.id,
                    token.segment_id,
                    token.sort_order,
                    token.token_text,
                    token.normalized_text,
                    token.char_start,
                    token.char_end,
                    token.external_ref,
                ),
            )
        self.connection.commit()

    def _document_from_row(self, row: sqlite3.Row) -> TranscriptDocument:
        return TranscriptDocument(
            id=row["id"],
            import_batch_id=row["import_batch_id"],
            media_asset_id=row["media_asset_id"],
            name=row["name"],
            source_format=SourceFormat(row["source_format"]),
            relative_path=row["relative_path"],
            original_filename=row["original_filename"],
            notes=row["notes"],
        )

    def _segment_from_row(self, row: sqlite3.Row) -> TranscriptSegment:
        return TranscriptSegment(
            id=row["id"],
            transcript_document_id=row["transcript_document_id"],
            media_asset_id=row["media_asset_id"],
            parent_segment_id=row["parent_segment_id"],
            speaker_id=row["speaker_id"],
            scene_id=row["scene_id"],
            segment_level=SegmentLevel(row["segment_level"]),
            sort_order=int(row["sort_order"]),
            start_ms=row["start_ms"],
            end_ms=row["end_ms"],
            text_original=row["text_original"],
            text_normalized=row["text_normalized"],
            external_ref=row["external_ref"],
            notes=row["notes"],
        )

    def _token_from_row(self, row: sqlite3.Row) -> Token:
        return Token(
            id=row["id"],
            segment_id=row["segment_id"],
            sort_order=int(row["sort_order"]),
            token_text=row["token_text"],
            normalized_text=row["normalized_text"],
            char_start=row["char_start"],
            char_end=row["char_end"],
            external_ref=row["external_ref"],
        )


class AnnotationRepository:
    """Read and write annotations."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def list_annotations(self) -> list[Annotation]:
        """Return all annotations."""

        rows = self.connection.execute("SELECT * FROM annotations ORDER BY updated_at").fetchall()
        return [self._annotation_from_row(row) for row in rows]

    def list_annotations_for_tokens(self, token_ids: Sequence[str]) -> dict[str, list[Annotation]]:
        """Return annotations grouped by token ID."""

        if not token_ids:
            return {}
        parameter_slots = ",".join("?" for _ in token_ids)
        rows = self.connection.execute(
            f"SELECT * FROM annotations WHERE token_id IN ({parameter_slots}) ORDER BY updated_at",
            tuple(token_ids),
        ).fetchall()
        grouped: dict[str, list[Annotation]] = {token_id: [] for token_id in token_ids}
        for row in rows:
            annotation = self._annotation_from_row(row)
            if annotation.token_id:
                grouped.setdefault(annotation.token_id, []).append(annotation)
        return grouped

    def get_effective_annotation_for_token(self, token_id: str) -> Annotation | None:
        """Return the effective annotation for one token."""

        from imbizo.domain.annotations import choose_effective_annotation

        rows = self.connection.execute(
            "SELECT * FROM annotations WHERE token_id = ? ORDER BY updated_at",
            (token_id,),
        ).fetchall()
        return choose_effective_annotation([self._annotation_from_row(row) for row in rows])

    def save_manual_annotation(self, annotation: Annotation) -> None:
        """Save a manual annotation and supersede older active manual annotations."""

        now = utc_now()
        target_column = "token_id" if annotation.token_id else "segment_id"
        target_value = annotation.token_id or annotation.segment_id
        self.connection.execute(
            f"""
            UPDATE annotations
            SET status = ?, updated_at = ?
            WHERE {target_column} = ? AND source = ? AND status = ?
            """,
            (
                AnnotationStatus.SUPERSEDED.value,
                now,
                target_value,
                AnnotationSource.MANUAL.value,
                AnnotationStatus.ACTIVE.value,
            ),
        )
        annotation.source = AnnotationSource.MANUAL
        annotation.status = AnnotationStatus.ACTIVE
        annotation.created_at = annotation.created_at or now
        annotation.updated_at = now
        self._insert_annotation(annotation)
        self.connection.commit()

    def save_auto_annotation(self, annotation: Annotation) -> None:
        """Save an automatic annotation without replacing manual work."""

        annotation.source = AnnotationSource.AUTO
        annotation.status = AnnotationStatus.ACTIVE
        annotation.created_at = annotation.created_at or utc_now()
        annotation.updated_at = annotation.updated_at or annotation.created_at
        self._insert_annotation(annotation)
        self.connection.commit()

    def reject_annotation(self, annotation_id: str) -> None:
        """Mark an annotation as rejected."""

        self.connection.execute(
            "UPDATE annotations SET status = ?, updated_at = ? WHERE id = ?",
            (AnnotationStatus.REJECTED.value, utc_now(), annotation_id),
        )
        self.connection.commit()

    def _insert_annotation(self, annotation: Annotation) -> None:
        self.connection.execute(
            """
            INSERT OR REPLACE INTO annotations (
                id, token_id, segment_id, source, status, language_id,
                matrix_language_id, embedded_language_id, switch_type,
                linguistic_status, trigger_text, direction_from_language_id,
                direction_to_language_id, researcher_confidence,
                auto_confidence, memo, created_by, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                annotation.id,
                annotation.token_id,
                annotation.segment_id,
                annotation.source.value,
                annotation.status.value,
                annotation.language_id,
                annotation.matrix_language_id,
                annotation.embedded_language_id,
                _enum_value(annotation.switch_type),
                _enum_value(annotation.linguistic_status),
                annotation.trigger_text,
                annotation.direction_from_language_id,
                annotation.direction_to_language_id,
                annotation.researcher_confidence,
                annotation.auto_confidence,
                annotation.memo,
                annotation.created_by,
                annotation.created_at,
                annotation.updated_at,
            ),
        )

    def _annotation_from_row(self, row: sqlite3.Row) -> Annotation:
        return Annotation(
            id=row["id"],
            token_id=row["token_id"],
            segment_id=row["segment_id"],
            source=AnnotationSource(row["source"]),
            status=AnnotationStatus(row["status"]),
            language_id=row["language_id"],
            matrix_language_id=row["matrix_language_id"],
            embedded_language_id=row["embedded_language_id"],
            switch_type=SwitchType(row["switch_type"]) if row["switch_type"] else None,
            linguistic_status=LinguisticStatus(row["linguistic_status"]) if row["linguistic_status"] else None,
            trigger_text=row["trigger_text"],
            direction_from_language_id=row["direction_from_language_id"],
            direction_to_language_id=row["direction_to_language_id"],
            researcher_confidence=row["researcher_confidence"],
            auto_confidence=row["auto_confidence"],
            memo=row["memo"],
            created_by=row["created_by"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


class MediaRepository:
    """Read and write media assets."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def save_media(self, media: MediaAsset) -> None:
        """Create or update a media asset."""

        self.connection.execute(
            """
            INSERT OR REPLACE INTO media_assets (
                id, import_batch_id, media_type, relative_path, original_filename,
                file_format, mime_type, duration_ms, sample_rate_hz, channels,
                sha256, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                media.id,
                media.import_batch_id,
                media.media_type.value,
                media.relative_path,
                media.original_filename,
                media.file_format,
                media.mime_type,
                media.duration_ms,
                media.sample_rate_hz,
                media.channels,
                media.sha256,
                media.notes,
            ),
        )
        self.connection.commit()

    def list_media(self) -> list[MediaAsset]:
        """Return media assets."""

        rows = self.connection.execute("SELECT * FROM media_assets ORDER BY original_filename").fetchall()
        return [
            MediaAsset(
                id=row["id"],
                import_batch_id=row["import_batch_id"],
                media_type=MediaType(row["media_type"]),
                relative_path=row["relative_path"],
                original_filename=row["original_filename"],
                file_format=row["file_format"],
                mime_type=row["mime_type"],
                duration_ms=row["duration_ms"],
                sample_rate_hz=row["sample_rate_hz"],
                channels=row["channels"],
                sha256=row["sha256"],
                notes=row["notes"],
            )
            for row in rows
        ]


class ImportRepository:
    """Read and write import batch records."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def save_import_batch(
        self,
        batch_id: str,
        source_label: str,
        original_path: str,
        copied_path: str,
        importer_name: str,
        source_sha256: str,
        report: dict[str, Any],
    ) -> None:
        """Save an import batch."""

        self.connection.execute(
            """
            INSERT INTO import_batches (
                id, source_label, original_path, copied_path, importer_name,
                source_sha256, import_report_json, imported_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                batch_id,
                source_label,
                original_path,
                copied_path,
                importer_name,
                source_sha256,
                json.dumps(report, ensure_ascii=False),
                utc_now(),
            ),
        )
        self.connection.commit()


class ProvenanceRepository:
    """Read and write provenance records."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def save(self, record: ProvenanceRecord) -> None:
        """Persist a provenance record."""

        self.connection.execute(
            """
            INSERT INTO provenance_records (
                id, event_type, actor_type, actor_name, target_table, target_id,
                related_table, related_id, tool_name, tool_version, confidence,
                message, payload_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.id,
                record.event_type,
                record.actor_type,
                record.actor_name,
                record.target_table,
                record.target_id,
                record.related_table,
                record.related_id,
                record.tool_name,
                record.tool_version,
                record.confidence,
                record.message,
                json.dumps(record.payload, ensure_ascii=False),
                record.created_at,
            ),
        )
        self.connection.commit()

    def list_for_target(self, target_table: str, target_id: str) -> list[ProvenanceRecord]:
        """Return provenance records for one target object."""

        rows = self.connection.execute(
            """
            SELECT * FROM provenance_records
            WHERE target_table = ? AND target_id = ?
            ORDER BY created_at
            """,
            (target_table, target_id),
        ).fetchall()
        return [
            ProvenanceRecord(
                id=row["id"],
                event_type=row["event_type"],
                actor_type=row["actor_type"],
                actor_name=row["actor_name"],
                target_table=row["target_table"],
                target_id=row["target_id"],
                related_table=row["related_table"],
                related_id=row["related_id"],
                tool_name=row["tool_name"],
                tool_version=row["tool_version"],
                confidence=row["confidence"],
                message=row["message"],
                payload=json.loads(row["payload_json"]),
                created_at=row["created_at"],
            )
            for row in rows
        ]


class MetricRepository:
    """Read and write metric runs and results."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def save_run(self, run: MetricRun) -> None:
        """Save a metric run."""

        self.connection.execute(
            """
            INSERT OR REPLACE INTO metric_runs (
                id, run_name, formula_version, input_filter_json, status,
                started_at, finished_at, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run.id,
                run.run_name,
                run.formula_version,
                json.dumps(run.input_filter, ensure_ascii=False),
                run.status.value,
                run.started_at,
                run.finished_at,
                run.error_message,
            ),
        )
        self.connection.commit()

    def save_results(self, results: Sequence[MetricResult]) -> None:
        """Save metric results."""

        for result in results:
            self.connection.execute(
                """
                INSERT OR REPLACE INTO metric_results (
                    id, metric_run_id, metric_name, scope_type, scope_id,
                    value_json, input_count, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result.id,
                    result.metric_run_id,
                    result.metric_name,
                    result.scope_type,
                    result.scope_id,
                    json.dumps(result.value, ensure_ascii=False),
                    result.input_count,
                    result.created_at,
                ),
            )
        self.connection.commit()

    def get_results(self, metric_run_id: str) -> list[MetricResult]:
        """Return results for one metric run."""

        rows = self.connection.execute(
            "SELECT * FROM metric_results WHERE metric_run_id = ? ORDER BY metric_name",
            (metric_run_id,),
        ).fetchall()
        return [
            MetricResult(
                id=row["id"],
                metric_run_id=row["metric_run_id"],
                metric_name=row["metric_name"],
                scope_type=row["scope_type"],
                scope_id=row["scope_id"],
                value=json.loads(row["value_json"]),
                input_count=int(row["input_count"]),
                created_at=row["created_at"],
            )
            for row in rows
        ]


class ExportRepository:
    """Read and write export records."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def save(self, record: ExportRecord) -> None:
        """Save an export record."""

        self.connection.execute(
            """
            INSERT OR REPLACE INTO exports (
                id, export_format, relative_path, options_json, sha256, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                record.id,
                record.export_format,
                record.relative_path,
                json.dumps(record.options, ensure_ascii=False),
                record.sha256,
                record.created_at,
            ),
        )
        self.connection.commit()
