"""Optional AfroLID adapter stub."""

from __future__ import annotations

from typing import Sequence

from imbizo.app.errors import UserFacingError
from imbizo.lid.providers import LanguageScore, LidOptions


class AfroLidProvider:
    """Optional AfroLID adapter; unavailable unless explicitly installed."""

    name = "afrolid_optional"
    version = "not-installed"

    def is_available(self) -> bool:
        """Return whether optional local resources are installed."""

        return False

    def predict(self, texts: Sequence[str], options: LidOptions) -> list[list[LanguageScore]]:
        """Rescore text only when local optional resources are available."""

        raise UserFacingError("AfroLID is optional and is not installed in this local project.")
