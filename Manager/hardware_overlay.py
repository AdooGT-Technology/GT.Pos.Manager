# -*- coding: utf-8 -*-
"""Hardware monitor overlay: the full telemetry of one machine.

Shows CPU usage/temperature, GPU usage/temperature, VRAM, RAM, disk (size,
usage and health) and the network link speed with traffic counters.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QComboBox, QDialog, QFrame, QGridLayout, QHBoxLayout, QLabel, QVBoxLayout,
    QWidget,
)

from Manager.theme import Colors
from Manager.ui import Bar, Card, Pill, button, icon_button, label


def _num(value, digits: int = 0, dash: str = "—") -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return dash
    if number <= 0:
        return dash
    return f"{number:,.{digits}f}"


def _gb(value) -> str:
    text = _num(value, 1)
    return "—" if text == "—" else f"{text} GB"


def traffic(value_gb) -> str:
    """Bytes were converted to GB by the client; switch to TB when big."""
    try:
        gb = float(value_gb)
    except (TypeError, ValueError):
        return "—"
    if gb <= 0:
        return "—"
    if gb >= 1024:
        return f"{gb / 1024:,.2f} TB"
    if gb >= 1:
        return f"{gb:,.1f} GB"
    return f"{gb * 1024:,.0f} MB"


HEALTH_LABELS = {
    "HEALTHY": "سليم", "OK": "سليم", "GOOD": "سليم",
    "WARNING": "تحذير", "CAUTION": "تحذير",
    "UNHEALTHY": "تالف", "BAD": "تالف", "FAILED": "تالف", "FAIL": "تالف",
}


def net_state(speed) -> tuple[str, str, str]:
    """(label, tone, description) for the link speed."""
    try:
        value = int(float(speed))
    except (TypeError, ValueError):
        value = 0
    if value >= 1000:
        return (f"{value} Mbps", "success", "رابط جيجابت")
    if value >= 100:
        return (f"{value} Mbps", "warning", "رابط 100 ميجابت")
    if value > 0:
        return (f"{value} Mbps", "warning", "رابط ضعيف")
    return ("لا يوجد رابط", "danger", "الشبكة مفقودة")


class Metric(QWidget):
    """Title + value + optional meter."""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(4)
        head = QHBoxLayout()
        head.setSpacing(6)
        self.title = label(title, "Caption")
        self.value = label("—", "Body")
        self.value.setAlignment(Qt.AlignmentFlag.AlignLeft)
        head.addWidget(self.title)
        head.addStretch()
        head.addWidget(self.value)
        root.addLayout(head)
        self.bar = Bar(0, height=5)
        root.addWidget(self.bar, 0, Qt.AlignmentFlag.AlignTop)

    def set(self, value: str, percent: float = None, tone: str = "accent"):
        self.value.setText(value)
        if percent is not None:
            self.bar.tone = tone
            self.bar.set_value(percent)
        self.bar.setVisible(percent is not None)


class NetworkBlock(QFrame):
    """Link speed with a colored dot plus upload/download/total counters."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Inset")
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 8, 10, 8)
        root.setSpacing(8)

        head = QHBoxLayout()
        head.setSpacing(6)
        head.addWidget(label("الشبكة", "Caption"))
        self.dot = QLabel("●")
        self.dot.setStyleSheet("font-size: 15px; border: none; background: transparent;")
        self.speed = label("—", "Title")
        self.note = label("", "Caption")
        head.addWidget(self.dot)
        head.addWidget(self.speed)
        head.addWidget(self.note)
        head.addStretch()
        root.addLayout(head)

        counters = QHBoxLayout()
        counters.setSpacing(12)
        self.up = self._counter(counters, "رفع", "↑")
        self.down = self._counter(counters, "تنزيل", "↓")
        self.total = self._counter(counters, "إجمالي", "Σ")
        root.addLayout(counters)

    @staticmethod
    def _line(text: str, color: str, size: int) -> tuple[QHBoxLayout, QLabel]:
        item = QLabel(text)
        item.setStyleSheet(
            f"color: {color}; font-size: {size}px; border: none; background: transparent;"
        )
        line = QHBoxLayout()
        line.setContentsMargins(0, 0, 0, 0)
        line.addWidget(item)
        line.addStretch()
        return line, item

    def _counter(self, row: QHBoxLayout, name: str, glyph: str) -> QLabel:
        box = QWidget()
        stack = QVBoxLayout(box)
        stack.setContentsMargins(0, 0, 0, 0)
        stack.setSpacing(1)
        caption_line, _ = self._line(f"{name} {glyph}", Colors.TEXT_MUTED, 11)
        value_line, value = self._line("—", Colors.TEXT_PRIMARY, 15)
        stack.addLayout(caption_line)
        stack.addLayout(value_line)
        row.addWidget(box, 1)
        return value

    def set(self, host: dict):
        speed_text, tone, note = net_state(host.get("Net_Speed"))
        color = {
            "success": Colors.GREEN, "warning": Colors.ORANGE, "danger": Colors.RED,
        }[tone]
        self.dot.setStyleSheet(
            f"color: {color}; font-size: 15px; border: none; background: transparent;"
        )
        self.speed.setText(speed_text)
        self.note.setText(note)
        self.up.setText(traffic(host.get("Net_Upload")))
        self.down.setText(traffic(host.get("Net_Download")))
        self.total.setText(traffic(host.get("Net_Total")))


class HardwareMonitor(Card):
    """Live telemetry panel; call set_host() with a hosts row."""

    def __init__(self, parent=None, compact: bool = False):
        super().__init__(parent, padding=14, spacing=8)
        self.host = {}
        self.compact = compact

        head = QHBoxLayout()
        head.setSpacing(8)
        self.device_name = label("اختر جهازاً", "Title")
        self.state = Pill("—", "muted")
        head.addWidget(self.device_name)
        head.addStretch()
        head.addWidget(self.state)
        self.body.addLayout(head)

        self.gpu_name = label("—", "Caption")
        self.body.addWidget(self.gpu_name)

        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(8)
        self.cpu = Metric("المعالج")
        self.gpu = Metric("كارت الشاشة")
        self.vram = Metric("ذاكرة الفيديو VRAM")
        self.ram = Metric("الذاكرة RAM")
        grid.addWidget(self.cpu, 0, 0)
        grid.addWidget(self.gpu, 0, 1)
        grid.addWidget(self.vram, 1, 0)
        grid.addWidget(self.ram, 1, 1)
        self.body.addLayout(grid)

        self.disk = Metric("القرص")
        self.body.addWidget(self.disk)

        disk_foot = QHBoxLayout()
        disk_foot.setSpacing(8)
        disk_foot.addWidget(label("صحة القرص", "Caption"))
        self.disk_health = Pill("—", "muted")
        disk_foot.addWidget(self.disk_health)
        disk_foot.addStretch()
        self.disk_foot = disk_foot
        self.body.addLayout(disk_foot)

        self.network = NetworkBlock()
        self.body.addWidget(self.network)

        self.footnote = label("", "Caption")
        self.ram_note = label("", "Caption")
        for note in (self.footnote, self.ram_note):
            note.setWordWrap(False)
            note.setStyleSheet("background: transparent;")
            line = QHBoxLayout()
            line.setContentsMargins(0, 0, 0, 0)
            line.addWidget(note)
            line.addStretch()
            self.body.addLayout(line)
        self.body.addStretch()

    def set_host(self, host: dict):
        self.host = host or {}
        if not host:
            self.device_name.setText("اختر جهازاً")
            self.state.setText("—")
            self.state.set_tone("muted")
            return

        busy = str(host.get("Status")) in ("مشغول", "InUse", "Busy")
        self.device_name.setText(str(host.get("HostName") or "PC"))
        self.state.setText("مشغول" if busy else "متاح")
        self.state.set_tone("warning" if busy else "success")
        self.gpu_name.setText(
            f"{host.get('GPU_Name') or 'كارت الشاشة غير معروف'}"
            f"  ·  {host.get('IPAddress') or '—'}"
        )

        cpu = float(host.get("CPU_Usage") or 0)
        cpu_temp = float(host.get("CPU_Temp") or 0)
        gpu = float(host.get("GPU_Usage") or 0)
        gpu_temp = float(host.get("GPU_Temp") or 0)
        self.cpu.set(
            f"{cpu:.0f}%  ·  {cpu_temp:.0f}°C" if cpu_temp else f"{cpu:.0f}%",
            cpu, self._tone(cpu),
        )
        self.gpu.set(
            f"{gpu:.0f}%  ·  {gpu_temp:.0f}°C" if gpu_temp else f"{gpu:.0f}%",
            gpu, self._tone(gpu_temp if gpu_temp else gpu),
        )

        self._memory(host)
        self._disk(host)
        self.network.set(host)

        uptime = host.get("UptimeMinutes")
        uptime_text = ""
        if uptime:
            try:
                minutes = int(uptime)
                hours, rest = divmod(minutes, 60)
                uptime_text = f"يعمل منذ {hours} ساعة و {rest} دقيقة"
            except (TypeError, ValueError):
                uptime_text = ""
        self.footnote.setText(uptime_text)

        speed = host.get("RAM_Speed")
        try:
            speed_value = int(float(speed)) if speed else 0
        except (TypeError, ValueError):
            speed_value = 0
        self.ram_note.setText(f"سرعة الذاكرة {speed_value} MHz" if speed_value else "")

    # ── helpers ──────────────────────────────────────────────────────────
    @staticmethod
    def _tone(percent: float) -> str:
        try:
            value = float(percent)
        except (TypeError, ValueError):
            return "accent"
        if value >= 88:
            return "danger"
        if value >= 70:
            return "warning"
        return "accent"

    def _memory(self, host: dict):
        vram_used = float(host.get("VRAM_Used") or 0)
        vram_total = float(host.get("VRAM_Total") or 0)
        if vram_total > 0 and vram_used > 0:
            percent = vram_used / vram_total * 100
            self.vram.set(f"{vram_used:.1f} / {vram_total:.0f} GB", percent, self._tone(percent))
        else:
            self.vram.set("لا بيانات", None)

        ram_total = float(host.get("RAM_Total") or 0)
        ram_percent = float(host.get("RAM_Usage") or 0)
        if ram_total > 0:
            used = ram_total * ram_percent / 100
            self.ram.set(f"{used:.1f} / {ram_total:.0f} GB", ram_percent, self._tone(ram_percent))
        else:
            self.ram.set(f"{ram_percent:.0f}%" if ram_percent else "لا بيانات",
                         ram_percent if ram_percent else None, self._tone(ram_percent))

    def _disk(self, host: dict):
        total = float(host.get("Disk_Total") or 0)
        percent = float(host.get("Disk_Usage") or 0)
        health = str(host.get("Disk_Health") or "").upper()
        health_tone = "success"
        if health and health not in ("OK", "GOOD", "HEALTHY"):
            health_tone = "danger" if health in ("BAD", "FAILED", "FAIL") else "warning"
        if total > 0:
            used = total * percent / 100
            text = f"{used:.0f} / {total:.0f} GB"
        else:
            text = f"{percent:.0f}% مستخدم" if percent else "لا بيانات"
        tone = self._tone(percent)
        self.disk.set(text, percent if percent else None, tone)
        if health:
            self.disk_health.setText(HEALTH_LABELS.get(health, health))
            self.disk_health.set_tone(health_tone)
        else:
            self.disk_health.setText("غير معروف")
            self.disk_health.set_tone("muted")


class HardwareDialog(QDialog):
    """Standalone monitor window for one machine."""

    def __init__(self, data, host: dict, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.data = data
        self.host_id = host.get("HostId")
        self.setWindowTitle(f"مراقبة العتاد — {host.get('HostName') or ''}")
        self.setMinimumSize(560, 520)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(10)

        head = QHBoxLayout()
        head.setSpacing(8)
        head.addWidget(label("مراقبة العتاد", "Title"))
        head.addStretch()
        self.picker = QComboBox()
        self.picker.setMinimumWidth(150)
        for item in self.data.hosts():
            self.picker.addItem(str(item.get("HostName") or "PC"), item.get("HostId"))
        index = self.picker.findData(self.host_id)
        if index >= 0:
            self.picker.setCurrentIndex(index)
        self.picker.currentIndexChanged.connect(self._pick)
        head.addWidget(self.picker)
        head.addWidget(icon_button("refresh", "تحديث", self.refresh, size=36, icon_size=20))
        head.addWidget(button("إغلاق", "ghost", self.accept, compact=True))
        root.addLayout(head)

        self.monitor = HardwareMonitor(compact=True)
        root.addWidget(self.monitor, 1)
        self.monitor.set_host(host)

        self._timer = QTimer(self)
        self._timer.setInterval(3000)
        self._timer.timeout.connect(self.refresh)
        self._timer.start()

    def _pick(self, _index: int):
        self.host_id = self.picker.currentData()
        self.setWindowTitle(f"مراقبة العتاد — {self.picker.currentText()}")
        self.refresh()

    def refresh(self):
        for host in self.data.hosts():
            if host.get("HostId") == self.host_id:
                self.monitor.set_host(host)
                return
