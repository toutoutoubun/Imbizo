"""Annotation table model data adapter."""

from __future__ import annotations

from dataclasses import dataclass, field

from imbizo.services.annotation_service import AnnotationEditorState, AnnotationRow


@dataclass(slots=True)
class AnnotationTableModel:
    """Lightweight annotation table data holder."""

    rows: list[AnnotationRow] = field(default_factory=list)

    def set_editor_state(self, state: AnnotationEditorState) -> None:
        """Replace rows from an annotation editor state."""

        self.rows = list(state.rows)

    def row_count(self) -> int:
        """Return row count."""

        return len(self.rows)
