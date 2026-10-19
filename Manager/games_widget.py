import os
import requests
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QScrollArea, QLineEdit, QDialog,
    QFileDialog, QMessageBox, QComboBox, QTextEdit
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QPixmap, QIcon, QImage
from Manager.theme import Colors
from Manager.trailer_dialog import TrailerPlayerDialog

class GameCard(QFrame):
    def __init__(self, game: dict, on_play_trailer=None, on_launch=None):
        super().__init__()
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.game = game
        self.on_play_trailer = on_play_trailer
        self.on_launch = on_launch
        
        self.setFixedSize(200, 360)
        self.setObjectName("GameCard")
        self.setStyleSheet(f"""
            QFrame#GameCard {{
                background-color: {Colors.BG_CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: 12px;
            }}
            QFrame#GameCard:hover {{
                border-color: {Colors.CYAN};
                background-color: {Colors.BG_HOVER};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        self.poster_lbl = QLabel()
        self.poster_lbl.setFixedSize(180, 240)
        self.poster_lbl.setStyleSheet(f"background-color: {Colors.BG_CARD_LIGHT}; border-radius: 8px;")
        self.poster_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        icon_path = game.get("IconPath", "")
        if icon_path and os.path.exists(icon_path):
            pix = QPixmap(icon_path)
            self.poster_lbl.setPixmap(self.resize_to_poster(pix))
        else:
            self.poster_lbl.setText("🎮\n" + game.get("GameName", "لعبة"))
            self.poster_lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            self.poster_lbl.setStyleSheet(f"color: {Colors.TEXT_MUTED}; background-color: {Colors.BG_CARD_LIGHT}; border-radius: 8px;")
            
        layout.addWidget(self.poster_lbl)

        title_lbl = QLabel(game.get("GameName", "اسم اللعبة"))
        title_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        title_lbl.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_lbl)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(6)

        if game.get("TrailerUrl"):
            btn_trailer = QPushButton("🎬 العرض")
            btn_trailer.setFont(QFont("Segoe UI", 9))
            btn_trailer.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_trailer.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Colors.PURPLE}33;
                    color: {Colors.PURPLE};
                    border: 1px solid {Colors.PURPLE}66;
                    border-radius: 6px;
                    padding: 5px;
                }}
                QPushButton:hover {{
                    background-color: {Colors.PURPLE};
                    color: #ffffff;
                }}
            """)
            if self.on_play_trailer:
                btn_trailer.clicked.connect(lambda: self.on_play_trailer(self.game))
            btn_layout.addWidget(btn_trailer)

        btn_launch = QPushButton("▶ تشغيل")
        btn_launch.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        btn_launch.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_launch.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.CYAN};
                color: #000000;
                border: none;
                border-radius: 6px;
                padding: 5px;
            }}
            QPushButton:hover {{
                background-color: {Colors.CYAN}DD;
            }}
        """)
        if self.on_launch:
            btn_launch.clicked.connect(lambda: self.on_launch(self.game))
        btn_layout.addWidget(btn_launch)

        layout.addLayout(btn_layout)

    def resize_to_poster(self, pixmap: QPixmap) -> QPixmap:
        target_w, target_h = 180, 240
        scaled = pixmap.scaled(target_w, target_h, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
        x = (scaled.width() - target_w) // 2
        y = (scaled.height() - target_h) // 2
        return scaled.copy(x, y, target_w, target_h)

class AddGameDialog(QDialog):
    def __init__(self, db=None, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.db = db
        self.icon_path = ""
        self.setWindowTitle("إضافة لعبة جديدة")
        self.setFixedSize(480, 520)
        self.setStyleSheet(f"background-color: {Colors.BG_DARK}; color: {Colors.TEXT_PRIMARY};")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        lbl_head = QLabel("🎮 إضافة لعبة إلى المكتبة")
        lbl_head.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        lbl_head.setStyleSheet(f"color: {Colors.CYAN};")
        layout.addWidget(lbl_head)

        self.txt_name = QLineEdit()
        self.txt_name.setPlaceholderText("اسم اللعبة (مثال: FC 25)")
        
        self.combo_cat = QComboBox()
        self.combo_cat.addItems(["ألعاب قتال", "ألعاب رياضة", "ألعاب شوتر", "ألعاب مغامرات", "ألعاب استراتيجية"])

        self.combo_platform = QComboBox()
        self.combo_platform.addItems(["Steam", "EA App", "Epic Games", "Battle.net", "Riot Games", "Standalone"])

        self.txt_exe = QLineEdit()
        self.txt_exe.setPlaceholderText("مسار ملف التشغيل (Exe Path)...")
        btn_browse_exe = QPushButton("📁 استعراض")
        btn_browse_exe.clicked.connect(self.browse_exe)
        exe_layout = QHBoxLayout()
        exe_layout.addWidget(self.txt_exe)
        exe_layout.addWidget(btn_browse_exe)

        self.txt_trailer = QLineEdit()
        self.txt_trailer.setPlaceholderText("رابط التريلر (YouTube / MP4)...")

        self.txt_desc = QTextEdit()
        self.txt_desc.setPlaceholderText("وصف مختصر عن اللعبة...")
        self.txt_desc.setFixedHeight(60)

        btn_icon = QPushButton("🖼️ اختيار بوستر اللعبة (180x240)")
        btn_icon.clicked.connect(self.browse_icon)

        for w in [self.txt_name, self.combo_cat, self.combo_platform, self.txt_trailer, self.txt_desc, btn_icon]:
            w.setStyleSheet(f"background-color: {Colors.BG_CARD}; border: 1px solid {Colors.BORDER}; border-radius: 6px; padding: 8px; color: {Colors.TEXT_PRIMARY};")

        layout.addWidget(QLabel("اسم اللعبة:"))
        layout.addWidget(self.txt_name)
        layout.addWidget(QLabel("الفئة:"))
        layout.addWidget(self.combo_cat)
        layout.addWidget(QLabel("المنصة:"))
        layout.addWidget(self.combo_platform)
        layout.addWidget(QLabel("ملف التشغيل:"))
        layout.addLayout(exe_layout)
        layout.addWidget(QLabel("رابط العرض الترويجي (Trailer):"))
        layout.addWidget(self.txt_trailer)
        layout.addWidget(btn_icon)

        btn_save = QPushButton("💾 حفظ اللعبة")
        btn_save.setFixedHeight(40)
        btn_save.setStyleSheet(f"background-color: {Colors.GREEN}; color: #000000; font-weight: bold; border-radius: 6px;")
        btn_save.clicked.connect(self.save_game)
        layout.addWidget(btn_save)

    def browse_exe(self):
        f, _ = QFileDialog.getOpenFileName(self, "اختر ملف اللعبة", "", "Executables (*.exe)")
        if f:
            self.txt_exe.setText(f)

    def browse_icon(self):
        f, _ = QFileDialog.getOpenFileName(self, "اختر بوستر اللعبة", "", "Images (*.png *.jpg *.jpeg)")
        if f:
            self.icon_path = f

    def save_game(self):
        name = self.txt_name.text().strip()
        if not name:
            QMessageBox.warning(self, "خطأ", "برجاء إدخال اسم اللعبة.")
            return

        if self.db and hasattr(self.db, 'get_connection'):
            try:
                conn = self.db.get_connection()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO Games (GameName, Category, Platform, ExePath, IconPath, TrailerUrl, Description)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (name, self.combo_cat.currentText(), self.combo_platform.currentText(),
                          self.txt_exe.text(), self.icon_path, self.txt_trailer.text(), self.txt_desc.toPlainText()))
                    conn.commit()
                    conn.close()
            except Exception as e:
                print("Error saving game:", e)

        self.accept()

class CategoriesDialog(QDialog):
    def __init__(self, db=None, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.db = db
        self.setWindowTitle("إدارة تصنيفات الألعاب")
        self.setFixedSize(400, 450)
        self.setStyleSheet(f"background-color: {Colors.BG_DARK}; color: {Colors.TEXT_PRIMARY};")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        lbl = QLabel("🏷️ تصنيفات الألعاب الحالية")
        lbl.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        lbl.setStyleSheet(f"color: {Colors.CYAN};")
        layout.addWidget(lbl)

        self.cat_list = QScrollArea()
        self.cat_list.setWidgetResizable(True)
        self.cat_w = QWidget()
        self.cat_lay = QVBoxLayout(self.cat_w)
        self.cat_list.setWidget(self.cat_w)
        layout.addWidget(self.cat_list)

        add_lay = QHBoxLayout()
        self.txt_cat = QLineEdit()
        self.txt_cat.setPlaceholderText("اسم التصنيف الجديد...")
        self.txt_cat.setStyleSheet(f"background-color: {Colors.BG_CARD}; border: 1px solid {Colors.BORDER}; padding: 6px; border-radius: 6px;")
        
        btn_add = QPushButton("➕ إضافة")
        btn_add.setStyleSheet(f"background-color: {Colors.CYAN}; color: #000; font-weight: bold; padding: 6px 12px; border-radius: 6px;")
        btn_add.clicked.connect(self.add_category)
        
        add_lay.addWidget(self.txt_cat)
        add_lay.addWidget(btn_add)
        layout.addLayout(add_lay)

        self.load_categories()

    def load_categories(self):
        while self.cat_lay.count():
            item = self.cat_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        cats = ["ألعاب قتال", "ألعاب رياضة", "ألعاب شوتر", "ألعاب مغامرات", "ألعاب استراتيجية"]
        for c in cats:
            lbl = QLabel(f"• {c}")
            lbl.setFont(QFont("Segoe UI", 10))
            self.cat_lay.addWidget(lbl)
        self.cat_lay.addStretch()

    def add_category(self):
        c_name = self.txt_cat.text().strip()
        if c_name:
            lbl = QLabel(f"• {c_name}")
            lbl.setFont(QFont("Segoe UI", 10))
            self.cat_lay.insertWidget(self.cat_lay.count() - 1, lbl)
            self.txt_cat.clear()

class GamesWidget(QWidget):
    def __init__(self, db=None):
        super().__init__()
        self.db = db
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setup_ui()
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(14)

        header = QHBoxLayout()
        
        btn_add_game = QPushButton("➕ إضافة لعبة")
        btn_add_game.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        btn_add_game.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add_game.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.CYAN};
                color: #000000;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: {Colors.CYAN}DD;
            }}
        """)
        btn_add_game.clicked.connect(self.open_add_game_dialog)

        btn_cats = QPushButton("🏷️ التصنيفات")
        btn_cats.setFont(QFont("Segoe UI", 10))
        btn_cats.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cats.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BG_CARD};
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid {Colors.BORDER};
                border-radius: 6px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                border-color: {Colors.CYAN};
            }}
        """)
        btn_cats.clicked.connect(self.open_categories_dialog)

        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("🔍 ابحث عن لعبة...")
        self.txt_search.setFixedWidth(260)
        self.txt_search.setStyleSheet(f"""
            QLineEdit {{
                background-color: {Colors.BG_CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: 6px;
                padding: 6px 12px;
                color: {Colors.TEXT_PRIMARY};
            }}
        """)
        self.txt_search.textChanged.connect(self.filter_games)

        header.addWidget(btn_add_game)
        header.addWidget(btn_cats)
        header.addStretch()
        header.addWidget(self.txt_search)
        
        main_layout.addLayout(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; }")

        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(14)
        
        scroll.setWidget(self.grid_widget)
        main_layout.addWidget(scroll)

        self.load_games()

    def open_add_game_dialog(self):
        dlg = AddGameDialog(self.db, self)
        if dlg.exec():
            self.load_games()

    def open_categories_dialog(self):
        dlg = CategoriesDialog(self.db, self)
        dlg.exec()

    def load_games(self):
        games = []
        if self.db and hasattr(self.db, 'get_connection'):
            try:
                conn = self.db.get_connection()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT GameId, GameName, Category, Platform, ExePath, IconPath, TrailerUrl FROM Games WHERE IsVisible=1")
                    cols = [column[0] for column in cursor.description]
                    for r in cursor.fetchall():
                        games.append(dict(zip(cols, r)))
                    conn.close()
            except Exception as e:
                print("Error loading games:", e)

        if not games:
            games = [
                {"GameName": "EA SPORTS FC 25", "Category": "ألعاب رياضة", "TrailerUrl": "https://www.youtube.com/watch?v=8367UsX3D4U"},
                {"GameName": "Call of Duty: Warzone", "Category": "ألعاب شوتر", "TrailerUrl": "https://www.youtube.com/watch?v=0E44INyxEVk"},
                {"GameName": "VALORANT", "Category": "ألعاب شوتر", "TrailerUrl": "https://www.youtube.com/watch?v=e_E9W2vsRbA"},
                {"GameName": "Grand Theft Auto V", "Category": "ألعاب مغامرات", "TrailerUrl": "https://www.youtube.com/watch?v=QkkoHAzjinY"},
                {"GameName": "League of Legends", "Category": "ألعاب استراتيجية", "TrailerUrl": "https://www.youtube.com/watch?v=aR-KAldshAE"},
                {"GameName": "Counter-Strike 2", "Category": "ألعاب شوتر", "TrailerUrl": "https://www.youtube.com/watch?v=c80VVp04Gdc"},
            ]

        self.all_games = games
        self.display_games(games)

    def display_games(self, games):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        cols_count = 5
        for i, g in enumerate(games):
            card = GameCard(g, on_play_trailer=self.play_trailer, on_launch=self.launch_game)
            r = i // cols_count
            c = i % cols_count
            self.grid_layout.addWidget(card, r, c)

    def filter_games(self, text):
        filtered = [g for g in self.all_games if text.lower() in g.get("GameName", "").lower()]
        self.display_games(filtered)

    def play_trailer(self, game):
        url = game.get("TrailerUrl")
        if url:
            dlg = TrailerPlayerDialog(game.get("GameName"), url, self)
            dlg.exec()

    def launch_game(self, game):
        QMessageBox.information(self, "تشغيل اللعبة", f"جاري إرسال أمر تشغيل {game.get('GameName')}...")