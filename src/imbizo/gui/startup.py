"""Startup-time licence notification helpers.

The warning is informational and offline. It exists so Tier-2 and Tier-3
resource obligations remain visible without interrupting scholarly work.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from imbizo.app.strings import StringCatalog


ACK_PATH = Path("dictionaries/imported/_provenance/licence_acknowledgement.json")
USER_ACK_PATH = Path("dictionaries/imported/_provenance/user_acknowledgements.json")


@dataclass(frozen=True)
class LicenceWarning:
    """Runtime warning data for active Tier-2 or Tier-3 resources."""

    should_show: bool
    message: str
    tiers: tuple[int, ...]
    source_ids: tuple[str, ...]


def licence_warning_for_project(project_path: Path, catalog: StringCatalog) -> LicenceWarning:
    """Return a non-blocking warning when Tier-2 or Tier-3 resources are active."""

    acknowledgement = _read_json(project_path / ACK_PATH)
    installed_tiers = tuple(int(tier) for tier in acknowledgement.get("installed_tiers", []) if tier in (2, 3))
    source_ids = tuple(str(item) for item in acknowledgement.get("installed_source_ids", []))
    user_ack = _read_json(project_path / USER_ACK_PATH)
    permanently_dismissed = bool(user_ack.get("dismissed_permanently"))
    if not installed_tiers or permanently_dismissed:
        return LicenceWarning(False, "", installed_tiers, source_ids)
    tier_label = ", ".join(f"Tier-{tier}" for tier in installed_tiers)
    message = catalog.text(
        "licence.warning.message",
        tiers=tier_label,
        resources=", ".join(source_ids) or catalog.text("licence.warning.unknown_resources"),
    )
    return LicenceWarning(True, message, installed_tiers, source_ids)


def record_permanent_dismissal(project_path: Path, source_ids: tuple[str, ...]) -> Path:
    """Record that the user dismissed the licence notice for this project."""

    path = project_path / USER_ACK_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "dismissed_permanently": True,
        "source_ids": list(source_ids),
        "timestamp": datetime.now(UTC).isoformat(),
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def build_licence_warning_panel(project_path: Path, catalog: StringCatalog) -> Any | None:
    """Build a PySide6 notification panel when Qt is available.

    Returning None is acceptable in tests or headless runs. The panel contains
    only local text and never blocks access to the project.
    """

    warning = licence_warning_for_project(project_path, catalog)
    if not warning.should_show:
        return None
    try:
        from PySide6.QtWidgets import QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QWidget
    except ImportError:
        return None

    widget = QWidget()
    widget.setAccessibleName(catalog.text("licence.warning.accessible_name"))
    layout = QVBoxLayout(widget)
    label = QLabel(warning.message)
    label.setWordWrap(True)
    layout.addWidget(label)
    button_row = QHBoxLayout()
    read_more = QPushButton(catalog.text("licence.warning.read_more"))
    read_more.setAccessibleName(catalog.text("licence.warning.read_more.accessible"))
    dismiss_session = QPushButton(catalog.text("licence.warning.dismiss_session"))
    dismiss_permanent = QPushButton(catalog.text("licence.warning.dismiss_permanent"))
    dismiss_session.clicked.connect(widget.hide)
    dismiss_permanent.clicked.connect(lambda: (record_permanent_dismissal(project_path, warning.source_ids), widget.hide()))
    button_row.addWidget(read_more)
    button_row.addWidget(dismiss_session)
    button_row.addWidget(dismiss_permanent)
    layout.addLayout(button_row)
    return widget


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    if isinstance(data, dict):
        return data
    return {}
