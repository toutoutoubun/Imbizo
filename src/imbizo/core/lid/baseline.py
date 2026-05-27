"""fastText-compatible local baseline LID API."""

from __future__ import annotations

from imbizo.lid.baseline import BaselineLidProvider
from imbizo.lid.providers import LanguageScore, LidOptions

__all__ = ["BaselineLidProvider", "LanguageScore", "LidOptions"]
