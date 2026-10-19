"""
GT-POS Manager - Backup & Restore
"""

import pyodbc
import os
from datetime import datetime


class BackupManager:
    def __init__(self, connection_string):
        self.connection_string = connection_string
        self.connection = None

    def connect(self):
        try:
            self.connection = pyodbc.connect(self.connection_string, autocommit=True)
            return True
        except:
            return False

    def disconnect(self):
        if self.connection:
            self.connection.close()

    def backup_database(self, db_name, backup_path=None):
        if backup_path is None:
            os.makedirs("backups", exist_ok=True)
            backup_path = os.path.abspath(f"backups/{db_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak")
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"BACKUP DATABASE [{db_name}] TO DISK = '{backup_path}' WITH FORMAT, INIT, COMPRESSION")
            while cursor.nextset():
                pass
            cursor.close()
            size_mb = round(os.path.getsize(backup_path) / (1024 * 1024), 2) if os.path.exists(backup_path) else 0
            return {'success': True, 'path': backup_path, 'size_mb': size_mb}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def restore_database(self, db_name, backup_path):
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"ALTER DATABASE [{db_name}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE")
            cursor.execute(f"RESTORE DATABASE [{db_name}] FROM DISK = '{backup_path}' WITH REPLACE")
            while cursor.nextset():
                pass
            cursor.execute(f"ALTER DATABASE [{db_name}] SET MULTI_USER")
            cursor.close()
            return {'success': True}
        except Exception as e:
            try:
                self.connection.cursor().execute(f"ALTER DATABASE [{db_name}] SET MULTI_USER")
            except:
                pass
            return {'success': False, 'error': str(e)}

    def list_backups(self, backup_dir="backups"):
        backups = []
        if os.path.exists(backup_dir):
            for f in sorted(os.listdir(backup_dir), reverse=True):
                if f.endswith('.bak') or f.endswith('.sql'):
                    path = os.path.join(backup_dir, f)
                    backups.append({
                        'filename': f, 'path': os.path.abspath(path),
                        'size_mb': round(os.path.getsize(path) / (1024 * 1024), 2),
                        'date': datetime.fromtimestamp(os.path.getmtime(path)).strftime('%Y-%m-%d %H:%M:%S')
                    })
        return backups

    def export_data_sql(self, db_name, output_path=None):
        if output_path is None:
            os.makedirs("backups", exist_ok=True)
            output_path = f"backups/{db_name}_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE' ORDER BY TABLE_NAME")
            tables = [r[0] for r in cursor.fetchall()]
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"-- GT-POS Data Export | {datetime.now().strftime('%Y-%m-%d %H:%M')}\nUSE [{db_name}]\nGO\n\n")
                for table in tables:
                    cursor.execute(f"SELECT COLUMN_NAME, COLUMNPROPERTY(OBJECT_ID('{table}'), COLUMN_NAME, 'IsIdentity') as IsId FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='{table}' ORDER BY ORDINAL_POSITION")
                    cols_info = cursor.fetchall()
                    all_cols = [c[0] for c in cols_info]
                    has_id = any(c[1] for c in cols_info)
                    cursor.execute(f"SELECT {', '.join(f'[{c}]' for c in all_cols)} FROM [{table}]")
                    rows = cursor.fetchall()
                    if rows:
                        f.write(f"\n-- {table} ({len(rows)} rows)\n")
                        if has_id:
                            f.write(f"SET IDENTITY_INSERT [{table}] ON\nGO\n")
                        for row in rows:
                            vals = []
                            for v in row:
                                if v is None: vals.append("NULL")
                                elif isinstance(v, str): vals.append(f"N'{v.replace(chr(39), chr(39)+chr(39))}'")
                                elif isinstance(v, datetime): vals.append(f"'{v.strftime('%Y-%m-%d %H:%M:%S')}'")
                                elif isinstance(v, bool): vals.append("1" if v else "0")
                                else: vals.append(str(v))
                            f.write(f"INSERT INTO [{table}] ({', '.join(f'[{c}]' for c in all_cols)}) VALUES ({', '.join(vals)})\n")
                        if has_id:
                            f.write(f"SET IDENTITY_INSERT [{table}] OFF\nGO\n")
                        f.write("GO\n")
            cursor.close()
            return {'success': True, 'path': output_path, 'tables': len(tables)}
        except Exception as e:
            return {'success': False, 'error': str(e)}