"""CI offline guard for runtime modules.

The bootstrap tools may fetch resources, but `core/`, `gui/`, and `plugins/`
must remain offline-only.
"""

from __future__ import annotations

import ast
from pathlib import Path


FORBIDDEN = {"urllib.request", "requests", "httpx", "aiohttp", "socket"}
RUNTIME_ROOTS = [Path("src/imbizo/core"), Path("src/imbizo/gui"), Path("src/imbizo/plugins")]


def main() -> None:
    """Exit non-zero if a runtime module imports a network library."""

    root = Path(__file__).resolve().parents[1]
    offenders: list[str] = []
    for runtime_root in RUNTIME_ROOTS:
        for path in sorted((root / runtime_root).rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if _forbidden(alias.name):
                            offenders.append(f"{path.relative_to(root)}: import {alias.name}")
                elif isinstance(node, ast.ImportFrom) and node.module and _forbidden(node.module):
                    offenders.append(f"{path.relative_to(root)}: from {node.module} import ...")
    if offenders:
        raise SystemExit("Forbidden runtime network imports:\n" + "\n".join(offenders))


def _forbidden(module_name: str) -> bool:
    return any(module_name == forbidden or module_name.startswith(f"{forbidden}.") for forbidden in FORBIDDEN)


if __name__ == "__main__":
    main()
