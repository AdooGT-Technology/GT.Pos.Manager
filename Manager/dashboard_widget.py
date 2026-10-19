# -*- coding: utf-8 -*-
"""Overview page: today's numbers, the floor, and one device in focus."""

from __future__ import annotations

from datetime import datetime

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget,
)

from Manager.theme import Colors
from Manager.ui import (
    Bar, Card, Kpi, Pill, Segmented, StatLine, button, hline, label,
)


def _money(value: float) -> str:
    return f"{value:,.2f}"


class DeviceRow(QFrame):
    """One line per machine: who is on it and how hard it is working."""

    def __init__(self, on_focus=None, on_open=None, parent=None):
        super().__init__(parent)
        self.setObjectName("Inset")
        self.host = {}
        self.on_focus = on_focus
        self.on_open = on_open
        self.setFixedHeight(56)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        self.name = label("—", "Body")
        self.name.setFixedWidth(78)
        self.user = label("", "Muted")
        self.user.setFixedWidth(110)
        self.cpu = Bar(0, height=5)
        self.cpu.setFixedWidth(96)
        self.cpu_text = label("0%", "Caption")
        self.cpu_text.setFixedWidth(34)
        self.temp = label("—", "Caption")
        self.temp.setFixedWidth(64)
        self.state = Pill("—", "muted")
        self.open_btn = button("فتح", "ghost", compact=True)
        self.open_btn.setFixedWidth(52)

        layout.addWidget(self.name)
        layout.addWidget(self.user)
        layout.addWidget(self.cpu)
        layout.addWidget(self.cpu_text)
        layout.addWidget(self.temp)
        layout.addStretch()
        layout.addWidget(self.state)
        layout.addWidget(self.open_btn)
        self.open_btn.clicked.connect(self._open)

    def _open(self):
        if self.on_open:
            self.on_open(self.host)

    def mousePressEvent(self, _event):
        if self.on_focus:
            self.on_focus(self.host)

    def set_host(self, host: dict):
        self.host = host
        busy = str(host.get("Status")) in ("مشغول", "InUse", "Busy")
        name = str(host.get("HostName") or f"PC-{host.get('HostNumber', 0):02d}")
        self.name.setText(name)
        self.user.setText(str(host.get("CurrentUser") or ("متاح الآن" if not busy else "بدون اسم")))
        cpu = float(host.get("CPU_Usage") or 0)
        self.cpu.set_value(cpu)
        self.cpu_text.setText(f"{cpu:.0f}%")
        gpu_temp = float(host.get("GPU_Temp") or 0)
        cpu_temp = float(host.get("CPU_Temp") or 0)
        if gpu_temp:
            self.temp.setText(f"{gpu_temp:.0f}° GPU")
        elif cpu_temp:
            self.temp.setText(f"{cpu_temp:.0f}° CPU")
        else:
            self.temp.setText("—")
        self.state.setText("مشغول" if busy else "متاح")
        self.state.set_tone("warning" if busy else "success")
        self.open_btn.setText("تحكم")
        self.open_btn.setVisible(True)


class DashboardWidget(QWidget):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.data = data
        self.navigate = None
        self._rows = {}
        self._focus_id = None
        self._timer = QTimer(self)
        self._timer.setInterval(3000)
        self._timer.timeout.connect(self._tick)

        self._build()
        QTimer.singleShot(0, self.reload)

    # ── layout ───────────────────────────────────────────────────────────
    def set_navigator(self, navigate):
        self.navigate = navigate

    def _build(self):
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(14)

        kpis = QHBoxLayout()
        kpis.setSpacing(12)
        self.kpi_busy = Kpi("أجهزة مشغولة", "—", "من إجمالي الأجهزة")
        self.kpi_idle = Kpi("أجهزة جاهزة", "—", "جاهزة للاستقبال")
        self.kpi_revenue = Kpi("إيراد اليوم", "—", "يشمل المبيعات والجلسات")
        self.kpi_members = Kpi("أعضاء مسجلون", "—", "حسابات نشطة")
        for card in (self.kpi_busy, self.kpi_idle, self.kpi_revenue, self.kpi_members):
            kpis.addWidget(card, 1)
        root.addLayout(kpis)

        content = QHBoxLayout()
        content.setSpacing(14)

        floor = Card()
        floor_head = QHBoxLayout()
        floor_head.addWidget(label("أجهزة الصالة", "Title"))
        floor_head.addStretch()
        self.filter = Segmented(
            [("all", "الكل"), ("busy", "مشغول"), ("idle", "متاح")], "all"
        )
        self.filter.changed.connect(lambda _key: self.reload())
        floor_head.addWidget(self.filter)
        floor_head.addWidget(button("إدارة الأجهزة", "ghost", self._open_devices, compact=True))
        floor.body.addLayout(floor_head)

        header = QWidget()
        header_row = QHBoxLayout(header)
        header_row.setContentsMargins(12, 0, 12, 0)
        header_row.setSpacing(12)
        name_head = label("الجهاز", "Caption")
        name_head.setFixedWidth(78)
        user_head = label("اللاعب", "Caption")
        user_head.setFixedWidth(110)
        cpu_head = label("المعالج", "Caption")
        cpu_head.setFixedWidth(96)
        pct_head = label("", "Caption")
        pct_head.setFixedWidth(34)
        temp_head = label("الحرارة", "Caption")
        temp_head.setFixedWidth(64)
        header_row.addWidget(name_head)
        header_row.addWidget(user_head)
        header_row.addWidget(cpu_head)
        header_row.addWidget(pct_head)
        header_row.addWidget(temp_head)
        header_row.addStretch()
        state_head = label("الحالة", "Caption")
        state_head.setFixedWidth(70)
        header_row.addWidget(state_head)
        floor.body.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        host = QWidget()
        self.rows_layout = QVBoxLayout(host)
        self.rows_layout.setContentsMargins(0, 0, 0, 0)
        self.rows_layout.setSpacing(6)
        self.rows_layout.addStretch()
        scroll.setWidget(host)
        floor.body.addWidget(scroll, 1)
        content.addWidget(floor, 3)

        side = QVBoxLayout()
        side.setSpacing(14)

        self.detail = Card()
        head = QHBoxLayout()
        self.detail_name = label("—", "Title")
        self.detail_state = Pill("—", "muted")
        head.addWidget(self.detail_name)
        head.addStretch()
        head.addWidget(self.detail_state)
        self.detail.body.addLayout(head)
        self.detail_user = label("اختر جهازاً من القائمة", "Muted")
        self.detail.body.addWidget(self.detail_user)
        self.detail.body.addWidget(hline())
        self.stat_cpu = StatLine("المعالج", "—", 0)
        self.stat_gpu = StatLine("كارت الشاشة", "—", 0)
        self.stat_ram = StatLine("الذاكرة", "—", 0)
        self.stat_disk = StatLine("القرص", "—", 0)
        for stat in (self.stat_cpu, self.stat_gpu, self.stat_ram, self.stat_disk):
            self.detail.body.addWidget(stat)
        self.detail.tail = label("—", "Caption")
        self.detail.body.addWidget(self.detail.tail)
        detail_actions = QHBoxLayout()
        detail_actions.setSpacing(6)
        detail_actions.addWidget(
            button("فتح الاستوديو", "quiet", self._open_studio, compact=True)
        )
        detail_actions.addWidget(
            button("مراقبة العتاد", "accent", self._open_hardware, compact=True)
        )
        self.detail.body.addLayout(detail_actions)
        side.addWidget(self.detail)

        actions = Card()
        actions.body.addWidget(label("إجراءات سريعة", "Title"))
        actions.body.addWidget(button("بيع سريع", "quiet", lambda: self._go("pos")))
        actions.body.addWidget(button("إيداع رصيد", "quiet", lambda: self._go("wallet")))
        actions.body.addWidget(button("إضافة لعبة", "quiet", lambda: self._go("library")))
        side.addWidget(actions)
        side.addStretch()
        content.addLayout(side, 2)
        root.addLayout(content, 1)

        self.footer = label("آخر تحديث: —", "Caption")
        root.addWidget(self.footer)

    # ── data ─────────────────────────────────────────────────────────────
    def on_shown(self):
        self.reload()
        self._timer.start()

    def hideEvent(self, event):
        self._timer.stop()
        super().hideEvent(event)

    def showEvent(self, event):
        self._timer.start()
        super().showEvent(event)

    def _tick(self):
        self._update_device_values()
        self.reload(stats_only=True)

    def reload(self, stats_only: bool = False):
        self._update_kpis()
        if not stats_only:
            self._rebuild_rows()
        self._update_device_values()
        self.footer.setText("آخر تحديث " + datetime.now().strftime("%H:%M:%S"))

    def _update_kpis(self):
        stats = self.data.today_stats()
        self.kpi_busy.set_value(str(stats["hosts_busy"]), f"من {stats['hosts_total']} جهاز")
        self.kpi_idle.set_value(str(stats["hosts_idle"]), "جاهزة للاستقبال")
        self.kpi_revenue.set_value(f"{_money(stats['revenue'])} ر.س",
                                   f"{stats['orders']} طلب اليوم" if stats["orders"] else "شامل الجلسات")
        self.kpi_members.set_value(str(stats["members"]), "حساب مسجل")

    def _visible_hosts(self):
        hosts = self.data.hosts()
        mode = self.filter.current
        if mode == "busy":
            hosts = [h for h in hosts if str(h.get("Status")) in ("مشغول", "InUse", "Busy")]
        elif mode == "idle":
            hosts = [h for h in hosts if str(h.get("Status")) not in ("مشغول", "InUse", "Busy")]
        return hosts

    def _rebuild_rows(self):
        hosts = self._visible_hosts()
        existing = list(self._rows.values())
        if len(existing) == len(hosts):
            for row, host in zip(existing, hosts):
                row.set_host(host)
            return
        for row in existing:
            self.rows_layout.removeWidget(row)
            row.deleteLater()
        self._rows = {}
        for host in hosts:
            row = DeviceRow(on_focus=self._focus, on_open=self._open_device)
            row.set_host(host)
            self.rows_layout.insertWidget(self.rows_layout.count() - 1, row)
            self._rows[host.get("HostId")] = row
        if hosts and self._focus_id not in self._rows:
            self._focus(hosts[0])
        if not hosts:
            self.detail_user.setText("لا توجد أجهزة بهذا الفلتر")

    def _update_device_values(self):
        for host in self._visible_hosts():
            row = self._rows.get(host.get("HostId"))
            if row is not None:
                row.set_host(host)
        focus = self._current_focus()
        if focus:
            self._paint_detail(focus)

    def _current_focus(self):
        if not self._rows:
            return None
        if self._focus_id in self._rows:
            return self._rows[self._focus_id].host
        return None

    def _focus(self, host: dict):
        self._focus_id = host.get("HostId")
        self._paint_detail(host)

    def _paint_detail(self, host: dict):
        busy = str(host.get("Status")) in ("مشغول", "InUse", "Busy")
        focus_id = host.get("HostId")
        for host_id, row in self._rows.items():
            selected = host_id == focus_id
            row.setStyleSheet(
                f"QFrame#Inset {{ background-color: {Colors.BG_CARD_LIGHT};"
                f" border: 1px solid {Colors.CYAN if selected else 'transparent'};"
                f" border-radius: 8px; }}"
            )
        self.detail_name.setText(str(host.get("HostName") or "—"))
        self.detail_state.setText("مشغول" if busy else "متاح")
        self.detail_state.set_tone("warning" if busy else "success")
        self.detail_user.setText(
            f"{host.get('CurrentUser') or 'لا يوجد لاعب'}"
            f"  ·  {host.get('IPAddress') or '—'}"
        )
        cpu = float(host.get("CPU_Usage") or 0)
        gpu = float(host.get("GPU_Usage") or 0)
        ram = float(host.get("RAM_Usage") or 0)
        disk = float(host.get("Disk_Usage") or 0)
        self.stat_cpu.set_value(f"{cpu:.0f}%  ·  حرارة {float(host.get('CPU_Temp') or 0):.0f}°", cpu)
        self.stat_gpu.set_value(f"{gpu:.0f}%  ·  حرارة {float(host.get('GPU_Temp') or 0):.0f}°", gpu)
        self.stat_ram.set_value(f"{ram:.0f}% من {int(host.get('RAM_Total') or 0)}GB", ram)
        self.stat_disk.set_value(f"{disk:.0f}% مستخدم", disk)
        self.detail.tail.setText(str(host.get("GPU_Name") or "—"))

    def _open_device(self, host: dict):
        if self.navigate:
            self.navigate("devices")

    def _open_devices(self):
        self._go("devices")

    def _open_hardware(self):
        from Manager.hardware_overlay import HardwareDialog
        host = self._current_focus()
        if host is None:
            return
        HardwareDialog(self.data, host, self).exec()

    def _open_studio(self):
        self._go("studio")

    def _go(self, key: str):
        if self.navigate:
            self.navigate(key)
