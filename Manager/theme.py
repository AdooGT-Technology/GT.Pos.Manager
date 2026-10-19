# -*- coding: utf-8 -*-
"""GT-POS Manager — design system.

Central place for color, spacing, typography and the single global stylesheet.
Widgets must not hard-code colors: use object names / dynamic properties so a
theme switch is a stylesheet swap, not a rebuild.
"""

from PyQt6.QtGui import QColor

# ── Scale ────────────────────────────────────────────────────────────────────
SPACE = {"xs": 4, "sm": 8, "md": 12, "lg": 16, "xl": 24, "2xl": 32}
RADIUS = {"sm": 8, "md": 12, "lg": 16}
FONT_STACK = '"Segoe UI", "Cairo", "Tahoma", sans-serif'
SIZES = {"caption": 11, "body": 13, "title": 15, "h2": 19, "h1": 25}

THEMES = {
    "night": {
        "name": "ليلي", "hint": "كحلي دافئ بلمسة عنبرية",
        "bg": "#0B0F13", "surface": "#121920", "surface2": "#18222B",
        "border": "#26323D", "text": "#E9EEF2", "muted": "#8FA0AE",
        "accent": "#E8B26A", "accent_text": "#1A1206",
        "success": "#63C08B", "warning": "#E8B26A", "danger": "#E07A7A",
    },
    "ink": {
        "name": "حبر", "hint": "رمادي بارد وأزرق هادئ",
        "bg": "#0C1017", "surface": "#141B24", "surface2": "#1B2431",
        "border": "#2A3543", "text": "#E7EDF5", "muted": "#93A3B8",
        "accent": "#7BA7E8", "accent_text": "#07101D",
        "success": "#5FC79A", "warning": "#E5B96B", "danger": "#E4838B",
    },
    "forest": {
        "name": "غابة", "hint": "أخضر طحلبي على فحمي",
        "bg": "#0C1210", "surface": "#131B18", "surface2": "#1A2722",
        "border": "#283B33", "text": "#E9F1EC", "muted": "#94A99E",
        "accent": "#8CC7A1", "accent_text": "#08140D",
        "success": "#8CC7A1", "warning": "#D8BC7A", "danger": "#DE8A83",
    },
    "plum": {
        "name": "توت", "hint": "بنفسجي خافت مع وردي",
        "bg": "#100C14", "surface": "#181320", "surface2": "#211A2C",
        "border": "#332A45", "text": "#F0EAF6", "muted": "#A79AB8",
        "accent": "#C3A0E8", "accent_text": "#150A22",
        "success": "#74C7A4", "warning": "#DCBB78", "danger": "#E28C9B",
    },
    "paper": {
        "name": "ورقي", "hint": "فاتح دافئ مريح للنهار",
        "bg": "#F5F2EC", "surface": "#FFFFFF", "surface2": "#EFEBE2",
        "border": "#DCD6C9", "text": "#211F1A", "muted": "#726C60",
        "accent": "#1F6F5C", "accent_text": "#FFFFFF",
        "success": "#1F7A4D", "warning": "#9A6512", "danger": "#B0433F",
    },
    "mist": {
        "name": "ضباب", "hint": "رمادي بارد فاتح",
        "bg": "#F3F5F7", "surface": "#FFFFFF", "surface2": "#E9EDF1",
        "border": "#D5DCE3", "text": "#1A2129", "muted": "#66727F",
        "accent": "#33587A", "accent_text": "#FFFFFF",
        "success": "#1F7A4D", "warning": "#8A5A11", "danger": "#A83E3E",
    },
}

DEFAULT_THEME = "night"


class Colors:
    """Read-through tokens. Always resolved at paint/style time."""

    CYAN = THEMES[DEFAULT_THEME]["accent"]
    PURPLE = THEMES[DEFAULT_THEME]["accent"]
    GREEN = THEMES[DEFAULT_THEME]["success"]
    RED = THEMES[DEFAULT_THEME]["danger"]
    ORANGE = THEMES[DEFAULT_THEME]["warning"]
    BG_DARK = THEMES[DEFAULT_THEME]["bg"]
    BG_CARD = THEMES[DEFAULT_THEME]["surface"]
    BG_CARD_LIGHT = THEMES[DEFAULT_THEME]["surface2"]
    BG_HOVER = THEMES[DEFAULT_THEME]["surface2"]
    BORDER = THEMES[DEFAULT_THEME]["border"]
    TEXT_PRIMARY = THEMES[DEFAULT_THEME]["text"]
    TEXT_MUTED = THEMES[DEFAULT_THEME]["muted"]
    ACCENT_BG = "rgba(232,178,106,0.12)"
    ACCENT_BLUE = THEMES[DEFAULT_THEME]["accent"]


def current_theme() -> dict:
    return THEMES[getattr(current_theme, "key", DEFAULT_THEME)]


def set_theme(key: str = DEFAULT_THEME) -> dict:
    theme = THEMES.get(key, THEMES[DEFAULT_THEME])
    current_theme.key = key if key in THEMES else DEFAULT_THEME

    Colors.CYAN = theme["accent"]
    Colors.PURPLE = theme["accent"]
    Colors.ACCENT_BLUE = theme["accent"]
    Colors.GREEN = theme["success"]
    Colors.RED = theme["danger"]
    Colors.ORANGE = theme["warning"]
    Colors.BG_DARK = theme["bg"]
    Colors.BG_CARD = theme["surface"]
    Colors.BG_CARD_LIGHT = theme["surface2"]
    Colors.BG_HOVER = theme["surface2"]
    Colors.BORDER = theme["border"]
    Colors.TEXT_PRIMARY = theme["text"]
    Colors.TEXT_MUTED = theme["muted"]
    Colors.ACCENT_BG = qcolor(theme["accent"], 0.14)
    return theme


def qcolor(hex_color: str, alpha: float = 1.0) -> str:
    color = QColor(hex_color)
    if alpha >= 1.0:
        return hex_color
    return f"rgba({color.red()}, {color.green()}, {color.blue()}, {alpha:.2f})"


def theme_key() -> str:
    return getattr(current_theme, "key", DEFAULT_THEME)


def get_stylesheet() -> str:
    t = current_theme()
    bg, surface, surface2 = t["bg"], t["surface"], t["surface2"]
    border, text, muted = t["border"], t["text"], t["muted"]
    accent, accent_text = t["accent"], t["accent_text"]
    success, danger = t["success"], t["danger"]
    accent_hover = QColor(accent).lighter(108).name()
    accent_soft = qcolor(accent, 0.14)
    hover = qcolor(text, 0.05)

    return f"""
    * {{ outline: none; }}
    QWidget {{
        color: {text};
        font-family: {FONT_STACK};
        font-size: {SIZES['body']}px;
        selection-background-color: {accent};
        selection-color: {accent_text};
    }}
    QMainWindow, QDialog {{ background-color: {bg}; }}
    QToolTip {{
        background-color: {surface2}; color: {text};
        border: 1px solid {border}; border-radius: 6px; padding: 5px 8px;
    }}

    /* ── Surfaces ─────────────────────────────────────────────── */
    QFrame#Card {{
        background-color: {surface};
        border: 1px solid {border};
        border-radius: {RADIUS['md']}px;
    }}
    QFrame#Inset {{
        background-color: {surface2};
        border: 1px solid transparent;
        border-radius: {RADIUS['sm']}px;
    }}
    QFrame#Sidebar {{
        background-color: {surface};
        border: none;
        border-left: 1px solid {border};
    }}
    QFrame#TopBar {{
        background-color: {bg};
        border: none;
        border-bottom: 1px solid {border};
    }}
    QFrame#Divider {{ background-color: {border}; max-height: 1px; border: none; }}

    /* ── Type ─────────────────────────────────────────────────── */
    QLabel {{ background: transparent; }}
    QLabel#H1 {{ font-size: {SIZES['h1']}px; font-weight: 600; }}
    QLabel#H2 {{ font-size: {SIZES['h2']}px; font-weight: 600; }}
    QLabel#Title {{ font-size: {SIZES['title']}px; font-weight: 600; }}
    QLabel#Body {{ font-size: {SIZES['body']}px; }}
    QLabel#Muted {{ color: {muted}; font-size: 12px; }}
    QLabel#Caption {{ color: {muted}; font-size: {SIZES['caption']}px; }}
    QLabel#Section {{ color: {muted}; font-size: 11px; font-weight: 600; }}
    QLabel#Value {{ font-size: 22px; font-weight: 600; }}
    QLabel#Accent {{ color: {accent}; }}
    QLabel#Money {{ font-size: 22px; font-weight: 600; }}

    /* ── Buttons ──────────────────────────────────────────────── */
    QPushButton {{
        background-color: {surface2};
        color: {text};
        border: 1px solid {border};
        border-radius: 9px;
        padding: 7px 14px;
        min-height: 20px;
        font-weight: 500;
    }}
    QPushButton:hover {{ border-color: {qcolor(accent, 0.55)}; background-color: {hover}; }}
    QPushButton:pressed {{ background-color: {accent_soft}; }}
    QPushButton:disabled {{ color: {muted}; border-color: {border}; background-color: transparent; }}
    QPushButton[variant="primary"] {{
        background-color: {accent}; color: {accent_text};
        border: 1px solid {accent}; font-weight: 600;
    }}
    QPushButton[variant="primary"]:hover {{ background-color: {accent_hover}; border-color: {accent_hover}; }}
    QPushButton[variant="ghost"] {{
        background-color: transparent; border: 1px solid transparent; color: {muted};
    }}
    QPushButton[variant="ghost"]:hover {{ color: {text}; background-color: {hover}; }}
    QPushButton[variant="quiet"] {{
        background-color: transparent; border: 1px solid {border}; color: {text};
    }}
    QPushButton[variant="quiet"]:hover {{ border-color: {qcolor(accent, 0.55)}; }}
    QPushButton[variant="danger"] {{ color: {danger}; border-color: {qcolor(danger, 0.4)}; background: transparent; }}
    QPushButton[variant="danger"]:hover {{ background-color: {qcolor(danger, 0.12)}; border-color: {danger}; }}
    QPushButton[variant="success"] {{ color: {success}; border-color: {qcolor(success, 0.4)}; background: transparent; }}
    QPushButton[variant="success"]:hover {{ background-color: {qcolor(success, 0.12)}; border-color: {success}; }}
    QPushButton[variant="icon"] {{
        padding: 0; border-radius: 10px;
        background-color: transparent; border: 1px solid transparent;
    }}
    QPushButton[variant="icon"]:hover {{ background-color: {hover}; border-color: {border}; }}
    QPushButton[variant="nav"] {{
        background: transparent; border: none; border-radius: 10px;
        padding: 0; text-align: right; color: {muted}; font-weight: 500;
    }}
    QPushButton[variant="nav"]:hover {{ background-color: {hover}; color: {text}; }}
    QPushButton[variant="nav"][active="true"] {{
        background-color: {accent_soft}; color: {text}; font-weight: 600;
    }}
    QPushButton[compact="true"] {{ padding: 4px 10px; min-height: 16px; font-size: 12px; }}

    /* ── Inputs ───────────────────────────────────────────────── */
    QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
        background-color: {surface2};
        color: {text};
        border: 1px solid {border};
        border-radius: 9px;
        padding: 7px 10px;
        min-height: 20px;
    }}
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus,
    QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
        border: 1px solid {accent};
        background-color: {qcolor(accent, 0.06)};
    }}
    QLineEdit:disabled, QComboBox:disabled {{ color: {muted}; }}
    QLineEdit[search="true"] {{ padding-right: 12px; }}
    QComboBox::drop-down {{ border: none; width: 22px; }}
    QComboBox QAbstractItemView {{
        background-color: {surface}; color: {text};
        border: 1px solid {border}; border-radius: 8px;
        padding: 4px; outline: 0;
        selection-background-color: {accent_soft};
        selection-color: {text};
    }}
    QCheckBox {{ spacing: 8px; }}
    QCheckBox::indicator {{
        width: 16px; height: 16px; border-radius: 4px;
        border: 1px solid {border}; background: {surface2};
    }}
    QCheckBox::indicator:checked {{ background-color: {accent}; border-color: {accent}; }}

    /* ── Tables & lists ───────────────────────────────────────── */
    QTableWidget, QTableView {{
        background-color: transparent;
        alternate-background-color: {qcolor(text, 0.02)};
        border: none;
        gridline-color: transparent;
        selection-background-color: {accent_soft};
        selection-color: {text};
    }}
    QTableWidget::item, QTableView::item {{ padding: 6px 8px; border: none; }}
    QHeaderView {{ background: transparent; }}
    QHeaderView::section {{
        background-color: transparent;
        color: {muted};
        border: none;
        border-bottom: 1px solid {border};
        padding: 8px;
        font-size: 11px;
        font-weight: 600;
    }}
    QListWidget {{ background: transparent; border: none; }}
    QListWidget::item {{ padding: 8px 10px; border-radius: 8px; }}
    QListWidget::item:selected {{ background-color: {accent_soft}; color: {text}; }}
    QListWidget::item:hover {{ background-color: {hover}; }}

    /* ── Scroll ───────────────────────────────────────────────── */
    QScrollArea {{ background: transparent; border: none; }}
    QScrollArea > QWidget > QWidget {{ background: transparent; }}
    QScrollBar:vertical {{ background: transparent; width: 9px; margin: 2px; }}
    QScrollBar::handle:vertical {{
        background: {qcolor(muted, 0.35)}; border-radius: 4px; min-height: 28px;
    }}
    QScrollBar::handle:vertical:hover {{ background: {qcolor(muted, 0.6)}; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
    QScrollBar:horizontal {{ background: transparent; height: 9px; margin: 2px; }}
    QScrollBar::handle:horizontal {{ background: {qcolor(muted, 0.35)}; border-radius: 4px; min-width: 28px; }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

    /* ── Menus, tabs, misc ────────────────────────────────────── */
    QMenu {{
        background-color: {surface}; border: 1px solid {border};
        border-radius: 10px; padding: 6px;
    }}
    QMenu::item {{ padding: 7px 14px; border-radius: 7px; }}
    QMenu::item:selected {{ background-color: {accent_soft}; }}
    QMenu::separator {{ height: 1px; background: {border}; margin: 6px 8px; }}
    QTabWidget::pane {{ border: none; }}
    QTabBar::tab {{
        background: transparent; color: {muted}; padding: 8px 14px;
        border: none; border-bottom: 2px solid transparent;
    }}
    QTabBar::tab:selected {{ color: {text}; border-bottom: 2px solid {accent}; }}
    QProgressBar {{ background-color: {surface2}; border: none; border-radius: 3px; text-align: center; }}
    QProgressBar::chunk {{ background-color: {accent}; border-radius: 3px; }}
    QSplitter::handle {{ background: transparent; }}
    QStatusBar {{ background: {surface}; color: {muted}; }}
    """


def get_login_stylesheet() -> str:
    t = current_theme()
    bg, surface, border = t["bg"], t["surface"], t["border"]
    text, muted, accent = t["text"], t["muted"], t["accent"]
    return f"""
    QMainWindow, QWidget#LoginRoot {{
        background-color: {bg}; color: {text};
        font-family: {FONT_STACK};
    }}
    QFrame#LoginCard {{
        background-color: {surface};
        border: 1px solid {border};
        border-radius: 18px;
    }}
    QFrame#LoginBrand {{ background-color: transparent; border: none; }}
    QLabel {{ color: {text}; }}
    QLabel#LoginTitle {{ font-size: 24px; font-weight: 600; }}
    QLabel#LoginMuted {{ color: {muted}; font-size: 12px; }}
    QLabel#LoginHint {{ color: {muted}; font-size: 11px; }}
    QLineEdit {{
        background-color: {t['surface2']}; color: {text};
        border: 1px solid {border}; border-radius: 10px;
        padding: 11px 12px; min-height: 22px;
    }}
    QLineEdit:focus {{ border: 1px solid {accent}; }}
    QPushButton {{
        background-color: {accent}; color: {t['accent_text']};
        border: none; border-radius: 10px; padding: 12px; font-weight: 600;
    }}
    QPushButton:hover {{ background-color: {QColor(accent).lighter(108).name()}; }}
    QPushButton#LinkButton {{
        background: transparent; color: {muted}; border: none;
        padding: 4px; font-weight: 400;
    }}
    QPushButton#LinkButton:hover {{ color: {accent}; }}
    """
