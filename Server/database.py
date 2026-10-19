import pyodbc
from Server.config import get_connection_string, get_master_connection_string, DB_NAME

class DatabaseManager:
    def __init__(self):
        self.conn_str = get_connection_string()

    def get_connection(self):
        return pyodbc.connect(self.conn_str, autocommit=True)

    def execute_query(self, query, params=None, fetch=True):
        conn = None
        try:
            conn = pyodbc.connect(self.conn_str, autocommit=True)
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            if fetch:
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                rows = cursor.fetchall()
                return [dict(zip(columns, row)) for row in rows]
            return True
        except Exception as e:
            print(f"DB Error: {e}")
            return [] if fetch else False
        finally:
            if conn:
                conn.close()

    def ensure_database(self):
        try:
            conn = pyodbc.connect(get_master_connection_string(), autocommit=True)
            cursor = conn.cursor()
            cursor.execute(f"IF NOT EXISTS (SELECT * FROM sys.databases WHERE name='{DB_NAME}') CREATE DATABASE [{DB_NAME}]")
            conn.close()
            return True
        except Exception as e:
            print(f"DB Create Error: {e}")
            return False

    def test_connection(self):
        try:
            conn = pyodbc.connect(self.conn_str, autocommit=True)
            conn.close()
            return True
        except:
            return False

Database = DatabaseManager