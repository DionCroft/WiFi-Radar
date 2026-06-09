"""Application bootstrap for the PySide6 desktop GUI."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from .gui import MainWindow


def main(argv: list[str] | None = None) -> int:
    """Start the desktop application."""

    app = QApplication(sys.argv if argv is None else argv)
    window = MainWindow()
    window.resize(1180, 780)
    window.show()
    return app.exec()

