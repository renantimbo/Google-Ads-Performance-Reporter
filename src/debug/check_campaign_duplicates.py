import sqlite3
from pathlib import Path
import pandas as pd

DB_PATH = Path("data.sqlite")

QUERY = """
SELECT
  date,
  customer_id,
  campaign_id,
  COUNT(*) AS n
FROM campaign_daily
GROUP BY date, customer_id, campaign_id
HAVING n > 1
ORDER BY n DESC;
"""

def main():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH.resolve()}")

    con = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(QUERY, con)
    con.close()

    if df.empty:
        print("No duplicate rows found in campaign_daily.")
    else:
        print("Duplicate rows found in campaign_daily:")
        print(df)
        print(f"\nTotal duplicated groups: {len(df)}")

if __name__ == "__main__":
    main()
