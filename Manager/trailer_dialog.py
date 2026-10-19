# -*- coding: utf-8 -*-
"""Trailer player: YouTube (no-cookie) or a local/external video file."""

from __future__ import annotations

import re

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtWidgets import QDialog, QHBoxLayout, QLabel, QVBoxLayout

from Manager.theme import Colors
from Manager.ui import button, label

try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    HAS_WEBENGINE = True
except ImportError:  # pragma: no cover - optional dependency
    HAS_WEBENGINE = False


def embed_url(url: str) -> str:
    """Turn a watch/share link into an embeddable one."""
    match = re.search(r"(?:youtu\.be/|v=)([\w-]{6,})", url)
    if match:
        return f"https://www.youtube-nocookie.com/embed/{match.group(1)}?rel=0&modestbranding=1"
    return url


class TrailerPlayerDialog(QDialog):
    def __init__(self, game_name: str, trailer_url: str, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setWindowTitle(f"العرض — {game_name}")
        self.resize(960, 580)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        head = QHBoxLayout()
        head.addWidget(label(game_name, "Title"))
        head.addStretch()
        head.addWidget(button("إغلاق", "ghost", self.accept, compact=True))
        layout.addLayout(head)

        if HAS_WEBENGINE:
            view = QWebEngineView()
            view.setUrl(QUrl(embed_url(trailer_url)))
            layout.addWidget(view, 1)
        else:
            message = QLabel(
                "محرك العرض غير مثبت.\n"
                "ثبّت PyQt6-WebEngine لعرض الترايلر داخل البرنامج،\n"
                f"أو افتح الرابط في المتصفح:\n{trailer_url}"
            )
            message.setWordWrap(True)
            message.setAlignment(Qt.AlignmentFlag.AlignCenter)
            message.setStyleSheet(f"color: {Colors.TEXT_MUTED}; padding: 30px;")
            layout.addWidget(message, 1)
