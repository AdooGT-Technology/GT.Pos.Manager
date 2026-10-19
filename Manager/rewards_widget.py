# -*- coding: utf-8 -*-
"""Rewards: the rules that turn play time into points."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox, QDoubleSpinBox, QHBoxLayout, QHeaderView, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget, QLineEdit,
)

from Manager.ui import (
    Card, FormDialog, Kpi, Toast, button, label,
)

DEFAULT_RULES = [
    {"name": "نقاط الجلسة", "trigger": "كل ساعة لعب", "value": 10, "active": True},
    {"name": "مكافأة الإيداع", "trigger": "إيداع 100 ر.س", "value": 15, "active": True},
    {"name": "إحالة صديق", "trigger": "أول جلسة للمُحال", "value": 50, "active": False},
]

TRIGGERS = ["كل ساعة لعب", "إيداع 100 ر.س", "أول جلسة للمُحال", "شراء من الكافتيريا", "حضور بطولة"]


class RuleDialog(FormDialog):
    def __init__(self, parent=None):
        super().__init__("قاعدة مكافأة", "النقاط تُضاف تلقائياً عند تحقق الشرط.", parent, width=420)
        self.name = self.add_field("اسم القاعدة", QLineEdit())
        self.trigger = self.add_combo("الشرط", TRIGGERS)
        self.value = QDoubleSpinBox()
        self.value.setRange(1, 1000)
        self.value.setValue(10)
        self.value.setSuffix(" نقطة")
        self.add_field("النقاط", self.value)
        self.save_btn.setText("إضافة")


class RewardsWidget(QWidget):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.data = data
        self.rules = []
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
        self.kpi_points = Kpi("نقاط لدى الأعضاء", "—", "مجموع النقاط الحالية")
        self.kpi_rules = Kpi("قواعد مفعّلة", "—", "من إجمالي القواعد")
        self.kpi_top = Kpi("أعلى رصيد نقاط", "—", "عضو واحد")
        for card in (self.kpi_points, self.kpi_rules, self.kpi_top):
            kpis.addWidget(card, 1)
        root.addLayout(kpis)

        body = QHBoxLayout()
        body.setSpacing(12)

        rules_card = Card(padding=12)
        head = QHBoxLayout()
        head.addWidget(label("قواعد النقاط", "Title"))
        head.addStretch()
        head.addWidget(button("قاعدة جديدة", "primary", self.add_rule, compact=True))
        rules_card.body.addLayout(head)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["القاعدة", "الشرط", "النقاط", ""])
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        rules_card.body.addWidget(self.table)
        body.addWidget(rules_card, 3)

        top_card = Card(padding=14)
        top_card.body.addWidget(label("أعلى الأعضاء نقاطاً", "Title"))
        self.leaders = QVBoxLayout()
        self.leaders.setSpacing(8)
        top_card.body.addLayout(self.leaders)
        top_card.body.addStretch()
        body.addWidget(top_card, 2)
        root.addLayout(body, 1)

    def on_shown(self):
        self.reload()

    def reload(self):
        stored = self.data.setting("rewards.rules", None)
        self.rules = stored if isinstance(stored, list) and stored else [dict(r) for r in DEFAULT_RULES]
        self._fill_rules()
        members = sorted(self.data.members(), key=lambda m: int(m.get("Points") or 0), reverse=True)
        points = sum(int(m.get("Points") or 0) for m in members)
        self.kpi_points.set_value(f"{points:,}", f"{len(members)} عضو")
        active = sum(1 for r in self.rules if r.get("active", True))
        self.kpi_rules.set_value(f"{active}", f"من {len(self.rules)}")
        top = members[0] if members else None
        self.kpi_top.set_value(str(top.get("Points") or 0) if top else "—",
                               str(top.get("FullName") or "—") if top else "")
        self._fill_leaders(members[:5])

    def _fill_rules(self):
        self.table.setRowCount(len(self.rules))
        for index, rule in enumerate(self.rules):
            self.table.setItem(index, 0, QTableWidgetItem(str(rule.get("name") or "—")))
            self.table.setItem(index, 1, QTableWidgetItem(str(rule.get("trigger") or "—")))
            self.table.setItem(index, 2, QTableWidgetItem(str(rule.get("value") or 0)))
            actions = QWidget()
            box = QHBoxLayout(actions)
            box.setContentsMargins(0, 0, 0, 0)
            box.setSpacing(4)
            toggle_text = "إيقاف" if rule.get("active", True) else "تفعيل"
            box.addWidget(button(toggle_text, "ghost", lambda _c=False, i=index: self._toggle(i), compact=True))
            box.addWidget(button("حذف", "danger", lambda _c=False, i=index: self._delete(i), compact=True))
            box.addStretch()
            self.table.setCellWidget(index, 3, actions)
            self.table.setRowHeight(index, 42)

    def _fill_leaders(self, members):
        while self.leaders.count():
            item = self.leaders.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for rank, member in enumerate(members, start=1):
            row = QWidget()
            line = QHBoxLayout(row)
            line.setContentsMargins(0, 0, 0, 0)
            line.addWidget(label(f"{rank}.", "Caption"))
            line.addWidget(label(str(member.get("FullName") or member.get("Username")), "Body"), 1)
            line.addWidget(label(f"{int(member.get('Points') or 0)} نقطة", "Muted"))
            self.leaders.addWidget(row)

    def _save(self):
        if not self.data.live:
            Toast(self, "قاعدة البيانات غير متصلة — لن يُحفظ التغيير", "warning")
            return
        ok = self.data.set_setting("rewards.rules", self.rules, "rewards")
        if not ok:
            Toast(self, "تعذر حفظ القواعد", "danger")

    def add_rule(self):
        dialog = RuleDialog(self)
        if dialog.exec() != RuleDialog.DialogCode.Accepted:
            return
        name = dialog.name.text().strip()
        if not name:
            Toast(self, "اكتب اسم القاعدة", "warning")
            return
        self.rules.append({
            "name": name,
            "trigger": dialog.trigger.currentText(),
            "value": int(dialog.value.value()),
            "active": True,
        })
        self._save()
        self._fill_rules()
        Toast(self, "أُضيفت القاعدة", "success")

    def _toggle(self, index: int):
        self.rules[index]["active"] = not self.rules[index].get("active", True)
        self._save()
        self.reload()

    def _delete(self, index: int):
        self.rules.pop(index)
        self._save()
        self.reload()
