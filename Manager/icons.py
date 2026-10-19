# -*- coding: utf-8 -*-
"""Small vector icon set drawn with QPainter.

Font glyphs rendered too small and inconsistently across machines, so the shell
uses these instead: they scale with the button, stay crisp on high-DPI screens
and take their color from the active theme.
"""

from __future__ import annotations

import math

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap

BOX = 24.0

ICON_NAMES = {
    "search", "refresh", "theme", "bell", "power", "sidebar", "grid",
    "monitor", "studio", "users", "cart", "wallet", "gamepad", "terminal",
    "chart", "gift", "trophy", "settings", "chevron", "chevron_down",
}


def _pen(painter: QPainter, color: str, width: float = 1.8):
    pen = QPen(QColor(color))
    pen.setWidthF(width)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)


def _draw(name: str, painter: QPainter, color: str):
    _pen(painter, color)

    if name == "search":
        painter.drawEllipse(QRectF(4.5, 4.5, 11, 11))
        painter.drawLine(QPointF(14.6, 14.6), QPointF(19.5, 19.5))

    elif name == "refresh":
        path = QPainterPath()
        path.arcMoveTo(QRectF(4, 4, 16, 16), 40)
        path.arcTo(QRectF(4, 4, 16, 16), 40, 275)
        painter.drawPath(path)
        # arrowhead sitting in the gap, pointing along the rotation
        start = math.radians(40)
        tip = QPointF(12 + 10.2 * math.cos(start), 12 - 10.2 * math.sin(start))
        back = QPointF(12 + 6.4 * math.cos(start), 12 - 6.4 * math.sin(start))
        side = QPointF(2.2 * math.sin(start), 2.2 * math.cos(start))
        arrow = QPainterPath()
        arrow.moveTo(tip)
        arrow.lineTo(back.x() + side.x(), back.y() + side.y())
        arrow.lineTo(back.x() - side.x(), back.y() - side.y())
        arrow.closeSubpath()
        painter.setBrush(QColor(color))
        painter.drawPath(arrow)
        painter.setBrush(Qt.BrushStyle.NoBrush)

    elif name == "theme":
        painter.drawEllipse(QRectF(3.6, 3.6, 16.8, 16.8))
        path = QPainterPath()
        path.moveTo(12, 4)
        path.arcTo(QRectF(4, 4, 16, 16), 90, -180)
        path.closeSubpath()
        painter.setBrush(QColor(color))
        painter.drawPath(path)
        painter.setBrush(Qt.BrushStyle.NoBrush)

    elif name == "bell":
        path = QPainterPath()
        path.moveTo(6.5, 16.5)
        path.lineTo(7.4, 14.6)
        path.lineTo(7.4, 10.6)
        path.cubicTo(7.4, 7.2, 9.4, 5.2, 12, 5.2)
        path.cubicTo(14.6, 5.2, 16.6, 7.2, 16.6, 10.6)
        path.lineTo(16.6, 14.6)
        path.lineTo(17.5, 16.5)
        path.closeSubpath()
        painter.drawPath(path)
        painter.drawLine(QPointF(10.4, 19.2), QPointF(13.6, 19.2))

    elif name == "power":
        path = QPainterPath()
        path.arcMoveTo(QRectF(4.4, 4.4, 15.2, 15.2), 70)
        path.arcTo(QRectF(4.4, 4.4, 15.2, 15.2), 70, 320)
        painter.drawPath(path)
        painter.drawLine(QPointF(12, 3.4), QPointF(12, 11.2))

    elif name == "sidebar":
        painter.drawRoundedRect(QRectF(3.4, 4.6, 17.2, 14.8), 3, 3)
        painter.drawLine(QPointF(9.2, 4.6), QPointF(9.2, 19.4))

    elif name == "grid":
        for x, y in ((4, 4), (13, 4), (4, 13), (13, 13)):
            painter.drawRoundedRect(QRectF(x, y, 7, 7), 1.8, 1.8)

    elif name == "monitor":
        painter.drawRoundedRect(QRectF(3, 4.6, 18, 12.4), 2.4, 2.4)
        painter.drawLine(QPointF(12, 17), QPointF(12, 19.6))
        painter.drawLine(QPointF(8.6, 20), QPointF(15.4, 20))

    elif name == "studio":
        painter.drawRoundedRect(QRectF(3, 4.6, 18, 12.4), 2.4, 2.4)
        painter.drawLine(QPointF(12, 17), QPointF(12, 19.6))
        painter.drawLine(QPointF(8.6, 20), QPointF(15.4, 20))
        play = QPainterPath()
        play.moveTo(10.4, 8.6)
        play.lineTo(15.2, 11)
        play.lineTo(10.4, 13.4)
        play.closeSubpath()
        painter.drawPath(play)

    elif name == "users":
        painter.drawEllipse(QRectF(4.2, 5.4, 6, 6))
        path = QPainterPath()
        path.arcMoveTo(QRectF(2.6, 12.4, 9.2, 9.2), 0)
        path.arcTo(QRectF(2.6, 12.4, 9.2, 9.2), 0, 180)
        painter.drawPath(path)
        painter.drawEllipse(QRectF(13.8, 6.4, 5.2, 5.2))
        path2 = QPainterPath()
        path2.arcMoveTo(QRectF(12.4, 12.8, 8.4, 8.4), 0)
        path2.arcTo(QRectF(12.4, 12.8, 8.4, 8.4), 0, 180)
        painter.drawPath(path2)

    elif name == "cart":
        painter.drawLine(QPointF(3.4, 5.2), QPointF(6.2, 5.2))
        painter.drawLine(QPointF(6.2, 5.2), QPointF(8.6, 15.4))
        painter.drawLine(QPointF(8.6, 15.4), QPointF(18.4, 15.4))
        painter.drawLine(QPointF(18.8, 7.6), QPointF(7.4, 7.6))
        painter.drawLine(QPointF(7.4, 7.6), QPointF(18.8, 7.6))
        painter.drawEllipse(QRectF(8.4, 17.6, 2.6, 2.6))
        painter.drawEllipse(QRectF(16, 17.6, 2.6, 2.6))

    elif name == "wallet":
        painter.drawRoundedRect(QRectF(3.2, 6.2, 17.6, 12.2), 2.6, 2.6)
        painter.drawLine(QPointF(3.2, 10.2), QPointF(20.8, 10.2))
        painter.setBrush(QColor(color))
        painter.drawEllipse(QRectF(15.6, 12.8, 2.4, 2.4))
        painter.setBrush(Qt.BrushStyle.NoBrush)

    elif name == "gamepad":
        painter.drawRoundedRect(QRectF(2.8, 7.4, 18.4, 10.4), 4.4, 4.4)
        painter.drawLine(QPointF(7.6, 10.6), QPointF(7.6, 14.4))
        painter.drawLine(QPointF(5.7, 12.5), QPointF(9.5, 12.5))
        painter.drawEllipse(QRectF(15.4, 10.6, 2.2, 2.2))
        painter.drawEllipse(QRectF(17.8, 13.2, 2.2, 2.2))

    elif name == "terminal":
        painter.drawRoundedRect(QRectF(3, 4.6, 18, 14.8), 2.6, 2.6)
        painter.drawLine(QPointF(7, 9.6), QPointF(9.8, 12))
        painter.drawLine(QPointF(9.8, 12), QPointF(7, 14.4))
        painter.drawLine(QPointF(12.4, 14.8), QPointF(16.8, 14.8))

    elif name == "chart":
        painter.drawLine(QPointF(4, 19.4), QPointF(20, 19.4))
        painter.drawLine(QPointF(7, 19.4), QPointF(7, 12.4))
        painter.drawLine(QPointF(12, 19.4), QPointF(12, 8.2))
        painter.drawLine(QPointF(17, 19.4), QPointF(17, 14.6))

    elif name == "gift":
        painter.drawRoundedRect(QRectF(4, 10.4, 16, 9.2), 2, 2)
        painter.drawLine(QPointF(3, 10.4), QPointF(21, 10.4))
        painter.drawLine(QPointF(12, 6.2), QPointF(12, 19.6))
        painter.drawEllipse(QRectF(6.6, 4.4, 5.4, 4.4))
        painter.drawEllipse(QRectF(12, 4.4, 5.4, 4.4))

    elif name == "trophy":
        path = QPainterPath()
        path.moveTo(7.4, 4.4)
        path.lineTo(16.6, 4.4)
        path.lineTo(16.6, 9.4)
        path.cubicTo(16.6, 12.4, 14.6, 14.4, 12, 14.4)
        path.cubicTo(9.4, 14.4, 7.4, 12.4, 7.4, 9.4)
        path.closeSubpath()
        painter.drawPath(path)
        painter.drawLine(QPointF(12, 14.6), QPointF(12, 18.2))
        painter.drawLine(QPointF(8.4, 19.8), QPointF(15.6, 19.8))
        painter.drawLine(QPointF(7.4, 6.2), QPointF(4.6, 6.2))
        painter.drawLine(QPointF(16.6, 6.2), QPointF(19.4, 6.2))

    elif name == "settings":
        painter.drawEllipse(QRectF(6.2, 6.2, 11.6, 11.6))
        painter.drawEllipse(QRectF(9.8, 9.8, 4.4, 4.4))
        painter.setPen(QPen(QColor(color), 2.4, Qt.PenStyle.SolidLine,
                            Qt.PenCapStyle.RoundCap))
        for step in range(8):
            angle = math.radians(step * 45)
            inner = QPointF(12 + 6.1 * math.cos(angle), 12 - 6.1 * math.sin(angle))
            outer = QPointF(12 + 8.8 * math.cos(angle), 12 - 8.8 * math.sin(angle))
            painter.drawLine(inner, outer)

    elif name == "chevron":
        painter.drawLine(QPointF(9.4, 6.4), QPointF(14.6, 12))
        painter.drawLine(QPointF(14.6, 12), QPointF(9.4, 17.6))

    elif name == "chevron_down":
        painter.drawLine(QPointF(6.4, 9.4), QPointF(12, 14.6))
        painter.drawLine(QPointF(12, 14.6), QPointF(17.6, 9.4))

    else:  # dot fallback
        painter.setBrush(QColor(color))
        painter.drawEllipse(QRectF(9, 9, 6, 6))


def make_pixmap(name: str, size: int, color: str) -> QPixmap:
    scale = 2
    pixmap = QPixmap(size * scale, size * scale)
    pixmap.fill(Qt.GlobalColor.transparent)
    pixmap.setDevicePixelRatio(scale)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    # The device pixel ratio already maps logical units to physical pixels.
    painter.scale(size / BOX, size / BOX)
    _draw(name, painter, color)
    painter.end()
    return pixmap


def make_icon(name: str, color: str, size: int = 20) -> QIcon:
    return QIcon(make_pixmap(name, size, color))
