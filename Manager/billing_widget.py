# -*- coding: utf-8 -*-
"""Billing page: user groups, host groups, billing profiles and time offers.

The layout follows the Gizmo model — groups point at profiles, host groups can
override them, and offers carry their own price for a block of minutes.
"""

from __future__ import annotations

from datetime import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QGridLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from Manager.billing import BillingCatalog, format_minutes
from Manager.ui import (
    Card, FormDialog, Segmented, Toast, button, hline, label,
)

EDITORS = {
    "usergroups": {
        "title": "مجموعات الأعضاء",
        "hint": "كل مجموعة لها ملف فوترة افتراضي ونسبة خصم ونقاط.",
        "columns": [
            ("name", "المجموعة", "text", 150),
            ("kind", "النوع", "text", 100),
            ("profile", "ملف الفوترة", "profile", 190),
            ("discount", "خصم %", "int", 90),
            ("points", "نقاط/ساعة", "int", 100),
        ],
    },
    "hostgroups": {
        "title": "مجموعات الأجهزة",
        "hint": "تجاوز سعر مجموعة العضو عند اللعب على أجهزة معينة (VIP أو كونسول).",
        "columns": [
            ("name", "المجموعة", "text", 170),
            ("profile", "ملف بديل", "profile", 200),
            ("note", "ملاحظة", "text", 280),
        ],
    },
    "profiles": {
        "title": "ملفات الفوترة",
        "hint": "السعر بالساعة، أقل مدة، وتقريب الوقت، وأسعار ساعات محددة.",
        "columns": [
            ("name", "الملف", "text", 170),
            ("hourly", "سعر الساعة", "float", 110),
            ("minimum", "أقل دقيقة", "int", 100),
            ("round", "تقريب", "int", 90),
            ("custom", "أسعار مخصصة", "text", 220),
        ],
    },
    "offers": {
        "title": "عروض الوقت",
        "hint": "باقات وقت بسعر ثابت، ويمكن حصرها في ساعات معينة.",
        "columns": [
            ("name", "العرض", "text", 180),
            ("minutes", "الدقائق", "int", 100),
            ("price", "السعر", "float", 100),
            ("from", "من", "text", 80),
            ("to", "إلى", "text", 80),
        ],
    },
}

TABS = [
    ("usergroups", "مجموعات الأعضاء"),
    ("hostgroups", "مجموعات الأجهزة"),
    ("profiles", "ملفات الفوترة"),
    ("offers", "عروض الوقت"),
]


class BillingWidget(QWidget):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.data = data
        self.catalog = BillingCatalog(data)
        self.tables = {}
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
        self.tabs = Segmented([(key, title) for key, title in TABS], "profiles")
        self.tabs.changed.connect(self._switch)
        toolbar.addWidget(self.tabs, 1)
        toolbar.addWidget(button("إضافة صف", "quiet", self._add_row, compact=True))
        toolbar.addWidget(button("حذف المحدد", "ghost", self._remove_row, compact=True))
        toolbar.addWidget(button("حفظ", "primary", self.save, compact=True))
        root.addLayout(toolbar)

        summary = QHBoxLayout()
        summary.setSpacing(12)
        self.kpi_profiles = self._kpi("ملفات الفوترة", "—", "سعر مستقل لكل فئة")
        self.kpi_users = self._kpi("مجموعات الأعضاء", "—", "زائر / عضو / VIP")
        self.kpi_hosts = self._kpi("مجموعات الأجهزة", "—", "تجاوز السعر حسب الجهاز")
        self.kpi_offers = self._kpi("عروض نشطة", "—", "الآن حسب الساعة")
        for card in (self.kpi_profiles, self.kpi_users, self.kpi_hosts, self.kpi_offers):
            summary.addWidget(card, 1)
        root.addLayout(summary)

        self.body = QVBoxLayout()
        self.body.setSpacing(10)
        root.addLayout(self.body)

        self.preview = Card(padding=14, spacing=6)
        self.preview.body.addWidget(label("أسعار الآن", "Title"))
        self.preview_hint = label("", "Caption")
        self.preview.setMinimumHeight(210)
        self.preview.body.addWidget(self.preview_hint)
        self.preview_rows = QGridLayout()
        self.preview_rows.setHorizontalSpacing(16)
        self.preview_rows.setVerticalSpacing(4)
        self.preview_rows.setColumnStretch(0, 0)
        self.preview_rows.setColumnStretch(1, 0)
        self.preview_rows.setColumnStretch(2, 1)
        self.preview.body.addLayout(self.preview_rows)
        self.preview.body.addWidget(hline())
        self.offers_line = label("", "Muted")
        self.preview.body.addWidget(self.offers_line)
        root.addWidget(self.preview)
        root.addStretch(1)

        self.footer = label("", "Caption")
        root.addWidget(self.footer)

        self._build_tabs()

    def _kpi(self, title, value, hint):
        card = Card(padding=14, spacing=2)
        card.body.addWidget(label(title, "Caption"))
        number = label(value, "H2")
        card.body.addWidget(number)
        card.body.addWidget(label(hint, "Caption"))
        card.number = number
        return card

    # ── tables ───────────────────────────────────────────────────────────
    def _build_tabs(self):
        for key, spec in EDITORS.items():
            card = Card(padding=12, spacing=6)
            card.body.addWidget(label(spec["title"], "Title"))
            card.body.addWidget(label(spec["hint"], "Caption"))
            table = QTableWidget(0, len(spec["columns"]))
            table.setHorizontalHeaderLabels([column[1] for column in spec["columns"]])
            table.verticalHeader().setVisible(False)
            table.setAlternatingRowColors(True)
            table.setShowGrid(False)
            table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            for index, column in enumerate(spec["columns"]):
                table.setColumnWidth(index, column[3])
            table.horizontalHeader().setStretchLastSection(True)
            table.itemChanged.connect(lambda _item, k=key: self._refresh_preview())
            card.body.addWidget(table)
            self.tables[key] = table
            self.body.addWidget(card)

        self._switch("profiles")

    def _switch(self, key: str):
        for table_key, table in self.tables.items():
            container = table
            while container is not None and container.__class__.__name__ != "Card":
                container = container.parentWidget()
            if container is not None:
                container.setVisible(table_key == key)
        self._refresh_preview()

    def _fill(self, key: str, rows):
        table = self.tables[key]
        spec = EDITORS[key]
        table.blockSignals(True)
        table.setRowCount(0)
        for row in rows:
            position = table.rowCount()
            table.insertRow(position)
            for index, (field, _title, kind, _width) in enumerate(spec["columns"]):
                value = row.get(field, False if kind == "bool" else "")
                item = QTableWidgetItem()
                if kind == "bool":
                    item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled
                                  | Qt.ItemFlag.ItemIsSelectable)
                    item.setCheckState(Qt.CheckState.Checked if value else Qt.CheckState.Unchecked)
                elif kind == "profile":
                    item.setText(str(value or "—"))
                else:
                    item.setText(str(value))
                item.setData(Qt.ItemDataRole.UserRole, str(value))
                table.setItem(position, index, item)
            table.setRowHeight(position, 36)
        table.blockSignals(False)
        visible = max(3, table.rowCount())
        table.setFixedHeight(min(430, 46 + visible * 36))

    def reload(self):
        self.catalog = BillingCatalog(self.data)
        self._fill("usergroups", self.catalog.user_groups())
        self._fill("hostgroups", self.catalog.host_groups())
        self._fill("profiles", self.catalog.profiles())
        self._fill("offers", self.catalog.offers())

        summary = self.catalog.summary()
        self.kpi_profiles.number.setText(str(summary["profiles"]))
        self.kpi_users.number.setText(str(summary["user_groups"]))
        self.kpi_hosts.number.setText(str(summary["host_groups"]))
        self.kpi_offers.number.setText(str(summary["offers"]))
        self._refresh_preview()
        self.footer.setText(f"آخر تحديث {datetime.now().strftime('%H:%M')}")

    # ── reading the grids ────────────────────────────────────────────────
    def _rows(self, key: str):
        table = self.tables[key]
        spec = EDITORS[key]
        rows = []
        for position in range(table.rowCount()):
            row = {}
            empty = True
            for index, (field, _title, kind, _width) in enumerate(spec["columns"]):
                item = table.item(position, index)
                text = item.text().strip() if item is not None else ""
                if kind in ("int", "float"):
                    try:
                        row[field] = int(float(text or 0)) if kind == "int" else float(text or 0)
                    except ValueError:
                        row[field] = 0 if kind == "int" else 0.0
                else:
                    row[field] = text
                if text:
                    empty = False
            if not empty:
                rows.append(row)
        return rows

    def _add_row(self):
        key = self.tabs.current
        table = self.tables[key]
        position = table.rowCount()
        table.insertRow(position)
        spec = EDITORS[key]
        for index, (_field, _title, kind, _width) in enumerate(spec["columns"]):
            item = QTableWidgetItem("")
            if kind in ("int", "float"):
                item.setText("0")
            table.setItem(position, index, item)
        table.setCurrentCell(position, 0)
        table.editItem(table.item(position, 0))

    def _remove_row(self):
        table = self.tables[self.tabs.current]
        row = table.currentRow()
        if row >= 0:
            table.removeRow(row)
            self._refresh_preview()

    def save(self):
        store = getattr(self.data, "settings", None)
        payloads = {
            "billing.usergroups": {"rows": self._rows("usergroups")},
            "billing.hostgroups": {"rows": self._rows("hostgroups")},
            "billing.profiles": {"rows": self._rows("profiles")},
            "billing.offers": {"rows": self._rows("offers")},
        }
        ok = True
        for key, payload in payloads.items():
            if store is not None:
                ok = store.save_section(key, payload) and ok
        Toast(self, "حُفظت إعدادات الفوترة" if ok else "حُفظت مؤقتاً — القاعدة غير متصلة",
              "success" if ok else "warning")
        self.catalog = BillingCatalog(self.data)
        self._refresh_preview()

    # ── live preview ─────────────────────────────────────────────────────
    def _refresh_preview(self):
        while self.preview_rows.count():
            item = self.preview_rows.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        now = datetime.now()
        groups = self._rows("usergroups") or self.catalog.user_groups()
        shown = 0
        for index, group in enumerate(groups[:5]):
            name = group.get("name") or "—"
            rate = self.catalog.rate_for(name, "أجهزة PC", now)
            notes = [rate["profile"]]
            if rate.get("window"):
                notes.append(f"سعر الفترة {rate['window']}")
            if rate.get("discount"):
                notes.append(f"خصم {rate['discount']:.0f}%")
            name_label = label(name, "Body")
            name_label.setMinimumWidth(70)
            self.preview_rows.addWidget(name_label, index, 0)
            price_label = label(f"{rate['hourly']:,.2f} ر.س/ساعة\u200f", "Body")
            price_label.setMinimumWidth(110)
            self.preview_rows.addWidget(price_label, index, 1)
            note_label = label(" · ".join(notes), "Caption")
            note_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.preview_rows.addWidget(note_label, index, 2)
            shown += 1
        if not shown:
            self.preview_rows.addWidget(label("لا توجد مجموعات بعد.", "Caption"))
        self.preview_hint.setText(
            f"السعر يُحسب الآن ({now.strftime('%H:%M')}) حسب الساعة ومجموعة اللاعب والجهاز."
        )
        offers = self.catalog.active_offers(now)
        self.offers_line.setText(
            "عروض سارية الآن: " + " · ".join(
                f"{offer.get('name')} ({format_minutes(offer.get('minutes'))} بـ{offer.get('price')})"
                for offer in offers
            ) if offers else "لا توجد عروض سارية في هذه الساعة."
        )


class OfferDialog(FormDialog):
    """Small helper used by the POS quick-sale list."""

    def __init__(self, offers, parent=None):
        super().__init__("عرض وقت", "اختر الباقة", parent, width=380)
        from PyQt6.QtWidgets import QComboBox

        self.combo = QComboBox()
        for offer in offers:
            self.combo.addItem(
                f"{offer.get('name')} · {offer.get('minutes')} د · {offer.get('price')} ر.س",
                offer,
            )
        self.add_field("الباقة", self.combo)

    def values(self):
        return self.combo.currentData() or {}
