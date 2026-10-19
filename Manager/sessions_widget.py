# -*- coding: utf-8 -*-
"""Live sessions page: who is playing, what it costs, and when time runs out."""

from __future__ import annotations

from datetime import datetime

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QComboBox, QDialog, QHBoxLayout, QMessageBox, QSpinBox, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)

from Manager.billing import BillingCatalog, format_minutes
from Manager.hardware_overlay import HardwareDialog
from Manager.sessions import SessionEngine
from Manager.theme import Colors
from Manager.ui import (
    Bar, Card, FormDialog, Pill, SearchInput, Segmented, Toast, button, hline, label,
)


class StartSessionDialog(FormDialog):
    """Pick a host, a player and how the time is paid for."""

    def __init__(self, engine: SessionEngine, hosts, members, parent=None, preselected=None):
        super().__init__("بدء جلسة", "اختر الجهاز واللاعب وطريقة احتساب الوقت.", parent, width=480)
        self.engine = engine
        self.members = members

        self.host_combo = QComboBox()
        for host in hosts:
            self.host_combo.addItem(
                f"{host.get('HostName')} · {host.get('HostGroup') or 'أجهزة PC'}", host
            )
        if preselected:
            index = self.host_combo.findText(
                f"{preselected.get('HostName')} · {preselected.get('HostGroup') or 'أجهزة PC'}"
            )
            if index >= 0:
                self.host_combo.setCurrentIndex(index)
        self.add_field("الجهاز", self.host_combo)

        self.member_combo = QComboBox()
        self.member_combo.addItem("ضيف", None)
        for member in members:
            self.member_combo.addItem(
                f"{member.get('FullName')} · {format_minutes(member.get('PurchasedMinutes') or 0)}"
                f" · رصيد {float(member.get('Balance') or 0):,.0f}",
                member,
            )
        self.add_field("اللاعب", self.member_combo)

        self.mode = Segmented(
            [("deposit", "رصيد"), ("fixed", "وقت ثابت"), ("offer", "عرض")], "deposit"
        )
        self.add_field("طريقة الدفع", self.mode)

        self.minutes = QSpinBox()
        self.minutes.setRange(15, 720)
        self.minutes.setSingleStep(15)
        self.minutes.setValue(60)
        self.minutes.setSuffix(" دقيقة")
        self.add_field("الوقت المشترى", self.minutes)

        self.offer_combo = QComboBox()
        for offer in BillingCatalog(engine.data).offers():
            self.offer_combo.addItem(
                f"{offer.get('name')} · {offer.get('minutes')} د · {offer.get('price')} ر.س",
                offer,
            )
        self.add_field("عرض الوقت (اختياري)", self.offer_combo)

        self.hint = label("", "Caption")
        self.root.insertWidget(self.root.count() - 1, self.hint)
        self.mode.changed.connect(lambda _k: self._sync_mode())
        self.member_combo.currentIndexChanged.connect(lambda _i: self._preview())
        self.host_combo.currentIndexChanged.connect(lambda _i: self._preview())
        self.offer_combo.currentIndexChanged.connect(lambda _i: self._pick_offer())
        self._sync_mode()
        self._preview()

    def _pick_offer(self):
        offer = self.offer_combo.currentData()
        if not offer:
            return
        self.mode.select("offer", emit=False)
        self.minutes.setValue(int(offer.get("minutes") or 60))
        self._sync_mode()

    def _sync_mode(self):
        mode = self.mode.current
        paid = mode in ("fixed", "offer")
        self.minutes.setEnabled(paid)
        self.offer_combo.setEnabled(mode == "offer")
        self._preview()

    def _rate(self):
        host = self.host_combo.currentData() or {}
        member = self.member_combo.currentData() or {}
        return self.engine.catalog.rate_for(
            member.get("MemberGroup") or "زائر", host.get("HostGroup") or "أجهزة PC"
        )

    def _preview(self):
        rate = self._rate()
        mode = self.mode.current
        if mode == "deposit":
            text = (
                f"سيُحتسب {rate['hourly']:.2f} ر.س/ساعة من رصيد اللاعب "
                f"({rate['profile']}{' · ' + rate['window'] if rate['window'] else ''})."
            )
        else:
            minutes = self.minutes.value()
            price = self.engine.catalog.cost(minutes, rate["hourly"])
            text = f"{minutes} دقيقة = {price:,.2f} ر.س · {rate['profile']}"
        self.hint.setText(text)

    def values(self):
        host = self.host_combo.currentData() or {}
        member = self.member_combo.currentData()
        mode = self.mode.current
        minutes = self.minutes.value() if mode in ("fixed", "offer") else 0
        amount = self.engine.catalog.cost(minutes, self._rate()["hourly"]) if minutes else 0
        if mode == "offer" and self.offer_combo.currentData():
            amount = float(self.offer_combo.currentData().get("price") or amount)
        return host, member, mode, minutes, amount


class SessionRow(QWidget):
    """Placeholder kept for future custom row rendering."""


class SessionsWidget(QWidget):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.data = data
        self.engine = SessionEngine(data)
        self.navigate = None
        self.selected_id = None
        self.rows = []
        self._build()
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)
        QTimer.singleShot(0, self.reload)

    def set_navigator(self, navigate):
        self.navigate = navigate

    # ── layout ───────────────────────────────────────────────────────────
    def _build(self):
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(12)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        self.search = SearchInput("ابحث بالجهاز أو اسم اللاعب")
        self.search.textChanged.connect(lambda _t: self.reload())
        toolbar.addWidget(self.search)
        self.filter = Segmented(
            [("all", "الكل"), ("deposit", "رصيد"), ("fixed", "وقت ثابت"), ("offer", "عروض")],
            "all",
        )
        self.filter.changed.connect(lambda _k: self.reload())
        toolbar.addWidget(self.filter)
        toolbar.addStretch()
        toolbar.addWidget(button("بدء جلسة", "primary", self._start, compact=True))
        toolbar.addWidget(button("إيقاف المحدد", "danger", self._stop_selected, compact=True))
        toolbar.addWidget(button("تحديث", "ghost", self.reload, compact=True))
        root.addLayout(toolbar)

        summary = QHBoxLayout()
        summary.setSpacing(12)
        self.kpi_active = self._kpi("جلسات نشطة", "—", "على أجهزة الصالة")
        self.kpi_idle = self._kpi("أجهزة متاحة", "—", "جاهزة للبدء")
        self.kpi_live = self._kpi("إيراد جارٍ", "—", "هذه اللحظة")
        self.kpi_avg = self._kpi("متوسط الجلسة", "—", "من الجلسات النشطة")
        for card in (self.kpi_active, self.kpi_idle, self.kpi_live, self.kpi_avg):
            summary.addWidget(card, 1)
        root.addLayout(summary)

        body = QHBoxLayout()
        body.setSpacing(12)

        table_card = Card(padding=12, spacing=8)
        table_card.body.addWidget(label("الجلسات", "Title"))
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(
            ["الجهاز", "اللاعب", "المجموعة", "النمط", "بدأت", "المتبقي", "التكلفة", "الحالة"]
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.itemSelectionChanged.connect(self._selection_changed)
        header = self.table.horizontalHeader()
        for index, width in enumerate((82, 110, 70, 100, 54, 88, 90, 66)):
            self.table.setColumnWidth(index, width)
        header.setStretchLastSection(True)
        header.setMinimumSectionSize(70)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.table.setMinimumWidth(560)
        table_card.body.addWidget(self.table, 1)
        body.addWidget(table_card, 3)

        self.detail = Card(padding=14, spacing=8)
        head = QHBoxLayout()
        self.detail_name = label("اختر جلسة", "Title")
        self.detail_state = Pill("—", "muted")
        head.addWidget(self.detail_name)
        head.addStretch()
        head.addWidget(self.detail_state)
        self.detail.body.addLayout(head)
        self.detail_meta = label("—", "Muted")
        self.detail_meta.setWordWrap(True)
        self.detail_meta.setMinimumHeight(44)
        self.detail.body.addWidget(self.detail_meta)
        self.detail.body.addWidget(hline())
        self.remain_line = label("المتبقي —", "Body")
        self.detail.body.addWidget(self.remain_line)
        self.remain_bar = Bar(0, height=6)
        self.remain_bar.setMinimumWidth(240)
        self.detail.body.addWidget(self.remain_bar)
        self.usage_line = label(" ", "Caption")
        self.detail.body.addWidget(self.usage_line)
        self.cost_line = label("التكلفة —", "Body")
        self.detail.body.addWidget(self.cost_line)
        self.rate_line = label("—", "Caption")
        self.detail.body.addWidget(self.rate_line)

        actions = QHBoxLayout()
        actions.setSpacing(6)
        actions.addWidget(button("+15", "quiet", lambda: self._extend(15), compact=True))
        actions.addWidget(button("+30", "quiet", lambda: self._extend(30), compact=True))
        actions.addWidget(button("+60", "quiet", lambda: self._extend(60), compact=True))
        self.detail.body.addLayout(actions)

        actions2 = QHBoxLayout()
        actions2.setSpacing(6)
        actions2.addWidget(button("إنهاء الجلسة", "danger", self._stop_selected, compact=True))
        actions2.addWidget(button("مراقبة العتاد", "accent", self._hardware, compact=True))
        self.detail.body.addLayout(actions2)
        self.detail.body.addStretch()
        self.detail.setMinimumWidth(340)
        self.detail.setMaximumWidth(430)
        body.addWidget(self.detail, 2)
        root.addLayout(body, 1)

        self.footer = label("آخر تحديث —", "Caption")
        root.addWidget(self.footer)

    def _kpi(self, title: str, value: str, hint: str) -> Card:
        card = Card(padding=14, spacing=2)
        card.body.addWidget(label(title, "Caption"))
        number = label(value, "H2")
        card.body.addWidget(number)
        card.body.addWidget(label(hint, "Caption"))
        card.number = number
        return card

    # ── lifecycle ────────────────────────────────────────────────────────
    def on_shown(self):
        self.reload()
        self._timer.start()

    def showEvent(self, event):
        self._timer.start()
        super().showEvent(event)

    def hideEvent(self, event):
        self._timer.stop()
        super().hideEvent(event)

    # ── data ─────────────────────────────────────────────────────────────
    def _visible(self):
        rows = self.engine.sessions()
        mode = self.filter.current
        if mode != "all":
            rows = [row for row in rows if row.mode == mode]
        needle = self.search.text().strip().lower()
        if needle:
            rows = [
                row for row in rows
                if needle in row.host_name.lower() or needle in row.member_name.lower()
            ]
        return rows

    def reload(self):
        self.rows = self._visible()
        hosts = self.data.hosts()
        busy = len(self.engine.sessions())
        revenue = sum(row.cost for row in self.engine.sessions())
        durations = [row.elapsed_minutes for row in self.engine.sessions()]
        self.kpi_active.number.setText(str(busy))
        self.kpi_idle.number.setText(str(max(0, len(hosts) - busy)))
        self.kpi_live.number.setText(f"{revenue:,.2f} ر.س")
        self.kpi_avg.number.setText(
            format_minutes(sum(durations) / len(durations)) if durations else "—"
        )

        self.table.setRowCount(0)
        for row in self.rows:
            position = self.table.rowCount()
            self.table.insertRow(position)
            remaining = row.remaining_minutes(self._balance_minutes(row))
            values = [
                row.host_name,
                row.member_name,
                row.member_group,
                row.label(),
                row.started.strftime("%H:%M"),
                format_minutes(remaining),
                f"{row.cost:,.2f} ر.س",
                "نشطة",
            ]
            for column, text in enumerate(values):
                item = QTableWidgetItem(text)
                item.setData(Qt.ItemDataRole.UserRole, row.session_id)
                if column in (4, 5, 6, 7):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if column == 5 and remaining <= 10:
                    item.setForeground(QColor(Colors.RED if remaining <= 0 else Colors.ORANGE))
                self.table.setItem(position, column, item)
            self.table.setRowHeight(position, 38)

        self._paint_detail()
        self.footer.setText(f"آخر تحديث {datetime.now().strftime('%H:%M:%S')}")

    def _balance_minutes(self, row) -> int:
        balance = 0.0
        for member in self.data.members():
            if row.member_id and int(member.get("MemberId") or 0) == int(row.member_id):
                balance = float(member.get("Balance") or 0)
                break
        return int(balance / row.hourly * 60) if row.hourly else 0

    def _current(self):
        for row in self.engine.sessions():
            if row.session_id == self.selected_id:
                return row
        return self.rows[0] if self.rows else None

    def _selection_changed(self):
        item = self.table.currentItem()
        if item is not None:
            self.selected_id = item.data(Qt.ItemDataRole.UserRole)
            self._paint_detail()

    def _paint_detail(self):
        row = self._current()
        if row is None:
            self.detail_name.setText("لا توجد جلسة")
            self.detail_state.setText("—")
            self.detail_state.set_tone("muted")
            self.detail_meta.setText("ابدأ جلسة جديدة لتظهر تفاصيلها هنا.")
            self.remain_line.setText("المتبقي —")
            self.usage_line.setText(" ")
            self.cost_line.setText("التكلفة —")
            self.rate_line.setText("")
            self.remain_bar.set_value(0)
            return
        self.selected_id = row.session_id
        self.detail_name.setText(f"{row.host_name} · {row.member_name}")
        self.detail_state.setText(row.label())
        self.detail_state.set_tone("warning" if row.mode in ("fixed", "offer") else "success")
        self.detail_meta.setText(
            f"المجموعة: {row.member_group}  ·  {row.host_group}\n"
            f"بدأت {row.started.strftime('%H:%M')} وتُحتسب على {row.profile}"
        )
        balance_minutes = self._balance_minutes(row)
        remaining = row.remaining_minutes(balance_minutes)
        total = row.purchased_minutes + balance_minutes
        self.remain_line.setText(
            f"المتبقي {format_minutes(remaining)} من {format_minutes(total)}\u200f"
        )
        self.remain_bar.set_value((remaining / total * 100) if total else 0)
        self.remain_bar.tone = (
            "danger" if remaining <= 10 else ("warning" if remaining <= 30 else "accent")
        )
        plan = row.usage_plan(balance_minutes)
        self.usage_line.setText(
            "  ·  ".join(
                f"{name} {used_part} من {total_part} د" if name != "تجاوز"
                else f"تجاوز {used_part} د"
                for name, used_part, total_part in plan
            ) or " "
        )
        self.cost_line.setText(f"التكلفة حتى الآن {row.cost:,.2f} ر.س\u200f")
        self.rate_line.setText(
            f"{row.hourly:,.2f} ر.س/ساعة  ·  {row.elapsed_minutes} دقيقة استخدام\u200f"
        )

    # ── actions ──────────────────────────────────────────────────────────
    def _start(self):
        hosts = [h for h in self.data.hosts()
                 if str(h.get("Status")) not in ("مشغول", "InUse", "Busy")]
        if not hosts:
            Toast(self, "كل الأجهزة مشغولة الآن", "warning")
            return
        dialog = StartSessionDialog(self.engine, hosts, self.data.members(), self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        host, member, mode, minutes, amount = dialog.values()
        session = self.engine.start(host, member, minutes, mode, amount)
        Toast(self, f"بدأت جلسة على {session.host_name}", "success")
        self.data.invalidate()
        self._timer.start()
        self.reload()

    def _stop_selected(self):
        row = self._current()
        if row is None:
            Toast(self, "اختر جلسة أولاً", "warning")
            return
        answer = QMessageBox.question(
            self, "إنهاء الجلسة",
            f"إنهاء جلسة {row.host_name} للاعب {row.member_name}؟\n"
            f"المدة {format_minutes(row.elapsed_minutes)} والتكلفة {row.cost:,.2f} ر.س.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        cost = self.engine.stop(row, settle=True)
        Toast(self, f"أُنهيت الجلسة — {cost:,.2f} ر.س", "success")
        self.selected_id = None
        self.data.invalidate()
        self.reload()

    def _extend(self, minutes: int):
        row = self._current()
        if row is None:
            Toast(self, "اختر جلسة أولاً", "warning")
            return
        self.engine.extend(row, minutes)
        Toast(self, f"أُضيفت {minutes} دقيقة إلى {row.host_name}", "success")
        self.reload()

    def _hardware(self):
        row = self._current()
        if row is None:
            return
        host = self.data.host(row.host_id)
        if host is None:
            return
        HardwareDialog(self.data, host, self).exec()

    def _tick(self):
        for kind, session, remaining in self.engine.tick():
            if kind == "low":
                Toast(self, f"{session.host_name}: باقي {remaining} دقيقة", "warning", 3200)
            elif kind == "expired":
                self.engine.stop(session, settle=True)
                Toast(self, f"انتهى وقت {session.host_name} وأُغلقت الجلسة", "danger", 3600)
                self.data.invalidate()
        self.reload()
