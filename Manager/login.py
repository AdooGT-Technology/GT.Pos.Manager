import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from Manager.theme import Colors, get_login_stylesheet
from Server.database import DatabaseManager

class LoginWindow(QMainWindow):
    login_successful = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.db = DatabaseManager()
        
        self.setWindowTitle("Gaming Center Pro - تسجيل الدخول")
        self.setFixedSize(450, 540)
        self.setStyleSheet(get_login_stylesheet())
        
        self.setup_ui()

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        
        layout = QVBoxLayout(central)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        logo_lbl = QLabel("🎮")
        logo_lbl.setFont(QFont("Segoe UI Emoji", 42))
        logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_lbl = QLabel("Gaming Center Pro")
        title_lbl.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title_lbl.setStyleSheet("color: #0f172a;")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        sub_lbl = QLabel("تسجيل الدخول إلى لوحة التحكم")
        sub_lbl.setFont(QFont("Segoe UI", 10))
        sub_lbl.setStyleSheet("color: #64748b;")
        sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(logo_lbl)
        layout.addWidget(title_lbl)
        layout.addWidget(sub_lbl)
        layout.addSpacing(10)

        self.txt_username = QLineEdit()
        self.txt_username.setPlaceholderText("اسم المستخدم (admin)")
        self.txt_username.setFixedHeight(44)
        
        self.txt_password = QLineEdit()
        self.txt_password.setPlaceholderText("كلمة المرور (admin123)")
        self.txt_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_password.setFixedHeight(44)

        layout.addWidget(self.txt_username)
        layout.addWidget(self.txt_password)

        btn_login = QPushButton("تسجيل الدخول ➔")
        btn_login.setFixedHeight(46)
        btn_login.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        btn_login.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_login.clicked.connect(self.handle_login)

        layout.addWidget(btn_login)
        layout.addStretch()

    def handle_login(self):
        username = self.txt_username.text().strip()
        password = self.txt_password.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "خطأ", "برجاء كتابة اسم المستخدم وكلمة المرور.")
            return

        conn = self.db.get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT Username, FullName FROM Staff WHERE LOWER(Username) = LOWER(?) AND PasswordHash = ? AND IsActive = 1", (username, password))
                row = cursor.fetchone()
                conn.close()
                if row:
                    self.login_successful.emit(row[1] or row[0])
                    return
            except Exception as e:
                print("DB Login Check Failed:", e)

        if username.lower() == "admin" and password == "admin123":
            self.login_successful.emit("مدير النظام")
        else:
            QMessageBox.critical(self, "فشل الدخول", "اسم المستخدم أو كلمة المرور غير صحيحة.")