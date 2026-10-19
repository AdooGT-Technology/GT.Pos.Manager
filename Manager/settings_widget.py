from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QLineEdit, QComboBox, QCheckBox,
    QGridLayout, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from Manager.theme import Colors, THEMES

class ToggleSwitch(QWidget):
    def __init__(self, checked=False, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.checked = checked
        self.setFixedSize(48, 24)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event):
        self.checked = not self.checked
        self.update()

    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter, QBrush, QColor
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        bg_color = QColor(Colors.CYAN) if self.checked else QColor(Colors.BG_CARD_LIGHT)
        p.setBrush(QBrush(bg_color))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(0, 0, 48, 24, 12, 12)
        
        knob_x = 26 if self.checked else 2
        p.setBrush(QBrush(QColor("#ffffff")))
        p.drawEllipse(knob_x, 2, 20, 20)

class SettingsCard(QFrame):
    def __init__(self, title: str, icon: str = "⚙️"):
        super().__init__()
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setObjectName("SettingsCard")
        self.setStyleSheet(f"""
            QFrame#SettingsCard {{
                background-color: {Colors.BG_CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: 12px;
            }}
        """)
        
        self.card_layout = QVBoxLayout(self)
        self.card_layout.setContentsMargins(18, 16, 18, 16)
        self.card_layout.setSpacing(14)

        header = QHBoxLayout()
        header.setSpacing(10)
        
        lbl_icon = QLabel(icon)
        lbl_icon.setFont(QFont("Segoe UI Emoji", 14))
        
        lbl_title = QLabel(title)
        lbl_title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        lbl_title.setStyleSheet(f"color: {Colors.CYAN};")

        header.addWidget(lbl_icon)
        header.addWidget(lbl_title)
        header.addStretch()
        
        self.card_layout.addLayout(header)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet(f"background-color: {Colors.BORDER}; max-height: 1px;")
        self.card_layout.addWidget(divider)

    def add_row(self, label_text: str, widget: QWidget):
        row = QHBoxLayout()
        row.setSpacing(12)
        
        lbl = QLabel(label_text)
        lbl.setFont(QFont("Segoe UI", 10))
        lbl.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")

        row.addWidget(lbl)
        row.addStretch()
        row.addWidget(widget)
        
        self.card_layout.addLayout(row)

class SettingsWidget(QWidget):
    def __init__(self, db=None, on_theme_change_callback=None):
        super().__init__()
        self.db = db
        self.on_theme_change = on_theme_change_callback
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setup_ui()
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; }")

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(16)

        card_theme = SettingsCard("مظهر الواجهة والتصميم", "🎨")
        self.combo_theme = QComboBox()
        for k, v in THEMES.items():
            self.combo_theme.addItem(v["name"], k)
        self.combo_theme.setStyleSheet(f"background-color: {Colors.BG_CARD_LIGHT}; color: {Colors.TEXT_PRIMARY}; border: 1px solid {Colors.BORDER}; padding: 6px; border-radius: 6px;")
        self.combo_theme.currentIndexChanged.connect(self.change_theme)
        card_theme.add_row("اختر المظهر المفضل للوحة التحكم:", self.combo_theme)
        container_layout.addWidget(card_theme)

        card_center = SettingsCard("معلومات المركز والفرع", "🏬")
        txt_center_name = QLineEdit("Gaming Center Pro")
        txt_center_name.setFixedWidth(220)
        txt_center_name.setStyleSheet(f"background-color: {Colors.BG_CARD_LIGHT}; color: {Colors.TEXT_PRIMARY}; border: 1px solid {Colors.BORDER}; padding: 6px; border-radius: 6px;")
        card_center.add_row("اسم المركز التجاري:", txt_center_name)
        container_layout.addWidget(card_center)

        card_financial = SettingsCard("المالية والتسعير", "💰")
        txt_rate = QLineEdit("15.00")
        txt_rate.setFixedWidth(100)
        txt_rate.setStyleSheet(f"background-color: {Colors.BG_CARD_LIGHT}; color: {Colors.TEXT_PRIMARY}; border: 1px solid {Colors.BORDER}; padding: 6px; border-radius: 6px;")
        card_financial.add_row("سعر الساعة الأساسي (ر.س):", txt_rate)
        container_layout.addWidget(card_financial)

        card_security = SettingsCard("الأمان والحسابات", "🔒")
        sw_2fa = ToggleSwitch(True)
        card_security.add_row("تفعيل التوثيق الثنائي (2FA) للمدراء:", sw_2fa)
        container_layout.addWidget(card_security)

        btn_save = QPushButton("💾 حفظ كافة الإعدادات")
        btn_save.setFixedHeight(46)
        btn_save.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.GREEN};
                color: #000000;
                border: none;
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background-color: {Colors.GREEN}EE;
            }}
        """)
        btn_save.clicked.connect(self.save_settings)
        container_layout.addWidget(btn_save)

        container_layout.addStretch()
        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    def change_theme(self, index):
        theme_key = self.combo_theme.itemData(index)
        if theme_key and self.on_theme_change:
            self.on_theme_change(theme_key)

    def save_settings(self):
        QMessageBox.information(self, "تم الحفظ", "تم حفظ الإعدادات بنجاح!")