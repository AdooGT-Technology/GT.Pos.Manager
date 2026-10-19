# -*- coding: utf-8 -*-
"""Wallet: balances on one side, the money trail on the other."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView, QComboBox, QDoubleSpinBox, QHBoxLayout, QHeaderView,
    QLineEdit, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from Manager.theme import Colors
from Manager.ui import (
    Card, FormDialog, Kpi, SearchInput, Toast, button, hline, label,
)


class MoneyDialog(FormDialog):
    def __init__(self, member: dict, mode: str = "in", parent=None):
        title = "إيداع" if mode == "in" else "سحب"
        super().__init__(
            f"{title} رصيد",
            f"{member.get('FullName') or member.get('Username')} — الحالي "
            f"{float(member.get('Balance') or 0):,.2f} ر.س",
            parent, width=420,
        )
        self.mode = mode
        self.amount = QDoubleSpinBox()
        self.amount.setRange(0.01, 5000)
        self.amount.setDecimals(2)
        self.amount.setSuffix(" ر.س")
        self.amount.setValue(50)
        self.add_field("المبلغ", self.amount)
        self.note = self.add_field("البيان", QLineEdit("إيداع نقدي" if mode == "in" else "سحب نقدي"))
        self.save_btn.setText(title)


class WalletWidget(QWidget):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.data = data
        self.members = []
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
        self.kpi_total = Kpi("إجمالي الأرصدة", "—", "لدى الأعضاء")
        self.kpi_in = Kpi("إيداعات", "—", "آخر الحركات")
        self.kpi_out = Kpi("سحوبات", "—", "آخر الحركات")
        self.kpi_count = Kpi("عدد الحسابات", "—", "نشطة")
        for card in (self.kpi_total, self.kpi_in, self.kpi_out, self.kpi_count):
            kpis.addWidget(card, 1)
        root.addLayout(kpis)

        body = QHBoxLayout()
        body.setSpacing(12)

        balances = Card(padding=12)
        head = QHBoxLayout()
        head.addWidget(label("أرصدة الأعضاء", "Title"))
        head.addStretch()
        self.search = SearchInput("ابحث عن عضو")
        self.search.textChanged.connect(lambda _t: self._fill_members())
        head.addWidget(self.search)
        balances.body.addLayout(head)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["العضو", "الرصيد", "النقاط", ""])
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        balances.body.addWidget(self.table)
        body.addWidget(balances, 3)

        trail = Card(padding=14)
        trail.body.addWidget(label("آخر الحركات", "Title"))
        trail.body.addWidget(hline())
        self.trail_box = QVBoxLayout()
        self.trail_box.setSpacing(8)
        trail.body.addLayout(self.trail_box)
        trail.body.addStretch()
        trail.body.addWidget(button("تحديث", "ghost", self.reload, compact=True))
        body.addWidget(trail, 2)
        root.addLayout(body, 1)

    def on_shown(self):
        self.reload()

    def reload(self):
        self.members = self.data.members()
        self._fill_members()
        self._fill_trail()
        total = sum(float(m.get("Balance") or 0) for m in self.members)
        self.kpi_total.set_value(f"{total:,.2f}", "ر.س")
        self.kpi_count.set_value(str(len(self.members)), "حساب")
        movements = self.data.transactions(limit=20)
        money_in = sum(float(t.get("Amount") or 0) for t in movements if float(t.get("Amount") or 0) > 0)
        money_out = -sum(float(t.get("Amount") or 0) for t in movements if float(t.get("Amount") or 0) < 0)
        self.kpi_in.set_value(f"{money_in:,.2f}", "ر.س")
        self.kpi_out.set_value(f"{money_out:,.2f}", "ر.س")

    def _visible_members(self):
        needle = self.search.text().strip().lower()
        if not needle:
            return self.members
        return [
            m for m in self.members
            if needle in str(m.get("FullName", "")).lower()
            or needle in str(m.get("Username", "")).lower()
        ]

    def _fill_members(self):
        rows = self._visible_members()
        self.table.setUpdatesEnabled(False)
        self.table.setRowCount(len(rows))
        for index, member in enumerate(rows):
            self.table.setItem(index, 0, QTableWidgetItem(
                f"{member.get('FullName') or '—'}  ·  {member.get('Username') or ''}"
            ))
            balance = QTableWidgetItem(f"{float(member.get('Balance') or 0):,.2f} ر.س")
            balance.setForeground(Qt.GlobalColor.green if float(member.get("Balance") or 0) > 0
                                  else Qt.GlobalColor.red)
            self.table.setItem(index, 1, balance)
            self.table.setItem(index, 2, QTableWidgetItem(str(member.get("Points") or 0)))
            actions = QWidget()
            box = QHBoxLayout(actions)
            box.setContentsMargins(0, 0, 0, 0)
            box.setSpacing(4)
            box.addWidget(button("إيداع", "ghost", lambda _c=False, m=member: self._move(m, "in"), compact=True))
            box.addWidget(button("سحب", "ghost", lambda _c=False, m=member: self._move(m, "out"), compact=True))
            box.addStretch()
            self.table.setCellWidget(index, 3, actions)
            self.table.setRowHeight(index, 42)
        self.table.setUpdatesEnabled(True)

    def _fill_trail(self):
        while self.trail_box.count():
            item = self.trail_box.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for row in self.data.transactions(limit=9):
            widget = QWidget()
            line = QHBoxLayout(widget)
            line.setContentsMargins(0, 0, 0, 0)
            line.setSpacing(8)
            amount = float(row.get("Amount") or 0)
            kind = label(str(row.get("TransType") or "حركة"), "Body")
            who = label(str(row.get("Username") or row.get("Description") or ""), "Caption")
            value = label(f"{amount:+,.2f}", "Body")
            value.setStyleSheet(f"color: {Colors.GREEN if amount >= 0 else Colors.RED};")
            line.addWidget(kind)
            line.addWidget(who, 1)
            line.addWidget(value)
            self.trail_box.addWidget(widget)

    def _move(self, member: dict, mode: str):
        if not self.data.live:
            Toast(self, "قاعدة البيانات غير متصلة — لن يُحفظ التغيير", "warning", 3000)
            return
        dialog = MoneyDialog(member, mode, parent=self)
        if dialog.exec() != MoneyDialog.DialogCode.Accepted:
            return
        amount = float(dialog.amount.value()) * (1 if mode == "in" else -1)
        before = float(member.get("Balance") or 0)
        self.data.execute(
            "UPDATE Members SET Balance = Balance + ? WHERE MemberId = ?",
            (amount, member.get("MemberId")),
        )
        ok = self.data.execute(
            "INSERT INTO TransactionHistory (MemberId, TransType, Amount, BalanceBefore,"
            " BalanceAfter, Description, CreatedBy) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (member.get("MemberId"), "إيداع" if mode == "in" else "سحب", amount,
             before, before + amount, dialog.note.text().strip(), "manager"),
        )
        Toast(self, "تم تسجيل الحركة" if ok else "تعذر تسجيل الحركة",
              "success" if ok else "danger")
        self.reload()
