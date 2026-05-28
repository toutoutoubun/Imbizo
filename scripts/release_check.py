"""Run release-readiness checks for Imbizo-CS Workbench."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.11+ always has tomllib.
    import tomli as tomllib  # type: ignore[no-redef]


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = [
    "CHANGELOG.md",
    "CITATION.cff",
    "INSTALL_OFFLINE.md",
    "LICENSE",
    "MANIFEST.in",
    "PRINCIPLES.md",
    "README.md",
    "pyproject.toml",
]


@dataclass(slots=True)
class CheckResult:
    """A single release-readiness check result."""

    name: str
    ok: bool
    detail: str


def main(argv: list[str] | None = None) -> int:
    """Run release checks and exit non-zero on failure."""

    parser = argparse.ArgumentParser(description="Check whether the repository is ready for a local release build.")
    parser.add_argument("--run-tests", action="store_true", help="Also run the full pytest suite.")
    args = parser.parse_args(argv)

    results: list[CheckResult] = []
    results.extend(_check_required_files())
    results.extend(_check_metadata_consistency())
    results.extend(_check_software_license_text())
    results.extend(_check_entry_points())
    results.extend(_check_tracked_artifacts())
    results.extend(_run_release_subchecks())
    if args.run_tests:
        results.append(_run_command("pytest", [sys.executable, "-m", "pytest", "-q"]))

    for result in results:
        marker = "PASS" if result.ok else "FAIL"
        print(f"[{marker}] {result.name}: {result.detail}")

    failed = [result for result in results if not result.ok]
    if failed:
        raise SystemExit(f"Release check failed: {len(failed)} failing check(s).")
    print("Release check passed.")
    return 0


def _check_required_files() -> list[CheckResult]:
    """Verify release-critical files exist."""

    results: list[CheckResult] = []
    for relative in REQUIRED_FILES:
        path = ROOT / relative
        results.append(CheckResult(f"required file {relative}", path.exists(), "present" if path.exists() else "missing"))
    return results


def _check_metadata_consistency() -> list[CheckResult]:
    """Check version, repository, and licence metadata agree across files."""

    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = pyproject["project"]
    pyproject_version = str(project["version"])
    package_version = _read_package_version()
    citation = _read_simple_cff(ROOT / "CITATION.cff")
    results = [
        CheckResult(
            "pyproject/package version",
            pyproject_version == package_version,
            f"pyproject={pyproject_version}, package={package_version}",
        ),
        CheckResult(
            "citation version",
            citation.get("version") == pyproject_version,
            f"citation={citation.get('version')}, pyproject={pyproject_version}",
        ),
        CheckResult(
            "software licence",
            str(project.get("license", {}).get("text")) == "AGPL-3.0-or-later"
            and citation.get("license") == "AGPL-3.0-or-later",
            f"pyproject={project.get('license')}, citation={citation.get('license')}",
        ),
        CheckResult(
            "repository URL",
            citation.get("repository-code") == "https://github.com/toutoutoubun/Imbizo",
            f"repository-code={citation.get('repository-code')}",
        ),
    ]
    return results


def _check_software_license_text() -> list[CheckResult]:
    """Verify the root LICENSE file carries the declared AGPLv3 text."""

    text = (ROOT / "LICENSE").read_text(encoding="utf-8", errors="replace")
    has_agpl = "GNU AFFERO GENERAL PUBLIC LICENSE" in text and "Version 3" in text
    stale_gpl_notice = "GPL-3.0-or-later" in text or "GNU General Public License version 3" in text
    return [
        CheckResult(
            "root LICENSE is AGPLv3",
            has_agpl and not stale_gpl_notice,
            "AGPLv3 text present" if has_agpl and not stale_gpl_notice else "root LICENSE does not match AGPLv3 declaration",
        )
    ]


def _read_package_version() -> str:
    """Read `__version__` from src/imbizo/__init__.py without importing."""

    text = (ROOT / "src" / "imbizo" / "__init__.py").read_text(encoding="utf-8")
    match = re.search(r'__version__\s*=\s*"([^"]+)"', text)
    if not match:
        return ""
    return match.group(1)


def _read_simple_cff(path: Path) -> dict[str, str]:
    """Read the simple top-level scalar fields used by this release check."""

    fields: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if ":" not in line or line.startswith(" ") or line.startswith("-"):
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip().strip('"')
    return fields


def _check_entry_points() -> list[CheckResult]:
    """Verify declared entry-point modules import locally."""

    command = [
        sys.executable,
        "-c",
        "import imbizo; import imbizo.main; import imbizo.cli; print(imbizo.__version__)",
    ]
    return [_run_command("entry point imports", command)]


def _check_tracked_artifacts() -> list[CheckResult]:
    """Verify generated binary artifacts are not tracked by git."""

    try:
        result = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        return [CheckResult("tracked artifact scan", False, str(exc))]
    tracked = [Path(item.decode()) for item in result.stdout.split(b"\0") if item]
    offenders = [
        str(path)
        for path in tracked
        if path.suffix in {".pyc", ".pyo"}
        or "__pycache__" in path.parts
        or path.parts[:1] in {( "dist", ), ( "build", )}
    ]
    return [
        CheckResult(
            "tracked generated artifacts",
            not offenders,
            "none" if not offenders else ", ".join(offenders[:8]),
        )
    ]


def _run_release_subchecks() -> list[CheckResult]:
    """Run local compliance and offline checks used by CI."""

    checks = [
        ("offline guard", [sys.executable, "tools/check_offline_guard.py"]),
        ("licence compliance", [sys.executable, "tools/check_compliance.py"]),
        ("no-network note", [sys.executable, "scripts/verify_no_network.py"]),
        ("offline import verification", [sys.executable, "scripts/verify_offline_install.py"]),
    ]
    return [_run_command(name, command) for name, command in checks]


def _run_command(name: str, command: list[str]) -> CheckResult:
    """Run a command with local PYTHONPATH and convert the result to a CheckResult."""

    env = dict(**os_environ_with_pythonpath())
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, env=env)
    output = (result.stdout + result.stderr).strip()
    detail = output.splitlines()[-1] if output else "ok"
    return CheckResult(name, result.returncode == 0, detail)


def os_environ_with_pythonpath() -> dict[str, str]:
    """Return an environment that imports the local src tree first."""

    import os

    env = dict(os.environ)
    current = env.get("PYTHONPATH")
    env["PYTHONPATH"] = f"{ROOT / 'src'}:{ROOT}" + (f":{current}" if current else "")
    return env


if __name__ == "__main__":
    raise SystemExit(main())
