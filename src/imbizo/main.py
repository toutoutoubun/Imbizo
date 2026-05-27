"""Application entry point."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


@dataclass(slots=True)
class AppLaunchOptions:
    """Command-line launch options."""

    project: Path | None = None


def parse_args(argv: Sequence[str]) -> AppLaunchOptions:
    """Parse command-line launch options without performing side effects."""

    parser = argparse.ArgumentParser(prog="imbizo")
    parser.add_argument("project", nargs="?", help="Optional local project folder to open.")
    args = parser.parse_args(list(argv))
    return AppLaunchOptions(project=Path(args.project) if args.project else None)


def main(argv: Sequence[str] | None = None) -> int:
    """Launch Imbizo-CS Workbench and return a process exit code."""

    options = parse_args(argv if argv is not None else sys.argv[1:])
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        print("PySide6 is not installed. Install the optional gui dependency to launch the desktop UI.")
        return 2

    from imbizo.gui.main_window import MainWindow

    app = QApplication(sys.argv[:1])
    main_window = MainWindow()
    window = main_window.build()
    if options.project:
        main_window.open_project(options.project)
    window.show()
    return int(app.exec())


if __name__ == "__main__":
    raise SystemExit(main())
