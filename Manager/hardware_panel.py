from PyQt6.QtWidgets import QWidget, QGridLayout, QLabel, QFrame, QHBoxLayout, QVBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from Manager.theme import Colors

class StatBox(QFrame):
    def __init__(self, title: str, value: str = "0", unit: str = "", accent_color: str = Colors.ACCENT_BLUE):
        super().__init__()
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.CARD_BG};
                border: 1px solid {Colors.BORDER_COLOR};
                border-radius: 6px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(2)

        t_lbl = QLabel(title)
        t_lbl.setFont(QFont("Segoe UI", 9))
        t_lbl.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; border: none;")
        layout.addWidget(t_lbl)

        self.val_lbl = QLabel(f"{value} {unit}".strip())
        self.val_lbl.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self.val_lbl.setStyleSheet(f"color: {accent_color}; border: none;")
        layout.addWidget(self.val_lbl)

    def set_value(self, val: str):
        self.val_lbl.setText(val)

class HardwarePanel(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("panelFrame")
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        header_lbl = QLabel("مراقبة العتاد والأجهزة والحالة الفنية (Gizmo Hardware Telemetry)")
        header_lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        header_lbl.setStyleSheet(f"color: {Colors.ACCENT_BLUE}; border: none;")
        main_layout.addWidget(header_lbl)

        grid = QGridLayout()
        grid.setSpacing(8)

        self.box_cpu_use = StatBox("استهلاك المعالج CPU", "0%", accent_color=Colors.ACCENT_BLUE)
        self.box_cpu_temp = StatBox("حرارة المعالج Temp", "0°C", accent_color=Colors.ACCENT_ORANGE)
        self.box_gpu_use = StatBox("استهلاك كارت الشاشة GPU", "0%", accent_color=Colors.ACCENT_GREEN)
        self.box_gpu_temp = StatBox("حرارة كارت الشاشة Temp", "0°C", accent_color=Colors.ACCENT_RED)
        
        self.box_ram_use = StatBox("الذاكرة RAM المستهلكة", "0.0 GB", accent_color=Colors.ACCENT_BLUE)
        self.box_ram_speed = StatBox("تردد الذاكرة Speed", "3200 MHz", accent_color=Colors.TEXT_PRIMARY)
        self.box_disk_use = StatBox("مساحة القرص Disk", "0 GB", accent_color=Colors.TEXT_PRIMARY)
        self.box_disk_health = StatBox("حالة القرص Health", "GOOD", accent_color=Colors.ACCENT_GREEN)

        self.box_vram_use = StatBox("ذاكرة الفيديو VRAM", "0 GB", accent_color=Colors.ACCENT_BLUE)
        self.box_gpu_name = StatBox("طراز كارت الشاشة GPU Model", "NVIDIA RTX 4070", accent_color=Colors.TEXT_PRIMARY)

        grid.addWidget(self.box_cpu_use, 0, 0)
        grid.addWidget(self.box_cpu_temp, 0, 1)
        grid.addWidget(self.box_gpu_use, 0, 2)
        grid.addWidget(self.box_gpu_temp, 0, 3)

        grid.addWidget(self.box_ram_use, 1, 0)
        grid.addWidget(self.box_ram_speed, 1, 1)
        grid.addWidget(self.box_disk_use, 1, 2)
        grid.addWidget(self.box_disk_health, 1, 3)

        grid.addWidget(self.box_vram_use, 2, 0)
        grid.addWidget(self.box_gpu_name, 2, 1, 1, 3)

        main_layout.addLayout(grid)

        status_bar = QFrame()
        status_bar.setStyleSheet(f"background-color: {Colors.CARD_BG}; border: 1px solid {Colors.BORDER_COLOR}; border-radius: 5px;")
        sb_layout = QHBoxLayout(status_bar)
        sb_layout.setContentsMargins(10, 5, 10, 5)

        self.lbl_session = QLabel("الجلسة: لا يوجد")
        self.lbl_client_ver = QLabel("الإصدار: v1.2.1")
        self.lbl_sync = QLabel("المزامنة: SYNCED")
        self.lbl_health = QLabel("الصحة: HEALTHY")
        self.lbl_queue = QLabel("الدور: 0")

        for lbl in [self.lbl_session, self.lbl_client_ver, self.lbl_sync, self.lbl_health, self.lbl_queue]:
            lbl.setFont(QFont("Segoe UI", 9))
            lbl.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; border: none;")
            sb_layout.addWidget(lbl)
            sb_layout.addStretch()

        main_layout.addWidget(status_bar)

    def update_telemetry(self, data: dict):
        self.box_cpu_use.set_value(f"{data.get('CpuUsage', 0)}%")
        self.box_cpu_temp.set_value(f"{data.get('CpuTemp', 0)}°C")
        self.box_gpu_use.set_value(f"{data.get('GpuUsage', 0)}%")
        self.box_gpu_temp.set_value(f"{data.get('GpuTemp', 0)}°C")
        self.box_ram_use.set_value(f"{data.get('RamUsage', 0)} GB")
        self.box_ram_speed.set_value(f"{data.get('RamSpeed', 3200)} MHz")
        self.box_disk_use.set_value(f"{data.get('DiskUsage', 0)} GB")
        self.box_disk_health.set_value(str(data.get('DiskHealth', 'GOOD')))
        self.box_vram_use.set_value(f"{data.get('VramUsage', 0)} GB")
        self.box_gpu_name.set_value(str(data.get('GpuName', 'NVIDIA RTX 4070')))
        
        username = data.get('CurrentUsername') or 'لا يوجد'
        self.lbl_session.setText(f"الجلسة: {username}")
        self.lbl_client_ver.setText(f"الإصدار: {data.get('ClientVersion', 'v1.2.1')}")
        self.lbl_sync.setText(f"المزامنة: {data.get('SyncStatus', 'SYNCED')}")
        self.lbl_health.setText(f"الصحة: {data.get('HealthStatus', 'HEALTHY')}")
        self.lbl_queue.setText(f"الدور: {data.get('QueuePosition', 0)}")