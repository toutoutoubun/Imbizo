"""Plain-language error dialog."""

from __future__ import annotations

from typing import Any

from imbizo.app.errors import explain_exception


def show_error(parent: Any, error: BaseException) -> None:
    """Show a plain-language error dialog."""

    from PySide6.QtWidgets import QMessageBox

    QMessageBox.critical(parent, "Something needs attention", explain_exception(error))
