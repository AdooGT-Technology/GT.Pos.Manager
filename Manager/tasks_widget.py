from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QLineEdit, QComboBox, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from Manager.theme import Colors

class TaskRow(QFrame):
    def __init__(self, task_data: dict, on_run=None):
        super().__init__()
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.task_data = task_data
        self.on_run = on_run
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BG_CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
            }}
            QFrame:hover {{
                border-color: {Colors.CYAN};
                background-color: {Colors.BG_HOVER};
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(16)
        
        icon = QLabel(task_data.get("icon", "⚙️"))
        icon.setFont(QFont("Segoe UI Emoji", 16))
        icon.setStyleSheet("border: none; background: transparent;")
        
        info_lay = QVBoxLayout()
        name = QLabel(task_data.get("name", "مهمة غير معروفة"))
        name.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        name.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; border: none; background: transparent;")
        
        desc = QLabel(task_data.get("desc", "وصف المهمة"))
        desc.setFont(QFont("Segoe UI", 9))
        desc.setStyleSheet(f"color: {Colors.TEXT_MUTED}; border: none; background: transparent;")
        
        info_lay.addWidget(name)
        info_lay.addWidget(desc)
        
        type_lbl = QLabel(task_data.get("type", "نظام"))
        type_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        type_lbl.setStyleSheet(f"""
            QLabel {{
                background-color: {Colors.PURPLE}22;
                color: {Colors.PURPLE};
                border: 1px solid {Colors.PURPLE}44;
                border-radius: 12px;
                padding: 4px 12px;
            }}
        """)
        
        btn_run = QPushButton("▶ تنفيذ المهمة")
        btn_run.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        btn_run.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_run.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.GREEN};
                color: #000000;
                border: none;
                border-radius: 6px;
                padding: 6px 16px;
            }}
            QPushButton:hover {{ opacity: 0.8; }}
        """)
        if self.on_run:
            btn_run.clicked.connect(lambda: self.on_run(self.task_data))
            
        btn_edit = QPushButton("✏️")
        btn_edit.setFixedSize(30, 30)
        btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_edit.setStyleSheet(f"""
            QPushButton {{ background-color: {Colors.BG_CARD_LIGHT}; border: 1px solid {Colors.BORDER}; border-radius: 6px; }}
            QPushButton:hover {{ border-color: {Colors.ORANGE}; color: {Colors.ORANGE}; }}
        """)
        
        layout.addWidget(icon)
        layout.addLayout(info_lay)
        layout.addStretch()
        layout.addWidget(type_lbl)
        layout.addWidget(btn_edit)
        layout.addWidget(btn_run)

class TasksWidget(QWidget):
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
        title = QLabel("🛠️ مكتبة المهام والعمليات (Task Library)")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {Colors.CYAN};")
        
        btn_add = QPushButton("➕ إضافة مهمة جديدة")
        btn_add.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add.setStyleSheet(f"""
            QPushButton {{ background-color: {Colors.CYAN}; color: #000000; border: none; border-radius: 6px; padding: 8px 16px; }}
            QPushButton:hover {{ opacity: 0.8; }}
        """)
        
        header.addWidget(title)
        header.addStretch()
        header.addWidget(btn_add)
        main_layout.addLayout(header)

        content = QHBoxLayout()
        content.setSpacing(16)
        
        # Sidebar for Categories
        cat_frame = QFrame()
        cat_frame.setFixedWidth(200)
        cat_frame.setStyleSheet(f"background-color: {Colors.BG_CARD}; border: 1px solid {Colors.BORDER}; border-radius: 8px;")
        cat_lay = QVBoxLayout(cat_frame)
        cat_lay.setContentsMargins(10, 10, 10, 10)
        
        lbl_c = QLabel("التصنيفات:")
        lbl_c.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        lbl_c.setStyleSheet(f"color: {Colors.TEXT_MUTED}; border: none;")
        cat_lay.addWidget(lbl_c)
        
        cats = ["الكل (All)", "إدارة الطاقة (Power)", "البرامج (Apps)", "الملفات (Files)", "سكربتات (Scripts)"]
        for c in cats:
            btn = QPushButton(c)
            btn.setStyleSheet(f"text-align: right; padding: 8px; border: none; border-radius: 4px; color: {Colors.TEXT_PRIMARY};")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            cat_lay.addWidget(btn)
        cat_lay.addStretch()
        
        content.addWidget(cat_frame)

        # Tasks List
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        self.list_container = QWidget()
        self.list_container.setStyleSheet("background: transparent;")
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(10)
        
        scroll.setWidget(self.list_container)
        content.addWidget(scroll, 1)
        
        main_layout.addLayout(content)
        self.load_mock_tasks()

    def load_mock_tasks(self):
        tasks = [
            {"icon": "🔄", "name": "إعادة تشغيل الأجهزة", "desc": "إرسال أمر Restart لجميع الأجهزة المحددة", "type": "Power"},
            {"icon": "🛑", "name": "إغلاق جميع التطبيقات", "desc": "إنهاء كافة المهام النشطة للمستخدم (Kill All)", "type": "Apps"},
            {"icon": "📦", "name": "نشر ملفات لعبة FC25", "desc": "نسخ التحديث الأخير من الخادم إلى أجهزة الكلاينت", "type": "Files"},
            {"icon": "💻", "name": "تحديث وكيل العميل", "desc": "تحديث برنامج Client Agent صامت", "type": "Scripts"},
            {"icon": "🧹", "name": "تنظيف الملفات المؤقتة", "desc": "حذف Temp & Prefetch لتسريع النظام", "type": "Scripts"},
        ]
        
        for t in tasks:
            row = TaskRow(t, on_run=self.execute_task)
            self.list_layout.addWidget(row)
        self.list_layout.addStretch()

    def execute_task(self, task):
        QMessageBox.information(self, "تنفيذ مهمة", f"جاري إرسال مهمة: {task['name']} للأجهزة المستهدفة...")
