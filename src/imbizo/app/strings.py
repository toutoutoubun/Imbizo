"""Externalized UI string loading."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class StringCatalog:
    """Lookup table for localized UI strings."""

    values: dict[str, str]
    fallback: dict[str, str]

    def text(self, key: str, **values: object) -> str:
        """Return localized text for a key."""

        template = self.values.get(key, self.fallback.get(key, key))
        return template.format(**values)


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        return {}
    return {str(key): str(value) for key, value in data.items()}


def load_string_catalog(locale_code: str, resources_dir: Path) -> StringCatalog:
    """Load UI strings for a locale from bundled resource files."""

    fallback = _load_json(resources_dir / "i18n" / "en.json")
    selected = _load_json(resources_dir / "i18n" / f"{locale_code}.json")
    return StringCatalog(values=selected or fallback, fallback=fallback)
