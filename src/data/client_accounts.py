import sqlite3
from pathlib import Path

DB_PATH = Path("data.sqlite")

def get_active_client_accounts():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""
        SELECT customer_id
        FROM client_accounts
        WHERE status = 'ENABLED'
        ORDER BY customer_id
    """)
    ids = [r[0] for r in cur.fetchall()]
    con.close()
    return ids
