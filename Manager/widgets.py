# -*- coding: utf-8 -*-
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QMenu)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction
from Manager.theme import Colors

class StatCard(QFrame):
    def __init__(self, title, value, icon_name, color):
        super().__init__()
        self.setObjectName("stat_card")
        self.setMinimumWidth(220)
        self.setFixedHeight(100)
        self.setStyleSheet(f"QFrame#stat_card {{ background-color: {Colors.BG_CARD}; border-radius: 12px; border-right: 4px solid {color}; }}")
        layout = QHBoxLayout(self)
        info_layout = QVBoxLayout()
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 14px;")
        self.value_label = QLabel(str(value))
        self.value_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-size: 24px; font-weight: bold;")
        info_layout.addWidget(self.title_label)
        info_layout.addWidget(self.value_label)
        icon_label = QLabel(icon_name)
        icon_label.setStyleSheet(f"color: {color}; font-size: 30px;")
        layout.addLayout(info_layout)
        layout.addStretch()
        layout.addWidget(icon_label)

class DeviceCard(QFrame):
    action_triggered = pyqtSignal(str, int)

    def __init__(self, host_data):
        super().__init__()
        self.host_id = host_data.get('HostID', 0)
        self.host_name = host_data.get('HostName', '')
        self.status = host_data.get('Status', 'Available')
        
        # Hardware Data
        self.cpu_t = host_data.get('CPUTemp', 45)
        self.ram_u = host_data.get('RAMUsage', 40)
        
        self.setFixedSize(180, 220)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if self.status == "Available":
            status_color = Colors.AVAILABLE
        elif self.status == "Maintenance":
            status_color = Colors.MAINTENANCE
        else:
            status_color = Colors.OCCUPIED
        
        self.setObjectName("device_card")
        self.setStyleSheet(f"QFrame#device_card {{ background-color: {Colors.BG_CARD}; border: 2px solid {Colors.BORDER}; border-radius: 15px; }} QFrame#device_card:hover {{ border: 2px solid {status_color}; }}")

        self.icon_label = QLabel("💻")
        self.icon_label.setStyleSheet("font-size: 40px;")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.name_label = QLabel(self.host_name)
        self.name_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-size: 18px; font-weight: bold;")
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # معلومات الهاردوير
        self.hw_label = QLabel(f"🌡️ {self.cpu_t}°C | 💾 {self.ram_u}%")
        self.hw_label.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 11px;")
        self.hw_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.icon_label)
        layout.addWidget(self.name_label)
        layout.addWidget(self.hw_label)

    def show_context_menu(self, pos):
        menu = QMenu(self)
        menu.setStyleSheet(f"background-color: {Colors.BG_INPUT}; color: white; border: 1px solid {Colors.BORDER};")
        
        # القائمة المطابقة لـ Gizmo (الصورة 2)
        menu.addAction("تسجيل الدخول (Login)").triggered.connect(lambda: self.action_triggered.emit("LOGIN", self.host_id))
        menu.addAction("تسجيل الخروج (Logout)").triggered.connect(lambda: self.action_triggered.emit("LOGOUT", self.host_id))
        menu.addAction("دخول ضيف (Guest)").triggered.connect(lambda: self.action_triggered.emit("GUEST", self.host_id))
        menu.addSeparator()
        menu.addAction("نقل الجهاز (Move)").triggered.connect(lambda: self.action_triggered.emit("MOVE", self.host_id))
        menu.addSeparator()
        menu.addAction("🛒 بيع منتجات (Sell)").triggered.connect(lambda: self.action_triggered.emit("SELL", self.host_id))
        menu.addAction("إغلاق الرصيد (Close balance)")
        menu.addAction("إيداع (Deposit)")
        menu.addAction("سحب (Withdraw)")
        menu.addSeparator()
        menu.addAction("تشغيل (Turn on)")
        menu.addAction("إيقاف (Turn off)")
        menu.addAction("إعادة تشغيل (Restart)")

        menu.exec(self.mapToGlobal(pos))