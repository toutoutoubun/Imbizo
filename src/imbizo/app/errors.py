"""Plain-language application errors."""

from __future__ import annotations


class ImbizoError(Exception):
    """Base class for expected Imbizo-CS Workbench errors."""


class UserFacingError(ImbizoError):
    """An error safe to show directly to a researcher."""


class ProjectError(UserFacingError):
    """A project creation, open, close, or archive error."""


class ImportFailure(UserFacingError):
    """An import failed without modifying the original source file."""


class ExportFailure(UserFacingError):
    """An export failed before producing a valid output file."""


class StorageError(UserFacingError):
    """A local SQLite or project-folder storage error."""


def explain_exception(error: BaseException) -> str:
    """Return a concise plain-language explanation for an exception."""

    if isinstance(error, UserFacingError):
        return str(error)
    return "Something unexpected happened. Your source files were not modified."
