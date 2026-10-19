"""
GT-POS Manager - Connection Test
اختبار سريع للاتصال بـ SQL Server
"""

import pyodbc
import sys


def test_connection(server="localhost", db_name="master", trusted=True, user="", pwd=""):
    print("=" * 50)
    print("🔍 GT-POS Connection Test")
    print("=" * 50)

    drivers = pyodbc.drivers()
    print(f"\n📡 ODBC Drivers المتاحة:")
    for d in drivers:
        print(f"   {'✅' if 'SQL Server' in d else '  '} {d}")

    driver = None
    for d in ["ODBC Driver 17 for SQL Server", "ODBC Driver 18 for SQL Server",
              "SQL Server Native Client 11.0", "SQL Server"]:
        if d in drivers:
            driver = d
            break

    if not driver:
        print("\n❌ لم يتم العثور على SQL Server ODBC Driver!")
        print("💡 قم بتحميله من: https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server")
        return False

    print(f"\n📡 Driver المستخدم: {driver}")

    if trusted:
        conn_str = f"DRIVER={{{driver}}};SERVER={server};DATABASE={db_name};Trusted_Connection=yes;"
    else:
        conn_str = f"DRIVER={{{driver}}};SERVER={server};DATABASE={db_name};UID={user};PWD={pwd};"

    try:
        conn = pyodbc.connect(conn_str, timeout=10)
        cursor = conn.cursor()
        cursor.execute("SELECT @@SERVERNAME, @@VERSION")
        row = cursor.fetchone()
        print(f"\n✅ تم الاتصال بنجاح!")
        print(f"   🖥️ السيرفر: {row[0]}")
        print(f"   📋 الإصدار: {row[1].split(chr(10))[0]}")

        cursor.execute("SELECT name FROM sys.databases ORDER BY name")
        dbs = [r[0] for r in cursor.fetchall()]
        print(f"\n🗄️ قواعد البيانات ({len(dbs)}):")
        for db in dbs:
            marker = " ⬅️" if db == "GT_POS_DB" else ""
            print(f"   {'🟢' if db == 'GT_POS_DB' else '⚪'} {db}{marker}")

        cursor.close()
        conn.close()
        return True
    except pyodbc.Error as e:
        print(f"\n❌ فشل الاتصال!")
        print(f"   الخطأ: {e}")
        print(f"\n💡 تأكد من:")
        print(f"   1. تشغيل SQL Server")
        print(f"   2. صحة اسم السيرفر: {server}")
        print(f"   3. صلاحيات المستخدم")
        print(f"   4. جدار الحماية")
        return False


if __name__ == '__main__':
    server = input("اسم السيرفر [localhost]: ").strip() or "localhost"
    auth = input("نوع المصادقة (1=Windows, 2=SQL) [1]: ").strip() or "1"
    user, pwd = "", ""
    if auth == "2":
        user = input("المستخدم [sa]: ").strip() or "sa"
        pwd = input("كلمة المرور: ").strip()
    test_connection(server, trusted=(auth == "1"), user=user, pwd=pwd)
    input("\nاضغط Enter للخروج...")