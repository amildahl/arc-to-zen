#!/usr/bin/env python3
"""Render the desktop app window used in README.md."""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from PySide6.QtWidgets import QApplication

from desktop_app import APP_STYLESHEET, MainWindow


def main() -> int:
    output = REPO_ROOT / "docs" / "app-screenshot.png"
    output.parent.mkdir(parents=True, exist_ok=True)

    app = QApplication.instance() or QApplication([])
    app.setStyleSheet(APP_STYLESHEET)

    window = MainWindow()
    window.arc_combo.clear()
    window.arc_combo.addItem("~/Library/Application Support/Arc")
    window.zen_combo.clear()
    window.zen_combo.addItem("~/Library/Application Support/zen/Profiles/default-release")
    window.log.setPlainText("Ready.")
    window.resize(900, 720)
    window.show()
    app.processEvents()

    pixmap = window.grab()
    if not pixmap.save(str(output), "PNG"):
        raise RuntimeError(f"Failed to write {output}")

    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
