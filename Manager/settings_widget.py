# -*- coding: utf-8 -*-
"""Settings hub.

The page mirrors the familiar admin tree (general, server, client, finance,
profiles, operators) instead of one long form. Every section writes to the
Settings table, and values that other pages read — currency, tax, start page —
take effect immediately.
"""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QSize, QTime, QUrl, Qt, pyqtSignal
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (
    QApplication, QComboBox, QDoubleSpinBox, QFrame, QHBoxLayout, QHeaderView,
    QLineEdit, QPlainTextEdit, QPushButton, QScrollArea, QSpinBox,
    QStackedWidget, QTableWidget, QTableWidgetItem, QTimeEdit, QVBoxLayout,
    QWidget,
)

from Manager.commands import CommandClient, server_address
from Manager.icons import make_pixmap
from Manager.settings_schema import GROUPS, sections
from Manager.settings_store import SettingsStore
from Manager.theme import Colors, get_stylesheet, set_theme
from Manager.ui import Card, Pill, Toast, ToggleSwitch, button, label
from Server.config import DB_NAME, DB_SERVER

try:
    from version import APP_VERSION
except Exception:  # pragma: no cover
    APP_VERSION = "3.6.2"

ROOT = Path(__file__).resolve().parent.parent


def make_icon(name: str, size: int = 18):
    from PyQt6.QtGui import QIcon
    return QIcon(make_pixmap(name, size, Colors.TEXT_MUTED))


# ── small building blocks ──────────────────────────────────────────────────
class FieldRow(QWidget):
    """Title + hint on one side, the control on the other."""

    def __init__(self, title: str, hint: str, widget: QWidget, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 5)
        layout.setSpacing(14)

        text = QVBoxLayout()
        text.setSpacing(1)
        text.addWidget(label(title, "Body"))
        if hint:
            text.addWidget(label(hint, "Caption"))
        layout.addLayout(text, 1)
        layout.addWidget(widget, 0, Qt.AlignmentFlag.AlignVCenter)


def _line_edit(value, password: bool = False) -> QLineEdit:
    edit = QLineEdit(str(value if value is not None else ""))
    if password:
        edit.setEchoMode(QLineEdit.EchoMode.Password)
    edit.setMinimumWidth(220)
    edit.setMaximumWidth(320)
    return edit


def _combo(options, current) -> QComboBox:
    combo = QComboBox()
    for text, value in options:
        combo.addItem(text, value)
    index = combo.findData(current)
    if index < 0:
        index = combo.findText(str(current))
    if index >= 0:
        combo.setCurrentIndex(index)
    combo.setMinimumWidth(180)
    combo.setMaximumWidth(280)
    return combo


def _spin(value, kind: str, field: dict) -> QSpinBox | QDoubleSpinBox:
    if kind == "int":
        box = QSpinBox()
        box.setRange(int(field.get("min", 0)), int(field.get("max", 100000)))
        box.setValue(int(float(value or 0)))
        box.setFixedWidth(field.get("width", 150))
    else:
        box = QDoubleSpinBox()
        box.setDecimals(2)
        low = float(field.get("min", 0))
        high = float(field.get("max", 1000000))
        box.setRange(low, high)
        box.setSingleStep(float(field.get("step", 0.5)))
        box.setValue(float(value or 0))
        box.setFixedWidth(field.get("width", 150))
    suffix = field.get("suffix")
    if suffix:
        box.setSuffix(f" {suffix}")
    return box


class TableEditor(QWidget):
    """Editable list stored as a list of dicts inside the section blob."""

    def __init__(self, columns, rows, parent=None):
        super().__init__(parent)
        self.columns = columns
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        self.table = QTableWidget(0, len(columns))
        self.table.setHorizontalHeaderLabels([column[1] for column in columns])
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.setMinimumHeight(230)
        self.table.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked
                                   | QTableWidget.EditTrigger.SelectedClicked
                                   | QTableWidget.EditTrigger.EditKeyPressed)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        header = self.table.horizontalHeader()
        for index, column in enumerate(columns):
            self.table.setColumnWidth(index, column[3])
            header.setSectionResizeMode(index, QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(True)
        root.addWidget(self.table)

        actions = QHBoxLayout()
        actions.setSpacing(8)
        actions.addWidget(button("إضافة صف", "quiet", self.add_row, compact=True))
        actions.addWidget(button("حذف المحدد", "ghost", self.remove_row, compact=True))
        actions.addStretch()
        self.count = label("", "Caption")
        actions.addWidget(self.count)
        root.addLayout(actions)

        for row in rows or []:
            self.add_row(row)
        self._sync_count()

    def add_row(self, values=None):
        values = values or {}
        row = self.table.rowCount()
        self.table.insertRow(row)
        for index, (key, _title, kind, _width) in enumerate(self.columns):
            value = values.get(key, False if kind == "bool" else "")
            item = QTableWidgetItem()
            if kind == "bool":
                item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled
                              | Qt.ItemFlag.ItemIsSelectable)
                item.setCheckState(Qt.CheckState.Checked if value else Qt.CheckState.Unchecked)
            else:
                item.setText(str(value))
            self.table.setItem(row, index, item)
        self._sync_count()
        return row

    def remove_row(self):
        row = self.table.currentRow()
        if row < 0 and self.table.rowCount():
            row = self.table.rowCount() - 1
        if row >= 0:
            self.table.removeRow(row)
            self._sync_count()

    def _sync_count(self):
        self.count.setText(f"{self.table.rowCount()} صف")

    def values(self) -> list:
        rows = []
        for row in range(self.table.rowCount()):
            entry = {}
            for index, (key, _title, kind, _width) in enumerate(self.columns):
                item = self.table.item(row, index)
                if item is None:
                    continue
                if kind == "bool":
                    entry[key] = item.checkState() == Qt.CheckState.Checked
                elif kind == "int":
                    try:
                        entry[key] = int(float(item.text() or 0))
                    except ValueError:
                        entry[key] = 0
                elif kind == "float":
                    try:
                        entry[key] = float(item.text() or 0)
                    except ValueError:
                        entry[key] = 0.0
                else:
                    entry[key] = item.text().strip()
            if any(str(value).strip() for value in entry.values()):
                rows.append(entry)
        return rows



class SettingsNav(QWidget):
    """Collapsible tree built from buttons so RTL indentation and the active
    row look exactly like the rest of the shell."""

    selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.groups = {}
        self.leaves = {}
        self.current = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        host = QWidget()
        self.column = QVBoxLayout(host)
        self.column.setContentsMargins(2, 2, 2, 2)
        self.column.setSpacing(1)

        for group in GROUPS:
            head = QPushButton("  " + group["title"])
            head.setProperty("variant", "nav")
            head.setProperty("group", "true")
            head.setCursor(Qt.CursorShape.PointingHandCursor)
            head.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            head.setFixedHeight(36)
            head.setIcon(make_icon(group.get("icon", "grid"), 18))
            head.setIconSize(QSize(18, 18))
            head.setStyleSheet(
                "QPushButton { text-align: right; padding: 0 10px; font-weight: 600;"
                " border: none; background: transparent; }"
            )
            box = QWidget()
            box_layout = QVBoxLayout(box)
            box_layout.setContentsMargins(0, 0, 0, 4)
            box_layout.setSpacing(1)

            head.clicked.connect(lambda _checked, b=box, g=group["key"]: self._toggle(g, b))
            self.column.addWidget(head)
            self.column.addWidget(box)
            self.groups[group["key"]] = {"head": head, "box": box, "open": True}

            for section in group["sections"]:
                leaf = QPushButton(section["title"])
                leaf.setProperty("variant", "nav")
                leaf.setCursor(Qt.CursorShape.PointingHandCursor)
                leaf.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
                leaf.setFixedHeight(32)
                leaf.setStyleSheet(
                    "QPushButton { text-align: right; padding: 0 12px 0 26px;"
                    " border: none; background: transparent; font-size: 13px; }"
                )
                leaf.clicked.connect(
                    lambda _checked, k=section["key"]: self.select(k)
                )
                box_layout.addWidget(leaf)
                self.leaves[section["key"]] = leaf

        self.column.addStretch()
        scroll.setWidget(host)
        root.addWidget(scroll, 1)

    def _toggle(self, group_key: str, box: QWidget):
        entry = self.groups[group_key]
        entry["open"] = not entry["open"]
        box.setVisible(entry["open"])

    def select(self, key: str):
        if key not in self.leaves:
            return
        self.current = key
        for leaf_key, leaf in self.leaves.items():
            active = leaf_key == key
            color = Colors.CYAN if active else Colors.TEXT_MUTED
            leaf.setStyleSheet(
                "QPushButton { text-align: right; padding: 0 12px 0 26px;"
                " border: none; background: %s; color: %s; border-radius: 7px;"
                " font-size: 13px; %s }"
                % (
                    Colors.ACCENT_BG if active else "transparent",
                    color,
                    "font-weight: 600;" if active else "",
                )
            )
            repolish_current(leaf)
        self.selected.emit(key)

    def filter(self, text: str):
        needle = text.strip().lower()
        for group in GROUPS:
            entry = self.groups[group["key"]]
            visible = 0
            for section in group["sections"]:
                leaf = self.leaves[section["key"]]
                haystack = f"{section['title']} {section.get('note','')} {group['title']}".lower()
                match = not needle or needle in haystack
                leaf.setVisible(match)
                visible += 1 if match else 0
            entry["head"].setVisible(visible > 0)
            if needle and visible:
                entry["open"] = True
            entry["box"].setVisible(visible > 0 and entry["open"])


def repolish_current(widget: QWidget):
    style = widget.style()
    style.unpolish(widget)
    style.polish(widget)
    widget.update()


# ── one section ────────────────────────────────────────────────────────────
class SectionPage(QWidget):
    def __init__(self, data, store: SettingsStore, spec: dict, parent=None):
        super().__init__(parent)
        self.data = data
        self.store = store
        self.spec = spec
        self.section_key = spec["key"]
        self.getters = {}
        self.toggles = {}
        self.table_editors = []
        self._build()

    # ── construction ─────────────────────────────────────────────────────
    def _build(self):
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        host = QWidget()
        self.column = QVBoxLayout(host)
        self.column.setContentsMargins(2, 2, 8, 12)
        self.column.setSpacing(12)
        self.column.setAlignment(Qt.AlignmentFlag.AlignTop)

        head = Card(padding=16, spacing=2)
        group_title = self.spec.get("group_title", "")
        if group_title:
            head.body.addWidget(label(group_title, "Caption"))
        head.body.addWidget(label(self.spec["title"], "H2"))
        note = self.spec.get("note")
        if note:
            head.body.addWidget(label(note, "Muted"))
        self.column.addWidget(head)

        values = self.store.section(self.section_key)
        kind = self.spec.get("kind", "form")

        if kind in ("form", "subscription", "network", "database", "backup", "filesystem"):
            self._build_form(values)
        if kind == "variables":
            self._build_variables(values)
        elif kind in ("features", "addons"):
            self._build_toggles(values)
        elif kind == "table":
            self._build_table(values)
        elif kind == "currencies":
            self._build_currencies(values)

        if kind == "database":
            self._build_database_tools()
        elif kind == "backup":
            self._build_backup_tools(values)
        elif kind == "network":
            self._build_network_tools(values)
        elif kind == "filesystem":
            self._build_filesystem_tools(values)
        elif kind == "subscription":
            self._build_subscription_status(values)

        self._build_footer()
        self.column.addStretch()

        scroll.setWidget(host)
        root.addWidget(scroll, 1)

    def _card(self, title: str) -> Card:
        card = Card(padding=16, spacing=8)
        if title:
            card.body.addWidget(label(title, "Title"))
        self.column.addWidget(card)
        return card

    def _field(self, card: Card, field: dict, values: dict):
        key = field["k"]
        kind = field.get("kind", "text")
        value = values.get(key, "")

        if kind == "bool":
            widget = ToggleSwitch(bool(value))
            self.toggles[key] = widget
            self.getters[key] = lambda w=widget: w.checked
        elif kind == "choice":
            widget = _combo(field.get("options") or [], value)
            self.getters[key] = lambda w=widget: w.currentData()
        elif kind in ("int", "float", "percent", "money"):
            widget = _spin(value, "int" if kind == "int" else "float", field)
            if kind == "percent" and not field.get("suffix"):
                widget.setSuffix(" %")
            elif kind == "money" and not field.get("suffix"):
                widget.setSuffix(f" {self.store.currency()}")
            self.getters[key] = lambda w=widget: (
                w.value() if isinstance(w, QSpinBox) else round(w.value(), 4)
            )
        elif kind == "multiline":
            widget = QPlainTextEdit(str(value or ""))
            widget.setFixedHeight(84)
            widget.setMaximumWidth(380)
            self.getters[key] = lambda w=widget: w.toPlainText().strip()
        elif kind == "time":
            widget = QTimeEdit()
            widget.setDisplayFormat("HH:mm")
            text = str(value or "00:00")
            parsed = QTime.fromString(text, "HH:mm")
            widget.setTime(parsed if parsed.isValid() else QTime(0, 0))
            widget.setFixedWidth(field.get("width", 120))
            self.getters[key] = lambda w=widget: w.time().toString("HH:mm")
        else:
            widget = _line_edit(value, password=(kind == "password"))
            self.getters[key] = lambda w=widget: w.text().strip()

        card.body.addWidget(FieldRow(field["t"], field.get("hint", ""), widget))

    # Section sub-headings keep long forms readable.
    FORM_GROUPS = {
        "subscription": [("الخطة", 3), ("الترخيص", 2), ("الدعم", 1)],
        "network": [("العنوان والمنفذ", 3), ("السلوك", 4)],
        "database": [("الاستعلام", 2), ("الصيانة", 1)],
        "backup": [("الجدول", 3), ("الاحتفاظ", 2)],
        "filesystem": [("المسارات", 3), ("التنظيف", 2)],
        "work": [("التوقيت", 2), ("الحساب", 2), ("الإقفال", 2)],
        "bookings": [("السماح", 3), ("المال", 3)],
        "client_ui": [("المظهر", 3), ("الشاشة", 3)],
        "client_agent": [("التشغيل", 3), ("الجلسة", 3)],
        "client_tasks": [("التنفيذ", 3), ("الأوامر", 3)],
        "client_misc": [("التحديث", 2), ("الإصدار", 2)],
        "dashboard": [("البداية", 2), ("المحتوى", 4)],
        "products": [("الافتراضيات", 3), ("المخزون", 3)],
        "assets": [("التتبع", 2), ("الفترات", 2)],
        "web": [("التشغيل", 2), ("الوصول", 3)],
        "server_misc": [("الحالة", 2), ("السجل", 3)],
        "currencies": [("العملة الافتراضية", 1)],
    }

    def _build_form(self, values: dict):
        fields = self.spec.get("fields") or []
        groups = self.FORM_GROUPS.get(self.section_key)
        if not groups:
            current = self._card("")
            for field in fields:
                self._field(current, field, values)
            return

        index = 0
        for title, count in groups:
            card = self._card(title)
            for field in fields[index:index + count]:
                self._field(card, field, values)
            index += count
        for field in fields[index:]:
            self._field(self._card(""), field, values)

    def _build_variables(self, values: dict):
        card = self._card("المتغيرات المشتركة")
        editor = TableEditor(
            [("name", "المتغير", "text", 200), ("value", "القيمة", "text", 320)],
            values.get("rows") or [],
        )
        self.table_editors.append(("rows", editor))
        card.body.addWidget(editor)

        hint = label(
            "استخدم المتغيرات في الفواتير مثل {center_name} و{receipt_footer}.",
            "Caption",
        )
        card.body.addWidget(hint)

    def _build_toggles(self, values: dict):
        key = "features" if self.section_key == "features" else "addons"
        card = self._card("")
        for item_key, title, hint in self.spec.get(key, []):
            toggle = ToggleSwitch(bool(values.get(item_key, False)))
            self.toggles[item_key] = toggle
            self.getters[item_key] = lambda w=toggle: w.checked
            card.body.addWidget(FieldRow(title, hint, toggle))

    def _build_table(self, values: dict):
        card = self._card("")
        editor = TableEditor(self.spec.get("columns") or [], values.get("rows") or [])
        self.table_editors.append(("rows", editor))
        card.body.addWidget(editor)

    def _build_currencies(self, values: dict):
        card = self._card("العملة الافتراضية")
        options = [
            (f"{row.get('code')} — {row.get('symbol')}", row.get("code"))
            for row in values.get("rows") or []
        ] or [("ريال سعودي", "SAR")]
        combo = _combo(options, values.get("default"))
        self.getters["default"] = lambda w=combo: w.currentData()
        card.body.addWidget(FieldRow(
            "العملة المستخدمة في الفواتير", "تُطبَّق على نقطة البيع والتقارير", combo
        ))
        self._build_table(values)

    def _build_subscription_status(self, values: dict):
        card = self._card("حالة الترخيص")
        self.license_state = Pill("", "muted")
        expires = str(values.get("expires") or "").strip()
        if expires:
            self.license_state.setText(f"ينتهي في {expires}")
            self.license_state.set_tone("warning")
        else:
            self.license_state.setText("ترخيص مفتوح")
            self.license_state.set_tone("success")
        row = QHBoxLayout()
        row.addWidget(label("الصلاحية", "Body"))
        row.addStretch()
        row.addWidget(self.license_state)
        card.body.addLayout(row)
        card.body.addWidget(label(f"إصدار اللوحة {APP_VERSION}", "Caption"))

    def _build_network_tools(self, values: dict):
        card = self._card("الفحص")
        row = QHBoxLayout()
        self.net_state = Pill("لم يُفحص", "muted")
        row.addWidget(self.net_state)
        row.addStretch()
        row.addWidget(button("فحص الاتصال", "quiet", self._test_network, compact=True))
        card.body.addLayout(row)

    def _build_database_tools(self):
        card = self._card("الاتصال الحالي")
        grid = QHBoxLayout()
        info = QVBoxLayout()
        info.setSpacing(2)
        info.addWidget(label(f"السيرفر: {DB_SERVER}", "Body"))
        info.addWidget(label(f"القاعدة: {DB_NAME}", "Caption"))
        grid.addLayout(info)
        grid.addStretch()
        self.db_state = Pill(
            "متصل" if self.data.live else "غير متصل",
            "success" if self.data.live else "danger",
        )
        grid.addWidget(self.db_state)
        card.body.addLayout(grid)

        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(button("فحص الاتصال", "quiet", self._test_db, compact=True))
        row.addWidget(button("تشغيل الترحيل", "quiet", self._migrate, compact=True))
        card.body.addLayout(row)

    def _build_backup_tools(self, values: dict):
        card = self._card("النسخ المتاحة")
        self.backup_list = QVBoxLayout()
        card.body.addLayout(self.backup_list)
        row = QHBoxLayout()
        row.addWidget(button("نسخة احتياطية الآن", "primary", self._backup, compact=True))
        row.addWidget(button("فتح المجلد", "ghost", self._open_backup_folder, compact=True))
        row.addStretch()
        card.body.addLayout(row)
        self._refresh_backups(values)

    def _refresh_backups(self, values: dict):
        while self.backup_list.count():
            item = self.backup_list.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        folder = ROOT / str(values.get("folder") or "backups")
        files = []
        if folder.exists():
            files = sorted(folder.glob("*.bak"), key=lambda p: p.stat().st_mtime, reverse=True)[:5]
        if not files:
            self.backup_list.addWidget(label("لا توجد نسخ بعد.", "Caption"))
        for path in files:
            size = path.stat().st_size / (1024 * 1024)
            self.backup_list.addWidget(
                label(f"{path.name}  ·  {size:.1f} MB", "Caption")
            )

    def _build_filesystem_tools(self, values: dict):
        card = self._card("فتح المواقع")
        row = QHBoxLayout()
        for key, title in (("logs", "السجلات"), ("backups", "النسخ"), ("icons", "الأيقونات")):
            row.addWidget(button(
                title, "quiet",
                lambda _c=False, k=key: self._open_folder(values.get(k) or "."),
                compact=True,
            ))
        row.addStretch()
        card.body.addLayout(row)

    def _build_footer(self):
        footer = QHBoxLayout()
        footer.addStretch()
        self.save_state = label("", "Caption")
        footer.addWidget(self.save_state)
        footer.addWidget(button("حفظ التغييرات", "primary", self.save, compact=False))
        self.column.addLayout(footer)

    # ── persistence ───────────────────────────────────────────────────────
    def collect(self) -> dict:
        values = {}
        for key, getter in self.getters.items():
            try:
                values[key] = getter()
            except Exception:
                pass
        for key, editor in self.table_editors:
            values[key] = editor.values()
        return values

    def save(self):
        values = self.collect()
        live = self.store.save_section(self.section_key, values)
        self.save_state.setText("محفوظ" if live else "محفوظ مؤقتاً — القاعدة غير متصلة")
        self.save_state.setStyleSheet(
            f"color: {Colors.GREEN if live else Colors.ORANGE};"
        )
        Toast(self, "حُفظت الإعدادات" if live else "حُفظت مؤقتاً (قاعدة البيانات غير متصلة)",
              "success" if live else "warning")
        self._apply_side_effects(values)

        window = self.window()
        if self.section_key == "features" and hasattr(window, "apply_feature_flags"):
            window.apply_feature_flags()

    def _apply_side_effects(self, values: dict):
        if self.section_key == "client_ui":
            pass
        if self.section_key == "network":
            self.net_state.setText("محفوظ — أعد تشغيل السيرفر للتطبيق")
            self.net_state.set_tone("success")

    # ── tools ────────────────────────────────────────────────────────────
    def _test_network(self):
        host = self.getters.get("host", lambda: server_address()[0])()
        try:
            port = int(self.getters.get("port", lambda: 54321)())
        except (TypeError, ValueError):
            port = 54321
        ok, message = CommandClient(host, port).send("PING")
        self.net_state.setText(message if ok else "تعذر الاتصال")
        self.net_state.set_tone("success" if ok else "danger")
        Toast(self, message, "success" if ok else "danger", 3200)

    def _test_db(self):
        self.data._live = None
        live = self.data.live
        self.db_state.setText("متصل" if live else "غير متصل")
        self.db_state.set_tone("success" if live else "danger")
        Toast(self, "قاعدة البيانات متصلة" if live else "تعذر الاتصال بقاعدة البيانات",
              "success" if live else "danger", 3200)

    def _migrate(self):
        try:
            from Server.config import get_connection_string
            from Tools.db_migration import DatabaseMigrator
            report = DatabaseMigrator(get_connection_string()).run_migration()
            added = [line for line in report if line.startswith("ADD")]
            Toast(self, f"الترحيل تم — {len(added)} تعديل", "success", 3600)
        except Exception as error:  # noqa: BLE001
            Toast(self, f"تعذر الترحيل: {error}", "danger", 3600)

    def _backup(self):
        if not self.data.live:
            Toast(self, "قاعدة البيانات غير متصلة", "warning")
            return
        try:
            from Server.config import get_connection_string
            from Tools.db_backup import BackupManager
            manager = BackupManager(get_connection_string())
            if manager.connect():
                path = manager.backup_database(DB_NAME)
                manager.disconnect()
                Toast(self, f"حُفظت النسخة: {path}" if path else "تعذر إنشاء النسخة",
                      "success" if path else "danger", 3600)
                self._refresh_backups(self.collect())
            else:
                Toast(self, "تعذر الاتصال لإنشاء النسخة", "danger")
        except Exception as error:  # noqa: BLE001
            Toast(self, f"تعذر النسخ: {error}", "danger", 3600)

    def _open_backup_folder(self):
        self._open_folder(self.collect().get("folder") or "backups")

    def _open_folder(self, relative: str):
        path = Path(relative)
        if not path.is_absolute():
            path = ROOT / path
        path.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
        Toast(self, f"فُتح: {path}", "accent")


# ── the hub ────────────────────────────────────────────────────────────────
class SettingsWidget(QWidget):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.data = data
        self.store = getattr(data, "settings", None) or SettingsStore(data)
        self.pages = {}
        self.rows = {}
        self._build()
        self.reload()

    def set_navigator(self, _navigate):
        pass

    def _build(self):
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        root = QHBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        # nav column
        nav = QFrame()
        nav.setObjectName("Card")
        nav.setFixedWidth(286)
        nav_layout = QVBoxLayout(nav)
        nav_layout.setContentsMargins(12, 12, 12, 12)
        nav_layout.setSpacing(8)

        self.search = QLineEdit()
        self.search.setPlaceholderText("ابحث في الإعدادات…")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self._filter)
        nav_layout.addWidget(self.search)

        self.nav = SettingsNav()
        self.nav.selected.connect(self._show_section)
        nav_layout.addWidget(self.nav, 1)

        self.version_note = label(f"الإصدار {APP_VERSION}", "Caption")
        nav_layout.addWidget(self.version_note)
        root.addWidget(nav)

        # content
        self.stack = QStackedWidget()
        root.addWidget(self.stack, 1)

        self.rows = dict(self.nav.leaves)

        self.nav.select("subscription")

    def _page(self, section_key: str) -> SectionPage:
        page = self.pages.get(section_key)
        if page is None:
            _group, spec = next(
                ((group, section) for group, section in sections()
                 if section["key"] == section_key),
                (None, None),
            )
            if spec is None:
                return None
            page = SectionPage(self.data, self.store, spec)
            self.pages[section_key] = page
            self.stack.addWidget(page)
        return page

    def _show_section(self, key: str):
        page = self._page(key)
        if page is not None:
            self.stack.setCurrentWidget(page)

    def _filter(self, text: str):
        self.nav.filter(text)

    def _change_theme(self, key: str):
        set_theme(key)
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(get_stylesheet())
        window = self.window()
        if hasattr(window, "_repolish_tree"):
            window._repolish_tree(window)
        if self.data.live:
            self.store.data.set_setting("ui.theme", key, "ui")

    # ── lifecycle ────────────────────────────────────────────────────────
    def on_shown(self):
        self.reload()

    def reload(self):
        self.store.invalidate()
        self.version_note.setText(f"الإصدار {APP_VERSION}")

    def start_page(self) -> str:
        return self.store.start_page()
