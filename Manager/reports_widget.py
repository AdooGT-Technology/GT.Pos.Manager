# -*- coding: utf-8 -*-
"""Reports: last seven days, best sellers, and a CSV export that works."""

from __future__ import annotations

import csv
from datetime import date, timedelta
from pathlib import Path

from PyQt6.QtCore import QRect, Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import (
    QHBoxLayout, QHeaderView, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from Manager.theme import Colors
from Manager.ui import Card, Kpi, Toast, button, hline, label

AR_DAYS = ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]


class WeekChart(QWidget):
    """Seven bars, no library, no noise."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.values = []
        self.setMinimumHeight(180)

    def set_values(self, values):
        self.values = list(values)[-7:]
        self.update()

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        width, height = self.width(), self.height()
        if not self.values:
            return
        pad_bottom, pad_top = 28, 18
        gap = 16
        count = max(1, len(self.values))
        slot = (width - gap * (count + 1)) / count
        bar_width = max(8, min(44, slot))
        peak = max((value for _, value in self.values), default=1) or 1

        painter.setFont(QFont("Segoe UI", 8))
        # newest day sits on the right, so the chart reads right → left like the UI
        ordered = list(reversed(self.values))
        for index, (day, value) in enumerate(ordered):
            x = width - gap - (index + 1) * (slot + gap) + (slot - bar_width) / 2
            bar_height = (height - pad_bottom - pad_top) * (value / peak)
            top = height - pad_bottom - bar_height
            color = QColor(Colors.CYAN)
            color.setAlpha(220 if index == 0 else 120)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)
            painter.drawRoundedRect(int(x), int(top), int(bar_width), int(bar_height), 5, 5)

            painter.setPen(QPen(QColor(Colors.TEXT_MUTED)))
            painter.drawText(
                QRect(int(x), height - 22, int(bar_width), 16),
                Qt.AlignmentFlag.AlignCenter, day,
            )
            if value:
                painter.setPen(QPen(QColor(Colors.TEXT_PRIMARY)))
                painter.drawText(
                    QRect(int(x), int(top) - 18, int(bar_width), 14),
                    Qt.AlignmentFlag.AlignCenter, f"{value:,.0f}",
                )

    def refresh_theme(self):
        self.update()


class ReportsWidget(QWidget):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.data = data
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
        self.kpi_week = Kpi("مبيعات الأسبوع", "—", "آخر 7 أيام")
        self.kpi_avg = Kpi("متوسط الفاتورة", "—", "لكل طلب")
        self.kpi_sessions = Kpi("جلسات مفتوحة", "—", "على الأجهزة الآن")
        self.kpi_best = Kpi("الأكثر مبيعاً", "—", "خلال الأسبوع")
        for card in (self.kpi_week, self.kpi_avg, self.kpi_sessions, self.kpi_best):
            kpis.addWidget(card, 1)
        root.addLayout(kpis)

        chart_card = Card(padding=16)
        head = QHBoxLayout()
        head.addWidget(label("حركة المبيعات", "Title"))
        head.addStretch()
        head.addWidget(button("تصدير CSV", "quiet", self.export_csv, compact=True))
        chart_card.body.addLayout(head)
        self.chart = WeekChart()
        chart_card.body.addWidget(self.chart)
        root.addWidget(chart_card, 1)

        bottom = QHBoxLayout()
        bottom.setSpacing(12)
        products = Card(padding=12)
        products.body.addWidget(label("أفضل المنتجات", "Title"))
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["المنتج", "الكمية", "الإيراد"])
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        products.body.addWidget(self.table)
        bottom.addWidget(products, 3)

        summary = Card(padding=16)
        summary.body.addWidget(label("ملخص سريع", "Title"))
        summary.body.addWidget(hline())
        self.summary_box = QVBoxLayout()
        self.summary_box.setSpacing(8)
        summary.body.addLayout(self.summary_box)
        summary.body.addStretch()
        bottom.addWidget(summary, 2)
        root.addLayout(bottom, 1)

    def on_shown(self):
        self.reload()

    def _week_rows(self):
        rows = self.data.query(
            "SELECT CAST(CreatedAt AS DATE) AS d, SUM(FinalAmount) AS total, COUNT(*) AS cnt"
            " FROM Orders WHERE CreatedAt >= DATEADD(day, -6, GETDATE())"
            " GROUP BY CAST(CreatedAt AS DATE) ORDER BY d", ttl=20, key="week_sales",
        )
        if rows:
            by_day = {}
            for row in rows:
                stamp = row.get("d")
                if hasattr(stamp, "date"):
                    stamp = stamp.date()
                by_day[str(stamp)] = float(row.get("total") or 0)
        else:
            today = date.today()
            demo = [840, 612, 930, 1180, 760, 1520, 486]
            by_day = {str(today - timedelta(days=6 - i)): demo[i] for i in range(7)}

        today = date.today()
        series = []
        for offset in range(6, -1, -1):
            day = today - timedelta(days=offset)
            series.append((AR_DAYS[day.weekday()], by_day.get(str(day), 0.0)))
        return series

    def reload(self):
        series = self._week_rows()
        self.chart.set_values(series)
        week_total = sum(value for _, value in series)
        self.kpi_week.set_value(f"{week_total:,.0f}", "ر.س")

        orders = self.data.recent_orders(limit=50)
        count = len(orders) or 1
        avg = sum(float(o.get("FinalAmount") or 0) for o in orders) / count
        self.kpi_avg.set_value(f"{avg:,.2f}", "ر.س")

        busy = sum(1 for h in self.data.hosts() if str(h.get("Status")) in ("مشغول", "InUse", "Busy"))
        self.kpi_sessions.set_value(str(busy), "على الأجهزة الآن")

        top = self.data.query(
            "SELECT TOP 5 ProductName, SUM(Quantity) AS qty, SUM(FinalAmount) AS total"
            " FROM Orders GROUP BY ProductName ORDER BY SUM(Quantity) DESC",
            ttl=30, key="top_products",
        )
        if not top:
            top = [
                {"ProductName": "Red Bull 250مل", "qty": 48, "total": 576},
                {"ProductName": "ساعة لعب إضافية", "qty": 31, "total": 775},
                {"ProductName": "قهوة مثلجة", "qty": 27, "total": 405},
                {"ProductName": "برينجلز كبير", "qty": 19, "total": 190},
            ]
        self.kpi_best.set_value(str(top[0].get("ProductName") or "—") if top else "—", "خلال الأسبوع")

        self.table.setUpdatesEnabled(False)
        self.table.setRowCount(len(top))
        for index, row in enumerate(top):
            self.table.setItem(index, 0, QTableWidgetItem(str(row.get("ProductName") or "—")))
            self.table.setItem(index, 1, QTableWidgetItem(str(int(row.get("qty") or 0))))
            self.table.setItem(index, 2, QTableWidgetItem(f"{float(row.get('total') or 0):,.2f}"))
        self.table.setUpdatesEnabled(True)

        while self.summary_box.count():
            item = self.summary_box.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        stats = self.data.today_stats()
        for name, value in (
            ("إيراد اليوم", f"{stats['revenue']:,.2f} ر.س"),
            ("طلبات اليوم", str(stats["orders"] or "—")),
            ("أجهزة مشغولة", f"{stats['hosts_busy']} من {stats['hosts_total']}"),
            ("أعضاء مسجلون", str(stats["members"])),
        ):
            row = QWidget()
            line = QHBoxLayout(row)
            line.setContentsMargins(0, 0, 0, 0)
            line.addWidget(label(name, "Muted"))
            line.addStretch()
            line.addWidget(label(value, "Body"))
            self.summary_box.addWidget(row)

    def export_csv(self):
        folder = Path("Exports")
        folder.mkdir(exist_ok=True)
        target = folder / f"sales-{date.today().isoformat()}.csv"
        try:
            with target.open("w", newline="", encoding="utf-8-sig") as handle:
                writer = csv.writer(handle)
                writer.writerow(["اليوم", "المبيعات"])
                for day, value in self._week_rows():
                    writer.writerow([day, f"{value:.2f}"])
        except OSError as error:
            Toast(self, f"تعذر إنشاء الملف: {error}", "danger")
            return
        Toast(self, f"حُفظ في {target}", "success", 3200)
