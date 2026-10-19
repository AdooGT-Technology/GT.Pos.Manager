from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView, QDialog, QComboBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from Manager.theme import Colors

class UserDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setWindowTitle("إضافة مستخدم جديد")
        self.setFixedSize(400, 350)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)
        
        title = QLabel("👤 إضافة لاعب / مستخدم جديد")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {Colors.CYAN};")
        layout.addWidget(title)
        
        self.txt_name = QLineEdit()
        self.txt_name.setPlaceholderText("الاسم الكامل...")
        
        self.txt_user = QLineEdit()
        self.txt_user.setPlaceholderText("اسم المستخدم (Username)...")
        
        self.txt_pass = QLineEdit()
        self.txt_pass.setPlaceholderText("كلمة المرور...")
        self.txt_pass.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.combo_group = QComboBox()
        self.combo_group.addItems(["عادي (Normal)", "مميز (VIP)", "بطولة (eSports)"])
        
        for w in [self.txt_name, self.txt_user, self.txt_pass, self.combo_group]:
            w.setStyleSheet(f"background-color: {Colors.BG_CARD_LIGHT}; border: 1px solid {Colors.BORDER}; border-radius: 6px; padding: 8px;")
            layout.addWidget(w)
            
        layout.addStretch()
        
        btn_save = QPushButton("💾 حفظ الحساب")
        btn_save.setFixedHeight(40)
        btn_save.setStyleSheet(f"background-color: {Colors.GREEN}; color: #000; font-weight: bold; border-radius: 6px;")
        btn_save.clicked.connect(self.accept)
        layout.addWidget(btn_save)

class UsersWidget(QWidget):
    def __init__(self, db=None):
        super().__init__()
        self.db = db
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setup_ui()
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)
        
        header = QHBoxLayout()
        title = QLabel("👥 إدارة حسابات اللاعبين")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {Colors.CYAN};")
        
        btn_add = QPushButton("➕ مستخدم جديد")
        btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add.setStyleSheet(f"background-color: {Colors.CYAN}; color: #000; font-weight: bold; border-radius: 6px; padding: 8px 16px;")
        btn_add.clicked.connect(self.add_user)
        
        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍 بحث بالاسم أو اليوزر...")
        self.search.setFixedWidth(300)
        
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.search)
        header.addWidget(btn_add)
        main_layout.addLayout(header)
        
        # جدول المستخدمين
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["ID", "الاسم", "اسم المستخدم", "المجموعة", "الرصيد", "الوقت المتبقي", "إجراءات"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet(f"""
            QTableWidget {{ background-color: {Colors.BG_CARD}; border: 1px solid {Colors.BORDER}; border-radius: 8px; color: {Colors.TEXT_PRIMARY}; }}
            QHeaderView::section {{ background-color: {Colors.BG_CARD_LIGHT}; color: {Colors.TEXT_MUTED}; font-weight: bold; padding: 8px; border: none; }}
        """)
        main_layout.addWidget(self.table)
        
        self.load_data()

    def add_user(self):
        dlg = UserDialog(self)
        if dlg.exec():
            self.load_data()

    def load_data(self):
        self.table.setRowCount(0)
        users = [
            {"id": "1", "name": "أحمد محمد", "user": "ahmed99", "group": "VIP", "balance": "150.00 ر.س", "time": "05:30:00"},
            {"id": "2", "name": "خالد عبدلله", "user": "khalid_x", "group": "عادي", "balance": "25.00 ر.س", "time": "01:15:00"},
            {"id": "3", "name": "فهد سعد", "user": "fahad2", "group": "عادي", "balance": "0.00 ر.س", "time": "00:00:00"},
        ]
        
        for i, u in enumerate(users):
            self.table.insertRow(i)
            self.table.setItem(i, 0, QTableWidgetItem(u["id"]))
            self.table.setItem(i, 1, QTableWidgetItem(u["name"]))
            self.table.setItem(i, 2, QTableWidgetItem(u["user"]))
            self.table.setItem(i, 3, QTableWidgetItem(u["group"]))
            
            bal_item = QTableWidgetItem(u["balance"])
            bal_item.setForeground(Qt.GlobalColor.green if "0.00" not in u["balance"] else Qt.GlobalColor.red)
            self.table.setItem(i, 4, bal_item)
            
            self.table.setItem(i, 5, QTableWidgetItem(u["time"]))
            
            actions = QWidget()
            actions.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            a_lay = QHBoxLayout(actions)
            a_lay.setContentsMargins(0, 0, 0, 0)
            a_lay.setSpacing(4)
            
            b_edit = QPushButton("✏️")
            b_edit.setStyleSheet(f"background: transparent; color: {Colors.CYAN}; border: none;")
            b_charge = QPushButton("💰 شحن")
            b_charge.setStyleSheet(f"background-color: {Colors.GREEN}; color: #000; border-radius: 4px; padding: 4px;")
            
            a_lay.addWidget(b_charge)
            a_lay.addWidget(b_edit)
            a_lay.addStretch()
            
            self.table.setCellWidget(i, 6, actions)
