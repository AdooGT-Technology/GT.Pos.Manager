from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QScrollArea, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from Manager.theme import Colors

class DeviceControlCard(QFrame):
    def __init__(self, pc_num, status):
        super().__init__()
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setFixedSize(240, 160)
        
        color = Colors.GREEN if status == "متصل" else Colors.RED if status == "مشغول" else Colors.TEXT_MUTED
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BG_CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: 12px;
                border-top: 4px solid {color};
            }}
            QFrame:hover {{ border-color: {color}; }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        
        header = QHBoxLayout()
        lbl_name = QLabel(f"PC-GAME-{pc_num:02d}")
        lbl_name.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        lbl_name.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; border: none;")
        
        lbl_status = QLabel(status)
        lbl_status.setFont(QFont("Segoe UI", 9))
        lbl_status.setStyleSheet(f"color: {color}; border: none;")
        
        header.addWidget(lbl_name)
        header.addStretch()
        header.addWidget(lbl_status)
        layout.addLayout(header)
        
        layout.addStretch()
        
        btn_lay1 = QHBoxLayout()
        btn_lock = QPushButton("🔒 قفل")
        btn_lock.setStyleSheet(f"background-color: {Colors.BG_CARD_LIGHT}; color: {Colors.ORANGE}; border-radius: 4px; padding: 6px;")
        btn_unlock = QPushButton("🔓 فتح")
        btn_unlock.setStyleSheet(f"background-color: {Colors.BG_CARD_LIGHT}; color: {Colors.CYAN}; border-radius: 4px; padding: 6px;")
        btn_lay1.addWidget(btn_lock)
        btn_lay1.addWidget(btn_unlock)
        
        btn_lay2 = QHBoxLayout()
        btn_restart = QPushButton("🔄 ريستارت")
        btn_restart.setStyleSheet(f"background-color: {Colors.BG_CARD_LIGHT}; color: {Colors.PURPLE}; border-radius: 4px; padding: 6px;")
        btn_shutdown = QPushButton("🛑 إيقاف")
        btn_shutdown.setStyleSheet(f"background-color: {Colors.BG_CARD_LIGHT}; color: {Colors.RED}; border-radius: 4px; padding: 6px;")
        btn_lay2.addWidget(btn_restart)
        btn_lay2.addWidget(btn_shutdown)
        
        layout.addLayout(btn_lay1)
        layout.addLayout(btn_lay2)

class DevicesWidget(QWidget):
    def __init__(self, db=None):
        super().__init__()
        self.db = db
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setup_ui()
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)
        
        header = QHBoxLayout()
        title = QLabel("🖥️ إدارة وتحكم الأجهزة (Remote Control)")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {Colors.CYAN};")
        
        btn_wake = QPushButton("⚡ تشغيل الكل (Wake on LAN)")
        btn_wake.setStyleSheet(f"background-color: {Colors.ORANGE}; color: #000; font-weight: bold; border-radius: 6px; padding: 8px 16px;")
        
        btn_restart_empty = QPushButton("🔄 ريستارت الأجهزة الفارغة")
        btn_restart_empty.setStyleSheet(f"background-color: {Colors.CYAN}; color: #000; font-weight: bold; border-radius: 6px; padding: 8px 16px;")
        
        header.addWidget(title)
        header.addStretch()
        header.addWidget(btn_wake)
        header.addWidget(btn_restart_empty)
        main_layout.addLayout(header)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        self.grid_w = QWidget()
        self.grid_w.setStyleSheet("background: transparent;")
        self.grid = QGridLayout(self.grid_w)
        self.grid.setSpacing(14)
        
        scroll.setWidget(self.grid_w)
        main_layout.addWidget(scroll)
        
        self.load_devices()

    def load_devices(self):
        statuses = ["متصل", "متصل", "مشغول", "مشغول", "مغلق", "مغلق"]
        for i in range(1, 19):
            st = statuses[i % len(statuses)]
            card = DeviceControlCard(i, st)
            row = (i - 1) // 5
            col = (i - 1) % 5
            self.grid.addWidget(card, row, col)
