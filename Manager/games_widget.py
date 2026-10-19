# -*- coding: utf-8 -*-
"""Game library: posters you can scan quickly, and controls that do something."""

from __future__ import annotations

import os

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QComboBox, QDialog, QFileDialog, QFrame, QGridLayout, QHBoxLayout,
    QLabel, QLineEdit, QMessageBox, QScrollArea, QTextEdit, QVBoxLayout, QWidget,
)

from Manager.theme import Colors
from Manager.trailer_dialog import TrailerPlayerDialog
from Manager.ui import (
    Card, EmptyState, FormDialog, SearchInput, Toast, button, hline, label,
)

PLATFORMS = ["Steam", "Epic Games", "EA App", "Battle.net", "Riot", "Standalone"]


class GameDialog(FormDialog):
    def __init__(self, data, game: dict = None, parent=None):
        editing = bool(game and game.get("GameId"))
        super().__init__(
            "تعديل لعبة" if editing else "لعبة جديدة",
            "البوستر يظهر بنسبة 3:4، وملف التشغيل يُستخدم من العميل.",
            parent, width=520,
        )
        self.data = data
        self.game = game or {}
        self.icon_path = self.game.get("IconPath") or ""

        self.name = self.add_field("اسم اللعبة", QLineEdit(self.game.get("GameName") or ""))
        self.category = self.add_field(
            "التصنيف", QComboBox()
        )
        self.category.addItems(data.categories())
        if self.game.get("Category"):
            if self.category.findText(self.game["Category"]) < 0:
                self.category.addItem(self.game["Category"])
            self.category.setCurrentText(self.game["Category"])

        self.platform = self.add_field("المنصة", QComboBox())
        self.platform.addItems(PLATFORMS)
        if self.game.get("Platform"):
            self.platform.setCurrentText(self.game["Platform"])

        exe_row = QHBoxLayout()
        self.exe = QLineEdit(self.game.get("ExePath") or "")
        self.exe.setPlaceholderText(r"C:\Games\game.exe")
        browse_exe = button("استعراض", "ghost", self._browse_exe, compact=True)
        exe_row.addWidget(self.exe, 1)
        exe_row.addWidget(browse_exe)
        self.form.addWidget(label("ملف التشغيل", "Caption"))
        self.form.addLayout(exe_row)

        self.trailer = self.add_field("رابط العرض", QLineEdit(self.game.get("TrailerUrl") or ""))
        self.description = QTextEdit(self.game.get("Description") or "")
        self.description.setFixedHeight(74)
        self.add_field("وصف قصير", self.description)

        self.poster_row = label(
            "البوستر: " + (os.path.basename(self.icon_path) if self.icon_path else "لم يُحدَّد"), "Caption"
        )
        self.form.addWidget(self.poster_row)
        self.form.addWidget(button("اختيار بوستر", "ghost", self._browse_icon, compact=True))
        self.save_btn.setText("حفظ التعديل" if editing else "إضافة")

    def _browse_exe(self):
        path, _ = QFileDialog.getOpenFileName(self, "ملف اللعبة", "", "Executables (*.exe)")
        if path:
            self.exe.setText(path)

    def _browse_icon(self):
        path, _ = QFileDialog.getOpenFileName(self, "بوستر اللعبة", "", "Images (*.png *.jpg *.jpeg)")
        if path:
            self.icon_path = path
            self.poster_row.setText("البوستر: " + os.path.basename(path))

    def save(self) -> bool:
        name = self.name.text().strip()
        if not name:
            Toast(self, "اسم اللعبة مطلوب", "warning")
            return False
        values = (
            name, self.category.currentText(), self.platform.currentText(),
            self.exe.text().strip(), self.icon_path, self.trailer.text().strip(),
            self.description.toPlainText().strip(),
        )
        if not self.data.live:
            Toast(self, "قاعدة البيانات غير متصلة — لن يُحفظ التغيير", "warning")
            return False
        if self.game.get("GameId"):
            ok = self.data.execute(
                "UPDATE Games SET GameName = ?, Category = ?, Platform = ?, ExePath = ?,"
                " IconPath = ?, TrailerUrl = ?, Description = ? WHERE GameId = ?",
                values + (self.game["GameId"],),
            )
        else:
            ok = self.data.execute(
                "INSERT INTO Games (GameName, Category, Platform, ExePath, IconPath,"
                " TrailerUrl, Description) VALUES (?, ?, ?, ?, ?, ?, ?)", values,
            )
        if not ok:
            Toast(self, "تعذر الحفظ", "danger")
        return ok


class CategoriesDialog(QDialog):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.data = data
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setWindowTitle("التصنيفات")
        self.setFixedSize(380, 460)
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(10)
        root.addWidget(label("تصنيفات المكتبة", "Title"))

        self.list_layout = QVBoxLayout()
        self.list_layout.setSpacing(6)
        root.addLayout(self.list_layout)
        root.addStretch()

        add_row = QHBoxLayout()
        self.input = QLineEdit()
        self.input.setPlaceholderText("تصنيف جديد")
        add_row.addWidget(self.input, 1)
        add_row.addWidget(button("إضافة", "primary", self._add, compact=True))
        root.addLayout(add_row)
        self._fill()

    def _fill(self):
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for name in self.data.categories():
            row = QFrame()
            row.setObjectName("Inset")
            line = QHBoxLayout(row)
            line.setContentsMargins(10, 6, 10, 6)
            line.addWidget(label(name, "Body"))
            self.list_layout.addWidget(row)

    def _add(self):
        name = self.input.text().strip()
        if not name:
            return
        if not self.data.live:
            Toast(self, "قاعدة البيانات غير متصلة", "warning")
            return
        self.data.execute(
            "IF NOT EXISTS (SELECT 1 FROM GameCategories WHERE CategoryName = ?)"
            " INSERT INTO GameCategories (CategoryName) VALUES (?)", (name, name),
        )
        self.input.clear()
        self.data.invalidate()
        self._fill()


class GameCard(Card):
    def __init__(self, game: dict, on_play=None, on_trailer=None, on_edit=None, on_delete=None, parent=None):
        super().__init__(parent, padding=10, spacing=6)
        self.game = game
        self.setFixedWidth(196)

        poster = QLabel()
        poster.setFixedHeight(200)
        poster.setAlignment(Qt.AlignmentFlag.AlignCenter)
        poster.setWordWrap(True)
        icon = game.get("IconPath") or ""
        if icon and os.path.exists(icon):
            pixmap = QPixmap(icon)
            poster.setPixmap(pixmap.scaled(
                172, 200, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            ))
            poster.setScaledContents(False)
        else:
            initials = str(game.get("GameName") or "?")[:2].upper()
            poster.setText(initials)
            poster.setStyleSheet(
                f"background-color: {Colors.BG_CARD_LIGHT}; color: {Colors.CYAN};"
                f" border-radius: 10px; font-size: 42px; font-weight: 600;"
            )
        self.body.addWidget(poster)

        title = label(str(game.get("GameName") or "لعبة"), "Body")
        title.setWordWrap(True)
        self.body.addWidget(title)
        meta = label(
            f"{game.get('Category') or 'عام'}  ·  {game.get('Platform') or 'Standalone'}", "Caption"
        )
        self.body.addWidget(meta)

        row = QHBoxLayout()
        row.setSpacing(4)
        play = button("تشغيل", "primary", lambda: on_play(self.game) if on_play else None, compact=True)
        row.addWidget(play, 1)
        if on_trailer:
            row.addWidget(button("عرض", "ghost",
                                 lambda: on_trailer(self.game) if game.get("TrailerUrl") else None,
                                 compact=True))
        row.addWidget(button("تعديل", "ghost", lambda: on_edit(self.game) if on_edit else None, compact=True))
        self.body.addLayout(row)

        if on_delete and game.get("GameId"):
            self.body.addWidget(button("إخفاء من المكتبة", "danger",
                                       lambda: on_delete(self.game), compact=True))


class GamesWidget(QWidget):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.data = data
        self.games = []
        self.category = "all"
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
        self.search = SearchInput("ابحث باسم اللعبة")
        self.search.textChanged.connect(lambda _t: self._fill())
        toolbar.addWidget(self.search)
        self.category_filter = QComboBox()
        self.category_filter.setFixedWidth(170)
        self.category_filter.currentIndexChanged.connect(self._filter_changed)
        toolbar.addWidget(self.category_filter)
        toolbar.addStretch()
        toolbar.addWidget(button("التصنيفات", "ghost", self.open_categories, compact=True))
        toolbar.addWidget(button("لعبة جديدة", "primary", self.add_game, compact=True))
        root.addLayout(toolbar)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        host = QWidget()
        self.grid = QGridLayout(host)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(12)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(host)
        root.addWidget(scroll, 1)

        self.empty = EmptyState(
            "المكتبة فارغة",
            "أضف أول لعبة، أو وصّل قاعدة البيانات لقراءة الألعاب الحالية.",
            button("أضف لعبة", "primary", self.add_game),
        )
        root.addWidget(self.empty)
        self.empty.hide()

    def on_shown(self):
        self.reload()

    def reload(self):
        self.games = self.data.games()
        self._refresh_categories()
        self._fill()

    def _refresh_categories(self):
        names = self.data.categories()
        current = self.category_filter.currentText()
        self.category_filter.blockSignals(True)
        self.category_filter.clear()
        self.category_filter.addItem("كل التصنيفات", "all")
        for name in names:
            self.category_filter.addItem(name, name)
        index = self.category_filter.findData(current)
        self.category_filter.setCurrentIndex(index if index >= 0 else 0)
        self.category_filter.blockSignals(False)
        self.category = self.category_filter.currentData() or "all"

    def _filter_changed(self, _index):
        self.category = self.category_filter.currentData() or "all"
        self._fill()

    def _visible(self):
        needle = self.search.text().strip().lower()
        rows = self.games
        if self.category != "all":
            rows = [g for g in rows if g.get("Category") == self.category]
        if needle:
            rows = [g for g in rows if needle in str(g.get("GameName", "")).lower()]
        return rows

    def _fill(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        rows = self._visible()
        columns = max(2, (self.width() - 40) // 210)
        for index, game in enumerate(rows):
            card = GameCard(
                game, on_play=self.launch, on_trailer=self.trailer,
                on_edit=self.edit_game, on_delete=self.hide_game,
            )
            self.grid.addWidget(card, index // columns, index % columns)
        self.empty.setVisible(not rows)

    def add_game(self):
        dialog = GameDialog(self.data, parent=self)
        if dialog.exec() != GameDialog.DialogCode.Accepted:
            return
        if dialog.save():
            self.data.invalidate()
            self.reload()
            Toast(self, "أُضيفت اللعبة", "success")

    def edit_game(self, game: dict):
        if not game.get("GameId"):
            Toast(self, "هذه لعبة تجريبية غير محفوظة", "warning")
            return
        dialog = GameDialog(self.data, game, parent=self)
        if dialog.exec() != GameDialog.DialogCode.Accepted:
            return
        if dialog.save():
            self.data.invalidate()
            self.reload()
            Toast(self, "حُفظت التعديلات", "success")

    def hide_game(self, game: dict):
        answer = QMessageBox.question(self, "إخفاء اللعبة", f"إخفاء {game.get('GameName')} من المكتبة؟")
        if answer != QMessageBox.StandardButton.Yes:
            return
        ok = self.data.execute("UPDATE Games SET IsVisible = 0 WHERE GameId = ?", (game.get("GameId"),))
        Toast(self, "أُخفيت اللعبة" if ok else "تعذر الإخفاء",
              "success" if ok else "danger")
        self.data.invalidate()
        self.reload()

    def open_categories(self):
        CategoriesDialog(self.data, self).exec()
        self.data.invalidate()
        self.reload()

    def trailer(self, game: dict):
        url = game.get("TrailerUrl")
        if url:
            TrailerPlayerDialog(str(game.get("GameName")), url, self).exec()

    def launch(self, game: dict):
        ok, message = (False, "لعبة غير محفوظة")
        if game.get("GameId"):
            from Manager.commands import CommandClient
            ok, message = CommandClient().send(
                "DEVICE_LAUNCH", {"game": game.get("GameName"), "exe": game.get("ExePath")}
            )
        Toast(
            self,
            f"أُرسل أمر تشغيل {game.get('GameName')}" if ok else f"لم يُرسل: {message}",
            "success" if ok else "warning", 3200,
        )
