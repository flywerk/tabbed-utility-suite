"""
Flywerk Automation
Three independent utilities in one window:
  1. PagesAutoclick - configurable autoclicker (clicks at cursor position)
  2. OpenChannels   - same engine, defaults tuned for opening channels in Chrome
  3. Progress       - 4 progress bars (credit / computer / apartment / total)

Each tab keeps its own state and worker thread; tabs do not share runtime data.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from PyQt6.QtCore import QPoint, QRect, Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QIntValidator, QMouseEvent
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
    font-family: 'Helvetica', 'Helvetica Neue', 'Arial', 'Liberation Sans', 'DejaVu Sans', sans-serif;
    font-size: 13px;
}}

/* Tabs */
QTabWidget::pane {{
    border: 1px solid {BORDER};
    border-radius: 14px;
    background-color: {BG_ELEVATED};
    top: -1px;
}}
QTabBar {{
    qproperty-drawBase: 0;
    background: transparent;
    margin-left: 4px;
}}
QTabBar::tab {{
    background-color: {BG_SUNKEN};
    color: {TEXT_MUTED};
    padding: 12px 30px;
    margin-right: 6px;
    border: 1px solid {BORDER};
    border-bottom: none;
    border-top-left-radius: 12px;
    border-top-right-radius: 12px;
    font-weight: 500;
    font-size: 13px;
    letter-spacing: 0.3px;
    min-width: 150px;
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
    font-size: 15px;
    font-weight: 500;
    letter-spacing: 0.1px;
}}
QLabel#FieldHint {{
    color: {TEXT_MUTED};
    font-size: 11px;
    font-weight: 400;
    margin-top: 2px;
}}
QLabel#SmallLabel {{
    color: {TEXT_MUTED};
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1.4px;
    padding: 4px 0 8px 14px;
}}
QLabel#TotalAmount {{
    color: {TEXT_PRIMARY};
    font-size: 22px;
    font-weight: 600;
    letter-spacing: 0.5px;
}}

/* Inputs */
QLineEdit {{
    background-color: {BG_SUNKEN};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 16px;
    padding: 12px 16px;
    font-size: 14px;
    selection-background-color: {SECONDARY};
}}
QLineEdit:focus {{
    border-color: {SECONDARY};
}}
QLineEdit#NumericInput {{
    font-size: 16px;
    font-weight: 600;
    qproperty-alignment: AlignCenter;
    min-width: 130px;
    padding: 13px 16px;
    border-radius: 18px;
}}
QLineEdit#TotalInput {{
    font-size: 16px;
    font-weight: 600;
    qproperty-alignment: AlignCenter;
    color: {TEXT_PRIMARY};
    background-color: #0a1018;
    border-radius: 18px;
}}

/* Buttons */
QPushButton {{
    background-color: {SECONDARY};
    color: white;
    border: none;
    border-radius: 10px;
    padding: 11px 26px;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 1.2px;
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
    font-weight: 500;
    letter-spacing: 0.5px;
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
    min-width: 180px;
    padding: 13px 28px;
    font-size: 13px;
}}
QPushButton#StartButton[counting="true"] {{
    background-color: transparent;
    color: {EMERALD};
    border: 2px solid {EMERALD};
    font-size: 24px;
    font-weight: 700;
    letter-spacing: 0;
    padding: 9px 28px;
}}
QPushButton#AddButton {{
    background-color: {SECONDARY};
    min-width: 110px;
    padding: 11px 18px;
}}

/* Cards */
QFrame#FieldRow {{
    background-color: #1f2a3a;
    border: none;
    border-radius: 18px;
}}
QFrame#FieldRow > QLabel {{
    background: transparent;
    border: none;
}}

QFrame#Card {{
    background-color: {BG_ELEVATED};
    border: 1px solid {BORDER};
    border-radius: 16px;
}}
QFrame#ProgressRow {{
    background-color: transparent;
}}

/* Progress bars */
QProgressBar {{
    background-color: {BG_SUNKEN};
    border: 1px solid {BORDER};
    border-radius: 10px;
    min-height: 42px;
    max-height: 42px;
    text-align: center;
    color: {TEXT_PRIMARY};
    font-weight: 600;
    font-size: 13px;
}}
QProgressBar::chunk {{
    background-color: {EMERALD};
    border-radius: 9px;
    margin: 1px;
}}
QProgressBar#TotalProgress {{
    min-height: 52px;
    max-height: 52px;
    font-size: 14px;
}}
QProgressBar#TotalProgress::chunk {{
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {SECONDARY}, stop:1 {EMERALD});
}}

/* Window control buttons */
QPushButton#WindowMin, QPushButton#WindowClose {{
    background-color: transparent;
    color: {TEXT_MUTED};
    border: none;
    border-radius: 8px;
    min-width: 38px;
    max-width: 38px;
    min-height: 30px;
    max-height: 30px;
    padding: 0;
    font-size: 18px;
    font-weight: 400;
    letter-spacing: 0;
}}
QPushButton#WindowMin:hover {{
    background-color: #1a2433;
    color: {TEXT_PRIMARY};
}}
QPushButton#WindowClose:hover {{
    background-color: {DANGER};
    color: white;
}}

/* Title bar widget */
QWidget#TitleBar {{
    background-color: {BG_PRIMARY};
}}
QLabel#WindowTitle {{
    color: {TEXT_MUTED};
    font-size: 12px;
    font-weight: 500;
    letter-spacing: 0.6px;
}}

/* Radio button (the round selector on the left of each progress bar) */
QPushButton#PickerDot {{
    background-color: transparent;
    color: {TEXT_MUTED};
    border: 1px solid {BORDER};
    border-radius: 14px;
    min-width: 28px;
    max-width: 28px;
    min-height: 28px;
    max-height: 28px;
    padding: 0;
    font-size: 18px;
    font-weight: 700;
}}
QPushButton#PickerDot:hover {{
    border-color: {SECONDARY};
    color: {SECONDARY};
}}
QPushButton#PickerDot:checked {{
    border-color: {SECONDARY};
    color: {SECONDARY};
    background-color: rgba(18, 130, 119, 0.12);
}}
"""


# ---------------------------------------------------------------------------
# Reusable widgets
# ---------------------------------------------------------------------------


def _fmt_thousands(n: int) -> str:
    """Format an integer with non-breaking spaces every three digits (e.g. 1 800 000)."""
    return f"{n:,}".replace(",", " ")


def make_field_row(label_text: str, default_value: str, hint: str | None = None,
                   numeric: bool = True) -> tuple[QWidget, QLineEdit]:
    """A label on the left, input on the right, on a rounded background row."""
    row = QFrame()
    row.setObjectName("FieldRow")
    row.setFrameShape(QFrame.Shape.NoFrame)
    row.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    h = QHBoxLayout(row)
    h.setContentsMargins(28, 14, 16, 14)
    h.setSpacing(20)

    label = QLabel(label_text)
    label.setObjectName("FieldLabel")
    h.addWidget(label, 1, Qt.AlignmentFlag.AlignVCenter)

    edit = QLineEdit(default_value)
    edit.setObjectName("NumericInput")
    edit.setFixedWidth(170)
    if numeric:
        edit.setValidator(QIntValidator(0, 10_000_000))
    h.addWidget(edit, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    return row, edit


# ---------------------------------------------------------------------------
# Background worker — countdown + click loop
# ---------------------------------------------------------------------------


class ClickerWorker(QThread):
    countdown = pyqtSignal(int)         # seconds left in pre-start delay
    progress = pyqtSignal(int, int)     # (done, total) clicks
    finished_ok = pyqtSignal()
    failed = pyqtSignal(str)

    def __init__(self, delay_sec: int, count: int, gap_ms: int) -> None:
        super().__init__()
        self.delay_sec = max(0, delay_sec)
        self.count = max(0, count)
        self.gap_ms = max(0, gap_ms)
        self._stop = False

    def stop(self) -> None:
        self._stop = True

    def _interruptible_sleep(self, total_ms: int) -> bool:
        """Sleep in 50 ms slices so cancel feels instant. Returns False if cancelled."""
        elapsed = 0
        slice_ms = 50
        while elapsed < total_ms:
            if self._stop:
                return False
            chunk = min(slice_ms, total_ms - elapsed)
            time.sleep(chunk / 1000.0)
            elapsed += chunk
        return not self._stop

    def run(self) -> None:
        try:
            import pyautogui
            pyautogui.FAILSAFE = True  # mouse to top-left corner aborts
            pyautogui.PAUSE = 0
        except Exception as exc:  # pragma: no cover - import guard
            self.failed.emit(f"pyautogui import failed: {exc}")
            return

        # Pre-start countdown
        for s in range(self.delay_sec, 0, -1):
            if self._stop:
                return
            self.countdown.emit(s)
            if not self._interruptible_sleep(1000):
                return

        # Click loop
        for i in range(self.count):
            if self._stop:
                return
            try:
                pyautogui.click()
            except Exception as exc:
                self.failed.emit(str(exc))
                return
            self.progress.emit(i + 1, self.count)
            if i < self.count - 1 and self.gap_ms > 0:
                if not self._interruptible_sleep(self.gap_ms):
                    return

        self.finished_ok.emit()


# ---------------------------------------------------------------------------
# Shared clicker tab (Tab 1 - PagesAutoclick, Tab 2 - OpenChannels)
# ---------------------------------------------------------------------------


class ClickerTab(QWidget):
    """Two-button tab: configure delay/count/gap, then START / CANCEL."""

    def __init__(self, default_delay: int, default_count: int, default_gap: int) -> None:
        super().__init__()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(36, 32, 36, 32)
        outer.setSpacing(0)

        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(48, 44, 48, 36)
        card_layout.setSpacing(22)

        delay_row, self.delay_input = make_field_row("Задержка (сек)", str(default_delay))
        count_row, self.count_input = make_field_row("Количество", str(default_count))
        gap_row, self.gap_input = make_field_row("Задержка между кликами", str(default_gap))

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
        self.start_btn.clicked.connect(self._on_start)

        self.cancel_btn = QPushButton("CANCEL")
        self.cancel_btn.setObjectName("DangerButton")
        self.cancel_btn.clicked.connect(self._on_cancel)
        self.cancel_btn.setEnabled(False)

        button_row.addWidget(self.start_btn)
        button_row.addWidget(self.cancel_btn)

        card_layout.addLayout(button_row)
        outer.addWidget(card)

        self.worker: ClickerWorker | None = None

    # ------------------------------------------------------------------ start/stop
    def _on_start(self) -> None:
        if self.worker is not None:
            return
        try:
            delay = int(self.delay_input.text() or "0")
            count = int(self.count_input.text() or "0")
            gap = int(self.gap_input.text() or "0")
        except ValueError:
            return
        if count <= 0:
            return

        self._set_counting_style(True)
        self.cancel_btn.setEnabled(True)
        self.start_btn.setEnabled(False)

        self.worker = ClickerWorker(delay, count, gap)
        self.worker.countdown.connect(self._on_countdown)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished_ok.connect(self._on_finished)
        self.worker.failed.connect(self._on_failed)
        self.worker.finished.connect(self._on_thread_done)
        self.worker.start()

    def _on_cancel(self) -> None:
        if self.worker is not None:
            self.worker.stop()

    # ------------------------------------------------------------------ signals
    def _on_countdown(self, seconds_left: int) -> None:
        self.start_btn.setText(str(seconds_left))

    def _on_progress(self, done: int, total: int) -> None:
        self.start_btn.setText(f"{done} / {total}")

    def _on_finished(self) -> None:
        self.start_btn.setText("DONE")

    def _on_failed(self, message: str) -> None:
        self.start_btn.setText("ERROR")
        # remember the message for diagnostics
        self.start_btn.setToolTip(message)

    def _on_thread_done(self) -> None:
        # thread cleanup (also fires on stop / failure)
        self.worker = None
        self.cancel_btn.setEnabled(False)
        self.start_btn.setEnabled(True)
        # restore look after a brief delay so the user sees the final state
        QTimer.singleShot(1200, self._restore_idle)

    def _restore_idle(self) -> None:
        if self.worker is not None:
            return
        self._set_counting_style(False)
        self.start_btn.setText("START")
        self.start_btn.setToolTip("")

    def _set_counting_style(self, on: bool) -> None:
        self.start_btn.setProperty("counting", on)
        self.start_btn.style().unpolish(self.start_btn)
        self.start_btn.style().polish(self.start_btn)


class AutoclickTab(ClickerTab):
    def __init__(self) -> None:
        super().__init__(default_delay=5, default_count=700, default_gap=10)


class OpenChannelsTab(ClickerTab):
    def __init__(self) -> None:
        super().__init__(default_delay=7, default_count=100, default_gap=50)


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
        grid.setContentsMargins(44, 36, 44, 36)
        grid.setSpacing(40)

        # Left column: progress bars
        left = QVBoxLayout()
        left.setSpacing(14)

        self.credit_bar = ProgressBarRow("Кредит", self.TARGET_CREDIT)
        self.computer_bar = ProgressBarRow("Компьютер", self.TARGET_COMPUTER)
        self.apartment_bar = ProgressBarRow("Квартира", self.TARGET_APARTMENT)
        self.total_bar = ProgressBarRow("Общий", self.TARGET_TOTAL)
        self.total_bar.bar.setObjectName("TotalProgress")
        # All bars start at 0
        self.credit_bar.set_value(0)
        self.computer_bar.set_value(0)
        self.apartment_bar.set_value(0)
        self.total_bar.set_value(0)

        # Map keys to bars and radio buttons
        self.bars = {
            "credit": self.credit_bar,
            "computer": self.computer_bar,
            "apartment": self.apartment_bar,
        }
        self.pickers: dict[str, QPushButton] = {}
        self.history: list[tuple[str, int]] = []
        self.selected = "credit"

        # Section label for which target the input is going to
        target_select = QLabel("Прогресс")
        target_select.setObjectName("SmallLabel")
        left.addWidget(target_select)

        left.addWidget(self._wrap_with_picker("credit", self.credit_bar))
        left.addWidget(self._wrap_with_picker("computer", self.computer_bar))
        left.addWidget(self._wrap_with_picker("apartment", self.apartment_bar))

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {BORDER}; background-color: {BORDER}; max-height: 1px;")
        left.addWidget(sep)

        total_label = QLabel("Общий прогресс")
        total_label.setObjectName("SmallLabel")
        left.addWidget(total_label)
        left.addWidget(self.total_bar)

        left.addStretch(1)

        # Right column: input area (equal spacing, mirrors left column rhythm)
        right = QVBoxLayout()
        right.setSpacing(14)

        right.addWidget(self._build_input_block("Добавить", "", numeric=True,
                                                button_text="Добавить",
                                                attr_name="add_input"))
        right.addWidget(self._build_input_block("Осталось",
                                                _fmt_thousands(self.TARGET_TOTAL),
                                                numeric=False,
                                                button_text=None,
                                                attr_name="remaining_input",
                                                readonly=True))
        right.addWidget(self._build_total_block())

        right.addStretch(1)

        cancel_row = QHBoxLayout()
        cancel_row.addStretch(1)
        self.undo_btn = QPushButton("Отменить")
        self.undo_btn.setObjectName("GhostButton")
        self.undo_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.undo_btn.clicked.connect(self._on_undo)
        cancel_row.addWidget(self.undo_btn)
        right.addLayout(cancel_row)

        grid.addLayout(left, 3)
        grid.addLayout(right, 2)

        outer.addWidget(card)

        # Wire the "Добавить" button (created inside _build_input_block as `self.add_button`)
        self.add_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_button.clicked.connect(self._on_add)
        self.add_input.returnPressed.connect(self._on_add)

    # ------------------------------------------------------------------
    # builders
    # ------------------------------------------------------------------
    def _wrap_with_picker(self, key: str, bar_widget: ProgressBarRow) -> QWidget:
        wrap = QFrame()
        wrap.setObjectName("ProgressRow")
        layout = QHBoxLayout(wrap)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        radio = QPushButton("●")
        radio.setObjectName("PickerDot")
        radio.setCheckable(True)
        radio.setCursor(Qt.CursorShape.PointingHandCursor)
        if key == "credit":
            radio.setChecked(True)
        radio.clicked.connect(lambda _checked, k=key: self._select_target(k))
        self.pickers[key] = radio

        layout.addWidget(radio, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(bar_widget, 1)
        return wrap

    def _select_target(self, key: str) -> None:
        self.selected = key
        for k, btn in self.pickers.items():
            btn.setChecked(k == key)

    # ------------------------------------------------------------------
    # add / undo
    # ------------------------------------------------------------------
    def _on_add(self) -> None:
        raw = (self.add_input.text() or "").strip().replace(" ", "")
        if not raw or not raw.isdigit():
            return
        amount = int(raw)
        if amount <= 0:
            return
        bar = self.bars[self.selected]
        room = bar.target - bar.value
        if room <= 0:
            return
        amount = min(amount, room)
        bar.set_value(bar.value + amount)
        self.history.append((self.selected, amount))
        self._refresh_total()
        self.add_input.clear()

    def _on_undo(self) -> None:
        if not self.history:
            return
        key, amount = self.history.pop()
        bar = self.bars[key]
        bar.set_value(bar.value - amount)
        self._refresh_total()

    def _refresh_total(self) -> None:
        total = self.credit_bar.value + self.computer_bar.value + self.apartment_bar.value
        self.total_bar.set_value(total)
        remaining = self.TARGET_TOTAL - total
        self.remaining_input.setText(_fmt_thousands(remaining))

    def _build_input_block(self, label_text: str, value: str, numeric: bool,
                           button_text: str | None, attr_name: str,
                           readonly: bool = False) -> QWidget:
        block = QFrame()
        block.setObjectName("Card")
        block.setStyleSheet(f"QFrame#Card {{ background-color: #16202d; }}")
        v = QVBoxLayout(block)
        v.setContentsMargins(20, 14, 20, 16)
        v.setSpacing(10)

        small = QLabel(label_text)
        small.setObjectName("SmallLabel")
        v.addWidget(small)

        row = QHBoxLayout()
        row.setSpacing(12)

        edit = QLineEdit(value)
        edit.setObjectName("NumericInput")
        edit.setPlaceholderText("0" if numeric and not readonly else "")
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
        block.setStyleSheet(f"QFrame#Card {{ background-color: #16202d; }}")
        v = QVBoxLayout(block)
        v.setContentsMargins(20, 14, 20, 16)
        v.setSpacing(10)
        small = QLabel("Цель")
        small.setObjectName("SmallLabel")
        v.addWidget(small)
        amount = QLabel("1 800 000")
        amount.setObjectName("TotalAmount")
        amount.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.addWidget(amount)
        return block


# ---------------------------------------------------------------------------
# Custom title bar (frameless window)
# ---------------------------------------------------------------------------


class TitleBar(QWidget):
    def __init__(self, parent_window: "MainWindow", title: str = "") -> None:
        super().__init__(parent_window)
        self.setObjectName("TitleBar")
        self.parent_window = parent_window
        self._drag_offset: QPoint | None = None
        self.setFixedHeight(44)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 6, 10, 6)
        layout.setSpacing(2)

        title_label = QLabel(title)
        title_label.setObjectName("WindowTitle")
        layout.addWidget(title_label)
        layout.addStretch(1)

        self.min_btn = QPushButton("\u2013")  # en dash – minimal "minus" glyph
        self.min_btn.setObjectName("WindowMin")
        self.min_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.min_btn.clicked.connect(parent_window.showMinimized)

        self.close_btn = QPushButton("\u00d7")  # × multiplication sign
        self.close_btn.setObjectName("WindowClose")
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.clicked.connect(parent_window.close)

        layout.addWidget(self.min_btn)
        layout.addWidget(self.close_btn)

    # drag the window by the title bar
    def mousePressEvent(self, ev: QMouseEvent) -> None:
        if ev.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = (
                ev.globalPosition().toPoint()
                - self.parent_window.frameGeometry().topLeft()
            )
            ev.accept()

    def mouseMoveEvent(self, ev: QMouseEvent) -> None:
        if self._drag_offset is not None and ev.buttons() & Qt.MouseButton.LeftButton:
            if self.parent_window.isMaximized():
                # restore on drag-from-maximized so the window follows the cursor
                self.parent_window.showNormal()
            self.parent_window.move(ev.globalPosition().toPoint() - self._drag_offset)
            ev.accept()

    def mouseReleaseEvent(self, ev: QMouseEvent) -> None:
        self._drag_offset = None

    def mouseDoubleClickEvent(self, ev: QMouseEvent) -> None:
        if self.parent_window.isMaximized():
            self.parent_window.showNormal()
        else:
            self.parent_window.showMaximized()


# ---------------------------------------------------------------------------
# Main window — frameless + edge-resizable
# ---------------------------------------------------------------------------


class MainWindow(QMainWindow):
    RESIZE_MARGIN = 6

    def __init__(self) -> None:
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setMouseTracking(True)
        self.setWindowTitle("Tri-Tab Utility")
        self.setMinimumSize(960, 620)
        self.resize(1080, 720)

        # resize state
        self._resize_dir: str | None = None
        self._resize_start_pos: QPoint | None = None
        self._resize_start_geom: QRect | None = None

        central = QWidget()
        central.setMouseTracking(True)
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Title bar
        self.title_bar = TitleBar(self, "FLYWERK AUTOMATION")
        layout.addWidget(self.title_bar)

        # Body container
        body = QWidget()
        body.setMouseTracking(True)
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(20, 4, 20, 20)
        body_layout.setSpacing(10)

        tabs = QTabWidget()
        tabs.setDocumentMode(True)
        tabs.addTab(AutoclickTab(), "PagesAutoclick")
        tabs.addTab(OpenChannelsTab(), "OpenChannels")
        tabs.addTab(ProgressTab(), "Progress")
        body_layout.addWidget(tabs)
        layout.addWidget(body)

    # ---------------- frameless edge resize ----------------
    def _hit_test(self, pos: QPoint) -> str | None:
        m = self.RESIZE_MARGIN
        rect = self.rect()
        x, y = pos.x(), pos.y()
        on_left = x <= m
        on_right = x >= rect.width() - m
        on_top = y <= m
        on_bottom = y >= rect.height() - m
        if on_top and on_left:
            return "tl"
        if on_top and on_right:
            return "tr"
        if on_bottom and on_left:
            return "bl"
        if on_bottom and on_right:
            return "br"
        if on_left:
            return "l"
        if on_right:
            return "r"
        if on_top:
            return "t"
        if on_bottom:
            return "b"
        return None

    def mouseMoveEvent(self, ev: QMouseEvent) -> None:
        if self._resize_dir and ev.buttons() & Qt.MouseButton.LeftButton:
            self._do_resize(ev.globalPosition().toPoint())
            return
        h = self._hit_test(ev.position().toPoint())
        cursors = {
            "l": Qt.CursorShape.SizeHorCursor,
            "r": Qt.CursorShape.SizeHorCursor,
            "t": Qt.CursorShape.SizeVerCursor,
            "b": Qt.CursorShape.SizeVerCursor,
            "tl": Qt.CursorShape.SizeFDiagCursor,
            "br": Qt.CursorShape.SizeFDiagCursor,
            "tr": Qt.CursorShape.SizeBDiagCursor,
            "bl": Qt.CursorShape.SizeBDiagCursor,
        }
        if h:
            self.setCursor(cursors[h])
        else:
            self.unsetCursor()
        super().mouseMoveEvent(ev)

    def mousePressEvent(self, ev: QMouseEvent) -> None:
        if ev.button() == Qt.MouseButton.LeftButton:
            h = self._hit_test(ev.position().toPoint())
            if h:
                self._resize_dir = h
                self._resize_start_pos = ev.globalPosition().toPoint()
                self._resize_start_geom = QRect(self.geometry())
                ev.accept()
                return
        super().mousePressEvent(ev)

    def mouseReleaseEvent(self, ev: QMouseEvent) -> None:
        self._resize_dir = None
        super().mouseReleaseEvent(ev)

    def _do_resize(self, gpos: QPoint) -> None:
        if not self._resize_dir or self._resize_start_geom is None:
            return
        delta = gpos - self._resize_start_pos
        g = QRect(self._resize_start_geom)
        d = self._resize_dir
        min_w = self.minimumWidth()
        min_h = self.minimumHeight()
        if "l" in d:
            new_left = g.left() + delta.x()
            if g.right() - new_left + 1 < min_w:
                new_left = g.right() - min_w + 1
            g.setLeft(new_left)
        if "r" in d:
            new_right = g.right() + delta.x()
            if new_right - g.left() + 1 < min_w:
                new_right = g.left() + min_w - 1
            g.setRight(new_right)
        if "t" in d:
            new_top = g.top() + delta.y()
            if g.bottom() - new_top + 1 < min_h:
                new_top = g.bottom() - min_h + 1
            g.setTop(new_top)
        if "b" in d:
            new_bottom = g.bottom() + delta.y()
            if new_bottom - g.top() + 1 < min_h:
                new_bottom = g.top() + min_h - 1
            g.setBottom(new_bottom)
        self.setGeometry(g)


def main() -> int:
    app = QApplication(sys.argv)
    app.setStyleSheet(QSS)
    app.setFont(QFont("Helvetica", 10))
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
