# -*- coding: utf-8 -*-
"""Tasks: small, explicit jobs an admin runs on purpose — with visible output."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import time
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLineEdit, QMessageBox, QPlainTextEdit, QScrollArea,
    QVBoxLayout, QWidget,
)

from Manager.commands import CommandClient
from Manager.theme import Colors
from Manager.ui import Card, Pill, Segmented, Toast, button, hline, label

CATEGORIES = [("all", "الكل"), ("system", "نظام"), ("network", "شبكة"), ("data", "بيانات")]

TASKS = [
    {"key": "ping", "cat": "network", "name": "فحص اتصال السيرفر",
     "text": "يرسل PING ويتأكد أن السيرفر يرد."},
    {"key": "db", "cat": "data", "name": "فحص قاعدة البيانات",
     "text": "اتصال سريع وقراءة إصدار SQL Server."},
    {"key": "export", "cat": "data", "name": "تصدير ملخص اليوم",
     "text": "يكتب ملف CSV بملخص الأجهزة والمبيعات."},
    {"key": "temp", "cat": "system", "name": "تنظيف الملفات المؤقتة",
     "text": "يحذف ملفات أقدم من 24 ساعة داخل مجلد Temp."},
    {"key": "disk", "cat": "system", "name": "مساحة القرص",
     "text": "يعرض المتاح والمستخدم على قرص النظام."},
    {"key": "unlock", "cat": "network", "name": "فتح كل الشاشات",
     "text": "يرسل فتح الشاشة إلى الأجهزة المشغولة."},
    {"key": "restart", "cat": "network", "name": "إعادة تشغيل الأجهزة",
     "text": "يعيد تشغيل كل الأجهزة المتصلة — يحتاج تأكيداً."},
]


class TaskRow(QFrame):
    def __init__(self, task: dict, on_run, parent=None):
        super().__init__(parent)
        self.setObjectName("Inset")
        self.task = task
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(12)

        text = QVBoxLayout()
        text.setSpacing(2)
        text.addWidget(label(task["name"], "Body"))
        text.addWidget(label(task["text"], "Caption"))
        layout.addLayout(text, 1)
        layout.addWidget(button("تشغيل", "ghost", lambda: on_run(task), compact=True))


class TasksWidget(QWidget):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.data = data
        self.category = "all"
        self._build()
        self._render()

    def set_navigator(self, _navigate):
        pass

    def _build(self):
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        root = QHBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(14)

        left = QVBoxLayout()
        left.setSpacing(10)
        self.filter = Segmented(CATEGORIES, "all")
        self.filter.changed.connect(self._change_category)
        left.addWidget(self.filter, alignment=Qt.AlignmentFlag.AlignRight)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        host = QWidget()
        self.list_layout = QVBoxLayout(host)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(8)
        self.list_layout.addStretch()
        scroll.setWidget(host)
        left.addWidget(scroll, 1)

        left.addWidget(label("أمر مخصص", "Title"))
        custom = QHBoxLayout()
        self.custom_input = QLineEdit()
        self.custom_input.setPlaceholderText("مثال: ipconfig /flushdns")
        custom.addWidget(self.custom_input, 1)
        custom.addWidget(button("تشغيل", "primary", self._run_custom))
        left.addLayout(custom)
        root.addLayout(left, 3)

        console = Card(padding=14)
        head = QHBoxLayout()
        head.addWidget(label("السجل", "Title"))
        self.state = Pill("جاهز", "muted")
        head.addStretch()
        head.addWidget(self.state)
        head.addWidget(button("مسح", "ghost", self._clear, compact=True))
        console.body.addLayout(head)
        console.body.addWidget(hline())
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet(
            f"QPlainTextEdit {{ background-color: {Colors.BG_CARD_LIGHT};"
            f" border: 1px solid {Colors.BORDER}; border-radius: 10px;"
            f" padding: 10px; font-family: Consolas, 'Courier New', monospace; font-size: 12px; }}"
        )
        console.body.addWidget(self.output, 1)
        root.addWidget(console, 2)

    def on_shown(self):
        pass

    def _change_category(self, key: str):
        self.category = key
        self._render()

    def _render(self):
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for task in TASKS:
            if self.category != "all" and task["cat"] != self.category:
                continue
            self.list_layout.insertWidget(self.list_layout.count() - 1, TaskRow(task, self.run))

    def _write(self, text: str, tone: str = "muted"):
        stamp = datetime.now().strftime("%H:%M:%S")
        self.output.appendPlainText(f"[{stamp}] {text}")

    def _clear(self):
        self.output.clear()

    def run(self, task: dict):
        key = task["key"]
        if key == "restart":
            answer = QMessageBox.question(
                self, "إعادة تشغيل الأجهزة",
                "سيُعاد تشغيل كل الأجهزة المتصلة. متابعة؟",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
        self.state.setText("يعمل…")
        self.state.set_tone("warning")
        self._write(f"تشغيل: {task['name']}")
        try:
            result = getattr(self, f"_{key}")()
        except Exception as error:  # noqa: BLE001 - surfaced to the operator
            result = f"فشل: {error}"
        self._write(result)
        self.state.setText("جاهز")
        self.state.set_tone("muted")

    # ── handlers ─────────────────────────────────────────────────────────
    def _ping(self):
        ok, message = CommandClient().send("PING")
        self.data.execute(
            "INSERT INTO ActivityLog (LogType, UserName, Description) VALUES (?, ?, ?)",
            ("task", "manager", f"فحص السيرفر: {'نجح' if ok else 'فشل'}"),
        )
        return f"السيرفر: {'متاح — ' + message if ok else message}"

    def _db(self):
        live = self.data.live
        if not live:
            return "تعذر الاتصال بقاعدة البيانات. راجع Server/config.py"
        rows = self.data.db.execute_query("SELECT @@VERSION AS v")
        version = str(rows[0].get("v", "")).splitlines()[0] if rows else "غير معروف"
        return f"متصل — {version}"

    def _export(self):
        folder = Path("Exports")
        folder.mkdir(exist_ok=True)
        target = folder / f"summary-{datetime.now():%Y%m%d-%H%M}.csv"
        stats = self.data.today_stats()
        target.write_text(
            "البند,القيمة\n"
            f"أجهزة مشغولة,{stats['hosts_busy']}\n"
            f"أجهزة جاهزة,{stats['hosts_idle']}\n"
            f"أعضاء,{stats['members']}\n"
            f"إيراد اليوم,{stats['revenue']:.2f}\n",
            encoding="utf-8-sig",
        )
        return f"حُفظ الملف: {target}"

    def _temp(self):
        root = Path(tempfile.gettempdir())
        cutoff = time.time() - 86400
        removed = 0
        for item in root.iterdir():
            try:
                if item.is_file() and item.stat().st_mtime < cutoff:
                    item.unlink()
                    removed += 1
            except OSError:
                continue
        return f"حُذف {removed} ملف من {root}"

    def _disk(self):
        usage = shutil.disk_usage(Path.cwd().anchor or "/")
        free = usage.free / (1024 ** 3)
        total = usage.total / (1024 ** 3)
        return f"متاح {free:.1f}GB من {total:.1f}GB"

    def _unlock(self):
        busy = [h.get("HostName") for h in self.data.hosts()
                if str(h.get("Status")) in ("مشغول", "InUse", "Busy")]
        ok, message = CommandClient().send("DEVICE_UNLOCK_ALL", {"hosts": busy})
        return f"{'أُرسل إلى ' + str(len(busy)) + ' جهاز' if ok else message}"

    def _restart(self):
        hosts = [h.get("HostName") for h in self.data.hosts()]
        ok, message = CommandClient().send("DEVICE_RESTART_ALL", {"hosts": hosts})
        return f"{'أُرسل إلى ' + str(len(hosts)) + ' جهاز' if ok else message}"

    def _run_custom(self):
        command = self.custom_input.text().strip()
        if not command:
            Toast(self, "اكتب الأمر أولاً", "warning")
            return
        answer = QMessageBox.question(
            self, "أمر مخصص",
            f"سيُنفَّذ على هذا الجهاز:\n{command}\n\nمتابعة؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self._write(f"$ {command}")
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=25
            )
            output = (result.stdout or result.stderr or "").strip()
            self._write(output[:4000] or f"انتهى بالرمز {result.returncode}")
        except subprocess.TimeoutExpired:
            self._write("تجاوز الأمر 25 ثانية وتم إيقافه")
        except OSError as error:
            self._write(f"تعذر التشغيل: {error}")
