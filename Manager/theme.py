class Colors:
    CYAN = "#00d4ff"
    PURPLE = "#8b5cf6"
    GREEN = "#10b981"
    RED = "#ef4444"
    ORANGE = "#f59e0b"
    BG_DARK = "#0a0c14"
    BG_CARD = "#121624"
    BG_CARD_LIGHT = "#1a2035"
    BG_HOVER = "#1e263d"
    BORDER = "#232d42"
    TEXT_PRIMARY = "#f8fafc"
    TEXT_MUTED = "#94a3b8"
    ACCENT_BG = "#00d4ff15"
    ACCENT_BLUE = "#00d4ff"

THEMES = {
    "aurora": {
        "name": "أورورا الأزرق", "cyan": "#00d4ff", "purple": "#8b5cf6", "green": "#10b981",
        "red": "#ef4444", "orange": "#f59e0b", "bg_dark": "#0a0c14", "bg_card": "#121624",
        "bg_card_light": "#1a2035", "bg_hover": "#1e263d", "border": "#232d42",
        "text_primary": "#f8fafc", "text_muted": "#94a3b8", "accent_bg": "#00d4ff15", "accent_blue": "#00d4ff"
    },
    "midnight": {
        "name": "منتصف الليل البنفسجي", "cyan": "#a78bfa", "purple": "#f0abfc", "green": "#34d399",
        "red": "#f87171", "orange": "#fbbf24", "bg_dark": "#0f0d1b", "bg_card": "#18142a",
        "bg_card_light": "#231e3d", "bg_hover": "#2e284f", "border": "#312952",
        "text_primary": "#f3e8ff", "text_muted": "#a78bfa", "accent_bg": "#a78bfa15", "accent_blue": "#a78bfa"
    },
    "emerald": {
        "name": "الزمرد الداكن", "cyan": "#34d399", "purple": "#a3e635", "green": "#10b981",
        "red": "#f87171", "orange": "#fbbf24", "bg_dark": "#061512", "bg_card": "#0c241f",
        "bg_card_light": "#14352e", "bg_hover": "#1c473e", "border": "#1c4a3e",
        "text_primary": "#ecfdf5", "text_muted": "#6ee7b7", "accent_bg": "#34d39915", "accent_blue": "#34d399"
    },
    "sunset": {
        "name": "غروب البرتقالي", "cyan": "#fb923c", "purple": "#f43f5e", "green": "#10b981",
        "red": "#ef4444", "orange": "#f97316", "bg_dark": "#180c0a", "bg_card": "#261410",
        "bg_card_light": "#361d17", "bg_hover": "#47261f", "border": "#4a241b",
        "text_primary": "#fff7ed", "text_muted": "#fdba74", "accent_bg": "#fb923c15", "accent_blue": "#fb923c"
    },
    "ocean": {
        "name": "أعماق المحيط", "cyan": "#22d3ee", "purple": "#2dd4bf", "green": "#34d399",
        "red": "#f87171", "orange": "#fbbf24", "bg_dark": "#08131e", "bg_card": "#0f2030",
        "bg_card_light": "#172e45", "bg_hover": "#1f3c5a", "border": "#1e4063",
        "text_primary": "#f0f9ff", "text_muted": "#7dd3fc", "accent_bg": "#22d3ee15", "accent_blue": "#22d3ee"
    },
    "rose": {
        "name": "الوردي الذهبي", "cyan": "#f472b6", "purple": "#fbbf24", "green": "#34d399",
        "red": "#ef4444", "orange": "#fb923c", "bg_dark": "#180b14", "bg_card": "#261220",
        "bg_card_light": "#361a2e", "bg_hover": "#47223d", "border": "#4a1f3d",
        "text_primary": "#fdf2f8", "text_muted": "#fbcfe8", "accent_bg": "#f472b615", "accent_blue": "#f472b6"
    },
    "light": {
        "name": "النهاري الفاتح", "cyan": "#0284c7", "purple": "#7c3aed", "green": "#059669",
        "red": "#dc2626", "orange": "#d97706", "bg_dark": "#f8fafc", "bg_card": "#ffffff",
        "bg_card_light": "#f1f5f9", "bg_hover": "#e2e8f0", "border": "#cbd5e1",
        "text_primary": "#0f172a", "text_muted": "#64748b", "accent_bg": "#0284c715", "accent_blue": "#0284c7"
    }
}

def set_theme(theme_key="aurora"):
    t = THEMES.get(theme_key, THEMES["aurora"])
    Colors.CYAN = t["cyan"]
    Colors.PURPLE = t["purple"]
    Colors.GREEN = t["green"]
    Colors.RED = t["red"]
    Colors.ORANGE = t["orange"]
    Colors.BG_DARK = t["bg_dark"]
    Colors.BG_CARD = t["bg_card"]
    Colors.BG_CARD_LIGHT = t["bg_card_light"]
    Colors.BG_HOVER = t["bg_hover"]
    Colors.BORDER = t["border"]
    Colors.TEXT_PRIMARY = t["text_primary"]
    Colors.TEXT_MUTED = t["text_muted"]
    Colors.ACCENT_BG = t["accent_bg"]
    Colors.ACCENT_BLUE = t["accent_blue"]
    return t

def get_main_stylesheet():
    return f"""
        QMainWindow, QDialog {{
            background-color: {Colors.BG_DARK};
            color: {Colors.TEXT_PRIMARY};
        }}
        QWidget {{
            font-family: 'Segoe UI', 'Cairo', 'Tahoma', sans-serif;
            color: {Colors.TEXT_PRIMARY};
        }}
        QFrame#Sidebar {{
            background-color: {Colors.BG_CARD};
            border-left: 1px solid {Colors.BORDER};
        }}
        QFrame#Header {{
            background-color: {Colors.BG_CARD};
            border-bottom: 1px solid {Colors.BORDER};
        }}
        
        /* General Input Styles to prevent hidden text */
        QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox {{
            background-color: {Colors.BG_CARD_LIGHT};
            color: {Colors.TEXT_PRIMARY};
            border: 1px solid {Colors.BORDER};
            border-radius: 6px;
            padding: 6px 12px;
        }}
        QLineEdit:focus, QTextEdit:focus {{
            border: 1px solid {Colors.CYAN};
        }}
        
        /* ComboBox Fixes */
        QComboBox {{
            background-color: {Colors.BG_CARD_LIGHT};
            color: {Colors.TEXT_PRIMARY};
            border: 1px solid {Colors.BORDER};
            border-radius: 6px;
            padding: 6px 12px;
        }}
        QComboBox::drop-down {{
            border: none;
        }}
        QComboBox QAbstractItemView {{
            background-color: {Colors.BG_CARD};
            color: {Colors.TEXT_PRIMARY};
            border: 1px solid {Colors.BORDER};
            selection-background-color: {Colors.CYAN};
            selection-color: #000000;
        }}
        
        /* GroupBox Style */
        QGroupBox {{
            border: 1px solid {Colors.BORDER};
            border-radius: 8px;
            margin-top: 14px;
            font-weight: bold;
            color: {Colors.CYAN};
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top right;
            padding: 0 8px;
            background-color: {Colors.BG_DARK};
        }}
        
        /* ScrollBar Fixes */
        QScrollArea {{
            border: none;
            background-color: transparent;
        }}
        QScrollArea > QWidget > QWidget {{
            background-color: transparent;
        }}
        QScrollBar:vertical {{
            border: none;
            background: {Colors.BG_DARK};
            width: 8px;
            margin: 0px;
        }}
        QScrollBar::handle:vertical {{
            background: {Colors.BORDER};
            min-height: 20px;
            border-radius: 4px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {Colors.CYAN};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
    """

def get_login_stylesheet():
    return f"""
        QMainWindow {{ background-color: #0f172a; }}
        QFrame {{ background-color: #ffffff; border-radius: 16px; }}
        QLineEdit {{
            background-color: #f8fafc; border: 1px solid #cbd5e1;
            border-radius: 8px; padding: 0 14px; color: #0f172a; font-size: 13px;
        }}
        QLineEdit:focus {{ border: 2px solid #0284c7; }}
        QPushButton {{
            background-color: #0284c7; color: #ffffff; border: none;
            border-radius: 8px; font-size: 14px; font-weight: bold;
        }}
        QPushButton:hover {{ background-color: #0369a1; }}
    """
