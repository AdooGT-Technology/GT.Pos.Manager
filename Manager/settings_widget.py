# -*- coding: utf-8 -*-
"""Settings: appearance, center details, connection and data — saved for real."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QLineEdit, QScrollArea, QVBoxLayout, QWidget,
)

from Manager.commands import CommandClient, server_address
from Manager.theme import THEMES, get_stylesheet, set_theme, theme_key
from Manager.ui import (
    Card, Pill, Segmented, Toast, ToggleSwitch, button, hline, label,
)
from Server.config import DB_NAME, DB_SERVER

try:
    from version import APP_VERSION
except Exception:  # pragma: no cover
    APP_VERSION = "3.6.0"


class Row(QWidget):
    def __init__(self, title: str, hint: str, widget: QWidget, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 6, 0, 6)
        layout.setSpacing(12)
        text = QVBoxLayout()
        text.setSpacing(2)
        text.addWidget(label(title, "Body"))
        if hint:
            text.addWidget(label(hint, "Caption"))
        layout.addLayout(text, 1)
        widget.setMinimumWidth(220)
        widget.setMaximumWidth(280)
        layout.addWidget(widget)


class SettingsWidget(QWidget):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.data = data
        self._build()
        self.reload()

    def set_navigator(self, _navigate):
        pass

    def _build(self):
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        host = QWidget()
        column = QVBoxLayout(host)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(12)
        column.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Appearance
        appearance = Card(padding=16, spacing=10)
        appearance.body.addWidget(label("المظهر", "Title"))
        appearance.body.addWidget(label(
            "الألوان تُطبَّق فوراً على كل الصفحات دون إعادة تشغيل.", "Muted"
        ))
        self.theme_control = Segmented(
            [(key, data_["name"]) for key, data_ in THEMES.items()], theme_key()
        )
        for btn in self.theme_control.buttons.values():
            btn.setMinimumHeight(32)
            btn.setStyleSheet("padding: 6px 16px;")
        self.theme_control.changed.connect(self._change_theme)
        appearance.body.addWidget(self.theme_control, alignment=Qt.AlignmentFlag.AlignRight)
        self.theme_hint = label("", "Caption")
        appearance.body.addWidget(self.theme_hint)
        column.addWidget(appearance)

        # Center profile
        profile = Card(padding=16, spacing=10)
        profile.body.addWidget(label("بيانات المركز", "Title"))
        self.center_name = QLineEdit()
        self.center_phone = QLineEdit()
        self.center_address = QLineEdit()
        profile.body.addWidget(Row("اسم المركز", "يظهر في الفواتير", self.center_name))
        profile.body.addWidget(Row("الجوال", "", self.center_phone))
        profile.body.addWidget(Row("العنوان", "", self.center_address))
        save_row = QHBoxLayout()
        save_row.addStretch()
        save_row.addWidget(button("حفظ البيانات", "primary", self._save_profile))
        profile.body.addLayout(save_row)
        column.addWidget(profile)

        # Connection
        connection = Card(padding=16, spacing=10)
        connection.body.addWidget(label("الاتصال", "Title"))
        host_value, port_value = server_address()
        self.host_input = QLineEdit(host_value)
        self.port_input = QLineEdit(str(port_value))
        self.port_input.setFixedWidth(110)
        connection.body.addWidget(Row("عنوان السيرفر", "عنوان جهاز السيرفر", self.host_input))
        connection.body.addWidget(Row("المنفذ", "الافتراضي 54321", self.port_input))
        self.db_state = Pill("—", "muted")
        connection.body.addWidget(Row(
            "قاعدة البيانات", f"{DB_SERVER} · {DB_NAME}", self.db_state
        ))
        actions = QHBoxLayout()
        actions.addStretch()
        actions.addWidget(button("فحص السيرفر", "quiet", self._test_server))
        actions.addWidget(button("فحص قاعدة البيانات", "quiet", self._test_db))
        connection.body.addLayout(actions)
        column.addWidget(connection)

        # Toggles
        behavior = Card(padding=16, spacing=10)
        behavior.body.addWidget(label("سلوك اللوحة", "Title"))
        self.toggle_sound = ToggleSwitch(self.data.setting("ui.sound", True))
        self.toggle_confirm = ToggleSwitch(self.data.setting("ui.confirm_destructive", True))
        self.toggle_demo = ToggleSwitch(self.data.setting("ui.show_demo", True))
        behavior.body.addWidget(Row("تنبيه صوتي", "عند نجاح أو فشل أمر", self.toggle_sound))
        behavior.body.addWidget(Row("تأكيد الأوامر الحساسة", "قبل الإيقاف وإعادة التشغيل", self.toggle_confirm))
        behavior.body.addWidget(Row("إظهار البيانات التجريبية", "عند تعذر الاتصال بقاعدة البيانات", self.toggle_demo))
        behavior.body.addWidget(button("حفظ التفضيلات", "quiet", self._save_behavior))
        column.addWidget(behavior)

        # Data
        data_card = Card(padding=16, spacing=10)
        data_card.body.addWidget(label("البيانات", "Title"))
        data_card.body.addWidget(label(
            "نسخة احتياطية كاملة تُحفظ في مجلد backups داخل المشروع.", "Muted"
        ))
        data_row = QHBoxLayout()
        data_row.addStretch()
        data_row.addWidget(button("نسخة احتياطية", "quiet", self._backup))
        data_card.body.addLayout(data_row)

        about = QHBoxLayout()
        about.addWidget(label(f"Gaming Center Pro — الإصدار {APP_VERSION}", "Caption"))
        about.addStretch()
        about.addWidget(label("GT POS Team", "Caption"))
        data_card.body.addWidget(hline())
        data_card.body.addLayout(about)
        column.addWidget(data_card)
        column.addStretch()

        scroll.setWidget(host)
        root.addWidget(scroll, 1)

    def on_shown(self):
        self.reload()

    def reload(self):
        profile = self.data.setting("center.profile", {}) or {}
        self.center_name.setText(str(profile.get("name") or "Gaming Center Pro"))
        self.center_phone.setText(str(profile.get("phone") or ""))
        self.center_address.setText(str(profile.get("address") or ""))
        self.db_state.setText("متصل" if self.data.live else "غير متصل")
        self.db_state.set_tone("success" if self.data.live else "danger")
        self.theme_hint.setText(THEMES[theme_key()]["hint"])

    # ── actions ──────────────────────────────────────────────────────────
    def _change_theme(self, key: str):
        set_theme(key)
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(get_stylesheet())
        self.theme_hint.setText(THEMES[key]["hint"])
        window = self.window()
        if hasattr(window, "_repolish_tree"):
            window._repolish_tree(window)
        if self.data.live:
            self.data.set_setting("ui.theme", key, "ui")

    def _save_profile(self):
        profile = {
            "name": self.center_name.text().strip(),
            "phone": self.center_phone.text().strip(),
            "address": self.center_address.text().strip(),
        }
        if not self.data.live:
            Toast(self, "قاعدة البيانات غير متصلة — لن يُحفظ", "warning")
            return
        ok = self.data.set_setting("center.profile", profile, "center")
        Toast(self, "حُفظت بيانات المركز" if ok else "تعذر الحفظ",
              "success" if ok else "danger")

    def _save_behavior(self):
        if not self.data.live:
            Toast(self, "قاعدة البيانات غير متصلة — لن يُحفظ", "warning")
            return
        payload = {
            "sound": self.toggle_sound.checked,
            "confirm_destructive": self.toggle_confirm.checked,
            "show_demo": self.toggle_demo.checked,
        }
        ok = self.data.set_setting("ui.preferences", payload, "ui")
        Toast(self, "حُفظت التفضيلات" if ok else "تعذر الحفظ",
              "success" if ok else "danger")

    def _test_server(self):
        ok, message = CommandClient(self.host_input.text().strip(),
                                    int(self.port_input.text().strip() or 54321)
                                    ).send("PING")
        Toast(self, f"السيرفر: {message}" if ok else message,
              "success" if ok else "warning", 3200)

    def _test_db(self):
        self.data._live = None
        live = self.data.live
        self.db_state.setText("متصل" if live else "غير متصل")
        self.db_state.set_tone("success" if live else "danger")
        Toast(self, "قاعدة البيانات متصلة" if live else "تعذر الاتصال بقاعدة البيانات",
              "success" if live else "danger", 3200)

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
                if path:
                    Toast(self, f"حُفظت النسخة: {path}", "success", 3600)
                else:
                    Toast(self, "تعذر إنشاء النسخة", "danger")
            else:
                Toast(self, "تعذر الاتصال لإنشاء النسخة", "danger")
        except Exception as error:  # noqa: BLE001
            Toast(self, f"تعذر النسخ: {error}", "danger", 3600)
