"""
DEBUG ONLY.
Lists all Google Ads accounts accessible by the OAuth credentials.
Not used by the data pipeline.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path("data.sqlite")


def get_active_client_accounts():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT customer_id
        FROM client_accounts
        WHERE status = 'ENABLED'
    """)

    rows = [row[0] for row in cur.fetchall()]
    conn.close()
    return rows
