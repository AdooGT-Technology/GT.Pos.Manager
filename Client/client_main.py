"""
GT-POS Client Application
تطبيق العميل (يعمل على أجهزة الكمبيوتر)
"""

import sys
import os
import subprocess
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QMessageBox, QFrame,
    QDialog, QFormLayout, QSystemTrayIcon, QMenu
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QColor, QGuiApplication, QScreen

from client_config import ClientConfig
from client_network import ClientNetwork


CLIENT_STYLE = """
QWidget {
    background-color: #0a0a1a;
    color: #e0e0e0;
    font-family: 'Segoe UI', Arial;
}
QLabel {
    background: transparent;
}
QPushButton {
    background-color: #1a5276;
    color: white;
    border: none;
    padding: 12px 24px;
    border-radius: 8px;
    font-size: 14px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #2471a3;
}
QPushButton:pressed {
    background-color: #e94560;
}
QLineEdit {
    background-color: #1a1a3e;
    color: white;
    border: 2px solid #333;
    padding: 12px;
    border-radius: 8px;
    font-size: 14px;
}
QLineEdit:focus {
    border-color: #e94560;
}
"""


class LockScreen(QMainWindow):
    """شاشة القفل - تظهر عندما يكون الجهاز مقفل"""
    
    login_success = pyqtSignal(dict)
    
    def __init__(self, network_client):
        super().__init__()
        self.network = network_client
        self.is_locked = True
        self.session_data = None
        self.setup_ui()
    
    def setup_ui(self):
        self.setWindowTitle("GT-POS Client")
        self.setStyleSheet(CLIENT_STYLE)
        
        # ملء الشاشة بدون إطار
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        
        screen = QGuiApplication.primaryScreen().geometry()
        self.setGeometry(screen)
        
        central = QWidget()
        self.setCentralWidget(central)
        
        layout = QVBoxLayout(central)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # الحاوية الرئيسية
        container = QFrame()
        container.setFixedSize(500, 600)
        container.setStyleSheet("""
            QFrame {
                background-color: #16213e;
                border-radius: 20px;
                border: 2px solid #333;
            }
        """)
        
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(20)
        container_layout.setContentsMargins(40, 40, 40, 40)
        
        # الشعار
        logo_label = QLabel("🖥️")
        logo_label.setFont(QFont('Segoe UI', 60))
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(logo_label)
        
        # اسم المحل
        title = QLabel("GT Cyber Cafe")
        title.setFont(QFont('Segoe UI', 28, QFont.Weight.Bold))
        title.setStyleSheet("color: #e94560;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(title)
        
        # حالة الاتصال
        self.status_label = QLabel("🔴 غير متصل بالسيرفر")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setFont(QFont('Segoe UI', 11))
        self.status_label.setStyleSheet("color: #e74c3c;")
        container_layout.addWidget(self.status_label)
        
        # رقم الجهاز
        pc_label = QLabel(f"PC-{ClientConfig.HOST_NUMBER:02d}")
        pc_label.setFont(QFont('Segoe UI', 16, QFont.Weight.Bold))
        pc_label.setStyleSheet("color: #3498db;")
        pc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(pc_label)
        
        container_layout.addSpacing(20)
        
        # الرسالة
        self.message_label = QLabel("يرجى تسجيل الدخول أو التواصل مع الإدارة")
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message_label.setFont(QFont('Segoe UI', 11))
        self.message_label.setStyleSheet("color: #888;")
        self.message_label.setWordWrap(True)
        container_layout.addWidget(self.message_label)
        
        # حقول تسجيل الدخول
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("👤 اسم المستخدم")
        self.username_input.setFont(QFont('Segoe UI', 13))
        container_layout.addWidget(self.username_input)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("🔒 كلمة المرور")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setFont(QFont('Segoe UI', 13))
        self.password_input.returnPressed.connect(self.request_login)
        container_layout.addWidget(self.password_input)
        
        # زر تسجيل الدخول
        login_btn = QPushButton("🔑 تسجيل الدخول")
        login_btn.setFont(QFont('Segoe UI', 14, QFont.Weight.Bold))
        login_btn.setMinimumHeight(50)
        login_btn.setStyleSheet("""
            QPushButton {
                background-color: #e94560;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        login_btn.clicked.connect(self.request_login)
        container_layout.addWidget(login_btn)
        
        # خطأ
        self.error_label = QLabel("")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setStyleSheet("color: #e74c3c;")
        container_layout.addWidget(self.error_label)
        
        # الساعة
        self.clock_label = QLabel("")
        self.clock_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.clock_label.setFont(QFont('Segoe UI', 14))
        self.clock_label.setStyleSheet("color: #555;")
        container_layout.addWidget(self.clock_label)
        
        layout.addWidget(container)
        
        # مؤقت الساعة
        self.clock_timer = QTimer()
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start(1000)
    
    def update_clock(self):
        self.clock_label.setText(datetime.now().strftime("%H:%M:%S"))
    
    def request_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        
        if not username or not password:
            self.error_label.setText("يرجى إدخال البيانات")
            return
        
        if self.network and self.network.connected:
            self.network.request_login(username, password)
            self.error_label.setText("جاري التحقق...")
            self.error_label.setStyleSheet("color: #f39c12;")
        else:
            self.error_label.setText("غير متصل بالسيرفر")
    
    def set_connected(self):
        self.status_label.setText("🟢 متصل بالسيرفر")
        self.status_label.setStyleSheet("color: #2ecc71;")
    
    def set_disconnected(self):
        self.status_label.setText("🔴 غير متصل بالسيرفر")
        self.status_label.setStyleSheet("color: #e74c3c;")
    
    def show_message(self, text):
        """عرض رسالة من السيرفر"""
        self.message_label.setText(text)
        self.message_label.setStyleSheet("color: #f39c12; font-size: 14px;")
    
    def unlock(self, member_data=None):
        """فتح القفل"""
        self.is_locked = False
        self.session_data = member_data
        self.hide()
        self.login_success.emit(member_data or {})
    
    def lock(self, message="تم قفل الجهاز"):
        """القفل"""
        self.is_locked = True
        self.message_label.setText(message)
        self.username_input.clear()
        self.password_input.clear()
        self.error_label.clear()
        self.showFullScreen()
    
    def keyPressEvent(self, event):
        # منع Alt+F4
        if event.key() == Qt.Key.Key_F4 and event.modifiers() == Qt.KeyboardModifier.AltModifier:
            event.ignore()
            return
        # منع Alt+Tab
        if event.key() == Qt.Key.Key_Tab and event.modifiers() == Qt.KeyboardModifier.AltModifier:
            event.ignore()
            return
        super().keyPressEvent(event)


class SessionInfoWidget(QMainWindow):
    """نافذة معلومات الجلسة (تظهر كـ overlay)"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        self.setWindowTitle("Session Info")
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool
        )
        self.setFixedSize(250, 100)
        self.setStyleSheet("""
            QMainWindow {
                background-color: rgba(22, 33, 62, 230);
                border: 2px solid #e94560;
                border-radius: 10px;
            }
        """)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(10, 5, 10, 5)
        
        self.member_label = QLabel("👤 ضيف")
        self.member_label.setFont(QFont('Segoe UI', 10, QFont.Weight.Bold))
        self.member_label.setStyleSheet("color: #f39c12;")
        layout.addWidget(self.member_label)
        
        self.time_label = QLabel("⏱ 00:00:00")
        self.time_label.setFont(QFont('Segoe UI', 16, QFont.Weight.Bold))
        self.time_label.setStyleSheet("color: #3498db;")
        layout.addWidget(self.time_label)
        
        self.cost_label = QLabel("💰 0.00")
        self.cost_label.setFont(QFont('Segoe UI', 10))
        self.cost_label.setStyleSheet("color: #2ecc71;")
        layout.addWidget(self.cost_label)
        
        # وضع في أعلى يمين الشاشة
        screen = QGuiApplication.primaryScreen().geometry()
        self.move(screen.width() - 260, 10)
    
    def update_info(self, member_name, elapsed_seconds, cost):
        hours = elapsed_seconds // 3600
        minutes = (elapsed_seconds % 3600) // 60
        seconds = elapsed_seconds % 60
        
        self.member_label.setText(f"👤 {member_name}")
        self.time_label.setText(f"⏱ {hours:02d}:{minutes:02d}:{seconds:02d}")
        self.cost_label.setText(f"💰 {cost:.2f}")


class ClientApp:
    """التطبيق الرئيسي للعميل"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setStyle('Fusion')
        
        ClientConfig.load()
        
        # إعداد الشبكة
        self.network = ClientNetwork(
            ClientConfig.SERVER_HOST,
            ClientConfig.SERVER_PORT,
            ClientConfig.HOST_ID,
            ClientConfig.HOST_NUMBER
        )
        
        # Callbacks
        self.network.on_connected = self.on_connected
        self.network.on_disconnected = self.on_disconnected
        self.network.on_command = self.on_command
        self.network.on_message = self.on_message
        self.network.on_time_warning = self.on_time_warning
        
        # شاشة القفل
        self.lock_screen = LockScreen(self.network)
        self.lock_screen.login_success.connect(self.on_login_success)
        
        # معلومات الجلسة
        self.session_info = SessionInfoWidget()
        
        # حالة الجلسة
        self.session_active = False
        self.session_start = None
        self.hourly_rate = 10.0
        self.member_name = "ضيف"
        
        # مؤقت الجلسة
        self.session_timer = QTimer()
        self.session_timer.timeout.connect(self.update_session)
        
        # الاتصال بالسيرفر
        self.connect_to_server()
    
    def connect_to_server(self):
        """الاتصال بالسيرفر"""
        if not self.network.connect():
            # محاولة إعادة الاتصال
            self.network.running = True
            self.network.auto_reconnect(ClientConfig.RECONNECT_INTERVAL)
    
    def on_connected(self):
        """عند الاتصال"""
        self.lock_screen.set_connected()
    
    def on_disconnected(self):
        """عند قطع الاتصال"""
        self.lock_screen.set_disconnected()
        if ClientConfig.AUTO_RECONNECT:
            self.network.auto_reconnect(ClientConfig.RECONNECT_INTERVAL)
    
    def on_command(self, command, data):
        """عند استقبال أمر"""
        if command == 'lock':
            self.lock_workstation(data.get('message', 'تم قفل الجهاز'))
        
        elif command == 'unlock':
            self.unlock_workstation(data.get('member'))
        
        elif command == 'shutdown':
            self.shutdown_computer()
        
        elif command == 'restart':
            self.restart_computer()
    
    def on_message(self, text):
        """عند استقبال رسالة"""
        QMessageBox.information(None, "رسالة من الإدارة", text)
    
    def on_time_warning(self, remaining_minutes, message):
        """تنبيه بقرب انتهاء الوقت"""
        QMessageBox.warning(None, "⚠️ تنبيه", message)
    
    def on_login_success(self, member_data):
        """عند نجاح تسجيل الدخول"""
        self.session_active = True
        self.session_start = datetime.now()
        self.member_name = member_data.get('FirstName', 'ضيف')
        self.hourly_rate = float(member_data.get('HourlyRate', 10))
        
        self.session_info.show()
        self.session_timer.start(1000)
    
    def update_session(self):
        """تحديث معلومات الجلسة"""
        if self.session_active and self.session_start:
            elapsed = (datetime.now() - self.session_start).total_seconds()
            cost = (elapsed / 3600) * self.hourly_rate
            self.session_info.update_info(self.member_name, int(elapsed), cost)
    
    def lock_workstation(self, message=""):
        """قفل الجهاز"""
        self.session_active = False
        self.session_timer.stop()
        self.session_info.hide()
        self.lock_screen.lock(message)
    
    def unlock_workstation(self, member_data=None):
        """فتح الجهاز"""
        self.lock_screen.unlock(member_data)
    
    def shutdown_computer(self):
        """إيقاف تشغيل الكمبيوتر"""
        if sys.platform == 'win32':
            os.system('shutdown /s /t 10 /c "تم إيقاف التشغيل من قبل الإدارة"')
    
    def restart_computer(self):
        """إعادة تشغيل الكمبيوتر"""
        if sys.platform == 'win32':
            os.system('shutdown /r /t 10 /c "تمت إعادة التشغيل من قبل الإدارة"')
    
    def run(self):
        """تشغيل التطبيق"""
        self.lock_screen.showFullScreen()
        return self.app.exec()


def main():
    app = ClientApp()
    sys.exit(app.run())


if __name__ == '__main__':
    main()