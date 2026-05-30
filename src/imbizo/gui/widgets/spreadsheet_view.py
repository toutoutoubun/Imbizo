"""Spreadsheet-style annotation view."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from imbizo.domain.annotations import AnnotationDraft
from imbizo.persistence.repositories import AnnotationRepository, TranscriptRepository
from imbizo.services.annotation_service import AnnotationRow, AnnotationService


TOKEN_ID_ROLE = 256


@dataclass(slots=True)
class SpreadsheetRow:
    """One visible row in the spreadsheet model."""

    document_name: str
    segment_order: int
    annotation_row: AnnotationRow


class SpreadsheetTableModel:
    """Qt table model for large transcript spreadsheets.

    QTableWidget eagerly creates one widget item per cell, which becomes slow
    and memory-hungry for the interview files Imbizo-CS is expected to handle.
    This model exposes all rows through QTableView while creating display data
    only for cells Qt asks to paint.
    """

    HEADERS = ["Document", "Segment", "Token #", "Token", "Language", "Source", "Confidence", "Switch", "Status", "Memo"]
    EDITABLE_COLUMNS = {4, 9}

    def __init__(self, owner: "SpreadsheetViewWidget") -> None:
        from PySide6.QtCore import QAbstractTableModel

        class _Model(QAbstractTableModel):
            def rowCount(model_self, parent: Any = None) -> int:  # noqa: ANN001 - Qt override.
                if parent is not None and parent.isValid():
                    return 0
                return len(owner.rows)

            def columnCount(model_self, parent: Any = None) -> int:  # noqa: ANN001 - Qt override.
                if parent is not None and parent.isValid():
                    return 0
                return len(SpreadsheetTableModel.HEADERS)

            def headerData(model_self, section: int, orientation: Any, role: int = 0) -> Any:
                from PySide6.QtCore import Qt

                if role != Qt.ItemDataRole.DisplayRole:
                    return None
                if orientation == Qt.Orientation.Horizontal:
                    return SpreadsheetTableModel.HEADERS[section]
                return str(section + 1)

            def data(model_self, index: Any, role: int = 0) -> Any:
                from PySide6.QtCore import Qt

                if not index.isValid():
                    return None
                row = owner.rows[index.row()]
                if role == TOKEN_ID_ROLE:
                    return row.annotation_row.token.id
                if role not in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
                    return None
                return owner._cell_text(row, index.column())

            def setData(model_self, index: Any, value: Any, role: int = 0) -> bool:
                from PySide6.QtCore import Qt

                if role != Qt.ItemDataRole.EditRole or not index.isValid() or index.column() not in SpreadsheetTableModel.EDITABLE_COLUMNS:
                    return False
                owner._persist_cell_edit(index.row(), index.column(), str(value))
                model_self.dataChanged.emit(model_self.index(index.row(), 0), model_self.index(index.row(), len(SpreadsheetTableModel.HEADERS) - 1), [])
                return True

            def flags(model_self, index: Any) -> Any:
                from PySide6.QtCore import Qt

                if not index.isValid():
                    return Qt.ItemFlag.NoItemFlags
                flags = Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
                if index.column() in SpreadsheetTableModel.EDITABLE_COLUMNS:
                    flags |= Qt.ItemFlag.ItemIsEditable
                return flags

        self.qt_model = _Model()
        self._owner = owner

    def reset(self) -> None:
        """Notify Qt that the underlying row list has been replaced."""

        self.qt_model.beginResetModel()
        self.qt_model.endResetModel()


class SpreadsheetViewWidget:
    """Excel-like annotation grid over imported project transcripts.

    The view is fully local and SQLite-backed. It deliberately shows every
    matching token row, not only the first page, because humanities review often
    requires scanning long interviews end to end. A model/view table keeps that
    feasible without constructing hundreds of thousands of cell objects.
    """

    def __init__(self, context: Any, annotation_service: AnnotationService | None = None) -> None:
        self.context = context
        self.annotation_service = annotation_service or AnnotationService()
        self.widget = None
        self.table = None
        self.document_filter = None
        self.search_box = None
        self.status_label = None
        self.languages_by_label: dict[str, str] = {}
        self.language_names_by_id: dict[str, str] = {}
        self.rows: list[SpreadsheetRow] = []
        self.model: SpreadsheetTableModel | None = None
        self._is_loading = False

    def build(self) -> Any:
        """Build and return a PySide6 widget."""

        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QAbstractItemView, QComboBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableView, QVBoxLayout, QWidget

        page = QWidget()
        layout = QVBoxLayout(page)
        toolbar = QHBoxLayout()

        self.document_filter = QComboBox()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Filter tokens or memos")
        refresh_button = QPushButton("Refresh")
        self.status_label = QLabel("No rows loaded")

        toolbar.addWidget(QLabel("Document"))
        toolbar.addWidget(self.document_filter, 2)
        toolbar.addWidget(QLabel("Search"))
        toolbar.addWidget(self.search_box, 2)
        toolbar.addWidget(refresh_button)
        toolbar.addWidget(self.status_label)
        layout.addLayout(toolbar)

        self.table = QTableView()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked
            | QAbstractItemView.EditTrigger.SelectedClicked
            | QAbstractItemView.EditTrigger.EditKeyPressed
        )
        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.table.setWordWrap(False)
        self.table.setAccessibleName("Spreadsheet annotation table")
        self.table.setToolTip("Edit Language or Memo cells directly. Other cells are read-only project evidence.")
        self.model = SpreadsheetTableModel(self)
        self.table.setModel(self.model.qt_model)
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        self.table.verticalHeader().setDefaultSectionSize(24)
        self.table.setSortingEnabled(False)
        self.table.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        layout.addWidget(self.table)

        refresh_button.clicked.connect(self.refresh)
        self.document_filter.currentIndexChanged.connect(self.refresh)
        self.search_box.textChanged.connect(self.refresh)
        self.widget = page
        self.refresh_documents()
        self.refresh()
        return page

    def refresh_documents(self) -> None:
        """Reload the document selector from the open project."""

        if self.document_filter is None:
            return
        documents = TranscriptRepository(self.context.connection).list_documents()
        current = self.document_filter.currentData()
        self.document_filter.blockSignals(True)
        self.document_filter.clear()
        self.document_filter.addItem("All imported documents", "")
        for document in documents:
            self.document_filter.addItem(document.name, document.id)
        if current:
            for index in range(self.document_filter.count()):
                if self.document_filter.itemData(index) == current:
                    self.document_filter.setCurrentIndex(index)
                    break
        self.document_filter.blockSignals(False)

    def refresh(self) -> None:
        """Reload spreadsheet rows from SQLite."""

        if self.table is None or self.model is None:
            return

        document_id = str(self.document_filter.currentData() or "") if self.document_filter is not None else ""
        search = self.search_box.text().strip().lower() if self.search_box is not None else ""
        documents = TranscriptRepository(self.context.connection).list_documents()
        selected_documents = [document for document in documents if not document_id or document.id == document_id]
        rows: list[SpreadsheetRow] = []
        languages_seen = {}
        language_names_by_id = {}
        for document in selected_documents:
            state = self.annotation_service.load_editor_state(self.context, document.id)
            for language in state.languages:
                languages_seen[language.name] = language.id
                languages_seen[language.code] = language.id
                language_names_by_id[language.id] = language.name
            for row in state.rows:
                haystack = f"{row.token.token_text} {row.annotation.memo if row.annotation else ''}".lower()
                if search and search not in haystack:
                    continue
                rows.append(SpreadsheetRow(document.name, row.segment.sort_order, row))

        self.languages_by_label = languages_seen
        self.language_names_by_id = language_names_by_id
        self._is_loading = True
        self.model.qt_model.beginResetModel()
        self.rows = rows
        self.model.qt_model.endResetModel()
        self._is_loading = False
        if self.status_label is not None:
            self.status_label.setText(f"{len(rows):,} token rows")

    def _persist_cell_edit(self, row_index: int, column: int, value: str) -> None:
        """Persist direct spreadsheet edits for language and memo cells."""

        if self._is_loading or column not in SpreadsheetTableModel.EDITABLE_COLUMNS:
            return
        row = self.rows[row_index]
        annotation = row.annotation_row.annotation
        language_label = value.strip() if column == 4 else self._cell_text(row, 4).strip()
        memo = value if column == 9 else self._cell_text(row, 9)
        saved = self.annotation_service.save_token_annotation(
            self.context,
            row.annotation_row.token.id,
            AnnotationDraft(language_id=self.languages_by_label.get(language_label, language_label or None), memo=memo),
        )
        row.annotation_row.annotation = AnnotationRepository(self.context.connection).get_effective_annotation_for_token(row.annotation_row.token.id) or saved

    def _cell_text(self, row: SpreadsheetRow, column: int) -> str:
        annotation = row.annotation_row.annotation
        confidence = ""
        if annotation is not None:
            confidence_value = annotation.researcher_confidence or annotation.auto_confidence
            confidence = str(confidence_value or "")
        values = [
            row.document_name,
            str(row.segment_order),
            str(row.annotation_row.token.sort_order),
            row.annotation_row.token.token_text,
            self._language_name(annotation.language_id if annotation else None),
            annotation.source.value if annotation else "",
            confidence,
            annotation.switch_type.value if annotation and annotation.switch_type else "",
            annotation.status.value if annotation else "",
            annotation.memo if annotation else "",
        ]
        return values[column]

    def _language_name(self, language_id: str | None) -> str:
        if not language_id:
            return ""
        return self.language_names_by_id.get(language_id, language_id)
