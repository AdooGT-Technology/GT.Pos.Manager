# -*- coding: utf-8 -*-
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QComboBox, QFormLayout)
from PyQt6.QtCore import Qt
from Manager.theme import Colors

class BaseDialog(QDialog):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(400)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Colors.BG_MAIN};
                border: 1px solid {Colors.PURPLE};
            }}
            QLabel {{ color: {Colors.TEXT_PRIMARY}; }}
            QLineEdit, QComboBox {{
                background-color: {Colors.BG_INPUT};
                border: 1px solid {Colors.BORDER};
                color: {Colors.TEXT_PRIMARY};
                padding: 8px;
                border-radius: 5px;
            }}
            QPushButton#btn_save {{
                background-color: {Colors.PURPLE};
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }}
        """)
        self.layout = QVBoxLayout(self)

class HostDialog(BaseDialog):
    """نافذة إضافة/تعديل جهاز"""
    def __init__(self, data=None, groups=None):
        super().__init__("إدارة بيانات الجهاز")
        self.form = QFormLayout()
        
        self.txt_name = QLineEdit()
        self.txt_name.setPlaceholderText("مثال: PC-01")
        if data: self.txt_name.setText(data['HostName'])
        
        self.cb_group = QComboBox()
        for g in groups or []:
            self.cb_group.addItem(g['GroupName'], g['GroupID'])
        
        self.txt_ip = QLineEdit()
        self.txt_ip.setPlaceholderText("192.168.1.100")
        
        self.form.addRow("اسم الجهاز:", self.txt_name)
        self.form.addRow("المجموعة:", self.cb_group)
        self.form.addRow("عنوان IP:", self.txt_ip)
        
        self.btn_save = QPushButton("حفظ البيانات")
        self.btn_save.setObjectName("btn_save")
        self.btn_save.clicked.connect(self.accept)
        
        self.layout.addLayout(self.form)
        self.layout.addWidget(self.btn_save)

    def get_data(self):
        return {
            "HostName": self.txt_name.text(),
            "GroupID": self.cb_group.currentData(),
            "IPAddress": self.txt_ip.text()
        }

class MemberDialog(BaseDialog):
    """نافذة إضافة/تعديل عضو"""
    def __init__(self, groups=None):
        super().__init__("إضافة عضو جديد")
        self.form = QFormLayout()
        
        self.txt_user = QLineEdit()
        self.txt_name = QLineEdit()
        self.txt_pass = QLineEdit()
        self.txt_pass.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.cb_group = QComboBox()
        for g in groups or []:
            self.cb_group.addItem(g['GroupName'], g['GroupID'])

        self.form.addRow("اسم المستخدم:", self.txt_user)
        self.form.addRow("الاسم الكامل:", self.txt_name)
        self.form.addRow("كلمة المرور:", self.txt_pass)
        self.form.addRow("الفئة:", self.cb_group)
        
        self.btn_save = QPushButton("إنشاء الحساب")
        self.btn_save.setObjectName("btn_save")
        self.btn_save.clicked.connect(self.accept)
        
        self.layout.addLayout(self.form)
        self.layout.addWidget(self.btn_save)