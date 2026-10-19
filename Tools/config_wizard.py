import sys
import pyodbc
from PyQt6.QtWidgets import (QApplication, QWizard, QWizardPage, QVBoxLayout,
                              QLabel, QLineEdit, QPushButton, QTextEdit, QHBoxLayout)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from Server.config import get_connection_string
from Tools.db_migration import DatabaseMigrator
from Server.database import DatabaseManager

class WelcomePage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("مرحباً بك في معالج الإعداد")
        layout = QVBoxLayout(self)
        lbl = QLabel("سيقوم المعالج بإعداد قاعدة البيانات والتحقق من الاتصال.")
        lbl.setWordWrap(True)
        lbl.setFont(QFont("Segoe UI", 12))
        layout.addWidget(lbl)

class ConnectionPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("فحص الاتصال")
        layout = QVBoxLayout(self)
        self.status_label = QLabel("اضغط فحص لاختبار الاتصال")
        layout.addWidget(self.status_label)
        btn = QPushButton("فحص الاتصال")
        btn.clicked.connect(self.test)
        layout.addWidget(btn)

    def test(self):
        db = DatabaseManager()
        if db.test_connection():
            self.status_label.setText("✅ الاتصال ناجح")
            self.status_label.setStyleSheet("color: green; font-size: 14px;")
        else:
            db.ensure_database()
            if db.test_connection():
                self.status_label.setText("✅ تم إنشاء قاعدة البيانات والاتصال ناجح")
                self.status_label.setStyleSheet("color: green; font-size: 14px;")
            else:
                self.status_label.setText("❌ فشل الاتصال")
                self.status_label.setStyleSheet("color: red; font-size: 14px;")

class MigrationPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("ترحيل قاعدة البيانات")
        layout = QVBoxLayout(self)
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        layout.addWidget(self.log)
        btn = QPushButton("بدء الترحيل")
        btn.clicked.connect(self.migrate)
        layout.addWidget(btn)

    def migrate(self):
        migrator = DatabaseMigrator(get_connection_string())
        results = migrator.run_migration()
        self.log.setPlainText("\n".join(results))

class ConfigWizard(QWizard):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("معالج الإعداد - Gaming Center Pro")
        self.setFixedSize(600, 450)
        self.addPage(WelcomePage())
        self.addPage(ConnectionPage())
        self.addPage(MigrationPage())

def main():
    app = QApplication(sys.argv)
    w = ConfigWizard()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()