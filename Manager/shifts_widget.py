# -*- coding: utf-8 -*-
"""Shifts: open the cash drawer, count it at the end, and keep the history."""

from __future__ import annotations

from datetime import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QDialog, QDoubleSpinBox, QHBoxLayout, QLineEdit, QMessageBox, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)

from Manager.billing import format_minutes
from Manager.sessions import SessionEngine
from Manager.theme import Colors
from Manager.ui import (
    Card, FormDialog, Toast, button, hline, label,
)


class ShiftDialog(FormDialog):
    def __init__(self, opening: bool, suggested: float = 0.0, staff: str = "", parent=None):
        title = "فتح وردية" if opening else "إغلاق الوردية"
        super().__init__(title, "أدخل المبلغ النقدي في الدرج.", parent, width=400)
        self.opening = opening
        self.cash = QDoubleSpinBox()
        self.cash.setRange(0, 1_000_000)
        self.cash.setDecimals(2)
        self.cash.setSuffix(" ر.س")
        self.cash.setValue(float(suggested))
        self.add_field("النقد في الدرج" if opening else "النقد المعدود", self.cash)

        self.staff_input = QLineEdit(staff)
        if opening:
            self.add_field("الموظف", self.staff_input)
        else:
            self.staff_input.setVisible(False)

        self.note = QLineEdit()
        self.note.setPlaceholderText("ملاحظة (اختياري)")
        self.add_field("ملاحظة", self.note)

    def values(self):
        return self.cash.value(), self.staff_input.text().strip(), self.note.text().strip()


class ShiftsWidget(QWidget):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.data = data
        self.engine = SessionEngine(data)
        self.current_shift = None
        self._build()
        self.reload()

    def set_navigator(self, _navigate):
        pass

    # ── layout ───────────────────────────────────────────────────────────
    def _build(self):
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(12)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        self.state = label("الوردية مغلقة", "Muted")
        toolbar.addWidget(self.state)
        toolbar.addStretch()
        self.open_btn = button("فتح وردية", "primary", self._open_shift, compact=True)
        self.close_btn = button("إغلاق الوردية", "danger", self._close_shift, compact=True)
        self.in_btn = button("إدخال نقد", "quiet", lambda: self._move("in"), compact=True)
        self.out_btn = button("إخراج نقد", "quiet", lambda: self._move("out"), compact=True)
        toolbar.addWidget(self.in_btn)
        toolbar.addWidget(self.out_btn)
        toolbar.addWidget(self.open_btn)
        toolbar.addWidget(self.close_btn)
        toolbar.addWidget(button("تحديث", "ghost", self.reload, compact=True))
        root.addLayout(toolbar)

        cards = QHBoxLayout()
        cards.setSpacing(12)
        self.kpi_sales = self._kpi("مبيعات الوردية", "—", "طلبات مسجلة")
        self.kpi_cash = self._kpi("النقد المتوقع", "—", "من بداية الوردية")
        self.kpi_sessions = self._kpi("جلسات مغلقة", "—", "خلال الوردية")
        self.kpi_playtime = self._kpi("وقت اللعب", "—", "مجموع الجلسات")
        for card in (self.kpi_sales, self.kpi_cash, self.kpi_sessions, self.kpi_playtime):
            cards.addWidget(card, 1)
        root.addLayout(cards)

        history = Card(padding=12, spacing=6)
        head = QHBoxLayout()
        head.addWidget(label("سجل الورديات", "Title"))
        head.addStretch()
        self.hint = label("", "Caption")
        head.addWidget(self.hint)
        history.body.addLayout(head)
        history.body.addWidget(hline())

        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(
            ["الموظف", "فتح", "نهاية", "افتتاحي", "متوقع", "معدود", "الفرق", "الحالة"]
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        for index, width in enumerate((150, 90, 90, 110, 110, 110, 110, 100)):
            self.table.setColumnWidth(index, width)
        self.table.horizontalHeader().setStretchLastSection(True)
        history.body.addWidget(self.table)
        root.addWidget(history, 1)

        movements = Card(padding=12, spacing=6)
        move_head = QHBoxLayout()
        move_head.addWidget(label("حركات النقد", "Title"))
        move_head.addStretch()
        self.move_total = label("", "Caption")
        move_head.addWidget(self.move_total)
        movements.body.addLayout(move_head)
        movements.body.addWidget(hline())
        self.movements = QTableWidget(0, 5)
        self.movements.setHorizontalHeaderLabels(
            ["النوع", "المبلغ", "السبب", "الموظف", "الوقت"]
        )
        self.movements.verticalHeader().setVisible(False)
        self.movements.setShowGrid(False)
        self.movements.setAlternatingRowColors(True)
        for index, width in enumerate((100, 110, 260, 150, 100)):
            self.movements.setColumnWidth(index, width)
        self.movements.horizontalHeader().setStretchLastSection(True)
        self.movements.setFixedHeight(190)
        movements.body.addWidget(self.movements)
        root.addWidget(movements)
        self.footer = label("", "Caption")
        root.addWidget(self.footer)

    def _kpi(self, title, value, hint):
        card = Card(padding=14, spacing=2)
        card.body.addWidget(label(title, "Caption"))
        number = label(value, "H2")
        card.body.addWidget(number)
        card.body.addWidget(label(hint, "Caption"))
        card.number = number
        return card

    # ── data ─────────────────────────────────────────────────────────────
    def on_shown(self):
        self.reload()

    def reload(self):
        rows = self.data.shifts()
        self.current_shift = next(
            (row for row in rows if str(row.get("Status")) == "مفتوحة"), None
        )
        is_open = self.current_shift is not None
        self.state.setText("● وردية مفتوحة الآن" if is_open else "○ الوردية مغلقة")
        self.state.setStyleSheet(
            f"color: {Colors.GREEN if is_open else Colors.TEXT_MUTED}; font-weight: 600;"
        )
        self.open_btn.setEnabled(not is_open)
        self.close_btn.setEnabled(is_open)

        today = datetime.now().date()
        sessions = self.engine.history(60)
        closed = [
            row for row in sessions
            if getattr(row, "ended", None) and row.ended.date() == today
        ]
        played = sum(row.elapsed_minutes for row in closed)
        self.kpi_sessions.number.setText(str(len(closed)))
        self.kpi_playtime.number.setText(format_minutes(played))
        orders = self.data.orders_today()
        if isinstance(orders, dict):
            count = int(orders.get("count") or 0)
            total = float(orders.get("total") or 0)
        else:
            count, total = 0, 0.0
        self.kpi_sales.number.setText(f"{total:,.2f} ر.س")
        self.hint.setText(f"{count} طلب مسجل اليوم · {len(rows)} وردية")
        moves = self.data.cash_movements(
            self.current_shift.get("ShiftId") if self.current_shift else None
        )
        cash_in = sum(float(m.get("Amount") or 0) for m in moves if m.get("Kind") == "in")
        cash_out = sum(float(m.get("Amount") or 0) for m in moves if m.get("Kind") == "out")
        opening = float(self.current_shift.get("OpeningCash") or 0) if is_open else 0.0
        expected = opening + total + cash_in - cash_out if is_open else total
        self.kpi_cash.number.setText(f"{expected:,.2f} ر.س")
        self._fill_movements(moves)
        self.in_btn.setEnabled(is_open)
        self.out_btn.setEnabled(is_open)

        self.table.setRowCount(0)
        for row in rows:
            position = self.table.rowCount()
            self.table.insertRow(position)
            opened = str(row.get("OpenedAt") or "")[:16].replace("T", " ")
            closed_at = str(row.get("ClosedAt") or "")[:16].replace("T", " ")
            difference = float(row.get("Difference") or 0)
            values = [
                str(row.get("StaffName") or "—"),
                opened[11:16] if opened else "—",
                closed_at[11:16] if closed_at else "—",
                f"{float(row.get('OpeningCash') or 0):,.2f}",
                f"{float(row.get('ExpectedCash') or 0):,.2f}",
                f"{float(row.get('ClosingCash') or 0):,.2f}",
                f"\u200e{difference:,.2f}",
                str(row.get("Status") or "—"),
            ]
            for column, text in enumerate(values):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if column == 6 and difference:
                    item.setForeground(QColor(Colors.RED if difference < 0 else Colors.GREEN))
                if column == 7:
                    item.setForeground(QColor(
                        Colors.GREEN if text == "مفتوحة" else Colors.TEXT_MUTED
                    ))
                self.table.setItem(position, column, item)
            self.table.setRowHeight(position, 36)

        if not rows:
            self.hint.setText("لا توجد ورديات مسجلة — افتح وردية لبدء اليوم.")
        self.footer.setText(f"آخر تحديث {datetime.now().strftime('%H:%M')}")

    def _fill_movements(self, moves):
        self.movements.setRowCount(0)
        cash_in = 0.0
        cash_out = 0.0
        for move in moves:
            kind = str(move.get("Kind") or "")
            amount = float(move.get("Amount") or 0)
            if kind == "in":
                cash_in += amount
            else:
                cash_out += amount
            position = self.movements.rowCount()
            self.movements.insertRow(position)
            created = str(move.get("CreatedAt") or "")
            values = [
                "إدخال" if kind == "in" else "إخراج",
                f"\u200e{amount:,.2f}",
                str(move.get("Reason") or "—"),
                str(move.get("CreatedBy") or "—"),
                created[11:16] if len(created) > 15 else "—",
            ]
            for column, text in enumerate(values):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if column == 0:
                    item.setForeground(QColor(Colors.GREEN if kind == "in" else Colors.RED))
                self.movements.setItem(position, column, item)
            self.movements.setRowHeight(position, 32)
        self.move_total.setText(
            f"داخل {cash_in:,.2f}  ·  خارج {cash_out:,.2f}  ·  الصافي {cash_in - cash_out:,.2f}"
            if moves else "لا حركات في هذه الوردية"
        )

    # ── actions ──────────────────────────────────────────────────────────
    def _open_shift(self):
        if self.current_shift is not None:
            Toast(self, "هناك وردية مفتوحة بالفعل", "warning")
            return
        dialog = ShiftDialog(True, 0.0, "مدير النظام", self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        cash, staff, note = dialog.values()
        if self.data.execute(
            "INSERT INTO Shifts (StaffName, OpeningCash, ExpectedCash, Status, Note)"
            " VALUES (?, ?, ?, N'مفتوحة', ?)",
            (staff or "مدير النظام", cash, cash, note),
        ):
            Toast(self, f"فُتحت الوردية برصيد {cash:,.2f} ر.س", "success")
        else:
            Toast(self, "تعذر فتح الوردية — القاعدة غير متصلة", "warning")
        self.data.invalidate()
        self.reload()

    def _move(self, kind: str):
        shift = self.current_shift
        if shift is None:
            Toast(self, "افتح وردية أولاً لتسجيل حركة نقد", "warning")
            return
        title = "إدخال نقد إلى الدرج" if kind == "in" else "إخراج نقد من الدرج"
        dialog = FormDialog(title, "سجّل الحركة مع السبب لتظهر في مطابقة الوردية.", self, width=400)
        amount = QDoubleSpinBox()
        amount.setRange(0.01, 1_000_000)
        amount.setDecimals(2)
        amount.setSuffix(" ر.س")
        amount.setValue(50.0)
        dialog.add_field("المبلغ", amount)
        reason = QLineEdit()
        reason.setPlaceholderText("مثال: شراء مستلزمات أو إيداع لاعب")
        dialog.add_field("السبب", reason)
        staff = QLineEdit(str(shift.get("StaffName") or "مدير النظام"))
        dialog.add_field("الموظف", staff)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        value, why, who = amount.value(), reason.text().strip(), staff.text().strip()
        ok = self.data.execute(
            "INSERT INTO CashMovements (ShiftId, Kind, Amount, Reason, CreatedBy)"
            " VALUES (?, ?, ?, ?, ?)",
            (shift.get("ShiftId"), kind, value, why, who),
        )
        Toast(
            self,
            f"{'أُدخل' if kind == 'in' else 'أُخرج'} {value:,.2f} ر.س" if ok
            else "لم تُحفظ الحركة — القاعدة غير متصلة",
            "success" if ok else "warning",
        )
        self.data.invalidate()
        self.reload()

    def _close_shift(self):
        shift = self.current_shift
        if shift is None:
            Toast(self, "لا توجد وردية مفتوحة", "warning")
            return
        orders = self.data.orders_today()
        expected = float(shift.get("ExpectedCash") or 0)
        if isinstance(orders, dict):
            expected += float(orders.get("total") or 0)
        dialog = ShiftDialog(False, expected, parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        counted, _staff, note = dialog.values()
        difference = round(counted - expected, 2)
        answer = QMessageBox.question(
            self, "تأكيد الإغلاق",
            f"المتوقع {expected:,.2f} ر.س والمعدود {counted:,.2f} ر.س\n"
            f"الفرق {difference:,.2f} ر.س. هل تريد الإغلاق؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        ok = self.data.execute(
            "UPDATE Shifts SET ClosedAt = GETDATE(), ExpectedCash = ?, ClosingCash = ?,"
            " Difference = ?, Status = N'مغلقة', Note = ? WHERE ShiftId = ?",
            (expected, counted, difference, note, shift.get("ShiftId")),
        )
        Toast(
            self,
            f"أُغلقت الوردية — الفرق {difference:,.2f} ر.س" if ok
            else "تعذر إغلاق الوردية — القاعدة غير متصلة",
            "success" if ok else "warning",
        )
        self.data.invalidate()
        self.reload()
