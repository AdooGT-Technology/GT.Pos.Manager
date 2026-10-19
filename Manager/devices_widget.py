# -*- coding: utf-8 -*-
"""Devices page: the floor at a glance plus real remote actions."""

from __future__ import annotations

from datetime import datetime

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QMessageBox, QScrollArea,
    QVBoxLayout, QWidget,
)

from Manager.commands import CommandClient, describe
from Manager.hardware_overlay import HardwareDialog
from Manager.ui import (
    Bar, Card, EmptyState, Pill, SearchInput, Segmented, Toast,
    button, label,
)
from Manager.theme import Colors

BUSY_STATES = ("مشغول", "InUse", "Busy")


def is_busy(host: dict) -> bool:
    return str(host.get("Status")) in BUSY_STATES


class DeviceCard(Card):
    """One machine with its live numbers and the four usual controls."""

    def __init__(self, host: dict, on_action=None, on_open=None,
                 on_hardware=None, parent=None):
        super().__init__(parent, padding=14, spacing=8)
        self.host = host
        self.on_action = on_action
        self.on_open = on_open
        self.on_hardware = on_hardware
        self.setMinimumSize(236, 196)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        head = QHBoxLayout()
        self.name = label(str(host.get("HostName") or "PC"), "Title")
        self.state = Pill("—", "muted")
        head.addWidget(self.name)
        head.addStretch()
        head.addWidget(self.state)
        self.body.addLayout(head)

        self.user = label("—", "Muted")
        self.body.addWidget(self.user)

        self.cpu = self._meter("CPU")
        self.ram = self._meter("RAM")
        self.body.addWidget(self.cpu["row"])
        self.body.addWidget(self.ram["row"])

        self.meta = label("—", "Caption")
        self.body.addWidget(self.meta)

        actions = QHBoxLayout()
        actions.setSpacing(6)
        self.btn_lock = button("قفل", "ghost", lambda: self._act("LOCK"), compact=True)
        self.btn_unlock = button("فتح", "ghost", lambda: self._act("UNLOCK"), compact=True)
        self.btn_restart = button("ريستارت", "ghost", lambda: self._act("RESTART"), compact=True)
        self.btn_off = button("إيقاف", "danger", lambda: self._act("SHUTDOWN"), compact=True)
        for btn in (self.btn_lock, self.btn_unlock, self.btn_restart, self.btn_off):
            actions.addWidget(btn)
        actions.addStretch()
        self.body.addLayout(actions)

        self.hardware_btn = button(
            "مراقبة العتاد", "quiet", lambda: self._hardware(), compact=True
        )
        self.body.addWidget(self.hardware_btn)
        self.set_host(host)

    def _hardware(self):
        if self.on_hardware:
            self.on_hardware(self.host)

    def _meter(self, name: str):
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        title = label(name, "Caption")
        title.setFixedWidth(30)
        bar = Bar(0, height=4)
        value = label("0%", "Caption")
        value.setFixedWidth(32)
        value.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(title)
        layout.addWidget(bar, 1)
        layout.addWidget(value)
        return {"row": row, "bar": bar, "value": value}

    def _act(self, action: str):
        if self.on_action:
            self.on_action(self.host, action)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.on_open:
            self.on_open(self.host)
        super().mousePressEvent(event)

    def set_host(self, host: dict):
        self.host = host
        busy = is_busy(host)
        self.name.setText(str(host.get("HostName") or "PC"))
        self.state.setText("مشغول" if busy else "متاح")
        self.state.set_tone("warning" if busy else "success")
        self.user.setText(str(host.get("CurrentUser") or "لا يوجد لاعب"))
        cpu = float(host.get("CPU_Usage") or 0)
        ram = float(host.get("RAM_Usage") or 0)
        self.cpu["bar"].set_value(cpu)
        self.cpu["value"].setText(f"{cpu:.0f}%")
        self.ram["bar"].set_value(ram)
        self.ram["value"].setText(f"{ram:.0f}%")
        temp = float(host.get("GPU_Temp") or 0)
        net = int(float(host.get("Net_Speed") or 0))
        net_text = "شبكة مفقودة" if net <= 0 else f"شبكة {net}"
        self.meta.setText(
            f"{host.get('GPU_Name') or '—'}  ·  {temp:.0f}°  ·  {net_text}"
            f"  ·  {host.get('IPAddress') or '—'}"
        )
        self.btn_lock.setEnabled(True)
        self.btn_unlock.setEnabled(busy)


class DevicesWidget(QWidget):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.data = data
        self.navigate = None
        self.cards = {}
        self._columns = 4
        self._timer = QTimer(self)
        self._timer.setInterval(5000)
        self._timer.timeout.connect(self._refresh_values)
        self._build()
        QTimer.singleShot(0, self.reload)

    def set_navigator(self, navigate):
        self.navigate = navigate

    def _build(self):
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(14)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        self.search = SearchInput("ابحث برقم الجهاز أو اسم اللاعب")
        self.search.textChanged.connect(lambda _text: self.reload())
        toolbar.addWidget(self.search)

        self.filter = Segmented(
            [("all", "الكل"), ("busy", "مشغول"), ("idle", "متاح")], "all"
        )
        self.filter.changed.connect(lambda _key: self.reload())
        toolbar.addWidget(self.filter)
        toolbar.addStretch()

        toolbar.addWidget(button("تشغيل الأجهزة النائمة", "quiet", self._wake_all, compact=True))
        toolbar.addWidget(button("فتح كل الشاشات", "quiet", self._unlock_all, compact=True))
        toolbar.addWidget(button("مراقبة العتاد", "accent", self._open_hardware_monitor, compact=True))
        toolbar.addWidget(button("تحديث", "ghost", self.reload, compact=True))
        root.addLayout(toolbar)

        summary = QHBoxLayout()
        summary.setSpacing(18)
        self.summary_busy = label("—", "Muted")
        self.summary_idle = label("—", "Muted")
        self.summary_temp = label("—", "Muted")
        for widget in (self.summary_busy, self.summary_idle, self.summary_temp):
            summary.addWidget(widget)
        summary.addStretch()
        root.addLayout(summary)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        host = QWidget()
        self.grid = QGridLayout(host)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(12)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(host)
        root.addWidget(scroll, 1)

        self.empty = EmptyState(
            "لا توجد أجهزة مطابقة",
            "جرّب فلتراً آخر أو امسح كلمة البحث.",
        )
        root.addWidget(self.empty)
        self.empty.hide()

    # ── data ─────────────────────────────────────────────────────────────
    def on_shown(self):
        self.reload()
        self._timer.start()

    def showEvent(self, event):
        self._timer.start()
        super().showEvent(event)

    def hideEvent(self, event):
        self._timer.stop()
        super().hideEvent(event)

    def _hosts(self):
        hosts = self.data.hosts()
        mode = self.filter.current
        if mode == "busy":
            hosts = [h for h in hosts if is_busy(h)]
        elif mode == "idle":
            hosts = [h for h in hosts if not is_busy(h)]
        needle = self.search.text().strip().lower()
        if needle:
            hosts = [
                h for h in hosts
                if needle in str(h.get("HostName", "")).lower()
                or needle in str(h.get("CurrentUser", "")).lower()
                or needle in str(h.get("IPAddress", ""))
            ]
        return hosts

    def reload(self):
        hosts = self._hosts()
        all_hosts = self.data.hosts()
        busy = sum(1 for host in all_hosts if is_busy(host))
        temps = [float(host.get("GPU_Temp") or 0) for host in all_hosts if host.get("GPU_Temp")]
        self.summary_busy.setText(f"مشغول {busy} من {len(all_hosts)}")
        self.summary_idle.setText(f"متاح {len(all_hosts) - busy}")
        self.summary_temp.setText(f"متوسط حرارة الكرت {sum(temps) / len(temps):.0f}°" if temps else "")

        wanted = {host.get("HostId") for host in hosts}
        for host_id in list(self.cards):
            if host_id not in wanted:
                card = self.cards.pop(host_id)
                self.grid.removeWidget(card)
                card.deleteLater()

        for index, host in enumerate(hosts):
            host_id = host.get("HostId")
            card = self.cards.get(host_id)
            if card is None:
                card = DeviceCard(
                    host, on_action=self._run_action, on_open=self._open_studio,
                    on_hardware=self._open_hardware_monitor,
                )
                self.cards[host_id] = card
            else:
                card.set_host(host)
            row, col = divmod(index, self._columns)
            self.grid.addWidget(card, row, col)

        self.empty.setVisible(not hosts)

    def _refresh_values(self):
        for host in self._hosts():
            card = self.cards.get(host.get("HostId"))
            if card is not None:
                card.set_host(host)

    def resizeEvent(self, event):
        width = event.size().width()
        columns = max(2, min(5, width // 280))
        if columns != self._columns:
            self._columns = columns
            self.reload()
        super().resizeEvent(event)

    # ── actions ──────────────────────────────────────────────────────────
    def _run_action(self, host: dict, action: str):
        name = host.get("HostName", "الجهاز")
        if action in ("SHUTDOWN", "RESTART"):
            answer = QMessageBox.question(
                self, describe(action),
                f"{describe(action)} على {name}؟",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
        ok, message = CommandClient().send(
            f"DEVICE_{action}",
            {"host": name, "host_id": host.get("HostId"), "issued_by": "manager"},
        )
        self._log(host, action, ok)
        if ok:
            Toast(self, f"{describe(action)} — {name}", "success")
            self.reload()
        else:
            Toast(self, f"لم يُنفَّذ: {message}", "warning", 3200)

    def _open_hardware_monitor(self, host=None):
        if host is None:
            hosts = self._hosts() or self.data.hosts()
            if not hosts:
                Toast(self, "لا يوجد جهاز لعرض قياساته", "warning")
                return
            host = hosts[0]
        HardwareDialog(self.data, host, self).exec()

    def _wake_all(self):
        sleeping = [h for h in self.data.hosts() if not is_busy(h)]
        if not sleeping:
            Toast(self, "كل الأجهزة تعمل بالفعل", "accent")
            return
        ok, message = CommandClient().send("DEVICE_WAKE", {"hosts": [h.get("HostName") for h in sleeping]})
        Toast(
            self,
            f"أُرسل التشغيل إلى {len(sleeping)} جهاز" if ok else f"لم يُنفَّذ: {message}",
            "success" if ok else "warning",
        )

    def _unlock_all(self):
        busy = [h for h in self.data.hosts() if is_busy(h)]
        if not busy:
            Toast(self, "لا توجد أجهزة مقفولة", "accent")
            return
        ok, message = CommandClient().send(
            "DEVICE_UNLOCK_ALL", {"hosts": [h.get("HostName") for h in busy]}
        )
        Toast(
            self,
            f"فُتح {len(busy)} جهاز" if ok else f"لم يُنفَّذ: {message}",
            "success" if ok else "warning",
        )

    def _open_studio(self, host: dict):
        if self.navigate:
            self.navigate("studio")

    def _log(self, host: dict, action: str, ok: bool):
        self.data.execute(
            "INSERT INTO ActivityLog (LogType, UserName, Description) VALUES (?, ?, ?)",
            ("device", "manager", f"{describe(action)} — {host.get('HostName')} — {'تم' if ok else 'فشل'}"),
        )
