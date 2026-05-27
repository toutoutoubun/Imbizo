"""MaskLID-style iterative masking API."""

from __future__ import annotations

from imbizo.lid.masklid import MaskLidDetector
from imbizo.lid.providers import LidSuggestionDraft

__all__ = ["LidSuggestionDraft", "MaskLidDetector"]
