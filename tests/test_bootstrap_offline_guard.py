"""Ensure only approved bootstrap tools import network libraries."""

from __future__ import annotations

import ast
from pathlib import Path

FORBIDDEN = {"urllib.request", "requests", "httpx", "aiohttp", "socket"}
ALLOWED_NETWORK_IMPORT_FILES = {Path("tools/bootstrap.py")}


def test_only_bootstrap_tools_import_network_libraries() -> None:
    """Fail loudly if any non-approved file imports forbidden network modules."""

    root = Path(__file__).resolve().parents[1]
    offenders: list[str] = []
    for path in sorted(root.rglob("*.py")):
        relative = path.relative_to(root)
        if _should_skip(relative):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if _is_forbidden(alias.name) and relative not in ALLOWED_NETWORK_IMPORT_FILES:
                        offenders.append(f"{relative}: import {alias.name}")
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                if _is_forbidden(node.module) and relative not in ALLOWED_NETWORK_IMPORT_FILES:
                    offenders.append(f"{relative}: from {node.module} import ...")
    assert not offenders, "Forbidden runtime network imports:\n" + "\n".join(offenders)


def _is_forbidden(module_name: str) -> bool:
    return any(module_name == forbidden or module_name.startswith(f"{forbidden}.") for forbidden in FORBIDDEN)


def _should_skip(relative: Path) -> bool:
    parts = set(relative.parts)
    return (
        "__pycache__" in parts
        or ".venv" in parts
        or relative.parts[0] in {".git", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
        or relative == Path("tests/test_bootstrap_offline_guard.py")
        or (len(relative.parts) >= 2 and relative.parts[0] == "tools" and relative.parts[1] == "adapters")
    )
