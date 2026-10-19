import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QStackedWidget, QFrame, QLineEdit,
    QDialog, QGridLayout, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QIcon, QPixmap
from Manager.theme import Colors, THEMES, set_theme, get_main_stylesheet
from Manager.dashboard_widget import DashboardWidget
from Manager.pos_widget import POSWidget
from Manager.settings_widget import SettingsWidget
from Manager.games_widget import GamesWidget
from Server.database import DatabaseManager

class SidebarButton(QPushButton):
    def __init__(self, icon_emoji: str, text: str, page_idx: int, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.page_idx = page_idx
        self.setCheckable(True)
        self.setFixedHeight(46)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(12)

        self.icon_lbl = QLabel(icon_emoji)
        self.icon_lbl.setFont(QFont("Segoe UI Emoji", 14))
        self.icon_lbl.setStyleSheet("border: none; background: transparent;")

        self.text_lbl = QLabel(text)
        self.text_lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Medium))
        self.text_lbl.setStyleSheet("border: none; background: transparent;")

        layout.addWidget(self.icon_lbl)
        layout.addWidget(self.text_lbl)
        layout.addStretch()

        self.update_style(False)

    def update_style(self, is_active: bool):
        self.setChecked(is_active)
        if is_active:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Colors.ACCENT_BG};
                    border: none;
                    border-right: 4px solid {Colors.CYAN};
                    border-radius: 6px;
                    text-align: right;
                }}
                QLabel {{ color: {Colors.CYAN}; font-weight: bold; }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    border: none;
                    border-radius: 6px;
                    text-align: right;
                }}
                QPushButton:hover {{
                    background-color: {Colors.BG_HOVER};
                }}
                QLabel {{ color: {Colors.TEXT_MUTED}; }}
            """)

class ThemeDialog(QDialog):
    def __init__(self, current_theme: str, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.selected_theme = current_theme
        self.setWindowTitle("اختيار مظهر الواجهة")
        self.setFixedSize(520, 420)
        self.setStyleSheet(f"background-color: {Colors.BG_DARK}; color: {Colors.TEXT_PRIMARY};")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        lbl_title = QLabel("🎨 اختر المظهر المفضل للوحة التحكم")
        lbl_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        lbl_title.setStyleSheet(f"color: {Colors.CYAN};")
        layout.addWidget(lbl_title)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        grid_widget = QWidget()
        grid = QGridLayout(grid_widget)
        grid.setSpacing(12)
        
        row = 0
        col = 0
        for t_key, t_data in THEMES.items():
            btn = QPushButton()
            btn.setFixedSize(150, 100)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            
            b_layout = QVBoxLayout(btn)
            b_layout.setContentsMargins(10, 10, 10, 10)
            
            swatch = QFrame()
            swatch.setFixedHeight(24)
            swatch.setStyleSheet(f"background: linear-gradient(90deg, {t_data['cyan']}, {t_data['purple']}); border-radius: 6px;")
            
            t_name = QLabel(t_data['name'])
            t_name.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            t_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
            t_name.setStyleSheet("border: none; color: #ffffff;")
            
            b_layout.addWidget(swatch)
            b_layout.addWidget(t_name)
            
            is_cur = (t_key == current_theme)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {t_data['bg_card']};
                    border: {2 if is_cur else 1}px solid {t_data['cyan'] if is_cur else Colors.BORDER};
                    border-radius: 10px;
                }}
                QPushButton:hover {{
                    border-color: {t_data['cyan']};
                }}
            """)
            
            btn.clicked.connect(lambda checked, k=t_key: self.select_and_close(k))
            
            grid.addWidget(btn, row, col)
            col += 1
            if col > 2:
                col = 0
                row += 1
                
        scroll.setWidget(grid_widget)
        layout.addWidget(scroll)

    def select_and_close(self, key):
        self.selected_theme = key
        self.accept()

class MainManager(QMainWindow):
    def __init__(self, username: str = "مدير النظام"):
        super().__init__()
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.username = username
        self.db = DatabaseManager()
        self.nav_buttons = []
        self.current_theme_key = "aurora"
        
        self.setWindowTitle("Gaming Center Pro - لوحة التحكم الاحترافية")
        self.resize(1400, 850)
        self.setMinimumSize(1100, 700)
        
        self.setup_ui()
        self.apply_theme(self.current_theme_key)

    def setup_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        root_layout = QHBoxLayout(main_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setFixedWidth(240)
        sidebar.setObjectName("Sidebar")
        
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 16, 12, 16)
        sidebar_layout.setSpacing(6)

        brand_frame = QFrame()
        brand_frame.setFixedHeight(60)
        brand_layout = QHBoxLayout(brand_frame)
        brand_layout.setContentsMargins(8, 0, 8, 0)
        
        logo_lbl = QLabel("🎮")
        logo_lbl.setFont(QFont("Segoe UI Emoji", 22))
        
        title_layout = QVBoxLayout()
        title_layout.setSpacing(0)
        
        app_title = QLabel("GAMING CENTER")
        app_title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        app_title.setStyleSheet(f"color: {Colors.CYAN}; letter-spacing: 1px;")
        
        app_sub = QLabel("GT-POS Manager v3.0")
        app_sub.setFont(QFont("Segoe UI", 8))
        app_sub.setStyleSheet(f"color: {Colors.TEXT_MUTED};")
        
        title_layout.addWidget(app_title)
        title_layout.addWidget(app_sub)
        
        brand_layout.addWidget(logo_lbl)
        brand_layout.addLayout(title_layout)
        brand_layout.addStretch()
        
        sidebar_layout.addWidget(brand_frame)
        
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet(f"background-color: {Colors.BORDER}; max-height: 1px; margin: 8px 0;")
        sidebar_layout.addWidget(divider)

        nav_items = [
            ("🏠", "الرئيسية", 0),
            ("🖥️", "إدارة الأجهزة", 1),
            ("👥", "المستخدمين", 2),
            ("🛒", "نقطة البيع", 3),
            ("💰", "المحفظة", 4),
            ("🎁", "المكافآت", 5),
            ("🏆", "المسابقات", 6),
            ("🎮", "الألعاب", 7),
            ("📊", "التقارير", 8),
            ("⚙️", "الإعدادات", 9),
        ]

        for icon, name, idx in nav_items:
            btn = SidebarButton(icon, name, idx)
            btn.clicked.connect(lambda checked, i=idx: self.switch_page(i))
            self.nav_buttons.append(btn)
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()

        user_frame = QFrame()
        user_frame.setFixedHeight(54)
        user_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BG_CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
            }}
        """)
        u_layout = QHBoxLayout(user_frame)
        u_layout.setContentsMargins(10, 6, 10, 6)
        
        u_avatar = QLabel("👤")
        u_avatar.setFont(QFont("Segoe UI Emoji", 14))
        
        u_info = QVBoxLayout()
        u_info.setSpacing(0)
        u_name = QLabel(self.username)
        u_name.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        u_name.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        
        u_role = QLabel("مدير النظام")
        u_role.setFont(QFont("Segoe UI", 8))
        u_role.setStyleSheet(f"color: {Colors.GREEN};")
        
        u_info.addWidget(u_name)
        u_info.addWidget(u_role)
        
        u_layout.addWidget(u_avatar)
        u_layout.addLayout(u_info)
        u_layout.addStretch()

        sidebar_layout.addWidget(user_frame)
        root_layout.addWidget(sidebar)

        body_layout = QVBoxLayout()
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        header = QFrame()
        header.setFixedHeight(60)
        header.setObjectName("Header")
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)

        self.lbl_page_title = QLabel("لوحة التحكم الرئيسية")
        self.lbl_page_title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.lbl_page_title.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")

        header_layout.addWidget(self.lbl_page_title)
        header_layout.addStretch()

        btn_theme = QPushButton("🎨 المظهر")
        btn_theme.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_theme.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BG_CARD};
                color: {Colors.CYAN};
                border: 1px solid {Colors.CYAN}44;
                border-radius: 8px;
                padding: 6px 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {Colors.CYAN};
                color: #000000;
            }}
        """)
        btn_theme.clicked.connect(self.open_theme_dialog)
        header_layout.addWidget(btn_theme)

        btn_logout = QPushButton("تسجيل الخروج")
        btn_logout.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_logout.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BG_CARD};
                color: {Colors.RED};
                border: 1px solid {Colors.RED}44;
                border-radius: 8px;
                padding: 6px 14px;
            }}
            QPushButton:hover {{
                background-color: {Colors.RED};
                color: #ffffff;
            }}
        """)
        btn_logout.clicked.connect(self.close)
        header_layout.addWidget(btn_logout)

        body_layout.addWidget(header)

        self.stack = QStackedWidget()
        
        self.dashboard_page = DashboardWidget(self.db)
        self.pos_page = POSWidget(self.db)
        self.settings_page = SettingsWidget(self.db, on_theme_change_callback=self.apply_theme)
        self.games_page = GamesWidget(self.db)
        
        self.stack.addWidget(self.dashboard_page)
        self.stack.addWidget(self.create_placeholder("🖥️ إدارة الأجهزة", "قريباً: التحكم بالأجهزة وإعادة التشغيل والقفل عن بُعد"))
        self.stack.addWidget(self.create_placeholder("👥 إدارة المستخدمين", "قريباً: إضافة وتعديل حسابات المستخدمين والرصيد"))
        self.stack.addWidget(self.pos_page)
        self.stack.addWidget(self.create_placeholder("💰 إدارة المحفظة", "قريباً: الشحن والسحوبات والسجل المالي"))
        self.stack.addWidget(self.create_placeholder("🎁 نظام المكافآت", "قريباً: النقاط والهدايا والخصومات"))
        self.stack.addWidget(self.create_placeholder("🏆 البطولة والمسابقات", "قريباً: تنطيم المسابقات والفرق والجوائز"))
        self.stack.addWidget(self.games_page)
        self.stack.addWidget(self.create_placeholder("📊 التقارير والإحصائيات", "قريباً: تقارير المبيعات الشاملة والأرباح"))
        self.stack.addWidget(self.settings_page)

        body_layout.addWidget(self.stack)
        
        body_widget = QWidget()
        body_widget.setLayout(body_layout)
        root_layout.addWidget(body_widget, 1)

        self.switch_page(0)

    def open_theme_dialog(self):
        dlg = ThemeDialog(self.current_theme_key, self)
        if dlg.exec():
            self.apply_theme(dlg.selected_theme)

    def apply_theme(self, theme_key: str):
        self.current_theme_key = theme_key
        set_theme(theme_key)
        self.setStyleSheet(get_main_stylesheet())

    def create_placeholder(self, title: str, desc: str) -> QWidget:
        w = QWidget()
        w.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        l = QVBoxLayout(w)
        l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        t = QLabel(title)
        t.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        t.setStyleSheet(f"color: {Colors.CYAN};")
        
        d = QLabel(desc)
        d.setFont(QFont("Segoe UI", 12))
        d.setStyleSheet(f"color: {Colors.TEXT_MUTED}; margin-top: 10px;")
        
        l.addWidget(t)
        l.addWidget(d)
        return w

    def switch_page(self, idx: int):
        self.stack.setCurrentIndex(idx)
        titles = [
            "الرئيسية", "إدارة الأجهزة", "المستخدمين", "نقطة البيع (POS)",
            "المحفظة المالية", "نظام المكافآت", "المسابقات والبطولات",
            "مكتبة الألعاب", "التقارير المالية", "إعدادات النظام"
        ]
        if idx < len(titles):
            self.lbl_page_title.setText(titles[idx])
            
        for btn in self.nav_buttons:
            btn.update_style(btn.page_idx == idx)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    from Manager.login import LoginWindow
    login = LoginWindow()
    
    def on_login(username):
        window = MainManager(username)
        window.show()
        login.close()
        
    login.login_successful.connect(on_login)
    login.show()
    sys.exit(app.exec())