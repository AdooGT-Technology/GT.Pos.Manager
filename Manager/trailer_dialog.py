import re
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QFont
from Manager.theme import Colors

try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    HAS_WEBENGINE = True
except ImportError:
    HAS_WEBENGINE = False

class TrailerPlayerDialog(QDialog):
    def __init__(self, game_name: str, trailer_url: str, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.game_name = game_name
        self.trailer_url = trailer_url
        
        self.setWindowTitle(f"العرض الترويجي - {game_name}")
        self.resize(1000, 600)
        self.setStyleSheet(f"background-color: #0d0e15; color: #ffffff;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QHBoxLayout()
        lbl_title = QLabel(f"🎬 {game_name} - Trailer")
        lbl_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        lbl_title.setStyleSheet(f"color: {Colors.CYAN};")

        btn_close = QPushButton("✕ إغلاق")
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BG_CARD};
                color: {Colors.RED};
                border: 1px solid {Colors.RED}44;
                border-radius: 6px;
                padding: 6px 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {Colors.RED};
                color: #ffffff;
            }}
        """)
        btn_close.clicked.connect(self.close)

        header.addWidget(lbl_title)
        header.addStretch()
        header.addWidget(btn_close)
        layout.addLayout(header)

        yt_id = self.extract_youtube_id(trailer_url)

        if HAS_WEBENGINE and yt_id:
            embed_url = f"https://www.youtube-nocookie.com/embed/{yt_id}?autoplay=1&rel=0&modestbranding=1"
            web_view = QWebEngineView()
            web_view.setUrl(QUrl(embed_url))
            web_view.setStyleSheet("border-radius: 10px; border: 1px solid #222;")
            layout.addWidget(web_view)
        else:
            fallback = QLabel(f"تعذر تشغيل الفيديو تلقائياً.\nالرابط: {trailer_url}")
            fallback.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fallback.setFont(QFont("Segoe UI", 12))
            fallback.setStyleSheet(f"color: {Colors.TEXT_MUTED}; border: 1px dashed {Colors.BORDER}; border-radius: 10px;")
            layout.addWidget(fallback)

    def extract_youtube_id(self, url: str) -> str:
        if not url:
            return ""
        match = re.search(r"(?:v=|\/embed\/|youtu\.be\/|\/v\/)([^\"&?\/\s]{11})", url)
        return match.group(1) if match else ""