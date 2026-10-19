import os
import random
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QScrollArea, QProgressBar, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, QTime
from PyQt6.QtGui import QFont
from Manager.theme import Colors, get_main_stylesheet

class MiniBar(QWidget):
    def __init__(self, value=0, color=None, height=6):
        super().__init__()
        self.setFixedHeight(height)
        self.value = max(0, min(100, value))
        self.color = color or Colors.CYAN
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setValue(self.value)
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(height)
        self.bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {Colors.BG_CARD_LIGHT};
                border: none;
                border-radius: {height//2}px;
            }}
            QProgressBar::chunk {{
                background-color: {self.color};
                border-radius: {height//2}px;
            }}
        """)
        layout.addWidget(self.bar)

    def set_value(self, val, color=None):
        self.value = max(0, min(100, val))
        self.bar.setValue(self.value)
        if color:
            self.color = color
            self.bar.setStyleSheet(f"""
                QProgressBar {{
                    background-color: {Colors.BG_CARD_LIGHT};
                    border: none;
                    border-radius: {self.bar.height()//2}px;
                }}
                QProgressBar::chunk {{
                    background-color: {self.color};
                    border-radius: {self.bar.height()//2}px;
                }}
            """)

class StatCard(QFrame):
    def __init__(self, icon: str, value: str, label: str, subtext: str = "", accent_color: str = None):
        super().__init__()
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        accent = accent_color or Colors.CYAN
        
        self.setObjectName("StatCard")
        self.setStyleSheet(f"""
            QFrame#StatCard {{
                background-color: {Colors.BG_CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: 12px;
                border-top: 3px solid {accent};
            }}
            QFrame#StatCard:hover {{
                border-color: {accent};
                background-color: {Colors.BG_HOVER};
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(12)

        icon_box = QFrame()
        icon_box.setFixedSize(48, 48)
        icon_box.setStyleSheet(f"""
            QFrame {{
                background-color: {accent}1A;
                border-radius: 10px;
                border: 1px solid {accent}33;
            }}
        """)
        ib_layout = QVBoxLayout(icon_box)
        ib_layout.setContentsMargins(0, 0, 0, 0)
        icon_lbl = QLabel(icon)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setFont(QFont("Segoe UI Emoji", 20))
        ib_layout.addWidget(icon_lbl)
        
        layout.addWidget(icon_box)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        
        self.lbl_value = QLabel(value)
        self.lbl_value.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self.lbl_value.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        
        self.lbl_title = QLabel(label)
        self.lbl_title.setFont(QFont("Segoe UI", 10))
        self.lbl_title.setStyleSheet(f"color: {Colors.TEXT_MUTED};")

        text_layout.addWidget(self.lbl_value)
        text_layout.addWidget(self.lbl_title)
        
        if subtext:
            self.lbl_sub = QLabel(subtext)
            self.lbl_sub.setFont(QFont("Segoe UI", 9))
            self.lbl_sub.setStyleSheet(f"color: {Colors.GREEN};")
            text_layout.addWidget(self.lbl_sub)
            
        layout.addLayout(text_layout)
        layout.addStretch()

    def update_value(self, value: str, subtext: str = None):
        self.lbl_value.setText(value)
        if subtext and hasattr(self, 'lbl_sub'):
            self.lbl_sub.setText(subtext)

class ClockWidget(QFrame):
    def __init__(self):
        super().__init__()
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setObjectName("ClockWidget")
        self.setStyleSheet(f"""
            QFrame#ClockWidget {{
                background-color: {Colors.BG_CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: 12px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(2)

        self.time_lbl = QLabel()
        self.time_lbl.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        self.time_lbl.setStyleSheet(f"color: {Colors.CYAN};")
        self.time_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.date_lbl = QLabel()
        self.date_lbl.setFont(QFont("Segoe UI", 9))
        self.date_lbl.setStyleSheet(f"color: {Colors.TEXT_MUTED};")
        self.date_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.time_lbl)
        layout.addWidget(self.date_lbl)

        timer = QTimer(self)
        timer.timeout.connect(self.update_time)
        timer.start(1000)
        self.update_time()

    def update_time(self):
        from PyQt6.QtCore import QDateTime
        now = QDateTime.currentDateTime()
        self.time_lbl.setText(now.toString("hh:mm:ss AP"))
        self.date_lbl.setText(now.toString("dd MMMM yyyy"))

class HardwareOverlay(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setObjectName("HardwareOverlay")
        self.setStyleSheet(f"""
            QFrame#HardwareOverlay {{
                background-color: {Colors.BG_CARD};
                border: 1px solid {Colors.CYAN}55;
                border-radius: 14px;
            }}
        """)
        self.hide()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        header = QHBoxLayout()
        self.lbl_pc_name = QLabel("💻 الجهاز #")
        self.lbl_pc_name.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self.lbl_pc_name.setStyleSheet(f"color: {Colors.CYAN};")
        
        btn_close = QPushButton("✕")
        btn_close.setFixedSize(28, 28)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BG_CARD_LIGHT};
                color: {Colors.TEXT_MUTED};
                border-radius: 14px;
                border: none;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {Colors.RED};
                color: #ffffff;
            }}
        """)
        btn_close.clicked.connect(self.hide)
        
        header.addWidget(self.lbl_pc_name)
        header.addStretch()
        header.addWidget(btn_close)
        layout.addLayout(header)
        
        grid = QGridLayout()
        grid.setSpacing(10)
        
        self.cpu_bar = MiniBar(45, Colors.CYAN, 8)
        self.lbl_cpu_text = QLabel("المعالج: Intel Core i7 13700K (45% | 58°C)")
        self.lbl_cpu_text.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-size: 11px;")
        
        self.gpu_bar = MiniBar(60, Colors.PURPLE, 8)
        self.lbl_gpu_text = QLabel("كرت الشاشة: RTX 4070 (60% | VRAM: 6.2/12 GB | 64°C)")
        self.lbl_gpu_text.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-size: 11px;")

        self.ram_bar = MiniBar(70, Colors.GREEN, 8)
        self.lbl_ram_text = QLabel("الذاكرة (RAM): 22.4 / 32 GB (70%)")
        self.lbl_ram_text.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-size: 11px;")

        self.disk_bar = MiniBar(82, Colors.ORANGE, 8)
        self.lbl_disk_text = QLabel("المساحة (NVMe): 820 / 1000 GB (سليم 99%)")
        self.lbl_disk_text.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-size: 11px;")

        grid.addWidget(self.lbl_cpu_text, 0, 0)
        grid.addWidget(self.cpu_bar, 1, 0)
        grid.addWidget(self.lbl_gpu_text, 2, 0)
        grid.addWidget(self.gpu_bar, 3, 0)
        grid.addWidget(self.lbl_ram_text, 4, 0)
        grid.addWidget(self.ram_bar, 5, 0)
        grid.addWidget(self.lbl_disk_text, 6, 0)
        grid.addWidget(self.disk_bar, 7, 0)
        
        layout.addLayout(grid)
        
        net_frame = QFrame()
        net_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BG_CARD_LIGHT};
                border-radius: 8px;
                padding: 8px;
            }}
        """)
        net_layout = QVBoxLayout(net_frame)
        net_layout.setContentsMargins(10, 8, 10, 8)
        net_layout.setSpacing(4)
        
        self.lbl_net_status = QLabel("🌐 حالة الشبكة: 1000 Mbps Full Duplex (ممتاز)")
        self.lbl_net_status.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.lbl_net_status.setStyleSheet(f"color: {Colors.GREEN};")
        
        self.lbl_traffic = QLabel("⬆ رفع: 14.2 Mbps  |  ⬇ تحميل: 88.5 Mbps  |  📦 إجمالي حركة البيانات: 102.7 Mbps")
        self.lbl_traffic.setFont(QFont("Segoe UI", 9))
        self.lbl_traffic.setStyleSheet(f"color: {Colors.TEXT_MUTED};")

        net_layout.addWidget(self.lbl_net_status)
        net_layout.addWidget(self.lbl_traffic)
        
        layout.addWidget(net_frame)

    def show_device_stats(self, host_number, host_name):
        self.lbl_pc_name.setText(f"💻 حالة العتاد والشبكة: {host_name} (#{host_number})")
        
        c_use = random.randint(15, 85)
        c_temp = random.randint(45, 75)
        g_use = random.randint(20, 95)
        g_vram = round(random.uniform(3.0, 11.0), 1)
        g_temp = random.randint(50, 78)
        r_use = random.randint(40, 90)
        r_gb = round(r_use * 0.32, 1)
        d_use = random.randint(50, 92)
        
        self.cpu_bar.set_value(c_use, Colors.RED if c_use > 80 else Colors.CYAN)
        self.lbl_cpu_text.setText(f"المعالج: Intel Core i7 13700K ({c_use}% | حرارة: {c_temp}°C)")
        
        self.gpu_bar.set_value(g_use, Colors.RED if g_use > 85 else Colors.PURPLE)
        self.lbl_gpu_text.setText(f"كرت الشاشة: NVIDIA RTX 4070 ({g_use}% | VRAM: {g_vram}/12 GB | حرارة: {g_temp}°C)")
        
        self.ram_bar.set_value(r_use, Colors.RED if r_use > 85 else Colors.GREEN)
        self.lbl_ram_text.setText(f"الذاكرة العشوائية: {r_gb} / 32 GB ({r_use}%)")
        
        self.disk_bar.set_value(d_use, Colors.ORANGE if d_use > 80 else Colors.CYAN)
        self.lbl_disk_text.setText(f"التخزين SSD NVMe: {int(d_use * 10)} / 1000 GB ({d_use}%) - حالة القرص: ممتازة 100%")
        
        up = round(random.uniform(1.0, 45.0), 1)
        down = round(random.uniform(5.0, 220.0), 1)
        self.lbl_traffic.setText(f"⬆ رفع: {up} Mbps  |  ⬇ تحميل: {down} Mbps  |  📦 إجمالي الحركة: {round(up+down, 1)} Mbps")
        
        self.show()

class DeviceRow(QFrame):
    def __init__(self, host: dict, on_toggle_callback=None, on_monitor_callback=None):
        super().__init__()
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.host = host
        self.on_toggle = on_toggle_callback
        self.on_monitor = on_monitor_callback
        
        self.setObjectName("DeviceRow")
        status = host.get("Status", "Offline")
        
        status_colors = {
            "Available": Colors.GREEN,
            "InUse": Colors.CYAN,
            "Busy": Colors.CYAN,
            "Maintenance": Colors.ORANGE,
            "Offline": Colors.TEXT_MUTED
        }
        status_ar = {
            "Available": "متاح للتشغيل",
            "InUse": "قيد الاستخدام",
            "Busy": "مشغول",
            "Maintenance": "صيانة",
            "Offline": "غير متصل"
        }
        
        accent = status_colors.get(status, Colors.TEXT_MUTED)
        ar_text = status_ar.get(status, "غير معروف")
        
        self.setStyleSheet(f"""
            QFrame#DeviceRow {{
                background-color: {Colors.BG_CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: 10px;
            }}
            QFrame#DeviceRow:hover {{
                border-color: {accent};
                background-color: {Colors.BG_HOVER};
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(12)
        
        pc_num = host.get("HostNumber", 0)
        num_lbl = QLabel(f"#{pc_num:02d}")
        num_lbl.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        num_lbl.setStyleSheet(f"color: {accent}; min-width: 40px;")
        
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        name_lbl = QLabel(host.get("HostName", "PC"))
        name_lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        name_lbl.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        
        ip_lbl = QLabel(f"IP: {host.get('IPAddress', '192.168.1.X')} | {host.get('Group', 'عامة')}")
        ip_lbl.setFont(QFont("Segoe UI", 9))
        ip_lbl.setStyleSheet(f"color: {Colors.TEXT_MUTED};")
        
        info_layout.addWidget(name_lbl)
        info_layout.addWidget(ip_lbl)
        
        st_pill = QLabel(ar_text)
        st_pill.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        st_pill.setAlignment(Qt.AlignmentFlag.AlignCenter)
        st_pill.setStyleSheet(f"""
            QLabel {{
                background-color: {accent}22;
                color: {accent};
                border: 1px solid {accent}44;
                border-radius: 12px;
                padding: 4px 12px;
            }}
        """)
        
        self.btn_monitor = QPushButton("📊 العتاد")
        self.btn_monitor.setFont(QFont("Segoe UI", 9))
        self.btn_monitor.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_monitor.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BG_CARD_LIGHT};
                color: {Colors.CYAN};
                border: 1px solid {Colors.CYAN}44;
                border-radius: 6px;
                padding: 5px 10px;
            }}
            QPushButton:hover {{
                background-color: {Colors.CYAN};
                color: #000000;
                font-weight: bold;
            }}
        """)
        if self.on_monitor:
            self.btn_monitor.clicked.connect(lambda: self.on_monitor(pc_num, host.get("HostName", "PC")))
        
        self.btn_action = QPushButton("تشغيل الجلسة" if status == "Available" else "إنهاء الجلسة")
        self.btn_action.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.btn_action.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_bg = Colors.GREEN if status == "Available" else (Colors.RED if status == "InUse" else Colors.BG_CARD_LIGHT)
        btn_fg = "#000000" if status == "Available" else "#ffffff"
        
        self.btn_action.setStyleSheet(f"""
            QPushButton {{
                background-color: {btn_bg};
                color: {btn_fg};
                border: none;
                border-radius: 6px;
                padding: 6px 14px;
            }}
            QPushButton:hover {{
                opacity: 0.8;
            }}
        """)
        
        layout.addWidget(num_lbl)
        layout.addLayout(info_layout)
        layout.addStretch()
        layout.addWidget(st_pill)
        layout.addWidget(self.btn_monitor)
        layout.addWidget(self.btn_action)

class DashboardWidget(QWidget):
    def __init__(self, db=None):
        super().__init__()
        self.db = db
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setup_ui()
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(12)

        self.s_devices = StatCard("💻", "0 / 0", "الأجهزة المتصلة", "جميع الأجهزة جاهزة", Colors.CYAN)
        self.s_users = StatCard("👥", "0", "المستخدمون النشطون", "لا توجد جلسات مفتوحة", Colors.PURPLE)
        self.s_hours = StatCard("⏱️", "0 س", "إجمالي ساعات اللعب", "اليوم", Colors.GREEN)
        self.s_sales = StatCard("💳", "0.00 ر.س", "مبيعات اليوم", "صافي الإيرادات", Colors.ORANGE)
        self.clock_widget = ClockWidget()

        stats_layout.addWidget(self.s_devices, 1)
        stats_layout.addWidget(self.s_users, 1)
        stats_layout.addWidget(self.s_hours, 1)
        stats_layout.addWidget(self.s_sales, 1)
        stats_layout.addWidget(self.clock_widget, 1)

        main_layout.addLayout(stats_layout)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(16)

        left_layout = QVBoxLayout()
        left_layout.setSpacing(10)

        dev_header = QHBoxLayout()
        lbl_dev_title = QLabel("🖥️ أجهزة الصالة والشبكة")
        lbl_dev_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        lbl_dev_title.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        
        btn_refresh = QPushButton("🔄 تحديث القائمة")
        btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_refresh.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BG_CARD};
                color: {Colors.CYAN};
                border: 1px solid {Colors.CYAN}44;
                border-radius: 6px;
                padding: 6px 12px;
            }}
            QPushButton:hover {{
                background-color: {Colors.CYAN};
                color: #000000;
            }}
        """)
        btn_refresh.clicked.connect(self.load_data)

        dev_header.addWidget(lbl_dev_title)
        dev_header.addStretch()
        dev_header.addWidget(btn_refresh)
        left_layout.addLayout(dev_header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; }")

        self.devices_container = QWidget()
        self.devices_layout = QVBoxLayout(self.devices_container)
        self.devices_layout.setContentsMargins(0, 0, 0, 0)
        self.devices_layout.setSpacing(8)
        self.devices_layout.addStretch()

        scroll.setWidget(self.devices_container)
        left_layout.addWidget(scroll)

        content_layout.addLayout(left_layout, 2)

        self.hw_overlay = HardwareOverlay(self)
        content_layout.addWidget(self.hw_overlay, 1)

        main_layout.addLayout(content_layout)

        self.load_data()

    def load_data(self):
        hosts = []
        if self.db and hasattr(self.db, 'get_connection'):
            try:
                conn = self.db.get_connection()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT HostId, HostName, HostNumber, IPAddress, Status, [Group] FROM Hosts ORDER BY HostNumber")
                    columns = [column[0] for column in cursor.description]
                    for row in cursor.fetchall():
                        hosts.append(dict(zip(columns, row)))
                    conn.close()
            except Exception as e:
                print("Error loading dashboard data:", e)

        if not hosts:
            hosts = [
                {"HostNumber": i, "HostName": f"PC-GAME-{i:02d}", "IPAddress": f"192.168.1.{100+i}", "Status": "Available" if i % 2 == 0 else "Offline", "Group": "VIP" if i > 5 else "العامة"}
                for i in range(1, 13)
            ]

        while self.devices_layout.count() > 1:
            item = self.devices_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        online_count = sum(1 for h in hosts if h.get("Status") in ["Available", "InUse", "Busy"])
        total_count = len(hosts)
        self.s_devices.update_value(f"{online_count} / {total_count}", "جميع الأجهزة تعمل بكفاءة")

        for h in hosts:
            row = DeviceRow(h, on_monitor_callback=self.show_hw_overlay)
            self.devices_layout.insertWidget(self.devices_layout.count() - 1, row)

    def show_hw_overlay(self, host_number, host_name):
        self.hw_overlay.show_device_stats(host_number, host_name)