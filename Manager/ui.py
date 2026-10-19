# -*- coding: utf-8 -*-
"""Shared UI kit: small, reusable pieces used by every page."""

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import (
    QComboBox, QDialog, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QPushButton, QSizePolicy, QVBoxLayout,
    QWidget,
)

from Manager.theme import Colors, RADIUS, SPACE


# ── helpers ─────────────────────────────────────────────────────────────────
def repolish(widget: QWidget):
    """Re-run style selectors after a dynamic property changed."""
    style = widget.style()
    style.unpolish(widget)
    style.polish(widget)
    widget.update()


def set_variant(widget: QWidget, variant: str):
    widget.setProperty("variant", variant)
    repolish(widget)


def hline() -> QFrame:
    line = QFrame()
    line.setObjectName("Divider")
    line.setFixedHeight(1)
    return line


def label(text: str, role: str = "Body", parent=None) -> QLabel:
    item = QLabel(text, parent)
    item.setObjectName(role)
    item.setWordWrap(role in {"Muted", "Caption"})
    return item


def icon_button(glyph: str, tooltip: str = "", on_click=None) -> QPushButton:
    button = QPushButton(glyph)
    button.setProperty("variant", "icon")
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    if tooltip:
        button.setToolTip(tooltip)
    if on_click:
        button.clicked.connect(on_click)
    return button


def button(text: str, variant: str = "quiet", on_click=None, compact=False) -> QPushButton:
    widget = QPushButton(text)
    widget.setProperty("variant", variant)
    widget.setCursor(Qt.CursorShape.PointingHandCursor)
    if compact:
        widget.setProperty("compact", "true")
    if on_click:
        widget.clicked.connect(on_click)
    return widget


# ── surfaces ────────────────────────────────────────────────────────────────
class Card(QFrame):
    def __init__(self, parent=None, padding: int = SPACE["lg"], spacing: int = SPACE["md"]):
        super().__init__(parent)
        self.setObjectName("Card")
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(padding, padding, padding, padding)
        self.body.setSpacing(spacing)

    def add_row(self, *widgets):
        row = QHBoxLayout()
        row.setSpacing(SPACE["sm"])
        for widget in widgets:
            if isinstance(widget, str):
                row.addWidget(label(widget, "Muted"))
            else:
                row.addWidget(widget)
        row.addStretch()
        self.body.addLayout(row)
        return row


class Inset(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Inset")
        self.body = QHBoxLayout(self)
        self.body.setContentsMargins(10, 8, 10, 8)
        self.body.setSpacing(SPACE["sm"])


class Page(QWidget):
    """Consistent page scaffold: title, subtitle, actions row, content area."""

    def __init__(self, title: str, subtitle: str = "", parent=None, margins=(28, 24, 28, 24)):
        super().__init__(parent)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(*margins)
        self.root.setSpacing(SPACE["lg"])

        head = QHBoxLayout()
        head.setSpacing(SPACE["md"])
        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        self.title_label = label(title, "H2")
        self.subtitle_label = label(subtitle, "Muted")
        text_col.addWidget(self.title_label)
        if subtitle:
            text_col.addWidget(self.subtitle_label)
        head.addLayout(text_col)
        head.addStretch()
        self.actions = QHBoxLayout()
        self.actions.setSpacing(SPACE["sm"])
        head.addLayout(self.actions)
        self.root.addLayout(head)

        self.body = QVBoxLayout()
        self.body.setSpacing(SPACE["md"])
        self.root.addLayout(self.body, 1)

    def add_action(self, widget: QWidget):
        self.actions.addWidget(widget)

    def set_subtitle(self, text: str):
        self.subtitle_label.setText(text)


# ── data display ────────────────────────────────────────────────────────────
class Kpi(Card):
    """A single metric card: value, label and optional hint/trend."""

    def __init__(self, title: str, value: str = "—", hint: str = "", parent=None):
        super().__init__(parent, padding=SPACE["lg"], spacing=6)
        self.setMinimumHeight(104)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        top = QHBoxLayout()
        top.setSpacing(SPACE["sm"])
        self.title = label(title, "Muted")
        self.title.setWordWrap(True)
        top.addWidget(self.title)
        top.addStretch()
        self.value = label(value, "Value")
        self.hint = label(hint, "Caption")
        self.body.addLayout(top)
        self.body.addWidget(self.value)
        self.body.addWidget(self.hint)

    def set_value(self, value: str, hint: str = None):
        self.value.setText(value)
        if hint is not None:
            self.hint.setText(hint)


class Pill(QLabel):
    TONES = {
        "accent": "accent", "success": "success", "warning": "warning",
        "danger": "danger", "muted": "muted",
    }

    def __init__(self, text: str = "", tone: str = "muted", parent=None):
        super().__init__(text, parent)
        self.tone = tone
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        self.refresh_theme()

    def set_tone(self, tone: str):
        self.tone = tone
        self.refresh_theme()

    def refresh_theme(self):
        palette = {
            "accent": (Colors.CYAN, 0.14),
            "success": (Colors.GREEN, 0.14),
            "warning": (Colors.ORANGE, 0.14),
            "danger": (Colors.RED, 0.14),
            "muted": (Colors.TEXT_MUTED, 0.10),
        }
        color, alpha = palette.get(self.tone, palette["muted"])
        tint = QColor(color)
        self.setStyleSheet(
            f"QLabel {{ color: {color}; background-color: rgba({tint.red()},{tint.green()},{tint.blue()},{alpha});"
            f" border-radius: 9px; padding: 2px 9px; font-size: 11px; font-weight: 600; }}"
        )


class Bar(QWidget):
    """Thin horizontal meter used for CPU/RAM/disk readings."""

    def __init__(self, value: float = 0, tone: str = "accent", height: int = 6, parent=None):
        super().__init__(parent)
        self._value = max(0.0, min(100.0, float(value)))
        self.tone = tone
        self.setFixedHeight(height)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_value(self, value: float):
        value = max(0.0, min(100.0, float(value)))
        if abs(value - self._value) >= 0.5:
            self._value = value
            self.update()

    def tone_color(self) -> str:
        return {
            "success": Colors.GREEN, "warning": Colors.ORANGE,
            "danger": Colors.RED, "muted": Colors.TEXT_MUTED,
        }.get(self.tone, Colors.CYAN)

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        radius = self.height() / 2
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(Colors.BG_CARD_LIGHT))
        painter.drawRoundedRect(self.rect(), radius, radius)

        width = int(self.width() * self._value / 100.0)
        if width > 0:
            painter.setBrush(QColor(self.tone_color()))
            painter.drawRoundedRect(0, 0, max(width, self.height()), self.height(), radius, radius)

    def refresh_theme(self):
        self.update()


class StatLine(QWidget):
    """Label + value + optional meter, stacked compactly."""

    def __init__(self, name: str, value: str = "—", bar_value: float = None, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(5)
        top = QHBoxLayout()
        top.setSpacing(8)
        self.name = label(name, "Caption")
        self.value = label(value, "Body")
        self.value.setAlignment(Qt.AlignmentFlag.AlignLeft)
        top.addWidget(self.name)
        top.addStretch()
        top.addWidget(self.value)
        self.layout.addLayout(top)
        self.bar = None
        if bar_value is not None:
            self.bar = Bar(bar_value)
            self.layout.addWidget(self.bar)

    def set_value(self, value: str, bar_value: float = None):
        self.value.setText(value)
        if self.bar is not None and bar_value is not None:
            tone = "accent"
            if bar_value >= 88:
                tone = "danger"
            elif bar_value >= 70:
                tone = "warning"
            self.bar.tone = tone
            self.bar.set_value(bar_value)


class EmptyState(QWidget):
    def __init__(self, title: str, text: str = "", action: QWidget = None, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 36, 24, 36)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        head = label(title, "Title")
        head.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(head)
        if text:
            body = label(text, "Muted")
            body.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(body)
        if action:
            action.setMaximumWidth(220)
            layout.addWidget(action, alignment=Qt.AlignmentFlag.AlignCenter)


# ── inputs ──────────────────────────────────────────────────────────────────
class SearchInput(QLineEdit):
    def __init__(self, placeholder: str = "بحث…", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setClearButtonEnabled(True)
        self.setProperty("search", "true")
        self.setMinimumWidth(220)
        self.setMaximumWidth(320)


class Segmented(QWidget):
    """Small segmented control; emits the selected key."""

    changed = pyqtSignal(str)

    def __init__(self, options, current: str = None, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.options = list(options)
        self.current = current or self.options[0][0]
        self.buttons = {}

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        for key, text in self.options:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setProperty("compact", "true")
            btn.clicked.connect(lambda _checked, k=key: self.select(k))
            layout.addWidget(btn)
            self.buttons[key] = btn
        self._sync()

    def select(self, key: str, emit: bool = True):
        if key not in self.buttons:
            return
        self.current = key
        self._sync()
        if emit:
            self.changed.emit(key)

    def _sync(self):
        for key, btn in self.buttons.items():
            active = key == self.current
            btn.setChecked(active)
            btn.setProperty("variant", "primary" if active else "ghost")
            repolish(btn)


class ToggleSwitch(QWidget):
    toggled = pyqtSignal(bool)

    def __init__(self, checked: bool = False, parent=None):
        super().__init__(parent)
        self.checked = checked
        self.setFixedSize(42, 24)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, _event):
        self.checked = not self.checked
        self.update()
        self.toggled.emit(self.checked)

    def set_checked(self, value: bool):
        self.checked = bool(value)
        self.update()

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        track = QColor(Colors.CYAN if self.checked else Colors.BG_CARD_LIGHT)
        painter.setPen(QPen(QColor(Colors.BORDER if not self.checked else Colors.CYAN), 1))
        painter.setBrush(track)
        painter.drawRoundedRect(0, 0, 42, 24, 12, 12)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#F8FAFC"))
        knob_x = 20 if self.checked else 2
        painter.drawEllipse(knob_x, 2, 20, 20)

    def refresh_theme(self):
        self.update()


# ── feedback ────────────────────────────────────────────────────────────────
class Toast(QFrame):
    """Transient message pinned to the bottom-left of its parent."""

    def __init__(self, parent, text: str, tone: str = "accent", msec: int = 2600):
        super().__init__(parent)
        self.setObjectName("Inset")
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        color = {"accent": Colors.CYAN, "success": Colors.GREEN,
                 "danger": Colors.RED, "warning": Colors.ORANGE}.get(tone, Colors.CYAN)
        self.setStyleSheet(
            f"QFrame#Inset {{ background-color: {Colors.BG_CARD}; border: 1px solid {Colors.BORDER};"
            f" border-radius: 10px; }}"
            f"QLabel {{ color: {Colors.TEXT_PRIMARY}; }}"
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        dot = QLabel("●")
        dot.setStyleSheet(f"color: {color}; border: none;")
        message = QLabel(text)
        message.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; border: none;")
        layout.addWidget(dot)
        layout.addWidget(message)
        self.adjustSize()
        self.move(24, parent.height() - self.height() - 24)
        self.show()
        self.raise_()
        QTimer.singleShot(msec, self.deleteLater)


class CommandPalette(QDialog):
    """Fast navigator (Ctrl/Cmd+K). Items: (icon, title, hint, callback)."""

    def __init__(self, items, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setModal(True)
        self.setFixedWidth(520)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.items = list(items)
        self.filtered = list(self.items)

        self.setStyleSheet(
            f"QDialog {{ background-color: {Colors.BG_CARD}; border: 1px solid {Colors.BORDER};"
            f" border-radius: 14px; }}"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 10)
        layout.setSpacing(8)

        self.search = QLineEdit()
        self.search.setPlaceholderText("اكتب اسم الصفحة أو الإجراء…")
        self.search.textChanged.connect(self._filter)
        self.search.returnPressed.connect(self._run_current)
        layout.addWidget(self.search)

        self.list = QListWidget()
        self.list.setMaximumHeight(320)
        self.list.itemActivated.connect(self._activate)
        layout.addWidget(self.list)

        hint = QLabel("Enter للتنفيذ  ·  Esc للإغلاق")
        hint.setObjectName("Caption")
        hint.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(hint)

        self._filter("")
        self.search.setFocus()

    def _filter(self, text: str):
        needle = text.strip().lower()
        self.filtered = [
            item for item in self.items
            if needle in (item[1] + " " + item[2]).lower()
        ]
        self.list.clear()
        for icon, title, hint, _ in self.filtered:
            entry = QListWidgetItem(f"{icon}   {title}    ·  {hint}")
            self.list.addItem(entry)
        if self.filtered:
            self.list.setCurrentRow(0)

    def _activate(self, item: QListWidgetItem):
        row = self.list.row(item)
        self._run(row)

    def _run_current(self):
        self._run(self.list.currentRow())

    def _run(self, row: int):
        if 0 <= row < len(self.filtered):
            callback = self.filtered[row][3]
            self.accept()
            QTimer.singleShot(0, callback)


class FormDialog(QDialog):
    """Dialog shell with a title, content area and cancel/save buttons."""

    def __init__(self, title: str, subtitle: str = "", parent=None, width: int = 460):
        super().__init__(parent)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setWindowTitle(title)
        self.setMinimumWidth(width)
        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(22, 20, 22, 18)
        self.root.setSpacing(SPACE["md"])

        head = QVBoxLayout()
        head.setSpacing(3)
        head.addWidget(label(title, "Title"))
        if subtitle:
            head.addWidget(label(subtitle, "Muted"))
        self.root.addLayout(head)

        self.form = QVBoxLayout()
        self.form.setSpacing(10)
        self.root.addLayout(self.form)

        self.footer = QHBoxLayout()
        self.footer.setSpacing(8)
        self.footer.addStretch()
        self.cancel_btn = button("إلغاء", "ghost", self.reject, compact=True)
        self.save_btn = button("حفظ", "primary", self.accept, compact=True)
        self.footer.addWidget(self.cancel_btn)
        self.footer.addWidget(self.save_btn)
        self.root.addLayout(self.footer)

    def add_field(self, title: str, widget: QWidget):
        self.form.addWidget(label(title, "Caption"))
        self.form.addWidget(widget)
        return widget

    def add_combo(self, title: str, options) -> QComboBox:
        combo = QComboBox()
        for option in options:
            if isinstance(option, tuple):
                combo.addItem(option[0], option[1])
            else:
                combo.addItem(option)
        return self.add_field(title, combo)
