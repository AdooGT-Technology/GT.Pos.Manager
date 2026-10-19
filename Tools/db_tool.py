"""
GT-POS Manager - Auto Database Setup
=====================================
إعداد تلقائي لقاعدة البيانات عند أول تشغيل
يقوم بإنشاء القاعدة والجداول والبيانات الافتراضية
"""

import os
import sys
import re
import pyodbc
import logging
from datetime import datetime

# ── إضافة مسار المشروع ──
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from Tools.db_migration import DatabaseMigrator
from Server.config import DB_SERVER, DB_NAME, DB_DRIVER, DB_TRUSTED

# ── إعداد الـ Logging ──
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("AutoSetup")


class AutoSetup:
    """معالج الإعداد التلقائي لقاعدة البيانات"""

    def __init__(self, server=None, database=None, driver=None, trusted=None):
        self.server = server or DB_SERVER
        self.database = database or DB_NAME
        self.driver = driver or DB_DRIVER
        self.trusted = trusted if trusted is not None else DB_TRUSTED

    def _master_connection_string(self):
        return (
            f"DRIVER={self.driver};"
            f"SERVER={self.server};"
            f"DATABASE=master;"
            f"{'Trusted_Connection=yes;' if self.trusted else ''}"
        )

    def test_server_connection(self):
        """اختبار الاتصال بالسيرفر"""
        print("=" * 60)
        print("🔍 GT-POS - Auto Database Check")
        print("=" * 60)
        print(f"📡 السيرفر: {self.server}")
        print(f"🗄️ القاعدة: {self.database}")

        try:
            conn = pyodbc.connect(self._master_connection_string(), timeout=10)
            conn.close()
            print("  ✅ الاتصال بالسيرفر ناجح")
            return True
        except pyodbc.Error as e:
            print(f"  ❌ فشل الاتصال: {e}")
            print()
            print("  💡 تأكد من:")
            print("     1. SQL Server يعمل")
            print("     2. اسم السيرفر صحيح")
            print("     3. SQL Server Browser يعمل")
            print("     4. TCP/IP مفعل في SQL Server Configuration Manager")
            return False

    def update_config_file(self):
        """تحديث Server/config.py بقيم الاتصال الحالية"""
        config_path = os.path.join(PROJECT_ROOT, "Server", "config.py")
        if not os.path.exists(config_path):
            logger.warning(f"ملف config.py غير موجود: {config_path}")
            return False

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                content = f.read()

            # استخدام lambda لتجنب مشكلة bad escape مع backslashes
            content = re.sub(
                r'DB_SERVER\s*=\s*r?["\'].*?["\']',
                lambda m: f'DB_SERVER = r"{self.server}"',
                content,
            )
            content = re.sub(
                r'DB_NAME\s*=\s*["\'].*?["\']',
                lambda m: f'DB_NAME = "{self.database}"',
                content,
            )
            content = re.sub(
                r'DB_DRIVER\s*=\s*["\'].*?["\']',
                lambda m: f'DB_DRIVER = "{self.driver}"',
                content,
            )

            with open(config_path, "w", encoding="utf-8") as f:
                f.write(content)

            logger.info("✅ تم تحديث config.py بنجاح")
            return True

        except Exception as e:
            logger.warning(f"⚠️ لم يتم تحديث config.py: {e}")
            return False

    def run_full_setup(self):
        """تنفيذ الإعداد الكامل"""
        print()
        logger.info("=" * 60)
        logger.info(f"🚀 GT-POS Database Setup | الإصدار: 1.2.0")
        logger.info(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"📡 السيرفر: {self.server}")
        logger.info(f"🗄️ القاعدة: {self.database}")
        logger.info("=" * 60)

        if not self.test_server_connection():
            return False

        try:
            migrator = DatabaseMigrator(
                server=self.server,
                database=self.database,
                driver=self.driver,
                trusted=self.trusted,
            )
            success = migrator.full_setup()

            if success:
                print()
                print(f"✅ قاعدة البيانات جاهزة! v1.2.0")
                self.update_config_file()
                return True
            else:
                print()
                print("❌ فشل إعداد قاعدة البيانات")
                return False

        except Exception as e:
            logger.error(f"❌ خطأ: {e}")
            import traceback
            traceback.print_exc()
            return False


# ──────────────────────────────────────────────
#  دالة سريعة للاستدعاء من setup.bat
# ──────────────────────────────────────────────
def auto_check_and_update(server=None, db_name=None):
    """
    دالة سريعة للإعداد التلقائي.
    يُستدعى من setup.bat:
      from auto_setup import auto_check_and_update; auto_check_and_update(...)
    """
    setup = AutoSetup(server=server, database=db_name)
    return setup.run_full_setup()


# ──────────────────────────────────────────────
#  نقطة الدخول
# ──────────────────────────────────────────────
def main():
    setup = AutoSetup()
    success = setup.run_full_setup()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())