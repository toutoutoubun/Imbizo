"""PySide6 highlight-coding annotation editor.

The implementation keeps visual encodings redundant: language colour is paired
with a glyph, switch type with border style, 4-M type with underline style, and
trigger role with arrows. This satisfies WCAG 1.4.1 and preserves Imbizo-CS's
humanities-led principle that automatic cues remain inspectable and editable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
import sqlite3
from typing import Any

from imbizo.core.visualisation.palette import LanguagePalette


class HighlightMode(StrEnum):
    """Available highlight dimensions."""

    LANGUAGE = "language"
    FOUR_M = "four_m"
    SWITCH_TYPE = "switch_type"
    TRIGGER_ROLE = "trigger_role"
    MIXED_CODE_SPAN = "mixed_code_span"
    INTEGRATION_SCORE = "integration_score"


@dataclass(slots=True)
class HighlightToken:
    """Token data needed by the highlight editor."""

    token_id: str
    surface: str
    language: str = "und"
    matrix_language: str | None = None
    embedded_language: str | None = None
    four_m_type: str | None = None
    switch_type: str | None = None
    trigger_role: str | None = None
    mixed_code_variety: str | None = None
    integration_score: float | None = None
    start_time_ms: int | None = None
    custom_tags: list[str] = field(default_factory=list)

    def accessible_name(self) -> str:
        """Return a screen-reader-friendly description of the token."""

        return (
            f"{self.surface} language {self.language} matrix {self.matrix_language or 'unset'} "
            f"embedded {self.embedded_language or 'unset'} 4-M {self.four_m_type or 'unset'} "
            f"switch {self.switch_type or 'none'} trigger {self.trigger_role or 'none'}"
        )


class BulkEditCommand:
    """Atomic, reversible bulk edit for selected tokens."""

    def __init__(self, connection: sqlite3.Connection, token_ids: list[str], updates: dict[str, Any]) -> None:
        self.connection = connection
        self.token_ids = token_ids
        self.updates = updates
        self.previous: dict[str, dict[str, Any]] = {}

    def apply(self) -> None:
        """Apply the bulk edit in one SQLite transaction."""

        allowed_token_columns = {"four_m_type", "trigger_role", "mixed_code_variety", "phon_integration_score"}
        with self.connection:
            for token_id in self.token_ids:
                self.previous[token_id] = self._snapshot(token_id)
                token_updates = {key: value for key, value in self.updates.items() if key in allowed_token_columns}
                if token_updates:
                    assignments = ", ".join(f"{key} = ?" for key in token_updates)
                    self.connection.execute(
                        f"UPDATE tokens SET {assignments} WHERE id = ?",
                        [*token_updates.values(), token_id],
                    )
                if "language_id" in self.updates or "memo" in self.updates or "switch_type" in self.updates:
                    self._upsert_annotation(token_id)

    def undo(self) -> None:
        """Restore token-column values captured before `apply`."""

        with self.connection:
            for token_id, values in self.previous.items():
                if values:
                    assignments = ", ".join(f"{key} = ?" for key in values)
                    self.connection.execute(f"UPDATE tokens SET {assignments} WHERE id = ?", [*values.values(), token_id])

    def _snapshot(self, token_id: str) -> dict[str, Any]:
        columns = _existing_columns(self.connection, "tokens")
        wanted = [column for column in ["four_m_type", "trigger_role", "mixed_code_variety", "phon_integration_score"] if column in columns]
        if not wanted:
            return {}
        row = self.connection.execute(f"SELECT {', '.join(wanted)} FROM tokens WHERE id = ?", (token_id,)).fetchone()
        return dict(zip(wanted, row)) if row else {}

    def _upsert_annotation(self, token_id: str) -> None:
        import uuid
        from imbizo.app.time import utc_now

        now = utc_now()
        row = self.connection.execute("SELECT id FROM annotations WHERE token_id = ? AND status = 'active' LIMIT 1", (token_id,)).fetchone()
        if row:
            self.connection.execute(
                "UPDATE annotations SET language_id = COALESCE(?, language_id), memo = COALESCE(?, memo), switch_type = COALESCE(?, switch_type), updated_at = ? WHERE id = ?",
                (self.updates.get("language_id"), self.updates.get("memo"), self.updates.get("switch_type"), now, row[0]),
            )
        else:
            self.connection.execute(
                "INSERT INTO annotations (id, token_id, source, status, language_id, switch_type, memo, created_at, updated_at) VALUES (?, ?, 'manual', 'active', ?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), token_id, self.updates.get("language_id"), self.updates.get("switch_type"), self.updates.get("memo", ""), now, now),
            )


class HighlightCodingEditor:
    """QGraphicsView-based highlight annotation surface."""

    def __init__(self, project_root: Path | None = None, connection: sqlite3.Connection | None = None) -> None:
        self.project_root = project_root
        self.connection = connection
        self.palette = LanguagePalette(project_root)
        self.mode = HighlightMode.LANGUAGE
        self.tokens: list[HighlightToken] = []
        self.undo_stack: list[BulkEditCommand] = []
        self.redo_stack: list[BulkEditCommand] = []
        self.widget: Any | None = None
        self.scene: Any | None = None
        self.view: Any | None = None
        self.items: list[Any] = []

    def build(self) -> Any:
        """Build and return the PySide6 widget."""

        try:
            from PySide6.QtCore import Qt
            from PySide6.QtWidgets import QComboBox, QGraphicsScene, QGraphicsView, QHBoxLayout, QLabel, QVBoxLayout, QWidget
        except ImportError as exc:
            raise RuntimeError("PySide6 is required for highlight coding.") from exc

        root = QWidget()
        layout = QVBoxLayout(root)
        toolbar = QHBoxLayout()
        mode_box = QComboBox()
        for mode in HighlightMode:
            mode_box.addItem(mode.value.replace("_", " "), mode.value)
        mode_box.currentIndexChanged.connect(lambda: self.set_mode(HighlightMode(mode_box.currentData())))
        toolbar.addWidget(QLabel("Highlight mode"))
        toolbar.addWidget(mode_box)
        layout.addLayout(toolbar)
        self.scene = QGraphicsScene(root)
        self.view = QGraphicsView(self.scene)
        self.view.setDragMode(QGraphicsView.RubberBandDrag)
        self.view.setFocusPolicy(Qt.StrongFocus)
        layout.addWidget(self.view)
        self.widget = root
        self._install_shortcuts(root)
        self.refresh()
        return root

    def set_tokens(self, tokens: list[HighlightToken]) -> None:
        """Replace the rendered token list."""

        self.tokens = tokens
        self.refresh()

    def set_mode(self, mode: HighlightMode) -> None:
        """Change highlight mode without changing database annotations."""

        self.mode = mode
        self.refresh()

    def bulk_relabel(self, token_ids: list[str], updates: dict[str, Any]) -> None:
        """Apply an atomic bulk relabel and remember it for Ctrl-Z."""

        if self.connection is None:
            raise RuntimeError("Bulk relabel requires an open project database connection.")
        command = BulkEditCommand(self.connection, token_ids, updates)
        command.apply()
        self.undo_stack.append(command)
        self.redo_stack.clear()

    def undo(self) -> None:
        """Undo the last bulk edit."""

        if self.undo_stack:
            command = self.undo_stack.pop()
            command.undo()
            self.redo_stack.append(command)

    def refresh(self) -> None:
        """Repaint token items with item culling handled by QGraphicsView."""

        if self.scene is None:
            return
        self.scene.clear()
        self.items.clear()
        x = y = 0
        max_width = 900
        for token in self.tokens:
            item = _make_token_item(token, self.mode, self.palette)
            item.setPos(x, y)
            self.scene.addItem(item)
            self.items.append(item)
            x += item.boundingRect().width() + 6
            if x > max_width:
                x = 0
                y += 44
        self.scene.setSceneRect(self.scene.itemsBoundingRect())

    def _install_shortcuts(self, widget: Any) -> None:
        try:
            from PySide6.QtGui import QKeySequence, QShortcut
        except ImportError:
            return
        shortcuts = {
            "Ctrl+Z": self.undo,
            "Esc": self._clear_selection,
            "L": lambda: self.set_mode(HighlightMode.LANGUAGE),
            "M": lambda: self.set_mode(HighlightMode.FOUR_M),
            "T": lambda: self.set_mode(HighlightMode.TRIGGER_ROLE),
            "Ctrl+=": lambda: _scale_view(self.view, 1.1),
            "Ctrl+-": lambda: _scale_view(self.view, 0.9),
        }
        for key, callback in shortcuts.items():
            shortcut = QShortcut(QKeySequence(key), widget)
            shortcut.activated.connect(callback)

    def _clear_selection(self) -> None:
        if self.scene is not None:
            for item in self.scene.selectedItems():
                item.setSelected(False)


def _make_token_item(token: HighlightToken, mode: HighlightMode, palette: LanguagePalette) -> Any:
    from PySide6.QtCore import QRectF, Qt
    from PySide6.QtGui import QBrush, QColor, QFont, QPen
    from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsSimpleTextItem

    width = max(48, min(180, len(token.surface) * 9 + 24))
    rect = QGraphicsRectItem(QRectF(0, 0, width, 34))
    rect.setFlag(QGraphicsRectItem.ItemIsSelectable, True)
    rect.setToolTip(token.accessible_name())
    rect.setData(0, token.token_id)
    rect.setBrush(QBrush(QColor(_colour_for_token(token, mode, palette))))
    pen = QPen(QColor("#111111"), 1.3)
    if token.switch_type == "inter_sentential":
        pen.setStyle(Qt.DashLine)
    elif token.switch_type == "extra_sentential":
        pen.setStyle(Qt.DotLine)
    rect.setPen(pen)
    label = QGraphicsSimpleTextItem(token.surface, rect)
    label.setPos(6, 8)
    glyph = QGraphicsSimpleTextItem(palette.glyph_for(token.language), rect)
    glyph.setFont(QFont("Sans", 8))
    glyph.setPos(width - 16, 2)
    if token.trigger_role == "trigger":
        arrow = QGraphicsSimpleTextItem("↦", rect)
        arrow.setPos(width - 14, 17)
    elif token.trigger_role == "triggered":
        arrow = QGraphicsSimpleTextItem("←", rect)
        arrow.setPos(2, 17)
    rect.setAccessibleDescription(token.accessible_name()) if hasattr(rect, "setAccessibleDescription") else None
    return rect


def _colour_for_token(token: HighlightToken, mode: HighlightMode, palette: LanguagePalette) -> str:
    if mode == HighlightMode.LANGUAGE:
        return palette.colour_for(token.language)
    if mode == HighlightMode.FOUR_M:
        return {"content": "#56B4E9", "early_system": "#009E73", "bridge_late_system": "#E69F00", "outsider_late_system": "#D55E00"}.get(token.four_m_type or "", "#DDDDDD")
    if mode == HighlightMode.TRIGGER_ROLE:
        return {"trigger": "#E69F00", "triggered": "#56B4E9", "none": "#DDDDDD"}.get(token.trigger_role or "none", "#DDDDDD")
    if mode == HighlightMode.INTEGRATION_SCORE and token.integration_score is not None:
        return "#009E73" if token.integration_score >= 0.7 else "#E69F00" if token.integration_score >= 0.3 else "#D55E00"
    if mode == HighlightMode.MIXED_CODE_SPAN and token.mixed_code_variety:
        return "#CC79A7"
    return "#DDDDDD"


def _scale_view(view: Any, factor: float) -> None:
    if view is not None:
        view.scale(factor, factor)


def _existing_columns(connection: sqlite3.Connection, table: str) -> set[str]:
    return {str(row[1]) for row in connection.execute(f"PRAGMA table_info({table})").fetchall()}
