"""Render the autoclick tab in 'counting' state for design preview."""
from __future__ import annotations

import sys
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtWidgets import QApplication, QTabWidget

sys.path.insert(0, ".")
from main import MainWindow, QSS  # noqa: E402


def shoot() -> None:
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyleSheet(QSS)
    app.setFont(QFont("DejaVu Sans", 10))

    win = MainWindow()
    win.resize(1080, 720)
    qt_tabs = win.findChild(QTabWidget)
    qt_tabs.setCurrentIndex(0)

    # set countdown state on the start button
    autoclick = qt_tabs.widget(0)
    btn = autoclick.start_btn
    btn.setText("3")
    btn.setProperty("counting", True)
    btn.style().unpolish(btn)
    btn.style().polish(btn)

    win.show()
    app.processEvents()

    pix: QPixmap = win.grab()
    out = "../mockups/tab1_counting.png"
    pix.save(out, "PNG")
    print(f"saved {out}")
    win.close()


if __name__ == "__main__":
    shoot()
