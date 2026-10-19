# -*- coding: utf-8 -*-
"""Receipts: build the bill, preview it and send it to a printer.

The receipt is plain text laid out for 80 mm thermal paper, with an optional
HTML preview so the cashier sees exactly what will be printed. The same module
sends the ESC/POS pulse that opens the cash drawer.
"""

from __future__ import annotations

import os
from datetime import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextDocument
from PyQt6.QtWidgets import QDialog, QHBoxLayout, QTextBrowser, QVBoxLayout

from Manager.theme import Colors
from Manager.ui import Card, Toast, button, label

DEFAULT_DRAWER_CODE = "27,112,0,25,250"


def _value(store, section: str, key: str, default=None):
    try:
        return store.section(section).get(key, default)
    except Exception:
        return default


def receipt_settings(store) -> dict:
    section = {}
    try:
        section = store.section("receipts") or {}
    except Exception:
        section = {}
    return {
        "header": section.get("header") or "GT Gaming Center",
        "footer": section.get("footer") or "شكراً لزيارتكم",
        "show_tax": bool(section.get("show_tax", True)),
        "show_qr": bool(section.get("show_qr", True)),
        "open_drawer": bool(section.get("open_drawer", True)),
        "copies": int(section.get("copies") or 1),
        "drawer_code": section.get("drawer_code") or DEFAULT_DRAWER_CODE,
        "prefix": section.get("prefix") or "INV",
        "width_mm": int(section.get("width_mm") or 80),
        "printer": section.get("printer") or "",
    }


def receipt_number(prefix: str = "INV") -> str:
    return f"{prefix}-{datetime.now().strftime('%y%m%d-%H%M%S')}"


def build_lines(items, subtotal: float, tax: float, total: float, store,
                cashier: str = "", member: str = "", paid: float = None) -> list[str]:
    """Plain-text receipt, ready for an 80 mm thermal printer."""
    cfg = receipt_settings(store)
    currency = ""
    money = None
    try:
        currency = store.currency()
        money = store.money
    except Exception:
        currency = "ر.س"

    def amount(value):
        return money(value) if money else f"{value:,.2f} {currency}"

    width = 40
    lines = [cfg["header"].center(width), "=" * width,
             f"رقم الفاتورة: {receipt_number(cfg['prefix'])}",
             f"التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}"]
    if cashier:
        lines.append(f"الكاشير: {cashier}")
    if member:
        lines.append(f"اللاعب: {member}")
    lines.append("=" * width)

    for item in items:
        name = str(item.get("name") or item.get("ProductName") or "صنف")
        qty = int(item.get("qty") or item.get("Quantity") or 1)
        unit = float(item.get("price") or item.get("UnitPrice") or 0)
        lines.append(name)
        lines.append(f"  {qty} × {amount(unit)} = {amount(qty * unit)}")

    lines.append("-" * width)
    lines.append(f"المجموع: {amount(subtotal)}")
    if tax:
        rate = 0.0
        try:
            rate = store.tax()[0]
        except Exception:
            pass
        label_text = f"الضريبة {rate * 100:.0f}%" if rate else "الضريبة"
        lines.append(f"{label_text}: {amount(tax)}")
    lines.append(f"الإجمالي: {amount(total)}")
    if paid is not None:
        lines.append(f"المدفوع: {amount(paid)}")
        change = paid - total
        if change >= 0:
            lines.append(f"الباقي: {amount(change)}")
    lines.append("=" * width)
    lines.append(cfg["footer"])
    if cfg["show_qr"]:
        lines.append("QR: " + receipt_number(cfg["prefix"]))
    return lines


def _has_arabic(text: str) -> bool:
    return any("\u0600" <= character <= "\u06ff" for character in text)


def receipt_html(lines: list[str]) -> str:
    rows = []
    for line in lines:
        content = line.replace(" ", "&nbsp;") or "&nbsp;"
        direction = "rtl" if _has_arabic(line) else "ltr"
        align = "right" if direction == "rtl" else "left"
        rows.append(
            f"<div dir='{direction}' style='margin:0;padding:0;text-align:{align};"
            f"unicode-bidi:plaintext'>{content}</div>"
        )
    body = "".join(rows)
    return (
        "<div style='background:#0f1720;padding:10px'>"
        "<div dir='rtl' style='font-family:Consolas,monospace;font-size:12px;"
        f"color:{Colors.TEXT_PRIMARY};background:#ffffff;padding:14px;"
        "border-radius:8px;line-height:1.5'>"
        f"<div style='color:#111'>{body}</div>"
        "</div></div>"
    )


def send_to_printer(lines: list[str], store, parent=None) -> bool:
    """Print through Qt when a printer is configured; otherwise report why not."""
    try:
        from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
    except Exception:
        if parent is not None:
            Toast(parent, "طباعة الإيصال غير متاحة على هذا النظام", "warning")
        return False

    cfg = receipt_settings(store)
    document = QTextDocument()
    document.setPlainText("\n".join(lines))

    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setDocName("Receipt")
    if cfg["printer"]:
        from PyQt6.QtPrintSupport import QPrinterInfo

        for info in QPrinterInfo.availablePrinters():
            if info.printerName() == cfg["printer"]:
                printer.setPrinterName(info.printerName())
                break

    dialog = QPrintDialog(printer, parent) if parent is not None else None
    if dialog is not None and dialog.exec() != QDialog.DialogCode.Accepted:
        return False
    document.print(printer)
    return True


def open_cash_drawer(store=None, parent=None) -> bool:
    """Send the ESC/POS pulse; on Windows this writes raw bytes to the spooler."""
    code = DEFAULT_DRAWER_CODE
    if store is not None:
        try:
            code = receipt_settings(store)["drawer_code"] or DEFAULT_DRAWER_CODE
        except Exception:
            pass
    payload = bytes(int(part.strip()) for part in code.split(",") if part.strip())
    try:
        import win32print  # type: ignore

        printer_name = win32print.GetDefaultPrinter()
        handle = win32print.OpenPrinter(printer_name)
        try:
            win32print.StartDocPrinter(handle, 1, ("drawer", None, "RAW"))
            win32print.StartPagePrinter(handle)
            win32print.WritePrinter(handle, payload)
            win32print.EndPagePrinter(handle)
            win32print.EndDocPrinter(handle)
        finally:
            win32print.ClosePrinter(handle)
        return True
    except Exception:
        return False


class ReceiptDialog(QDialog):
    """Preview + print + drawer, shown right after checkout."""

    def __init__(self, lines: list[str], store, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setWindowTitle("الإيصال")
        self.setMinimumSize(420, 560)
        self.lines = lines
        self.store = store

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(10)

        head = QHBoxLayout()
        head.addWidget(label("الإيصال جاهز", "Title"))
        head.addStretch()
        head.addWidget(label(receipt_number(receipt_settings(store)["prefix"]), "Caption"))
        root.addLayout(head)

        card = Card(padding=8, spacing=4)
        self.view = QTextBrowser()
        self.view.setOpenExternalLinks(False)
        self.view.setHtml(receipt_html(lines))
        card.body.addWidget(self.view)
        root.addWidget(card, 1)

        actions = QHBoxLayout()
        actions.setSpacing(8)
        actions.addWidget(button("طباعة", "primary", self.print_now, compact=True))
        actions.addWidget(button("فتح الدرج", "quiet", self.drawer_now, compact=True))
        actions.addWidget(button("نسخ النص", "ghost", self.copy_text, compact=True))
        actions.addStretch()
        actions.addWidget(button("إغلاق", "ghost", self.accept, compact=True))
        root.addLayout(actions)

    def print_now(self):
        if send_to_printer(self.lines, self.store, self):
            Toast(self, "أُرسل الإيصال إلى الطابعة", "success")
        else:
            Toast(self, "لم تُنفَّذ الطباعة — تحقق من الطابعة", "warning")

    def drawer_now(self):
        ok = open_cash_drawer(self.store, self)
        Toast(self, "أُرسل أمر فتح الدرج" if ok else "تعذر فتح الدرج على هذا النظام",
              "success" if ok else "warning")

    def copy_text(self):
        from PyQt6.QtWidgets import QApplication

        QApplication.clipboard().setText("\n".join(self.lines))
        Toast(self, "نُسخ نص الإيصال", "success")


def receipt_path(lines: list[str]) -> str:
    """Save a copy under receipts/ for reference."""
    folder = os.path.join(os.getcwd(), "receipts")
    os.makedirs(folder, exist_ok=True)
    name = f"receipt-{datetime.now().strftime('%Y%m%d-%H%M%S')}.txt"
    path = os.path.join(folder, name)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines))
    return path
