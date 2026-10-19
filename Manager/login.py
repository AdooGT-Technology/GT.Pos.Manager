# -*- coding: utf-8 -*-
"""Sign-in window. One card, two columns, no detours."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox,
    QPushButton, QVBoxLayout, QWidget,
)

from Manager.theme import get_login_stylesheet, set_theme, theme_key
from Server.database import DatabaseManager

try:
    from version import APP_VERSION
except Exception:  # pragma: no cover
    APP_VERSION = "3.6.0"


class LoginWindow(QMainWindow):
    login_successful = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.db = DatabaseManager()
        self.setWindowTitle("Gaming Center Pro — الدخول")
        self.setFixedSize(860, 540)
        set_theme(theme_key())
        self.setStyleSheet(get_login_stylesheet())
        self._build()

    def _build(self):
        root = QWidget()
        root.setObjectName("LoginRoot")
        self.setCentralWidget(root)
        outer = QHBoxLayout(root)
        outer.setContentsMargins(40, 40, 40, 40)

        card = QFrame()
        card.setObjectName("LoginCard")
        outer.addWidget(card)
        layout = QHBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        brand = QFrame()
        brand.setObjectName("LoginBrand")
        brand.setFixedWidth(310)
        brand_layout = QVBoxLayout(brand)
        brand_layout.setContentsMargins(28, 32, 28, 28)
        brand_layout.setSpacing(10)
        mark = QLabel("GT")
        mark.setFixedSize(42, 42)
        mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mark.setStyleSheet(
            "background-color: rgba(255,255,255,0.08); border-radius: 12px; font-weight: 700;"
        )
        brand_layout.addWidget(mark)
        brand_layout.addSpacing(12)
        name = QLabel("Gaming Center Pro")
        name.setObjectName("LoginTitle")
        brand_layout.addWidget(name)
        subtitle = QLabel("لوحة إدارة الصالة: الأجهزة، الأعضاء، الحسابات.")
        subtitle.setObjectName("LoginMuted")
        subtitle.setWordWrap(True)
        brand_layout.addWidget(subtitle)
        brand_layout.addSpacing(16)
        for line in ("متابعة الأجهزة والجلسات لحظياً",
                     "بيع سريع وحسابات دقيقة",
                     "تحكم عن بُعد بأوامر واضحة"):
            bullet = QLabel("—  " + line)
            bullet.setObjectName("LoginMuted")
            brand_layout.addWidget(bullet)
        brand_layout.addStretch()
        version = QLabel(f"الإصدار {APP_VERSION}")
        version.setObjectName("LoginHint")
        brand_layout.addWidget(version)
        layout.addWidget(brand)

        form = QWidget()
        form_layout = QVBoxLayout(form)
        form_layout.setContentsMargins(34, 40, 34, 30)
        form_layout.setSpacing(10)

        title = QLabel("تسجيل الدخول")
        title.setObjectName("LoginTitle")
        form_layout.addWidget(title)
        hint = QLabel("استخدم حساب موظف من جدول Staff.")
        hint.setObjectName("LoginHint")
        form_layout.addWidget(hint)
        form_layout.addSpacing(10)

        form_layout.addWidget(self._caption("اسم المستخدم"))
        self.txt_username = QLineEdit()
        self.txt_username.setPlaceholderText("admin")
        form_layout.addWidget(self.txt_username)

        form_layout.addWidget(self._caption("كلمة المرور"))
        self.txt_password = QLineEdit()
        self.txt_password.setPlaceholderText("••••••••")
        self.txt_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_password.returnPressed.connect(self.handle_login)
        form_layout.addWidget(self.txt_password)

        form_layout.addSpacing(10)
        self.btn_login = QPushButton("دخول")
        self.btn_login.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_login.clicked.connect(self.handle_login)
        form_layout.addWidget(self.btn_login)

        self.status = QLabel("")
        self.status.setObjectName("LoginHint")
        self.status.setWordWrap(True)
        form_layout.addWidget(self.status)
        form_layout.addStretch()

        note = QLabel("أول مرة؟ الحساب الافتراضي admin / admin123")
        note.setObjectName("LoginHint")
        form_layout.addWidget(note)
        layout.addWidget(form, 1)

        self.txt_username.setFocus()

    @staticmethod
    def _caption(text: str) -> QLabel:
        widget = QLabel(text)
        widget.setObjectName("LoginHint")
        return widget

    def handle_login(self):
        username = self.txt_username.text().strip()
        password = self.txt_password.text().strip()
        if not username or not password:
            self.status.setText("اكتب اسم المستخدم وكلمة المرور.")
            return

        self.btn_login.setEnabled(False)
        self.status.setText("جارٍ التحقق…")

        display_name = None
        try:
            conn = self.db.get_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT Username, FullName FROM Staff WHERE LOWER(Username) = LOWER(?)"
                    " AND PasswordHash = ? AND IsActive = 1",
                    (username, password),
                )
                row = cursor.fetchone()
                conn.close()
                if row:
                    display_name = row[1] or row[0]
        except Exception as error:  # noqa: BLE001 - reported inside the window
            self.status.setText(f"تعذر الاتصال بقاعدة البيانات ({error.__class__.__name__}).")

        if display_name is None and username.lower() == "admin" and password == "admin123":
            display_name = "مدير النظام"

        self.btn_login.setEnabled(True)
        if display_name:
            self.login_successful.emit(display_name)
            return
        self.status.setText("بيانات الدخول غير صحيحة.")
        self.txt_password.clear()
        self.txt_password.setFocus()

    def show_error(self, text: str):
        QMessageBox.warning(self, "الدخول", text)
