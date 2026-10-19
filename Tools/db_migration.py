import pyodbc
from Tools.db_schema import TABLE_SCHEMAS, REQUIRED_COLUMNS, STORED_PROCEDURES, DEFAULT_DATA

class DatabaseMigrator:
    def __init__(self, conn_str):
        self.conn_str = conn_str

    def run_migration(self):
        results = []
        try:
            conn = pyodbc.connect(self.conn_str, autocommit=True)
            cursor = conn.cursor()

            for table_name, create_sql in TABLE_SCHEMAS.items():
                cursor.execute(f"SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME='{table_name}'")
                if cursor.fetchone()[0] == 0:
                    cursor.execute(create_sql)
                    results.append(f"CREATE TABLE [{table_name}]")
                else:
                    results.append(f"TABLE [{table_name}] exists")

            for table_name, columns in REQUIRED_COLUMNS.items():
                for col_name, col_def in columns.items():
                    cursor.execute(f"SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='{table_name}' AND COLUMN_NAME='{col_name}'")
                    if cursor.fetchone()[0] == 0:
                        try:
                            cursor.execute(f"ALTER TABLE [{table_name}] ADD [{col_name}] {col_def}")
                            results.append(f"ADD COLUMN [{table_name}].[{col_name}]")
                        except Exception as e:
                            results.append(f"SKIP COLUMN [{table_name}].[{col_name}]: {e}")

            for sp_name, sp_sql in STORED_PROCEDURES.items():
                try:
                    cursor.execute(sp_sql)
                    results.append(f"PROCEDURE {sp_name}")
                except Exception as e:
                    results.append(f"SKIP SP {sp_name}: {e}")

            for table_name, statements in DEFAULT_DATA.items():
                for stmt in statements:
                    if isinstance(stmt, str):
                        try:
                            cursor.execute(stmt)
                        except Exception as e:
                            results.append(f"SKIP DATA [{table_name}]: {e}")
                results.append(f"DATA [{table_name}]")

            conn.close()
        except Exception as e:
            results.append(f"MIGRATION ERROR: {e}")
        return results