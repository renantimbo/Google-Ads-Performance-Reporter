import sqlite3
from pathlib import Path

DB_PATH = Path("data.sqlite")

def connect():
    return sqlite3.connect(DB_PATH)

def init_db():
    with connect() as con:
        con.executescript(Path("src/schema.sql").read_text(encoding="utf-8"))
    print("Initialized the database.")