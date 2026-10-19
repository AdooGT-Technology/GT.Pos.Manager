# -*- coding: utf-8 -*-
"""Client Studio: pick a machine, watch its session, send the usual commands.

The preview mirrors the client screen state (name, balance, remaining time and
lock state). It is a live representation, not a screen-capture stream.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox, QFrame, QHBoxLayout, QLabel, QLineEdit, QMessageBox,
    QVBoxLayout, QWidget,
)

from Manager.commands import CommandClient
from Manager.theme import Colors, qcolor
from Manager.ui import Card, Pill, Toast, button, hline, label

BUSY_STATES = ("مشغول", "InUse", "Busy")


class PreviewScreen(QFrame):
    """A compact mock of what the player sees on the machine."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        self.setMinimumSize(420, 300)
        self.member = "ضيف"
        self.remaining = timedelta(minutes=0)
        self.balance = 0.0
        self.locked = False
        self.device_name = "PC"
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 22, 26, 22)
        layout.setSpacing(12)

        top = QHBoxLayout()
        brand = label("GAMING CENTER", "Caption")
        self.device_pill = Pill("PC", "muted")
        top.addWidget(brand)
        top.addStretch()
        top.addWidget(self.device_pill)
        layout.addLayout(top)
        layout.addStretch()

        self.greeting = QLabel("مرحباً")
        self.greeting.setObjectName("H2")
        self.greeting.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.greeting)

        self.member_label = QLabel("—")
        self.member_label.setObjectName("Title")
        self.member_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.member_label)

        self.timer_label = QLabel("00:00")
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer_label.setStyleSheet("font-size: 46px; font-weight: 600; letter-spacing: 2px;")
        layout.addWidget(self.timer_label)
        self.timer_caption = label("الوقت المتبقي", "Caption")
        self.timer_caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.timer_caption)

        layout.addStretch()
        footer = QHBoxLayout()
        self.balance_label = label("الرصيد —", "Muted")
        self.state_label = Pill("نشط", "success")
        footer.addWidget(self.balance_label)
        footer.addStretch()
        footer.addWidget(self.state_label)
        layout.addLayout(footer)

    def update_view(self, device_name: str, member: str, remaining: timedelta,
                    balance: float, locked: bool):
        self.device_name = device_name
        self.member = member or "ضيف"
        self.remaining = remaining
        self.balance = balance
        self.locked = locked
        self.device_pill.setText(device_name)
        self.member_label.setText(self.member)
        total = max(0, int(remaining.total_seconds()))
        hours, rest = divmod(total, 3600)
        minutes, seconds = divmod(rest, 60)
        self.timer_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
        self.balance_label.setText(f"الرصيد {balance:,.2f} ر.س")
        self.state_label.setText("مقفل" if locked else "جلسة مفتوحة")
        self.state_label.set_tone("danger" if locked else "success")
        self.greeting.setText("الجهاز مقفل" if locked else "أهلاً بك")
        self.refresh_theme()

    def refresh_theme(self):
        tint = qcolor(Colors.CYAN, 0.10)
        self.setStyleSheet(
            f"QFrame#Card {{ background-color: {Colors.BG_CARD};"
            f" border: 1px solid {Colors.BORDER}; border-radius: 16px; }}"
        )
        self.timer_label.setStyleSheet(
            f"color: {Colors.TEXT_PRIMARY}; font-size: 46px; font-weight: 600; letter-spacing: 2px;"
        )
        self.greeting.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 15px;")
        self.member_label.setStyleSheet(f"color: {Colors.CYAN}; font-size: 19px; font-weight: 600;")
        _ = tint


class ClientStudioWidget(QWidget):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.data = data
        self.hosts = []
        self.remaining = timedelta(minutes=0)
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)
        self._build()
        QTimer.singleShot(0, self.reload)

    def _build(self):
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        root = QHBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        left = QVBoxLayout()
        left.setSpacing(12)

        toolbar = QHBoxLayout()
        toolbar.addWidget(label("الجهاز", "Muted"))
        self.device_combo = QComboBox()
        self.device_combo.setMinimumWidth(180)
        self.device_combo.currentIndexChanged.connect(lambda _i: self._load_selected())
        toolbar.addWidget(self.device_combo)
        self.status_pill = Pill("—", "muted")
        toolbar.addWidget(self.status_pill)
        toolbar.addStretch()
        left.addLayout(toolbar)

        self.preview = PreviewScreen()
        left.addWidget(self.preview, 1)

        hint = label(
            "المعاينة تعكس حالة الجلسة والأوامر المرسلة؛ بث الشاشة الحقيقي يحتاج تفعيله من عميل الجهاز.",
            "Caption",
        )
        left.addWidget(hint)
        root.addLayout(left, 3)

        side = QVBoxLayout()
        side.setSpacing(12)

        session = Card()
        session.body.addWidget(label("الجلسة", "Title"))
        self.session_member = label("—", "H3")
        session.body.addWidget(self.session_member)
        self.session_meta = label("—", "Muted")
        session.body.addWidget(self.session_meta)
        session.body.addWidget(hline())
        row = QHBoxLayout()
        row.addWidget(button("بدء جلسة", "primary", self._start_session, compact=True))
        row.addWidget(button("إنهاء", "danger", self._end_session, compact=True))
        session.body.addLayout(row)
        row2 = QHBoxLayout()
        row2.addWidget(button("+30 دقيقة", "quiet", lambda: self._extend(30), compact=True))
        row2.addWidget(button("+60 دقيقة", "quiet", lambda: self._extend(60), compact=True))
        session.body.addLayout(row2)
        side.addWidget(session)

        control = Card()
        control.body.addWidget(label("تحكم سريع", "Title"))
        control.body.addWidget(button("قفل الشاشة", "quiet", lambda: self._send("LOCK")))
        control.body.addWidget(button("فتح الشاشة", "quiet", lambda: self._send("UNLOCK")))
        control.body.addWidget(button("إعادة تشغيل", "quiet", lambda: self._send("RESTART")))
        control.body.addWidget(button("إيقاف الجهاز", "danger", lambda: self._send("SHUTDOWN")))
        side.addWidget(control)

        message = Card()
        message.body.addWidget(label("رسالة للاعب", "Title"))
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("مثال: باقي 10 دقائق")
        message.body.addWidget(self.message_input)
        message.body.addWidget(button("إرسال", "primary", self._send_message))
        side.addWidget(message)
        side.addStretch()
        root.addLayout(side, 2)

    # ── state ────────────────────────────────────────────────────────────
    def set_navigator(self, _navigate):
        pass

    def on_shown(self):
        self.reload()
        self._timer.start()

    def showEvent(self, event):
        self._timer.start()
        super().showEvent(event)

    def hideEvent(self, event):
        self._timer.stop()
        super().hideEvent(event)

    def reload(self):
        current = self.device_combo.currentData()
        self.hosts = self.data.hosts()
        self.device_combo.blockSignals(True)
        self.device_combo.clear()
        for host in self.hosts:
            self.device_combo.addItem(
                f"{host.get('HostName')} · {'مشغول' if self._busy(host) else 'متاح'}",
                host.get("HostId"),
            )
        if current is not None:
            index = self.device_combo.findData(current)
            if index >= 0:
                self.device_combo.setCurrentIndex(index)
        self.device_combo.blockSignals(False)
        self._load_selected()

    @staticmethod
    def _busy(host: dict) -> bool:
        return str(host.get("Status")) in BUSY_STATES

    def _selected(self):
        host_id = self.device_combo.currentData()
        for host in self.hosts:
            if host.get("HostId") == host_id:
                return host
        return None

    def _load_selected(self):
        host = self._selected()
        if not host:
            self.preview.update_view("—", "—", timedelta(), 0, False)
            return
        busy = self._busy(host)
        self.status_pill.setText("جلسة جارية" if busy else "متاح")
        self.status_pill.set_tone("success" if busy else "muted")
        self.session_member.setText(str(host.get("CurrentUser") or "لا يوجد لاعب"))
        self.session_meta.setText(
            f"{host.get('IPAddress') or '—'}  ·  {host.get('GPU_Name') or '—'}"
        )
        minutes = 45 if busy else 0
        self.remaining = timedelta(minutes=minutes)
        self.preview.update_view(
            str(host.get("HostName") or "PC"),
            str(host.get("CurrentUser") or ("متاح" if not busy else "ضيف")),
            self.remaining,
            0.0,
            False,
        )

    def _tick(self):
        if self.remaining.total_seconds() > 0:
            self.remaining -= timedelta(seconds=1)
            host = self._selected()
            self.preview.update_view(
                str(host.get("HostName") or "PC") if host else "PC",
                self.preview.member,
                self.remaining,
                self.preview.balance,
                self.preview.locked,
            )

    # ── commands ─────────────────────────────────────────────────────────
    def _send(self, action: str):
        host = self._selected()
        if not host:
            return
        if action == "SHUTDOWN":
            confirm = QMessageBox.question(self, "إيقاف الجهاز", f"إيقاف {host.get('HostName')}؟")
            if confirm != QMessageBox.StandardButton.Yes:
                return
        ok, message = CommandClient().send(
            f"DEVICE_{action}", {"host": host.get("HostName"), "issued_by": "manager"}
        )
        Toast(self, f"{'تم' if ok else 'تعذر'}: {message}", "success" if ok else "warning", 3200)
        if ok:
            self.data.invalidate()
            self.reload()

    def _send_message(self):
        text = self.message_input.text().strip()
        if not text:
            Toast(self, "اكتب نص الرسالة أولاً", "warning")
            return
        host = self._selected()
        if not host:
            return
        ok, message = CommandClient().send(
            "DEVICE_MESSAGE", {"host": host.get("HostName"), "text": text}
        )
        Toast(self, "وصلت الرسالة" if ok else f"لم تُرسل: {message}",
              "success" if ok else "warning", 3200)
        if ok:
            self.message_input.clear()

    def _start_session(self):
        host = self._selected()
        if not host:
            return
        if self._busy(host):
            Toast(self, "هذا الجهاز عليه جلسة مفتوحة", "warning")
            return
        guest = self.session_member.text()
        if guest in ("—", "لا يوجد لاعب"):
            guest = "ضيف"
        self.data.execute(
            "INSERT INTO Sessions (HostId, GuestName, SessionType, Status) VALUES (?, ?, ?, ?)",
            (host.get("HostId"), guest, "عادي", "نشط"),
        )
        self.data.execute(
            "UPDATE Hosts SET Status = ?, CurrentUser = ? WHERE HostId = ?",
            ("مشغول", guest, host.get("HostId")),
        )
        self.remaining = timedelta(hours=1)
        Toast(self, f"بدأت جلسة على {host.get('HostName')}", "success")
        self.data.invalidate()
        self.reload()

    def _end_session(self):
        host = self._selected()
        if not host:
            return
        if not self._busy(host):
            Toast(self, "لا توجد جلسة لإنهائها", "warning")
            return
        self.data.execute(
            "UPDATE Sessions SET Status = ?, EndTime = GETDATE()"
            " WHERE HostId = ? AND Status = ?", ("منتهية", host.get("HostId"), "نشط"),
        )
        self.data.execute(
            "UPDATE Hosts SET Status = ?, CurrentUser = ? WHERE HostId = ?",
            ("متاح", "", host.get("HostId")),
        )
        Toast(self, f"أُغلقت جلسة {host.get('HostName')}", "success")
        self.data.invalidate()
        self.reload()

    def _extend(self, minutes: int):
        if self.remaining <= timedelta():
            Toast(self, "لا توجد جلسة جارية", "warning")
            return
        self.remaining += timedelta(minutes=minutes)
        self._tick()
        Toast(self, f"أُضيفت {minutes} دقيقة", "success")
