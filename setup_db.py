import sys
from Server.database import DatabaseManager
from Server.config import get_connection_string
from Tools.db_migration import DatabaseMigrator
from version import APP_VERSION

VERSION = APP_VERSION

def main():
    print(f"=== GT-POS Setup v{VERSION} ===")
    db = DatabaseManager()
    print("Ensuring database exists...")
    db.ensure_database()
    print("Running migrations...")
    migrator = DatabaseMigrator(get_connection_string())
    results = migrator.run_migration()
    for r in results:
        print(f"  {r}")
    print("Setup complete!")

if __name__ == "__main__":
    main()