import sqlite3
from pathlib import Path
from src.config import settings

SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"

def connect() -> sqlite3.Connection:
    return sqlite3.connect(settings.db_path)

def init_db() -> None:
    """
    Initialize the SQLite database using schema.sql.
    Safe to call multiple times (uses IF NOT EXISTS).
    """
    settings.db_path.parent.mkdir(parents=True, exist_ok=True)

    with connect() as con:
        con.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        con.commit()

    print("Initialized the database.")
