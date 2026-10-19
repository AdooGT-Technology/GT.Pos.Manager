import os

DB_SERVER = r"localhost\SQLEXPRESS"
DB_NAME = "GT-POS-Manager"
DB_DRIVER = "{ODBC Driver 17 for SQL Server}"
DB_TRUSTED = True

def get_connection_string():
    return (
        f"DRIVER={DB_DRIVER};"
        f"SERVER={DB_SERVER};"
        f"DATABASE=GT-POS-Manager;"
        f"Trusted_Connection=yes;"
    )

def get_master_connection_string():
    return (
        f"DRIVER={DB_DRIVER};"
        f"SERVER={DB_SERVER};"
        f"DATABASE=master;"
        f"Trusted_Connection=yes;"
    )

SERVER_HOST = "0.0.0.0"
SERVER_PORT = 54321

ICONS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Icons")
GAMES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "GameIcons")

os.makedirs(ICONS_DIR, exist_ok=True)
os.makedirs(GAMES_DIR, exist_ok=True)

class Config:
    DB_SERVER = DB_SERVER
    DB_NAME = DB_NAME
    DB_DRIVER = DB_DRIVER
    DB_TRUSTED = DB_TRUSTED
    SERVER_HOST = SERVER_HOST
    SERVER_PORT = SERVER_PORT
    ICONS_DIR = ICONS_DIR
    GAMES_DIR = GAMES_DIR
    get_connection_string = staticmethod(get_connection_string)
    get_master_connection_string = staticmethod(get_master_connection_string)