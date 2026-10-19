# -*- coding: utf-8 -*-
"""Point of sale: pick items, adjust quantities, close the bill."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QMessageBox, QScrollArea, QSizePolicy,
    QVBoxLayout, QWidget,
)

from Manager.receipts import (
    ReceiptDialog, build_lines, open_cash_drawer, receipt_path, receipt_settings,
)
from Manager.ui import (
    Card, EmptyState, SearchInput, Segmented, Toast, button, hline, label,
)

FALLBACK_TAX = 0.15


def _currency_text(amount) -> str:
    try:
        return f"{float(amount or 0):,.2f} ر.س"
    except (TypeError, ValueError):
        return "0.00 ر.س"


class ProductTile(QFrame):
    def __init__(self, product: dict, on_add=None, parent=None):
        super().__init__(parent)
        self.product = product
        self.on_add = on_add
        self.setObjectName("Card")
        self.setMinimumHeight(112)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        top = QHBoxLayout()
        glyph = label(str(product.get("Icon") or product.get("IconPath") or "▦"), "Title")
        glyph.setStyleSheet("font-size: 20px;")
        stock = int(product.get("Stock") or 0)
        stock_pill = label(f"متبقي {stock}" if stock < 900 else "خدمة", "Caption")
        top.addWidget(glyph)
        top.addStretch()
        top.addWidget(stock_pill)
        layout.addLayout(top)

        name = label(str(product.get("ProductName") or "منتج"), "Body")
        name.setWordWrap(True)
        layout.addWidget(name)

        bottom = QHBoxLayout()
        price = label(_currency_text(product.get("Price")), "Title")
        add = button("إضافة", "ghost", self._add, compact=True)
        bottom.addWidget(price)
        bottom.addStretch()
        bottom.addWidget(add)
        layout.addLayout(bottom)

    def _add(self):
        if self.on_add:
            self.on_add(self.product)

    def mouseDoubleClickEvent(self, _event):
        self._add()


class POSWidget(QWidget):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.data = data
        self.cart = []
        self.products_data = []
        self.category = "all"
        self._build()
        self.reload()

    def set_navigator(self, _navigate):
        pass

    def _build(self):
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        root = QHBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        left = QVBoxLayout()
        left.setSpacing(12)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        self.search = SearchInput("ابحث عن منتج")
        self.search.textChanged.connect(lambda _text: self._fill_products())
        toolbar.addWidget(self.search)
        self.categories = Segmented([("all", "الكل")], "all")
        self.categories.changed.connect(self._category_changed)
        toolbar.addWidget(self.categories)
        toolbar.addStretch()
        left.addLayout(toolbar)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        host = QWidget()
        self.grid = QGridLayout(host)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(10)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(host)
        left.addWidget(scroll, 1)

        self.empty = EmptyState("لا توجد منتجات مطابقة", "غيّر التصنيف أو امسح البحث.")
        left.addWidget(self.empty)
        self.empty.hide()
        root.addLayout(left, 3)

        cart = Card(padding=16, spacing=10)
        cart.setFixedWidth(360)
        head = QHBoxLayout()
        head.addWidget(label("الفاتورة", "Title"))
        self.cart_count = label("0 عنصر", "Caption")
        head.addStretch()
        head.addWidget(self.cart_count)
        cart.body.addLayout(head)
        cart.body.addWidget(hline())

        self.cart_box = QVBoxLayout()
        self.cart_box.setSpacing(6)
        cart.body.addLayout(self.cart_box)
        cart.body.addStretch()

        cart.body.addWidget(hline())
        self.subtotal_label = label("المجموع 0.00", "Muted")
        self.tax_label = label("الضريبة 0.00", "Muted")
        self.total_label = label("0.00", "Money")
        cart.body.addWidget(self.subtotal_label)
        cart.body.addWidget(self.tax_label)
        cart.body.addWidget(self.total_label)
        cart.body.addWidget(button("إتمام البيع", "primary", self.checkout))
        self.receipt_button = button("الإيصال", "quiet", self.show_receipt, compact=True)
        self.receipt_button.setEnabled(False)
        cart.body.addWidget(self.receipt_button)
        cart.body.addWidget(button("تفريغ الفاتورة", "ghost", self.clear_cart, compact=True))
        root.addWidget(cart)

    # ── products ─────────────────────────────────────────────────────────
    def on_shown(self):
        self.reload()

    def reload(self):
        self.products_data = self.data.products()
        names = ["all"] + sorted({str(p.get("Category") or "عام") for p in self.products_data})
        labels = [("all", "الكل")] + [(name, name) for name in names[1:]]
        if [key for key, _ in labels] != [key for key, _ in self.categories.options]:
            if self.category not in {key for key, _ in labels}:
                self.category = "all"
            self.categories.options = labels
            self._rebuild_categories()
        self._fill_products()

    def _rebuild_categories(self):
        layout = self.categories.layout()
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.categories.buttons = {}
        for key, text in self.categories.options:
            widget = button(text, "ghost", lambda _c=False, k=key: self.categories.select(k), compact=True)
            widget.setCheckable(True)
            layout.addWidget(widget)
            self.categories.buttons[key] = widget
        self.categories.current = "all" if self.categories.current not in self.categories.buttons else self.categories.current
        self.categories._sync()

    def _category_changed(self, key: str):
        self.category = key
        self._fill_products()

    def _visible_products(self):
        needle = self.search.text().strip().lower()
        rows = self.products_data
        if self.category != "all":
            rows = [p for p in rows if str(p.get("Category")) == self.category]
        if needle:
            rows = [p for p in rows if needle in str(p.get("ProductName", "")).lower()]
        return rows

    def _fill_products(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        rows = self._visible_products()
        columns = 3
        for index, product in enumerate(rows):
            tile = ProductTile(product, on_add=self.add_to_cart)
            self.grid.addWidget(tile, index // columns, index % columns)
        self.empty.setVisible(not rows)

    # ── cart ─────────────────────────────────────────────────────────────
    def add_to_cart(self, product: dict):
        product_id = product.get("ProductId")
        for line in self.cart:
            if line["product"].get("ProductId") == product_id:
                line["qty"] += 1
                self._render_cart()
                return
        self.cart.append({"product": product, "qty": 1})
        self._render_cart()

    def clear_cart(self):
        self.cart.clear()
        self._render_cart()

    def _render_cart(self):
        while self.cart_box.count():
            item = self.cart_box.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        subtotal = 0.0
        count = 0
        for line in self.cart:
            product = line["product"]
            qty = line["qty"]
            total = float(product.get("Price") or 0) * qty
            subtotal += total
            count += qty

            row = QFrame()
            row.setObjectName("Inset")
            box = QHBoxLayout(row)
            box.setContentsMargins(10, 8, 10, 8)
            box.setSpacing(6)
            name = label(str(product.get("ProductName")), "Body")
            name.setWordWrap(True)
            box.addWidget(name, 1)
            box.addWidget(button("−", "ghost", lambda _c=False, l=line: self._change(l, -1), compact=True))
            box.addWidget(label(str(qty), "Body"))
            box.addWidget(button("+", "ghost", lambda _c=False, l=line: self._change(l, 1), compact=True))
            box.addWidget(button(f"{total:,.2f}", "ghost", lambda _c=False, l=line: self._change(l, -qty), compact=True))
            self.cart_box.addWidget(row)

        rate, inclusive, tax_name = self.data.settings.tax()
        tax = 0.0 if inclusive else subtotal * rate
        self._tax_rate = rate
        money = self.data.settings.money
        self.cart_count.setText(f"{count} عنصر")
        self.subtotal_label.setText(f"المجموع {money(subtotal)}")
        self.tax_label.setText(
            f"{tax_name} {rate * 100:.0f}%  {money(tax)}" if rate
            else f"{tax_name}: لا توجد ضريبة"
        )
        self.total_label.setText(self.data.settings.money(subtotal + tax))
        if hasattr(self, "receipt_button"):
            self.receipt_button.setEnabled(bool(self.cart))

    def _change(self, line: dict, delta: int):
        line["qty"] += delta
        if line["qty"] <= 0:
            self.cart.remove(line)
        self._render_cart()

    def remove_cart_item(self, row: int):
        if 0 <= row < len(self.cart):
            self.cart.pop(row)
            self._render_cart()

    def show_receipt(self):
        """Preview the bill before paying."""
        if not self.cart:
            Toast(self, "الفاتورة فارغة", "warning")
            return
        subtotal = sum(float(l["product"].get("Price") or 0) * l["qty"] for l in self.cart)
        rate, inclusive, _name = self.data.settings.tax()
        total = subtotal if inclusive else subtotal * (1 + rate)
        lines = build_lines(
            [
                {
                    "name": line["product"].get("ProductName"),
                    "qty": line["qty"],
                    "price": line["product"].get("Price"),
                }
                for line in self.cart
            ],
            subtotal,
            total - subtotal if not inclusive else 0.0,
            total,
            self.data.settings,
            cashier="مدير النظام",
        )
        ReceiptDialog(lines, self.data.settings, self).exec()

    # ── checkout ─────────────────────────────────────────────────────────
    def checkout(self):
        if not self.cart:
            Toast(self, "الفاتورة فارغة", "warning")
            return
        subtotal = sum(float(l["product"].get("Price") or 0) * l["qty"] for l in self.cart)
        rate, inclusive, _name = self.data.settings.tax()
        total = subtotal if inclusive else subtotal * (1 + rate)
        answer = QMessageBox.question(
            self, "إتمام البيع",
            f"سيتم تسجيل فاتورة بمبلغ {self.data.settings.money(total)}.\nهل تريد المتابعة؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        saved = True
        if self.data.live:
            for line in self.cart:
                product = line["product"]
                qty = line["qty"]
                unit = float(product.get("Price") or 0)
                ok = self.data.execute(
                    "INSERT INTO Orders (ProductId, ProductName, Quantity, UnitPrice,"
                    " TotalPrice, FinalAmount, Status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (product.get("ProductId"), product.get("ProductName"), qty,
                     unit, unit * qty, unit * qty * (1 + rate), "مكتمل"),
                )
                saved = saved and ok
                if int(product.get("Stock") or 0) < 900:
                    self.data.execute(
                        "UPDATE Products SET Stock = Stock - ? WHERE ProductId = ?",
                        (qty, product.get("ProductId")),
                    )
        else:
            saved = False

        if saved:
            Toast(self, f"سُجّلت الفاتورة — {self.data.settings.money(total)}", "success")
        else:
            Toast(self, "لم تُحفظ الفاتورة: قاعدة البيانات غير متصلة", "warning", 3200)
        lines = build_lines(
            [
                {
                    "name": line["product"].get("ProductName"),
                    "qty": line["qty"],
                    "price": line["product"].get("Price"),
                }
                for line in self.cart
            ],
            subtotal,
            total - subtotal if not inclusive else 0.0,
            total,
            self.data.settings,
            cashier="مدير النظام",
        )
        try:
            receipt_path(lines)
        except OSError:
            pass
        self.clear_cart()
        if saved:
            self.data.invalidate()
            self.reload()
        if receipt_settings(self.data.settings).get("open_drawer"):
            open_cash_drawer(self.data.settings, self)
        ReceiptDialog(lines, self.data.settings, self).exec()
