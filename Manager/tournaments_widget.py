# -*- coding: utf-8 -*-
"""Tournaments: small board for upcoming and running events."""

from __future__ import annotations

from datetime import date, timedelta

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox, QDateEdit, QDoubleSpinBox, QHBoxLayout, QLineEdit,
    QVBoxLayout, QWidget,
)
from PyQt6.QtCore import QDate

from Manager.ui import Card, FormDialog, Kpi, Pill, Toast, button, hline, label

DEFAULT_EVENTS = [
    {"name": "كأس الجمعة — FC 25", "game": "EA SPORTS FC 25", "date": "", "slots": 16,
     "prize": 500, "status": "التسجيل مفتوح"},
    {"name": "ليلة فالورانت", "game": "VALORANT", "date": "", "slots": 10,
     "prize": 300, "status": "قريباً"},
]

STATUSES = ["التسجيل مفتوح", "قريباً", "جارية", "منتهية"]


class EventDialog(FormDialog):
    def __init__(self, parent=None):
        super().__init__("بطولة جديدة", "الحد الأقصى للمشاركين والجائزة يظهران للاعبين.", parent, width=440)
        self.name = self.add_field("اسم البطولة", QLineEdit())
        self.game = self.add_field("اللعبة", QLineEdit())
        self.date = QDateEdit(QDate.currentDate().addDays(7))
        self.date.setCalendarPopup(True)
        self.add_field("التاريخ", self.date)
        self.slots = QDoubleSpinBox()
        self.slots.setRange(2, 128)
        self.slots.setDecimals(0)
        self.slots.setValue(16)
        self.add_field("عدد المقاعد", self.slots)
        self.prize = QDoubleSpinBox()
        self.prize.setRange(0, 100000)
        self.prize.setDecimals(0)
        self.prize.setValue(500)
        self.prize.setSuffix(" ر.س")
        self.add_field("الجائزة", self.prize)
        self.status = self.add_combo("الحالة", STATUSES)
        self.save_btn.setText("إضافة")


class TournamentsWidget(QWidget):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.data = data
        self.events = []
        self._build()
        self.reload()

    def set_navigator(self, _navigate):
        pass

    def _build(self):
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(12)

        kpis = QHBoxLayout()
        kpis.setSpacing(12)
        self.kpi_open = Kpi("بطولات مفتوحة", "—", "تقبل التسجيل")
        self.kpi_live = Kpi("جارية الآن", "—", "على أجهزة الصالة")
        self.kpi_prize = Kpi("مجموع الجوائز", "—", "للبطولات القادمة")
        for card in (self.kpi_open, self.kpi_live, self.kpi_prize):
            kpis.addWidget(card, 1)
        root.addLayout(kpis)

        head = QHBoxLayout()
        head.addWidget(label("جدول البطولات", "Title"))
        head.addStretch()
        head.addWidget(button("بطولة جديدة", "primary", self.add_event))
        root.addLayout(head)

        self.list_layout = QVBoxLayout()
        self.list_layout.setSpacing(10)
        root.addLayout(self.list_layout)
        root.addStretch()

    def on_shown(self):
        self.reload()

    def reload(self):
        stored = self.data.setting("events.list", None)
        self.events = stored if isinstance(stored, list) and stored else [dict(e) for e in DEFAULT_EVENTS]
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for index, event in enumerate(self.events):
            card = Card(padding=14, spacing=6)
            top = QHBoxLayout()
            top.addWidget(label(str(event.get("name") or "بطولة"), "Title"))
            top.addStretch()
            pill = Pill(str(event.get("status") or "قريباً"), "accent")
            top.addWidget(pill)
            card.body.addLayout(top)
            meta = QHBoxLayout()
            meta.addWidget(label(str(event.get("game") or "—"), "Muted"))
            meta.addWidget(label("·", "Caption"))
            meta.addWidget(label(str(event.get("date") or "بدون تاريخ"), "Muted"))
            meta.addWidget(label("·", "Caption"))
            meta.addWidget(label(f"{int(event.get('slots') or 0)} مقعد", "Muted"))
            meta.addStretch()
            meta.addWidget(button("تغيير الحالة", "ghost", lambda _c=False, i=index: self._cycle(i), compact=True))
            meta.addWidget(button("حذف", "danger", lambda _c=False, i=index: self._delete(i), compact=True))
            meta.addWidget(label(f"{float(event.get('prize') or 0):,.0f} ر.س", "Title"))
            card.body.addLayout(meta)
            self.list_layout.addWidget(card)

        self.kpi_open.set_value(str(sum(1 for e in self.events if e.get("status") == "التسجيل مفتوح")),
                                f"من {len(self.events)}")
        self.kpi_live.set_value(str(sum(1 for e in self.events if e.get("status") == "جارية")), "بطولة")
        prize = sum(float(e.get("prize") or 0) for e in self.events if e.get("status") != "منتهية")
        self.kpi_prize.set_value(f"{prize:,.0f}", "ر.س")

    def _save(self):
        if not self.data.live:
            Toast(self, "قاعدة البيانات غير متصلة — لن يُحفظ التغيير", "warning")
            return False
        ok = self.data.set_setting("events.list", self.events, "events")
        if not ok:
            Toast(self, "تعذر حفظ البطولات", "danger")
        return True

    def add_event(self):
        dialog = EventDialog(self)
        if dialog.exec() != EventDialog.DialogCode.Accepted:
            return
        name = dialog.name.text().strip()
        if not name:
            Toast(self, "اكتب اسم البطولة", "warning")
            return
        self.events.append({
            "name": name,
            "game": dialog.game.text().strip() or "—",
            "date": dialog.date.date().toString("yyyy-MM-dd"),
            "slots": int(dialog.slots.value()),
            "prize": float(dialog.prize.value()),
            "status": dialog.status.currentText(),
        })
        self._save()
        self.reload()
        Toast(self, "أُضيفت البطولة", "success")

    def _cycle(self, index: int):
        current = self.events[index].get("status") or STATUSES[0]
        nxt = STATUSES[(STATUSES.index(current) + 1) % len(STATUSES)] if current in STATUSES else STATUSES[0]
        self.events[index]["status"] = nxt
        self._save()
        self.reload()

    def _delete(self, index: int):
        self.events.pop(index)
        self._save()
        self.reload()
