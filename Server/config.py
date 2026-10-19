import os

DB_SERVER = os.environ.get("GT_DB_SERVER", r"localhost\SQLEXPRESS")
DB_NAME = os.environ.get("GT_DB_NAME", "GT-POS-Manager")
DB_DRIVER = os.environ.get("GT_DB_DRIVER", "{ODBC Driver 17 for SQL Server}")
DB_TRUSTED = os.environ.get("GT_DB_TRUSTED", "1") == "1"
DB_TIMEOUT = int(os.environ.get("GT_DB_TIMEOUT", "3"))


def _auth():
    return "Trusted_Connection=yes;" if DB_TRUSTED else ""


def get_connection_string():
    return (
        f"DRIVER={DB_DRIVER};"
        f"SERVER={DB_SERVER};"
        f"DATABASE={DB_NAME};"
        f"{_auth()}"
        f"Connection Timeout={DB_TIMEOUT};"
    )


def get_master_connection_string():
    return (
        f"DRIVER={DB_DRIVER};"
        f"SERVER={DB_SERVER};"
        f"DATABASE=master;"
        f"{_auth()}"
        f"Connection Timeout={DB_TIMEOUT};"
    )


SERVER_HOST = os.environ.get("GT_SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.environ.get("GT_SERVER_PORT", "54321"))
BUFFER_SIZE = 8192

ICONS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Icons")
GAMES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "GameIcons")

os.makedirs(ICONS_DIR, exist_ok=True)
os.makedirs(GAMES_DIR, exist_ok=True)


class Config:
    DB_SERVER = DB_SERVER
    DB_NAME = DB_NAME
    DB_DRIVER = DB_DRIVER
    DB_TRUSTED = DB_TRUSTED
    DB_TIMEOUT = DB_TIMEOUT
    SERVER_HOST = SERVER_HOST
    SERVER_PORT = SERVER_PORT
    BUFFER_SIZE = BUFFER_SIZE
    ICONS_DIR = ICONS_DIR
    GAMES_DIR = GAMES_DIR
    get_connection_string = staticmethod(get_connection_string)
    get_master_connection_string = staticmethod(get_master_connection_string)
