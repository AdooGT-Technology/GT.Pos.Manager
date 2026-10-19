# -*- coding: utf-8 -*-
"""Members page: accounts, balances and top-ups."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView, QComboBox, QDoubleSpinBox, QHBoxLayout, QHeaderView,
    QLineEdit, QMessageBox, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from Manager.theme import Colors
from Manager.ui import (
    Card, FormDialog, Pill, SearchInput, Toast, button, label,
)

TYPES = ["عادي", "VIP", "eSports"]


class MemberDialog(FormDialog):
    def __init__(self, member: dict = None, parent=None):
        editing = bool(member)
        super().__init__(
            "تعديل حساب" if editing else "حساب جديد",
            "الاسم ورقم الجوال يظهران في الفواتير.",
            parent,
        )
        self.member = member or {}
        self.name_input = self.add_field("الاسم الكامل", QLineEdit(self.member.get("FullName") or ""))
        self.user_input = self.add_field("اسم المستخدم", QLineEdit(self.member.get("Username") or ""))
        self.phone_input = self.add_field("الجوال", QLineEdit(self.member.get("Phone") or ""))
        type_index = TYPES.index(self.member.get("MemberType")) if self.member.get("MemberType") in TYPES else 0
        self.type_combo = self.add_combo("نوع الحساب", TYPES)
        self.type_combo.setCurrentIndex(type_index)
        if editing:
            self.user_input.setReadOnly(True)
        self.save_btn.setText("حفظ التعديل" if editing else "إنشاء الحساب")

    def values(self):
        return {
            "name": self.name_input.text().strip(),
            "username": self.user_input.text().strip(),
            "phone": self.phone_input.text().strip(),
            "type": self.type_combo.currentText(),
        }


class ChargeDialog(FormDialog):
    def __init__(self, member: dict, parent=None):
        super().__init__(
            "إيداع رصيد",
            f"{member.get('FullName') or member.get('Username')} — الحالي "
            f"{float(member.get('Balance') or 0):,.2f} ر.س",
            parent,
            width=420,
        )
        self.amount = QDoubleSpinBox()
        self.amount.setRange(0.01, 5000)
        self.amount.setDecimals(2)
        self.amount.setValue(50)
        self.amount.setSuffix(" ر.س")
        self.add_field("المبلغ", self.amount)
        self.note = self.add_field("ملاحظة", QLineEdit("شحن رصيد"))
        self.save_btn.setText("إيداع")


class UsersWidget(QWidget):
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

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        self.search = SearchInput("ابحث بالاسم أو اسم المستخدم")
        self.search.textChanged.connect(lambda _text: self._fill())
        toolbar.addWidget(self.search)

        self.filter = QComboBox()
        self.filter.addItems(["كل الأنواع"] + TYPES)
        self.filter.currentIndexChanged.connect(lambda _i: self._fill())
        self.filter.setFixedWidth(150)
        toolbar.addWidget(self.filter)

        self.count_label = label("—", "Muted")
        toolbar.addWidget(self.count_label)
        toolbar.addStretch()
        toolbar.addWidget(button("حساب جديد", "primary", self.add_member))
        root.addLayout(toolbar)

        card = Card(padding=8)
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["اللاعب", "اسم المستخدم", "النوع", "الرصيد", "النقاط", "الحالة", ""]
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.table.doubleClicked.connect(lambda _index: self.edit_member())
        card.body.addWidget(self.table)
        root.addWidget(card, 1)

    def on_shown(self):
        self.reload()

    def reload(self):
        self.members = self.data.members()
        self._fill()

    def _visible(self):
        needle = self.search.text().strip().lower()
        kind = self.filter.currentText()
        rows = self.members
        if kind != "كل الأنواع":
            rows = [m for m in rows if m.get("MemberType") == kind]
        if needle:
            rows = [
                m for m in rows
                if needle in str(m.get("FullName", "")).lower()
                or needle in str(m.get("Username", "")).lower()
                or needle in str(m.get("Phone", ""))
            ]
        return rows

    def _fill(self):
        rows = self._visible()
        self.count_label.setText(f"{len(rows)} حساب")
        self.table.setUpdatesEnabled(False)
        self.table.setRowCount(len(rows))
        for index, member in enumerate(rows):
            name = QTableWidgetItem(str(member.get("FullName") or member.get("Username") or "—"))
            name.setData(Qt.ItemDataRole.UserRole, member)
            self.table.setItem(index, 0, name)
            self.table.setItem(index, 1, QTableWidgetItem(str(member.get("Username") or "—")))
            self.table.setItem(index, 2, QTableWidgetItem(str(member.get("MemberType") or "عادي")))

            balance = float(member.get("Balance") or 0)
            balance_item = QTableWidgetItem(f"{balance:,.2f} ر.س")
            balance_item.setForeground(
                Qt.GlobalColor.green if balance > 0 else Qt.GlobalColor.red
            )
            self.table.setItem(index, 3, balance_item)
            self.table.setItem(index, 4, QTableWidgetItem(str(member.get("Points") or 0)))

            active = bool(member.get("IsActive", 1))
            status = QTableWidgetItem("نشط" if active else "موقوف")
            status.setForeground(Qt.GlobalColor.green if active else Qt.GlobalColor.gray)
            self.table.setItem(index, 5, status)

            actions = QWidget()
            box = QHBoxLayout(actions)
            box.setContentsMargins(0, 0, 0, 0)
            box.setSpacing(4)
            box.addWidget(button("إيداع", "ghost", lambda _c=False, m=member: self.charge(m), compact=True))
            box.addWidget(button("تعديل", "ghost", lambda _c=False, m=member: self.edit_member(m), compact=True))
            box.addStretch()
            self.table.setCellWidget(index, 6, actions)
            self.table.setRowHeight(index, 44)
        self.table.setUpdatesEnabled(True)

    # ── actions ──────────────────────────────────────────────────────────
    def _require_db(self) -> bool:
        if self.data.live:
            return True
        Toast(self, "قاعدة البيانات غير متصلة — لن يُحفظ التغيير", "warning", 3000)
        return False

    def add_member(self):
        dialog = MemberDialog(parent=self)
        if dialog.exec() != MemberDialog.DialogCode.Accepted:
            return
        values = dialog.values()
        if not values["username"]:
            Toast(self, "اسم المستخدم مطلوب", "warning")
            return
        if self._require_db():
            ok = self.data.execute(
                "INSERT INTO Members (Username, PasswordHash, FullName, Phone, MemberType)"
                " VALUES (?, ?, ?, ?, ?)",
                (values["username"], "", values["name"], values["phone"], values["type"]),
            )
            Toast(self, "أُنشئ الحساب" if ok else "تعذر إنشاء الحساب", "success" if ok else "danger")
        self.reload()

    def edit_member(self, member: dict = None):
        if member is None:
            row = self.table.currentRow()
            if row < 0:
                return
            member = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        dialog = MemberDialog(member, parent=self)
        if dialog.exec() != MemberDialog.DialogCode.Accepted:
            return
        values = dialog.values()
        if self._require_db():
            ok = self.data.execute(
                "UPDATE Members SET FullName = ?, Phone = ?, MemberType = ? WHERE MemberId = ?",
                (values["name"], values["phone"], values["type"], member.get("MemberId")),
            )
            Toast(self, "حُفظ الحساب" if ok else "تعذر الحفظ", "success" if ok else "danger")
        self.reload()

    def charge(self, member: dict):
        dialog = ChargeDialog(member, parent=self)
        if dialog.exec() != ChargeDialog.DialogCode.Accepted:
            return
        amount = float(dialog.amount.value())
        before = float(member.get("Balance") or 0)
        if self._require_db():
            self.data.execute(
                "UPDATE Members SET Balance = Balance + ? WHERE MemberId = ?",
                (amount, member.get("MemberId")),
            )
            ok = self.data.execute(
                "INSERT INTO TransactionHistory (MemberId, TransType, Amount,"
                " BalanceBefore, BalanceAfter, Description, CreatedBy)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (member.get("MemberId"), "إيداع", amount, before, before + amount,
                 dialog.note.text().strip() or "شحن رصيد", "manager"),
            )
            Toast(self, f"أُضيف {amount:,.2f} ر.س" if ok else "تعذر تسجيل الإيداع",
                  "success" if ok else "danger")
        self.reload()
