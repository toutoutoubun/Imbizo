"""Local application preferences."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass(slots=True)
class AppSettings:
    """Local user preferences such as theme, font size, and recent projects."""

    locale: str = "en"
    theme: str = "default"
    font_size: int = 11
    recent_projects: list[str] = field(default_factory=list)


def _default_settings_path() -> Path:
    return Path.home() / ".imbizo-cs-workbench" / "settings.json"


def load_app_settings(settings_path: Path | None = None) -> AppSettings:
    """Load local app settings from disk."""

    path = settings_path or _default_settings_path()
    if not path.exists():
        return AppSettings()
    data = json.loads(path.read_text(encoding="utf-8"))
    return AppSettings(
        locale=str(data.get("locale", "en")),
        theme=str(data.get("theme", "default")),
        font_size=int(data.get("font_size", 11)),
        recent_projects=[str(item) for item in data.get("recent_projects", [])],
    )


def save_app_settings(settings: AppSettings, settings_path: Path | None = None) -> None:
    """Save local app settings without writing research data outside a project."""

    path = settings_path or _default_settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(settings), ensure_ascii=False, indent=2), encoding="utf-8")
