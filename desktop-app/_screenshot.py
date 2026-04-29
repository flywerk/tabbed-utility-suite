"""Render the main window and save a PNG for review."""

from __future__ import annotations

import sys
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QPixmap

sys.path.insert(0, ".")
from main import MainWindow, QApplication, QSS, QFont  # type: ignore  # noqa: E402


def shoot(out_path: str, tab_index: int = 0, size=(1080, 720)) -> None:
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyleSheet(QSS)
    app.setFont(QFont("DejaVu Sans", 10))

    win = MainWindow()
    win.resize(*size)
    # switch tab
    central = win.centralWidget()
    tabs = central.findChild(type(central.layout().itemAt(0).widget()))
    # simpler: find QTabWidget directly
    from PyQt6.QtWidgets import QTabWidget
    qt_tabs = win.findChild(QTabWidget)
    qt_tabs.setCurrentIndex(tab_index)

    win.show()
    app.processEvents()

    pix: QPixmap = win.grab()
    pix.save(out_path, "PNG")
    win.close()
    print(f"saved {out_path}")


if __name__ == "__main__":
    shoot("../mockups/tab1_autoclick.png", 0)
    shoot("../mockups/tab2_channels.png", 1)
    shoot("../mockups/tab3_progress.png", 2)
