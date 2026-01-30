import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = Path("data.sqlite")
OUTPUT_PATH = Path("reports/baseline_roas_180_days.csv")

con = sqlite3.connect(DB_PATH)

query = """
SELECT
  campaign_name,
  ROUND(SUM(cost_micros) / 1e6, 2) AS cost,
  ROUND(SUM(conversions), 2) AS conversions,
  ROUND(SUM(conversions_value), 2) AS conversions_value,
  CASE
    WHEN SUM(cost_micros) > 0
    THEN ROUND(
      SUM(conversions_value) / (SUM(cost_micros) / 1e6),
      2
    )
    ELSE NULL
  END AS roas
FROM campaign_daily
WHERE date >= date('now','-180 day')
GROUP BY campaign_name
ORDER BY roas DESC;
"""

df = pd.read_sql_query(query, con)

print("\nROAS por campanha (últimos 180 dias):")
print(df)

df.to_csv(OUTPUT_PATH, index=False)

print(f"\nBaseline salvo em: {OUTPUT_PATH.resolve()}")

con.close()
