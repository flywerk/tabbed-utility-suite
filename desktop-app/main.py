"""
Tri-Tab Desktop App
Three independent utilities in one window:
  1. PagesAutoclick - configurable autoclicker
  2. OpenChannels  - sequential channel opener (Chrome)
  3. Progress      - 4 progress bars (credit / computer / apartment / total)

UI-only build for design approval. Logic is wired in a follow-up pass.
"""

from __future__ import annotations

import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon, QIntValidator
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

# ---------------------------------------------------------------------------
# Theme
# ---------------------------------------------------------------------------

BG_PRIMARY = "#111924"
BG_ELEVATED = "#1a2433"
BG_SUNKEN = "#0c121b"
SECONDARY = "#128277"
SECONDARY_HOVER = "#16a092"
SECONDARY_PRESSED = "#0e6b62"
EMERALD = "#10b981"
TEXT_PRIMARY = "#e6edf3"
TEXT_MUTED = "#7d8a9c"
BORDER = "#243245"
DANGER = "#b3344a"
DANGER_HOVER = "#cc3d56"

QSS = f"""
QMainWindow, QWidget {{
    background-color: {BG_PRIMARY};
    color: {TEXT_PRIMARY};
    font-family: 'Segoe UI', 'Inter', 'Helvetica Neue', Arial, sans-serif;
    font-size: 14px;
}}

/* Tabs */
QTabWidget::pane {{
    border: 1px solid {BORDER};
    border-radius: 12px;
    background-color: {BG_ELEVATED};
    top: -1px;
}}
QTabBar {{
    qproperty-drawBase: 0;
    background: transparent;
}}
QTabBar::tab {{
    background-color: {BG_SUNKEN};
    color: {TEXT_MUTED};
    padding: 10px 26px;
    margin-right: 4px;
    border: 1px solid {BORDER};
    border-bottom: none;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    font-weight: 500;
    min-width: 140px;
}}
QTabBar::tab:hover {{
    color: {TEXT_PRIMARY};
    background-color: #18222f;
}}
QTabBar::tab:selected {{
    color: {SECONDARY};
    background-color: {BG_ELEVATED};
    border-color: {BORDER};
    font-weight: 600;
}}

/* Labels */
QLabel#FieldLabel {{
    color: {TEXT_PRIMARY};
    font-size: 18px;
    font-weight: 500;
}}
QLabel#FieldHint {{
    color: {TEXT_MUTED};
    font-size: 12px;
}}
QLabel#SmallLabel {{
    color: {TEXT_MUTED};
    font-size: 12px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}
QLabel#TotalAmount {{
    color: {TEXT_PRIMARY};
    font-size: 22px;
    font-weight: 600;
}}

/* Inputs */
QLineEdit {{
    background-color: {BG_SUNKEN};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 10px;
    padding: 10px 14px;
    font-size: 16px;
    selection-background-color: {SECONDARY};
}}
QLineEdit:focus {{
    border-color: {SECONDARY};
}}
QLineEdit#NumericInput {{
    font-size: 18px;
    font-weight: 600;
    qproperty-alignment: AlignCenter;
    min-width: 140px;
}}
QLineEdit#TotalInput {{
    font-size: 18px;
    font-weight: 600;
    qproperty-alignment: AlignCenter;
    color: {TEXT_MUTED};
}}

/* Buttons */
QPushButton {{
    background-color: {SECONDARY};
    color: white;
    border: none;
    border-radius: 10px;
    padding: 11px 28px;
    font-size: 14px;
    font-weight: 600;
    letter-spacing: 0.4px;
    text-transform: uppercase;
}}
QPushButton:hover {{
    background-color: {SECONDARY_HOVER};
}}
QPushButton:pressed {{
    background-color: {SECONDARY_PRESSED};
}}
QPushButton:disabled {{
    background-color: #2a3647;
    color: #5a6878;
}}
QPushButton#GhostButton {{
    background-color: transparent;
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
}}
QPushButton#GhostButton:hover {{
    border-color: {SECONDARY};
    color: {SECONDARY};
}}
QPushButton#DangerButton {{
    background-color: transparent;
    color: {TEXT_MUTED};
    border: 1px solid {BORDER};
}}
QPushButton#DangerButton:hover {{
    color: white;
    border-color: {DANGER};
    background-color: {DANGER};
}}
QPushButton#StartButton {{
    min-width: 170px;
}}
QPushButton#StartButton[counting="true"] {{
    background-color: transparent;
    color: {EMERALD};
    border: 2px solid {EMERALD};
    font-size: 22px;
    font-weight: 700;
}}
QPushButton#AddButton {{
    background-color: {SECONDARY};
    min-width: 100px;
}}

/* Cards */
QFrame#Card {{
    background-color: {BG_ELEVATED};
    border: 1px solid {BORDER};
    border-radius: 14px;
}}
QFrame#ProgressRow {{
    background-color: transparent;
}}

/* Progress bars */
QProgressBar {{
    background-color: {BG_SUNKEN};
    border: 1px solid {BORDER};
    border-radius: 10px;
    height: 44px;
    text-align: center;
    color: {TEXT_PRIMARY};
    font-weight: 600;
    font-size: 14px;
}}
QProgressBar::chunk {{
    background-color: {EMERALD};
    border-radius: 9px;
}}
QProgressBar#TotalProgress {{
    height: 52px;
    font-size: 15px;
}}
QProgressBar#TotalProgress::chunk {{
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {SECONDARY}, stop:1 {EMERALD});
}}
"""


# ---------------------------------------------------------------------------
# Reusable widgets
# ---------------------------------------------------------------------------


def make_field_row(label_text: str, default_value: str, hint: str | None = None,
                   numeric: bool = True) -> tuple[QWidget, QLineEdit]:
    """A label on the left, hint underneath, input on the right."""
    row = QWidget()
    row.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    h = QHBoxLayout(row)
    h.setContentsMargins(0, 0, 0, 0)
    h.setSpacing(20)

    label_box = QVBoxLayout()
    label_box.setSpacing(2)

    label = QLabel(label_text)
    label.setObjectName("FieldLabel")
    label_box.addWidget(label)

    if hint:
        hint_label = QLabel(hint)
        hint_label.setObjectName("FieldHint")
        label_box.addWidget(hint_label)

    h.addLayout(label_box, 1)

    edit = QLineEdit(default_value)
    edit.setObjectName("NumericInput")
    edit.setFixedWidth(160)
    if numeric:
        edit.setValidator(QIntValidator(0, 10_000_000))
    h.addWidget(edit, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    return row, edit


# ---------------------------------------------------------------------------
# Tab 1 - PagesAutoclick
# ---------------------------------------------------------------------------


class AutoclickTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(36, 32, 36, 32)
        outer.setSpacing(0)

        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(40, 36, 40, 32)
        card_layout.setSpacing(28)

        intro = QLabel("Автокликер для активной страницы")
        intro.setObjectName("SmallLabel")
        card_layout.addWidget(intro)

        delay_row, self.delay_input = make_field_row("Задержка (сек)", "5")
        count_row, self.count_input = make_field_row("Количество", "700")
        gap_row, self.gap_input = make_field_row(
            "Задержка между кликами", "10", hint="дефолт 10ms"
        )

        card_layout.addWidget(delay_row)
        card_layout.addWidget(count_row)
        card_layout.addWidget(gap_row)

        card_layout.addStretch(1)

        button_row = QHBoxLayout()
        button_row.setSpacing(12)
        button_row.addStretch(1)

        self.start_btn = QPushButton("START")
        self.start_btn.setObjectName("StartButton")
        self.start_btn.setProperty("counting", False)
        self.cancel_btn = QPushButton("CANCEL")
        self.cancel_btn.setObjectName("DangerButton")

        button_row.addWidget(self.start_btn)
        button_row.addWidget(self.cancel_btn)

        card_layout.addLayout(button_row)
        outer.addWidget(card)


# ---------------------------------------------------------------------------
# Tab 2 - OpenChannels
# ---------------------------------------------------------------------------


class OpenChannelsTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(36, 32, 36, 32)
        outer.setSpacing(0)

        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(40, 36, 40, 32)
        card_layout.setSpacing(28)

        intro = QLabel("Поочерёдное открытие каналов max.ru на закреплённой вкладке Chrome")
        intro.setObjectName("SmallLabel")
        intro.setWordWrap(True)
        card_layout.addWidget(intro)

        delay_row, self.delay_input = make_field_row("Задержка (сек)", "7")
        count_row, self.count_input = make_field_row("Количество", "100")
        gap_row, self.gap_input = make_field_row(
            "Задержка между кликами", "50", hint="дефолт 50ms"
        )

        card_layout.addWidget(delay_row)
        card_layout.addWidget(count_row)
        card_layout.addWidget(gap_row)
        card_layout.addStretch(1)

        button_row = QHBoxLayout()
        button_row.setSpacing(12)
        button_row.addStretch(1)
        self.start_btn = QPushButton("START")
        self.start_btn.setObjectName("StartButton")
        self.start_btn.setProperty("counting", False)
        self.cancel_btn = QPushButton("CANCEL")
        self.cancel_btn.setObjectName("DangerButton")
        button_row.addWidget(self.start_btn)
        button_row.addWidget(self.cancel_btn)

        card_layout.addLayout(button_row)
        outer.addWidget(card)


# ---------------------------------------------------------------------------
# Tab 3 - Progress
# ---------------------------------------------------------------------------


class ProgressBarRow(QWidget):
    def __init__(self, title: str, target: int) -> None:
        super().__init__()
        self.title = title
        self.target = target
        self.value = 0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.bar = QProgressBar()
        self.bar.setRange(0, 1000)  # use 1000 for fine percentage
        self.bar.setValue(0)
        self.bar.setTextVisible(True)
        self.bar.setFormat(self._format_text())
        layout.addWidget(self.bar)

    def _format_text(self) -> str:
        pct = (self.value / self.target * 100) if self.target else 0
        if self.target >= 1_000_000:
            short = f"{self.target // 1_000_000} млн"
        else:
            short = f"{self.target // 1000}к"
        return f"{self.title} ({short}) — {pct:.2f}%"

    def set_value(self, v: int) -> None:
        self.value = max(0, min(self.target, v))
        ratio = self.value / self.target if self.target else 0
        self.bar.setValue(int(round(ratio * 1000)))
        self.bar.setFormat(self._format_text())


class ProgressTab(QWidget):
    TARGET_CREDIT = 500_000
    TARGET_COMPUTER = 300_000
    TARGET_APARTMENT = 1_000_000
    TARGET_TOTAL = TARGET_CREDIT + TARGET_COMPUTER + TARGET_APARTMENT

    def __init__(self) -> None:
        super().__init__()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(36, 32, 36, 32)
        outer.setSpacing(0)

        card = QFrame()
        card.setObjectName("Card")
        grid = QHBoxLayout(card)
        grid.setContentsMargins(36, 32, 36, 32)
        grid.setSpacing(36)

        # Left column: progress bars
        left = QVBoxLayout()
        left.setSpacing(18)

        self.credit_bar = ProgressBarRow("Кредит", self.TARGET_CREDIT)
        self.computer_bar = ProgressBarRow("Компьютер", self.TARGET_COMPUTER)
        self.apartment_bar = ProgressBarRow("Квартира", self.TARGET_APARTMENT)
        self.total_bar = ProgressBarRow("Общий", self.TARGET_TOTAL)
        self.total_bar.bar.setObjectName("TotalProgress")
        # Mock visible progress for the screenshot
        self.credit_bar.set_value(1900)
        self.computer_bar.set_value(0)
        self.apartment_bar.set_value(0)
        self.total_bar.set_value(1900)

        # Section label for which target the input is going to
        target_select = QLabel("Прогресс")
        target_select.setObjectName("SmallLabel")
        left.addWidget(target_select)

        left.addWidget(self._wrap_with_picker("Кредит", self.credit_bar))
        left.addWidget(self._wrap_with_picker("Компьютер", self.computer_bar))
        left.addWidget(self._wrap_with_picker("Квартира", self.apartment_bar))

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {BORDER}; background-color: {BORDER}; max-height: 1px;")
        left.addWidget(sep)

        total_label = QLabel("Общий прогресс")
        total_label.setObjectName("SmallLabel")
        left.addWidget(total_label)
        left.addWidget(self.total_bar)

        left.addStretch(1)

        # Right column: input area
        right = QVBoxLayout()
        right.setSpacing(20)

        right.addWidget(self._build_input_block("Добавить", "1400", numeric=True,
                                                button_text="Добавить",
                                                attr_name="add_input"))
        right.addWidget(self._build_input_block("Осталось", "174 200", numeric=False,
                                                button_text=None,
                                                attr_name="remaining_input",
                                                readonly=True))

        right.addStretch(1)

        right.addWidget(self._build_total_block())

        cancel_row = QHBoxLayout()
        cancel_row.addStretch(1)
        self.undo_btn = QPushButton("Отменить")
        self.undo_btn.setObjectName("GhostButton")
        cancel_row.addWidget(self.undo_btn)
        right.addLayout(cancel_row)

        grid.addLayout(left, 3)
        grid.addLayout(right, 2)

        outer.addWidget(card)

    # ------------------------------------------------------------------
    # builders
    # ------------------------------------------------------------------
    def _wrap_with_picker(self, name: str, bar_widget: ProgressBarRow) -> QWidget:
        wrap = QFrame()
        wrap.setObjectName("ProgressRow")
        layout = QHBoxLayout(wrap)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        radio = QPushButton("●")
        radio.setObjectName("GhostButton")
        radio.setFixedWidth(46)
        radio.setCheckable(True)
        if name == "Кредит":
            radio.setChecked(True)
            radio.setStyleSheet(f"color: {SECONDARY}; border-color: {SECONDARY};")
        layout.addWidget(radio)
        layout.addWidget(bar_widget, 1)
        return wrap

    def _build_input_block(self, label_text: str, value: str, numeric: bool,
                           button_text: str | None, attr_name: str,
                           readonly: bool = False) -> QWidget:
        block = QFrame()
        block.setObjectName("Card")
        v = QVBoxLayout(block)
        v.setContentsMargins(20, 16, 20, 18)
        v.setSpacing(8)

        small = QLabel(label_text)
        small.setObjectName("SmallLabel")
        v.addWidget(small)

        row = QHBoxLayout()
        row.setSpacing(10)

        edit = QLineEdit(value)
        edit.setObjectName("NumericInput")
        if numeric:
            edit.setValidator(QIntValidator(0, 10_000_000))
        if readonly:
            edit.setReadOnly(True)
            edit.setObjectName("TotalInput")
        row.addWidget(edit, 1)

        if button_text:
            btn = QPushButton(button_text)
            btn.setObjectName("AddButton")
            row.addWidget(btn)
            setattr(self, "add_button", btn)

        v.addLayout(row)
        setattr(self, attr_name, edit)
        return block

    def _build_total_block(self) -> QWidget:
        block = QFrame()
        block.setObjectName("Card")
        v = QVBoxLayout(block)
        v.setContentsMargins(20, 16, 20, 18)
        v.setSpacing(6)
        small = QLabel("Цель")
        small.setObjectName("SmallLabel")
        v.addWidget(small)
        amount = QLabel("1 800 000")
        amount.setObjectName("TotalAmount")
        amount.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.addWidget(amount)
        return block


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Tri-Tab Utility")
        self.setMinimumSize(960, 620)
        self.resize(1080, 720)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        tabs = QTabWidget()
        tabs.setDocumentMode(True)
        tabs.addTab(AutoclickTab(), "PagesAutoclick")
        tabs.addTab(OpenChannelsTab(), "OpenChannels")
        tabs.addTab(ProgressTab(), "Progress")
        layout.addWidget(tabs)


def main() -> int:
    app = QApplication(sys.argv)
    app.setStyleSheet(QSS)
    # nicer default font weight on linux render
    f = QFont("Segoe UI", 10)
    app.setFont(f)
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
