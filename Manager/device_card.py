from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout, QMenu
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from Manager.theme import Colors

class MiniStatWidget(QFrame):
    def __init__(self, label: str, value: str, color: str):
        super().__init__()
        self.setStyleSheet(f"background-color: transparent; border: none;")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(2, 2, 2, 2)
        lay.setSpacing(1)
        
        lbl = QLabel(label)
        lbl.setFont(QFont("Segoe UI", 8))
        lbl.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; border: none;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(lbl)
        
        self.val_lbl = QLabel(value)
        self.val_lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.val_lbl.setStyleSheet(f"color: {color}; border: none;")
        self.val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.val_lbl)

    def set_value(self, v: str):
        self.val_lbl.setText(v)

class DeviceCard(QFrame):
    action_requested = pyqtSignal(str, int)
    
    def __init__(self, host_data: dict):
        super().__init__()
        self.host_data = host_data
        self.host_id = host_data.get("HostId")
        self.setObjectName("deviceCard")
        self.setFixedSize(320, 230)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.open_context_menu)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        # Header (اسم الجهاز + حالة الدوت)
        header = QHBoxLayout()
        
        st_code = self.host_data.get("Status", 0)
        if st_code == 1:
            st_color = Colors.STATUS_ACTIVE
            st_text = "نشط"
        elif st_code == 2:
            st_color = Colors.STATUS_OFF
            st_text = "مغلق"
        else:
            st_color = Colors.STATUS_IDLE
            st_text = "متاح"
        
        dot = QLabel("●")
        dot.setStyleSheet(f"color: {st_color}; font-size: 20px; border: none;")
        header.addWidget(dot)
        
        name_lbl = QLabel(str(self.host_data.get("HostName", "PC-??")))
        name_lbl.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        name_lbl.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; border: none;")
        header.addWidget(name_lbl)
        
        header.addStretch()
        
        st_lbl = QLabel(st_text)
        st_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        st_lbl.setStyleSheet(f"color: {st_color}; border: 1px solid {st_color}; padding: 2px 8px; border-radius: 10px;")
        header.addWidget(st_lbl)
        
        layout.addLayout(header)

        # اسم المستخدم الحالي
        user = self.host_data.get("CurrentUsername") or "— لا يوجد مستخدم —"
        user_lbl = QLabel(f"👤 {user}")
        user_lbl.setFont(QFont("Segoe UI", 10))
        user_lbl.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; border: none;")
        layout.addWidget(user_lbl)

        # IP والعتاد في شبكة
        info_lbl = QLabel(f"🌐 {self.host_data.get('IpAddress') or '192.168.1.100'} | 🎮 {self.host_data.get('GpuName', 'NVIDIA RTX 4070')[:22]}")
        info_lbl.setFont(QFont("Segoe UI", 8))
        info_lbl.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; border: none;")
        layout.addWidget(info_lbl)

        # شبكة إحصائيات العتاد (CPU / GPU / RAM / Temp)
        hw_grid = QGridLayout()
        hw_grid.setSpacing(5)
        
        cpu_use = self.host_data.get("CpuUsage", 0)
        cpu_temp = self.host_data.get("CpuTemp", 0)
        gpu_use = self.host_data.get("GpuUsage", 0)
        gpu_temp = self.host_data.get("GpuTemp", 0)
        ram_use = self.host_data.get("RamUsage", 0)
        ram_total = self.host_data.get("RamTotal", 16)
        disk_use = self.host_data.get("DiskUsage", 0)
        
        self.cpu_box = MiniStatWidget("CPU", f"{cpu_use}% / {cpu_temp}°", Colors.ACCENT_BLUE)
        self.gpu_box = MiniStatWidget("GPU", f"{gpu_use}% / {gpu_temp}°", Colors.ACCENT_GREEN)
        self.ram_box = MiniStatWidget("RAM", f"{ram_use}/{ram_total}GB", Colors.ACCENT_ORANGE)
        self.disk_box = MiniStatWidget("DISK", f"{disk_use} GB", Colors.ACCENT_PURPLE)
        
        hw_grid.addWidget(self.cpu_box, 0, 0)
        hw_grid.addWidget(self.gpu_box, 0, 1)
        hw_grid.addWidget(self.ram_box, 0, 2)
        hw_grid.addWidget(self.disk_box, 0, 3)
        
        layout.addLayout(hw_grid)
        layout.addStretch()

        # Footer (الصحة / المزامنة)
        footer = QHBoxLayout()
        health_lbl = QLabel(f"✓ {self.host_data.get('HealthStatus', 'HEALTHY')}")
        health_lbl.setFont(QFont("Segoe UI", 8))
        health_lbl.setStyleSheet(f"color: {Colors.ACCENT_GREEN}; border: none;")
        footer.addWidget(health_lbl)
        
        sync_lbl = QLabel(f"⟲ {self.host_data.get('SyncStatus', 'SYNCED')}")
        sync_lbl.setFont(QFont("Segoe UI", 8))
        sync_lbl.setStyleSheet(f"color: {Colors.ACCENT_BLUE}; border: none;")
        footer.addWidget(sync_lbl)
        
        footer.addStretch()
        
        ver_lbl = QLabel(str(self.host_data.get("ClientVersion", "v1.2.3")))
        ver_lbl.setFont(QFont("Segoe UI", 8))
        ver_lbl.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; border: none;")
        footer.addWidget(ver_lbl)
        
        layout.addLayout(footer)

    def open_context_menu(self, pos):
        menu = QMenu(self)
        actions = [
            ("تسجيل دخول عضو (Login)", "login"),
            ("بدء جلسة ضيف (Guest)", "guest"),
            ("إغلاق الجلسة (Logout)", "logout"),
            None,
            ("بيع منتجات (POS)", "sell"),
            ("شحن رصيد (Deposit)", "deposit"),
            ("سحب رصيد (Withdraw)", "withdraw"),
            None,
            ("تشغيل الجهاز (Power ON)", "poweron"),
            ("إعادة تشغيل", "restart"),
            ("إيقاف تشغيل", "poweroff"),
            ("وضع الصيانة", "maintenance"),
        ]
        for item in actions:
            if item is None:
                menu.addSeparator()
            else:
                lbl, key = item
                act = menu.addAction(lbl)
                act.setData(key)
        
        chosen = menu.exec(self.mapToGlobal(pos))
        if chosen:
            self.action_requested.emit(chosen.data(), self.host_id)