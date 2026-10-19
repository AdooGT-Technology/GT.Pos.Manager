# -*- coding: utf-8 -*-
"""Hardware monitor: every reading the client reports, in one panel.

Covered here — CPU usage and temperature, GPU usage and temperature, VRAM
used/total, RAM used/total (plus bus speed), disk size/used/free/health and the
network link with a traffic-light badge (green gigabit, amber 100 Mbit, red
when the link is gone) together with upload, download and grand totals.
"""

from __future__ import annotations

from collections import deque
from datetime import datetime

from PyQt6.QtCore import QPointF, Qt, QTimer
from PyQt6.QtGui import QColor, QLinearGradient, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import (
    QComboBox, QDialog, QFrame, QGridLayout, QHBoxLayout, QLabel, QVBoxLayout,
    QWidget,
)

from Manager.theme import Colors
from Manager.ui import Bar, Card, Pill, button, hline, icon_button, label


def ltr(text: str) -> str:
    """Isolate a number/unit run so Arabic sentences keep it in order."""
    return f"\u2066{text}\u2069"


def _float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _num(value, digits: int = 0, dash: str = "—") -> str:
    number = _float(value)
    if number <= 0:
        return dash
    return f"{number:,.{digits}f}"


def _gb(value, digits: int = 1) -> str:
    text = _num(value, digits)
    return "—" if text == "—" else f"{text} GB"


def traffic(value_gb) -> str:
    """Counters arrive as GB; step up to TB when the numbers get big."""
    gb = _float(value_gb)
    if gb <= 0:
        return "—"
    if gb >= 1024:
        return f"{gb / 1024:,.2f} TB"
    if gb >= 1:
        return f"{gb:,.1f} GB"
    return f"{gb * 1024:,.0f} MB"


def speed_rate(mb_per_second) -> str:
    """Live throughput in MB/s, dropping to KB/s for idle machines."""
    value = _float(mb_per_second)
    if value <= 0:
        return "0 MB/s"
    if value < 1:
        return f"{value * 1024:,.0f} KB/s"
    return f"{value:,.1f} MB/s"


HEALTH_LABELS = {
    "HEALTHY": "سليم", "OK": "سليم", "GOOD": "سليم",
    "WARNING": "تحذير", "CAUTION": "تحذير",
    "UNHEALTHY": "تالف", "BAD": "تالف", "FAILED": "تالف", "FAIL": "تالف",
}
HEALTH_TONES = {"سليم": "success", "تحذير": "warning", "تالف": "danger"}


def net_state(speed) -> tuple[str, str, str]:
    """(link label, tone, note) — gigabit is green, 100 Mbit amber, lost is red."""
    value = int(_float(speed))
    if value >= 1000:
        return (f"{value} Mbps", "success", "رابط جيجابت")
    if value >= 100:
        return (f"{value} Mbps", "warning", "رابط 100 ميجابت")
    if value > 0:
        return (f"{value} Mbps", "warning", "رابط ضعيف")
    return ("انقطع الرابط", "danger", "لا توجد شبكة")


def tone_color(tone: str) -> str:
    return {
        "success": Colors.GREEN, "warning": Colors.ORANGE, "danger": Colors.RED,
    }.get(tone, Colors.CYAN)


def load_tone(percent: float) -> str:
    value = _float(percent)
    if value >= 88:
        return "danger"
    if value >= 70:
        return "warning"
    return "accent"


def heat_tone(celsius: float) -> str:
    value = _float(celsius)
    if value >= 85:
        return "danger"
    if value >= 70:
        return "warning"
    return "success"


class LinkLight(QWidget):
    """Painted LED: coloured core with a soft halo (no font glyphs)."""

    def __init__(self, diameter: int = 16, parent=None):
        super().__init__(parent)
        self._diameter = diameter
        self._color = QColor(Colors.TEXT_MUTED)
        self._pulse = False
        self.setFixedSize(diameter + 12, diameter + 12)
        self._timer = QTimer(self)
        self._timer.setInterval(700)
        self._timer.timeout.connect(self._blink)

    def set_state(self, color: str, pulse: bool = False):
        self._color = QColor(color)
        if pulse and not self._timer.isActive():
            self._timer.start()
        elif not pulse:
            self._timer.stop()
        self._pulse = pulse
        self.update()

    def _blink(self):
        self._pulse = not self._pulse
        self.update()

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        center = QPointF(self.width() / 2, self.height() / 2)
        radius = self._diameter / 2

        halo = QColor(self._color)
        halo.setAlpha(70 if self._pulse or not self._timer.isActive() else 25)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(halo)
        painter.drawEllipse(center, radius + 4, radius + 4)

        painter.setBrush(self._color)
        painter.drawEllipse(center, radius, radius)

        highlight = QColor(255, 255, 255, 150)
        painter.setBrush(highlight)
        painter.drawEllipse(
            QPointF(center.x() - radius * 0.3, center.y() - radius * 0.35),
            radius * 0.28, radius * 0.28,
        )


class Sparkline(QWidget):
    """Small rolling chart for a percentage series."""

    def __init__(self, points: int = 40, parent=None):
        super().__init__(parent)
        self.values = deque(maxlen=points)
        self.tone = "accent"
        self.setFixedHeight(34)
        self.setMinimumWidth(80)

    def push(self, value: float, tone: str = "accent"):
        self.values.append(max(0.0, min(100.0, _float(value))))
        self.tone = tone
        self.update()

    def clear(self):
        self.values.clear()
        self.update()

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(1, 3, -1, -3)
        if len(self.values) < 2:
            painter.setPen(QPen(QColor(Colors.BORDER), 1, Qt.PenStyle.DashLine))
            painter.drawLine(
                QPointF(rect.left(), rect.bottom()), QPointF(rect.right(), rect.bottom())
            )
            return

        values = list(self.values)
        step = rect.width() / max(1, len(values) - 1)
        path = QPainterPath()
        for index, value in enumerate(values):
            x = rect.left() + index * step
            y = rect.bottom() - (value / 100.0) * rect.height()
            if index == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)

        fill = QPainterPath(path)
        fill.lineTo(QPointF(rect.right(), rect.bottom()))
        fill.lineTo(QPointF(rect.left(), rect.bottom()))
        fill.closeSubpath()

        color = QColor(tone_color(self.tone))
        gradient = QLinearGradient(0, rect.top(), 0, rect.bottom())
        start = QColor(color)
        start.setAlpha(90)
        end = QColor(color)
        end.setAlpha(0)
        gradient.setColorAt(0.0, start)
        gradient.setColorAt(1.0, end)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(gradient)
        painter.drawPath(fill)

        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(color, 1.8))
        painter.drawPath(path)


class MetricTile(QWidget):
    """Caption + big reading + sub-line + meter + sparkline."""

    def __init__(self, title: str, history: bool = True, parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(3)

        head = QHBoxLayout()
        head.setSpacing(6)
        head.addWidget(label(title, "Caption"))
        head.addStretch()
        self.badge = label("", "Caption")
        head.addWidget(self.badge)
        root.addLayout(head)

        self.value = label("—", "H2")
        root.addWidget(self.value)
        self.sub = label(" ", "Caption")
        self.sub.setWordWrap(False)
        root.addWidget(self.sub)

        self.bar = Bar(0, height=5)
        root.addWidget(self.bar)

        self.spark = Sparkline() if history else None
        if self.spark is not None:
            root.addWidget(self.spark)

    def set(self, value: str, sub: str = "", percent: float = None,
            tone: str = "accent", badge: str = "", sample: float = None):
        self.value.setText(value)
        self.sub.setText(sub or " ")
        self.badge.setText(badge)
        if percent is None:
            self.bar.setVisible(False)
        else:
            self.bar.setVisible(True)
            self.bar.tone = tone
            self.bar.set_value(percent)
        if self.spark is not None and sample is not None:
            self.spark.push(sample, tone)


class DiskBlock(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Inset")
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(6)

        head = QHBoxLayout()
        head.setSpacing(8)
        head.addWidget(label("القرص", "Title"))
        self.health = Pill("—", "muted")
        head.addWidget(self.health)
        head.addStretch()
        self.drive = label("", "Caption")
        head.addWidget(self.drive)
        root.addLayout(head)

        self.size = label("—", "Body")
        root.addWidget(self.size)
        self.bar = Bar(0, height=6)
        root.addWidget(self.bar)
        self.detail = label(" ", "Caption")
        self.detail.setWordWrap(False)
        root.addWidget(self.detail)

    def set(self, host: dict):
        total = _float(host.get("Disk_Total"))
        percent = _float(host.get("Disk_Usage"))
        used = total * percent / 100 if total > 0 else 0
        free = max(0.0, total - used)
        health_raw = str(host.get("Disk_Health") or "").upper()
        health = HEALTH_LABELS.get(health_raw, health_raw)
        self.health.setText(health or "غير معروف")
        self.health.set_tone(HEALTH_TONES.get(health, "muted") if health else "muted")

        if total > 0:
            self.size.setText(
                f"المستخدم {ltr(f'{used:,.0f} GB')} من {ltr(f'{total:,.0f} GB')}"
            )
        else:
            self.size.setText(
                f"المستخدم {ltr(f'{percent:,.0f}%')}" if percent else "لا بيانات"
            )
        self.bar.tone = load_tone(percent)
        self.bar.set_value(percent)
        parts = [f"متاح {ltr(f'{free:,.0f} GB')}"] if total > 0 else []
        if percent:
            parts.append(f"الإشغال {ltr(f'{percent:,.0f}%')}")
        drive = host.get("DriveLetter") or host.get("SystemDrive") or ""
        self.detail.setText("  ·  ".join(parts) or "بانتظار تقرير العميل")
        self.drive.setText(str(drive))


class NetworkBlock(QFrame):
    """Traffic-light link badge plus upload, download and total counters."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Inset")
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(8)

        head = QHBoxLayout()
        head.setSpacing(8)
        self.light = LinkLight()
        head.addWidget(self.light)
        title = QVBoxLayout()
        title.setSpacing(0)
        self.speed = label("—", "Title")
        title.addWidget(self.speed)
        self.note = label("", "Caption")
        title.addWidget(self.note)
        head.addLayout(title)
        head.addStretch()
        self.adapter = label("", "Caption")
        head.addWidget(self.adapter)
        root.addLayout(head)
        root.addWidget(hline())

        rates = QHBoxLayout()
        rates.setSpacing(14)
        self.rate_up = self._box(rates, "رفع الآن", "↑")
        self.rate_down = self._box(rates, "تنزيل الآن", "↓")
        root.addLayout(rates)

        totals = QHBoxLayout()
        totals.setSpacing(14)
        self.up = self._box(totals, "إجمالي الرفع", "↑")
        self.down = self._box(totals, "إجمالي التنزيل", "↓")
        self.total = self._box(totals, "الإجمالي", "Σ")
        root.addLayout(totals)

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

    def _box(self, row: QHBoxLayout, name: str, glyph: str) -> QLabel:
        box = QWidget()
        stack = QVBoxLayout(box)
        stack.setContentsMargins(0, 0, 0, 0)
        stack.setSpacing(1)
        caption_line, _ = self._line(f"{name} {glyph}", Colors.TEXT_MUTED, 11)
        value_line, value = self._line("—", Colors.TEXT_PRIMARY, 14)
        value.setMinimumWidth(78)
        stack.addLayout(caption_line)
        stack.addLayout(value_line)
        row.addWidget(box, 1)
        return value

    def set(self, host: dict, rates: dict | None = None):
        speed_text, tone, note = net_state(host.get("Net_Speed"))
        self.speed.setText(speed_text)
        self.note.setText(note)
        self.light.set_state(tone_color(tone), pulse=(tone == "danger"))
        self.adapter.setText(str(host.get("Net_Name") or ""))

        rates = rates or {}
        self.rate_up.setText(ltr(speed_rate(rates.get("up", 0))))
        self.rate_down.setText(ltr(speed_rate(rates.get("down", 0))))
        self.up.setText(ltr(traffic(host.get("Net_Upload"))))
        self.down.setText(ltr(traffic(host.get("Net_Download"))))
        self.total.setText(ltr(traffic(host.get("Net_Total"))))


class HardwareMonitor(Card):
    """Live telemetry panel; call set_host() with a hosts row."""

    def __init__(self, parent=None, compact: bool = False):
        super().__init__(parent, padding=16, spacing=10)
        self.host = {}
        self.compact = compact
        self._last_net = {}
        self._last_seen = None

        head = QHBoxLayout()
        head.setSpacing(8)
        self.device_name = label("اختر جهازاً", "Title")
        self.state = Pill("—", "muted")
        head.addWidget(self.device_name)
        head.addWidget(self.state)
        head.addStretch()
        self.stamp = label("", "Caption")
        head.addWidget(self.stamp)
        self.body.addLayout(head)

        self.device_line = label("—", "Caption")
        self.body.addWidget(self.device_line)
        self.body.addWidget(hline())

        grid = QGridLayout()
        grid.setHorizontalSpacing(26)
        grid.setVerticalSpacing(12)
        self.cpu = MetricTile("المعالج · الاستخدام")
        self.cpu_temp = MetricTile("حرارة المعالج", history=False)
        self.gpu = MetricTile("كارت الشاشة · الاستخدام")
        self.gpu_temp = MetricTile("حرارة الكارت", history=False)
        self.vram = MetricTile("ذاكرة الفيديو VRAM")
        self.ram = MetricTile("الذاكرة RAM")
        layout = (
            (self.cpu, 0, 0), (self.cpu_temp, 0, 1), (self.ram, 0, 2),
            (self.gpu, 1, 0), (self.gpu_temp, 1, 1), (self.vram, 1, 2),
        )
        for tile, row, column in layout:
            grid.addWidget(tile, row, column, 1, 1)
        for column in range(3):
            grid.setColumnStretch(column, 1)
        self.body.addLayout(grid)
        self.body.addWidget(hline())

        self.disk = DiskBlock()
        self.body.addWidget(self.disk)
        self.network = NetworkBlock()
        self.body.addWidget(self.network)

        self.footnote = label(" ", "Caption")
        self.footnote.setWordWrap(False)
        self.body.addWidget(self.footnote)
        if not compact:
            self.body.addStretch()

    # ── data ─────────────────────────────────────────────────────────────
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
        gpu_name = host.get("GPU_Name") or "كارت الشاشة غير معروف"
        address = host.get("IPAddress") or "—"
        self.device_line.setText(f"{gpu_name}  ·  {address}\u200f")

        cpu = _float(host.get("CPU_Usage"))
        cpu_temp = _float(host.get("CPU_Temp"))
        gpu = _float(host.get("GPU_Usage"))
        gpu_temp = _float(host.get("GPU_Temp"))

        self.cpu.set(
            f"{cpu:.0f}%", self._load_note(cpu) + "\u200f", cpu, load_tone(cpu), sample=cpu
        )
        self.cpu_temp.set(
            f"{cpu_temp:.0f}°C" if cpu_temp else "—",
            self._heat_note(cpu_temp, "المعالج") + "\u200f", cpu_temp if cpu_temp else None,
            heat_tone(cpu_temp), badge="بارد" if 0 < cpu_temp < 55 else "",
        )
        self.gpu.set(
            f"{gpu:.0f}%", self._load_note(gpu) + "\u200f", gpu, load_tone(gpu), sample=gpu
        )
        self.gpu_temp.set(
            f"{gpu_temp:.0f}°C" if gpu_temp else "—",
            self._heat_note(gpu_temp, "الكارت") + "\u200f", gpu_temp if gpu_temp else None,
            heat_tone(gpu_temp),
        )

        self._memory(host)
        self.disk.set(host)
        self.network.set(host, self._rates(host))
        self._footer(host)

    def _rates(self, host: dict) -> dict:
        """Bytes counters only grow, so the delta over time gives throughput."""
        now = datetime.now()
        key = host.get("HostId")
        upload = _float(host.get("Net_Upload"))
        download = _float(host.get("Net_Download"))
        previous = self._last_net.get(key)
        rates = {"up": 0.0, "down": 0.0}
        link = _float(host.get("Net_Speed"))
        ceiling = (link / 8) if link > 0 else 125.0  # Mbps -> MB/s
        if previous is not None:
            seconds = (now - previous["at"]).total_seconds()
            if seconds >= 0.25:
                rates["up"] = min(ceiling, max(0.0, (upload - previous["up"]) / seconds * 1024))
                rates["down"] = min(ceiling, max(0.0, (download - previous["down"]) / seconds * 1024))
        self._last_net[key] = {"up": upload, "down": download, "at": now}
        return rates

    @staticmethod
    def _load_note(percent: float) -> str:
        if percent >= 88:
            return "حمل مرتفع جدًا"
        if percent >= 70:
            return "حمل مرتفع"
        if percent >= 30:
            return "استخدام طبيعي"
        return "شبه خامل"

    @staticmethod
    def _heat_note(celsius: float, part: str) -> str:
        if not celsius:
            return f"لا يبلّغ {part} عن الحرارة"
        if celsius >= 85:
            return "حرارة حرجة — تحقق من التبريد"
        if celsius >= 70:
            return "حرارة مرتفعة"
        return f"حرارة {part} آمنة"

    def _memory(self, host: dict):
        vram_used = _float(host.get("VRAM_Used"))
        vram_total = _float(host.get("VRAM_Total"))
        if vram_total > 0:
            percent = vram_used / vram_total * 100
            self.vram.set(
                f"{vram_used:.1f} / {vram_total:.0f} GB",
                f"مستخدم {ltr(f'{percent:.0f}%')} من ذاكرة الكارت",
                percent, load_tone(percent), sample=percent,
            )
        else:
            self.vram.set("لا بيانات", "العميل لم يرسل ذاكرة الفيديو", None)

        ram_total = _float(host.get("RAM_Total"))
        ram_percent = _float(host.get("RAM_Usage"))
        speed = int(_float(host.get("RAM_Speed")))
        speed_note = f"  ·  {ltr(f'{speed} MHz')}" if speed else ""
        if ram_total > 0:
            used = ram_total * ram_percent / 100
            self.ram.set(
                f"{used:.1f} / {ram_total:.0f} GB",
                f"مستخدم {ltr(f'{ram_percent:.0f}%')}  ·  "
                f"متاح {ltr(f'{ram_total - used:.1f} GB')}{speed_note}",
                ram_percent, load_tone(ram_percent), sample=ram_percent,
            )
        else:
            self.ram.set(
                f"{ram_percent:.0f}%" if ram_percent else "لا بيانات",
                f"الحجم الكلي غير معروف{speed_note}", None,
            )

    def _footer(self, host: dict):
        self.stamp.setText(datetime.now().strftime("آخر قراءة %H:%M:%S"))
        uptime = int(_float(host.get("UptimeMinutes")))
        pieces = []
        if uptime:
            hours, minutes = divmod(uptime, 60)
            pieces.append(f"يعمل منذ {hours} ساعة و {minutes} دقيقة")
        if str(host.get("Disk_Health") or "").upper() in ("WARNING", "UNHEALTHY"):
            pieces.append("تحذير على صحة القرص")
        speed, tone, note = net_state(host.get("Net_Speed"))
        pieces.append(f"الشبكة: {ltr(speed)} ({note})")
        self.footnote.setText("  ·  ".join(pieces))


class HardwareDialog(QDialog):
    """Standalone monitor window for one machine."""

    def __init__(self, data, host: dict, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.data = data
        self.host_id = host.get("HostId")
        self.setWindowTitle(f"مراقبة العتاد — {host.get('HostName') or ''}")
        self.setMinimumSize(720, 660)

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(10)

        head = QHBoxLayout()
        head.setSpacing(8)
        head.addWidget(label("مراقبة العتاد", "Title"))
        head.addStretch()
        self.picker = QComboBox()
        self.picker.setMinimumWidth(160)
        for item in self.data.hosts():
            self.picker.addItem(str(item.get("HostName") or "PC"), item.get("HostId"))
        index = self.picker.findData(self.host_id)
        if index >= 0:
            self.picker.setCurrentIndex(index)
        self.picker.currentIndexChanged.connect(self._pick)
        head.addWidget(self.picker)

        self.interval = QComboBox()
        self.interval.addItem("تحديث كل ثانية", 1000)
        self.interval.addItem("تحديث كل 3 ثوان", 3000)
        self.interval.addItem("تحديث كل 10 ثوان", 10000)
        self.interval.setCurrentIndex(0)
        self.interval.currentIndexChanged.connect(self._set_interval)
        head.addWidget(self.interval)

        head.addWidget(icon_button("refresh", "تحديث", self.refresh, size=36, icon_size=20))
        head.addWidget(button("إغلاق", "ghost", self.accept, compact=True))
        root.addLayout(head)

        self.monitor = HardwareMonitor(compact=True)
        root.addWidget(self.monitor, 1)
        self.monitor.set_host(host)

        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self.refresh)
        self._timer.start()

    def _set_interval(self, _index: int):
        self._timer.setInterval(int(self.interval.currentData() or 1000))

    def _pick(self, _index: int):
        self.host_id = self.picker.currentData()
        self.setWindowTitle(f"مراقبة العتاد — {self.picker.currentText()}")
        self.monitor._last_net.clear()
        self.refresh()

    def refresh(self):
        for host in self.data.hosts():
            if host.get("HostId") == self.host_id:
                self.monitor.set_host(host)
                return
