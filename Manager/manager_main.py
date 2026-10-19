# -*- coding: utf-8 -*-
"""Application shell: sidebar, top bar, lazy page loading, theme switching."""

from __future__ import annotations

import sys

from PyQt6.QtCore import QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QLabel, QMainWindow, QMenu,
    QPushButton, QScrollArea, QStackedWidget, QVBoxLayout, QWidget,
)

from Manager.data import Data
from Manager.theme import THEMES, Colors, get_stylesheet, set_theme, theme_key
from Manager.icons import make_icon, make_pixmap
from Manager.ui import CommandPalette, Pill, icon_button, label, repolish
from Server.database import DatabaseManager

try:
    from version import APP_VERSION
except Exception:  # pragma: no cover
    APP_VERSION = "3.6.0"


# (key, icon, title, group, factory-import)
PAGE_SPECS = [
    ("overview", "grid", "نظرة عامة", "التشغيل", "Manager.dashboard_widget:DashboardWidget"),
    ("devices", "monitor", "الأجهزة", "التشغيل", "Manager.devices_widget:DevicesWidget"),
    ("studio", "studio", "استوديو العميل", "التشغيل", "Manager.client_studio:ClientStudioWidget"),
    ("members", "users", "الأعضاء", "العملاء", "Manager.users_widget:UsersWidget"),
    ("sessions", "clock", "الجلسات المباشرة", "التشغيل", "Manager.sessions_widget:SessionsWidget"),
    ("shifts", "calendar", "الورديات", "التشغيل", "Manager.shifts_widget:ShiftsWidget"),
    ("pos", "cart", "نقطة البيع", "العملاء", "Manager.pos_widget:POSWidget"),
    ("wallet", "wallet", "المحفظة", "العملاء", "Manager.wallet_widget:WalletWidget"),
    ("library", "gamepad", "مكتبة الألعاب", "المحتوى", "Manager.games_widget:GamesWidget"),
    ("tasks", "terminal", "المهام", "المحتوى", "Manager.tasks_widget:TasksWidget"),
    ("reports", "chart", "التقارير", "الإدارة", "Manager.reports_widget:ReportsWidget"),
    ("rewards", "gift", "المكافآت", "الإدارة", "Manager.rewards_widget:RewardsWidget"),
    ("events", "trophy", "البطولات", "الإدارة", "Manager.tournaments_widget:TournamentsWidget"),
    ("billing", "receipt", "الفوترة والتسعير", "الإدارة", "Manager.billing_widget:BillingWidget"),
    ("settings", "settings", "الإعدادات", "الإدارة", "Manager.settings_widget:SettingsWidget"),
]

PAGE_SUBTITLES = {
    "overview": "حالة الصالة الآن، والأرقام التي تهمك اليوم",
    "devices": "من يعمل، ومن جاهز، والتحكم عن بُعد",
    "studio": "معاينة شاشة العميل وأوامر الجلسة",
    "members": "حسابات اللاعبين والأرصدة",
    "sessions": "من يلعب الآن، والوقت المتبقي في كل جلسة",
    "shifts": "فتح الدرج وإغلاقه ومطابقة النقد",
    "pos": "بيع سريع للكاشير",
    "wallet": "إيداع وسحب وسجل الحركة",
    "library": "ألعاب الصالة وملفات التشغيل",
    "tasks": "أوامر جاهزة تُنفَّذ على الأجهزة",
    "reports": "مبيعات وجلسات وأداء",
    "rewards": "قواعد النقاط والمكافآت",
    "events": "بطولات وجدول مباريات",
    "billing": "المجموعات والملفات والعروض والأسعار",
    "settings": "الشكل والاتصال والبيانات",
}


def _load(factory_path: str, *args):
    module_path, class_name = factory_path.split(":")
    module = __import__(module_path, fromlist=[class_name])
    return getattr(module, class_name)(*args)


class NavButton(QPushButton):
    """Sidebar row: a vector icon and a label inside a clickable button.

    Qt draws QPushButton icons on the wrong side in RTL and shrinks them, so the
    row is laid out manually with two labels nested in the button.
    """

    def __init__(self, icon: str, text: str, parent=None):
        super().__init__(parent)
        self.icon_name = icon
        self.title = text
        self.collapsed = False
        self.setProperty("variant", "nav")
        self.setProperty("active", "false")
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(44)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 14, 0)
        row.setSpacing(10)

        self.icon_label = QLabel(self)
        self.icon_label.setFixedSize(24, 24)
        self.icon_label.setStyleSheet("background: transparent; border: none;")
        self.text_label = QLabel(text, self)
        self.text_label.setStyleSheet("background: transparent; border: none; font-size: 14px;")
        for widget in (self.icon_label, self.text_label):
            widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        row.addStretch(0)
        row.addWidget(self.icon_label)
        row.addWidget(self.text_label)
        row.addStretch(1)
        self.refresh_theme()

    def refresh_theme(self):
        color = Colors.CYAN if self.property("active") == "true" else Colors.TEXT_PRIMARY
        self.icon_label.setPixmap(make_pixmap(self.icon_name, 22, color))
        self.text_label.setStyleSheet(
            "background: transparent; border: none; font-size: 14px; color: %s;" % color
        )

    def set_active(self, active: bool):
        self.setChecked(active)
        self.setProperty("active", "true" if active else "false")
        repolish(self)
        self.refresh_theme()

    def set_collapsed(self, collapsed: bool):
        self.collapsed = collapsed
        self.text_label.setVisible(not collapsed)
        row = self.layout()
        row.setContentsMargins(0, 0, 0 if collapsed else 14, 0)
        row.setSpacing(0 if collapsed else 10)
        row.setStretch(0, 1 if collapsed else 0)
        row.setStretch(3, 1)


class Sidebar(QFrame):
    navigate = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(248)
        self.collapsed = False
        self.buttons = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 16, 12, 12)
        root.setSpacing(10)

        brand = QHBoxLayout()
        brand.setSpacing(10)
        mark = QLabel("GT")
        mark.setFixedSize(34, 34)
        mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mark.setStyleSheet(
            "background-color: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.12);"
            " border-radius: 9px; font-weight: 700; font-size: 12px;"
        )
        self.brand_text = QVBoxLayout()
        self.brand_text.setSpacing(0)
        name = label("Gaming Center", "Title")
        self.version_label = label(f"الإصدار {APP_VERSION}", "Caption")
        self.brand_text.addWidget(name)
        self.brand_text.addWidget(self.version_label)
        self.name_label = name
        brand.addWidget(mark)
        brand.addLayout(self.brand_text)
        brand.addStretch()
        root.addLayout(brand)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        nav_host = QWidget()
        self.nav_layout = QVBoxLayout(nav_host)
        self.nav_layout.setContentsMargins(0, 4, 0, 4)
        self.nav_layout.setSpacing(2)

        current_group = None
        self.sections = []
        for key, glyph, title, group, _ in PAGE_SPECS:
            if group != current_group:
                current_group = group
                section = label(group, "Section")
                section.setContentsMargins(10, 12, 10, 4)
                self.sections.append(section)
                self.nav_layout.addWidget(section)
            button = NavButton(glyph, title)
            button.clicked.connect(lambda _checked, k=key: self.navigate.emit(k))
            self.buttons[key] = button
            self.nav_layout.addWidget(button)
        self.nav_layout.addStretch()
        self.scroll.setWidget(nav_host)
        root.addWidget(self.scroll, 1)

        self.status_pill = Pill("قاعدة البيانات", "muted")
        root.addWidget(self.status_pill, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.user_button = QPushButton()
        self.user_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.user_button.setProperty("variant", "ghost")
        self.user_button.setStyleSheet("QPushButton { text-align: right; padding: 8px; }")
        self.user_button.setFixedHeight(46)
        root.addWidget(self.user_button)

    def set_user(self, name: str):
        self.user_button.setText(f"  {name}\n      مدير النظام")
        self.user_button.setIcon(make_icon("users", Colors.TEXT_MUTED, 20))
        self.user_button.setIconSize(QSize(20, 20))

    def set_active(self, key: str):
        for page_key, button in self.buttons.items():
            button.set_active(page_key == key)

    def set_db_state(self, live: bool):
        if live:
            self.status_pill.setText("متصل بقاعدة البيانات")
            self.status_pill.set_tone("success")
        else:
            self.status_pill.setText("وضع البيانات التجريبية")
            self.status_pill.set_tone("warning")

    def toggle_collapsed(self):
        self.collapsed = not self.collapsed
        self.setFixedWidth(76 if self.collapsed else 248)
        self.name_label.setVisible(not self.collapsed)
        self.version_label.setVisible(not self.collapsed)
        self.status_pill.setVisible(not self.collapsed)
        for section in getattr(self, "sections", []):
            section.setVisible(not self.collapsed)
        for button in self.buttons.values():
            button.set_collapsed(self.collapsed)


class MainManager(QMainWindow):
    logout_requested = pyqtSignal()

    def __init__(self, username: str = "مدير النظام"):
        super().__init__()
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.username = username
        self.db = DatabaseManager()
        self.data = Data(self.db)
        self.pages = {}
        self.current_key = None
        self._theme_items = {}

        self.setWindowTitle(f"Gaming Center Pro — {APP_VERSION}")
        self.resize(1360, 840)
        self.setMinimumSize(1080, 680)

        set_theme(theme_key())
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(get_stylesheet())
        self._build_shell()
        self.apply_feature_flags()
        self.show_page(self._start_page())
        QTimer.singleShot(400, self._probe_connection)

    # ── settings-driven shell ────────────────────────────────────────────
    FEATURE_PAGES = {
        "pos": "pos", "wallet": "wallet", "library": "library", "tasks": "tasks",
        "reports": "reports", "rewards": "rewards", "tournaments": "events",
        "studio": "studio", "sessions": "sessions", "shifts": "shifts",
        "billing": "billing",
    }

    def _start_page(self) -> str:
        try:
            page = self.data.settings.start_page()
        except Exception:
            page = "overview"
        keys = {spec[0] for spec in PAGE_SPECS}
        return page if page in keys else "overview"

    def apply_feature_flags(self):
        """Hide the pages the operator switched off in الإعدادات ← الخصائص."""
        try:
            features = self.data.settings.section("features")
        except Exception:
            return
        for feature, page_key in self.FEATURE_PAGES.items():
            enabled = bool(features.get(feature, True))
            button = self.sidebar.buttons.get(page_key)
            if button is not None:
                button.setVisible(enabled)
            if not enabled and self.current_key == page_key:
                self.show_page("overview")

    # ── shell ────────────────────────────────────────────────────────────
    def _build_shell(self):
        root = QWidget()
        self.setCentralWidget(root)
        shell = QHBoxLayout(root)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(0)

        self.sidebar = Sidebar()
        self.sidebar.set_user(self.username)
        self.sidebar.navigate.connect(self.show_page)
        self.sidebar.user_button.clicked.connect(self._open_user_menu)
        shell.addWidget(self.sidebar)

        body = QVBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        body.addWidget(self._build_topbar())

        self.stack = QStackedWidget()
        self.stack.setContentsMargins(0, 0, 0, 0)
        body.addWidget(self.stack, 1)

        body_host = QWidget()
        body_host.setLayout(body)
        shell.addWidget(body_host, 1)

        QShortcut(QKeySequence("Ctrl+K"), self, activated=self.open_palette)
        QShortcut(QKeySequence("Ctrl+B"), self, activated=self.sidebar.toggle_collapsed)
        QShortcut(QKeySequence("F5"), self, activated=self.refresh_current)

    def _build_topbar(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("TopBar")
        bar.setFixedHeight(64)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(24, 0, 20, 0)
        layout.setSpacing(8)

        title_col = QVBoxLayout()
        title_col.setSpacing(0)
        self.page_title = label("نظرة عامة", "Title")
        self.page_subtitle = label(PAGE_SUBTITLES["overview"], "Caption")
        title_col.addWidget(self.page_title)
        title_col.addWidget(self.page_subtitle)
        layout.addLayout(title_col)
        layout.addStretch()

        search = QPushButton("  بحث      Ctrl K")
        search.setCursor(Qt.CursorShape.PointingHandCursor)
        search.setProperty("variant", "quiet")
        search.setFixedWidth(188)
        search.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        search.setIcon(make_icon("search", Colors.TEXT_MUTED, 18))
        search.setIconSize(QSize(18, 18))
        search.setStyleSheet(
            "QPushButton { text-align: right; padding: 0 10px; color: %s; font-size: 12px; }" % "#8FA0AE"
        )
        search.clicked.connect(self.open_palette)
        layout.addWidget(search)

        layout.addWidget(icon_button("refresh", "تحديث الصفحة (F5)", self.refresh_current,
                                     size=40, icon_size=22))
        self.theme_button = icon_button("theme", "المظهر", self._open_theme_menu,
                                        size=40, icon_size=22)
        layout.addWidget(self.theme_button)
        self.bell_button = icon_button("bell", "آخر الأحداث", self._open_activity_menu,
                                       size=40, icon_size=22)
        layout.addWidget(self.bell_button)
        layout.addWidget(icon_button("power", "تسجيل الخروج", self._logout,
                                     size=40, icon_size=22))

        avatar = QPushButton(self.username[:1])
        avatar.setFixedSize(34, 34)
        avatar.setCursor(Qt.CursorShape.PointingHandCursor)
        avatar.setToolTip(self.username)
        avatar.setStyleSheet(
            "QPushButton { border-radius: 17px; border: 1px solid rgba(255,255,255,0.14);"
            " background-color: rgba(255,255,255,0.06); font-weight: 600; }"
        )
        avatar.clicked.connect(self._open_user_menu)
        layout.addWidget(avatar)
        return bar

    # ── navigation ───────────────────────────────────────────────────────
    def _ensure_page(self, key: str):
        if key in self.pages:
            return self.pages[key]
        spec = next((s for s in PAGE_SPECS if s[0] == key), None)
        if spec is None:
            return None
        widget = _load(spec[4], self.data)
        if hasattr(widget, "set_navigator"):
            widget.set_navigator(self.show_page)
        self.pages[key] = widget
        self.stack.addWidget(widget)
        return widget

    def show_page(self, key: str):
        if not any(spec[0] == key for spec in PAGE_SPECS):
            return
        page = self._ensure_page(key)
        if page is None:
            return
        self.stack.setCurrentWidget(page)
        self.current_key = key
        self.sidebar.set_active(key)
        title = next((s[2] for s in PAGE_SPECS if s[0] == key), "")
        self.page_title.setText(title)
        self.page_subtitle.setText(PAGE_SUBTITLES.get(key, ""))
        if hasattr(page, "on_shown"):
            page.on_shown()
        if key == "settings":
            self.apply_feature_flags()

    def switch_page(self, index: int):
        """Backwards-compatible index navigation."""
        if 0 <= index < len(PAGE_SPECS):
            self.show_page(PAGE_SPECS[index][0])

    def refresh_current(self):
        page = self.pages.get(self.current_key)
        for method in ("reload", "refresh", "load_data"):
            if page is not None and hasattr(page, method):
                getattr(page, method)()
                break
        self.data.invalidate()
        self._toast("تم التحديث")

    def open_palette(self):
        items = [(spec[1], spec[2], spec[3], lambda k=spec[0]: self.show_page(k))
                 for spec in PAGE_SPECS]
        items += [
            ("theme", "تغيير المظهر", "الشكل", self._open_theme_menu),
            ("refresh", "تحديث الصفحة", "F5", self.refresh_current),
            ("power", "تسجيل الخروج", "إنهاء الجلسة", self._logout),
        ]
        CommandPalette(items, self).exec()

    # ── menus ────────────────────────────────────────────────────────────
    def _open_theme_menu(self):
        menu = QMenu(self)
        menu.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        for key, theme in THEMES.items():
            action = QAction(f"{theme['name']}  —  {theme['hint']}", menu)
            action.setCheckable(True)
            action.setChecked(key == theme_key())
            action.triggered.connect(lambda _checked, k=key: self.apply_theme(k))
            menu.addAction(action)
        menu.exec(self.theme_button.mapToGlobal(self.theme_button.rect().bottomLeft()))

    def _open_activity_menu(self):
        menu = QMenu(self)
        menu.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        rows = self.data.query(
            "SELECT TOP 6 Description, Details, CreatedAt FROM ActivityLog ORDER BY LogId DESC",
            ttl=5, key="activity",
        )
        if not rows:
            rows = [
                {"Description": "بدء وردية المساء", "Details": "مدير النظام", "CreatedAt": "12 د"},
                {"Description": "شحن رصيد", "Details": "noura.g +320.50", "CreatedAt": "38 د"},
                {"Description": "إغلاق جلسة", "Details": "PC-04 — 2:10", "CreatedAt": "ساعة"},
            ]
        for row in rows:
            stamp = row.get("CreatedAt")
            when = stamp.strftime("%H:%M") if hasattr(stamp, "strftime") else str(stamp or "")
            menu.addAction(f"{row.get('Description', '')}  ·  {row.get('Details', '')}   {when}")
        menu.addSeparator()
        menu.addAction("فتح التقارير", lambda: self.show_page("reports"))
        menu.exec(self.bell_button.mapToGlobal(self.bell_button.rect().bottomLeft()))

    def _open_user_menu(self):
        menu = QMenu(self)
        menu.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        menu.addAction(self.username, lambda: None).setEnabled(False)
        menu.addSeparator()
        menu.addAction("الإعدادات", lambda: self.show_page("settings"))
        menu.addAction("الملف الشخصي", lambda: self._toast("بيانات الحساب تُدار من جدول الموظفين"))
        menu.addSeparator()
        menu.addAction("تسجيل الخروج", self._logout)
        menu.exec(self.sidebar.user_button.mapToGlobal(self.sidebar.user_button.rect().topLeft()))

    # ── theme & status ───────────────────────────────────────────────────
    def apply_theme(self, key: str):
        set_theme(key)
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(get_stylesheet())
        self._repolish_tree(self)
        self._toast(f"المظهر: {THEMES[key]['name']}", "accent")

    def apply_theme_and_refresh(self, key: str):
        """Kept for compatibility; no longer rebuilds the UI."""
        self.apply_theme(key)

    def _repolish_tree(self, root: QWidget):
        for child in root.findChildren(QWidget):
            if hasattr(child, "refresh_theme"):
                try:
                    child.refresh_theme()
                except Exception:
                    pass
        root.update()

    def _probe_connection(self):
        live = self.data.live
        for page in self.pages.values():
            for method in ("reload", "refresh"):
                if hasattr(page, method):
                    try:
                        getattr(page, method)()
                    except Exception:
                        pass
                    break
        self.sidebar.set_db_state(live)
        if not live:
            self._toast("تعذر الاتصال بقاعدة البيانات — تعمل الواجهة ببيانات تجريبية", "warning", 3600)

    def _logout(self):
        self.logout_requested.emit()
        self.close()

    def _toast(self, text: str, tone: str = "accent", msec: int = 2200):
        from Manager.ui import Toast
        Toast(self, text, tone, msec)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self._logout_prompt()
        super().keyPressEvent(event)

    def _logout_prompt(self):
        # Esc should not close the manager; ignore.
        pass


class AppController:
    """Owns the login → manager → logout cycle in one QApplication."""

    def __init__(self):
        self.login = None
        self.manager = None

    def start(self):
        from Manager.login import LoginWindow
        self.open_login()

    def open_login(self):
        from Manager.login import LoginWindow
        self.login = LoginWindow()
        self.login.login_successful.connect(self.open_manager)
        self.login.show()

    def open_manager(self, username: str):
        self.manager = MainManager(username)
        self.manager.logout_requested.connect(self._on_logout)
        self.manager.show()
        if self.login is not None:
            self.login.close()
            self.login = None

    def _on_logout(self):
        QTimer.singleShot(0, self.open_login)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Gaming Center Pro")
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    set_theme(theme_key())
    app.setStyleSheet(get_stylesheet())
    controller = AppController()
    controller.start()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
