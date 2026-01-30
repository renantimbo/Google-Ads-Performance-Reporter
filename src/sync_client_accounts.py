from google.ads.googleads.client import GoogleAdsClient
import sqlite3
from pathlib import Path
from datetime import date

DB_PATH = Path("data.sqlite")

QUERY = """
SELECT
  customer_client.id,
  customer_client.descriptive_name,
  customer_client.currency_code,
  customer_client.time_zone,
  customer_client.status
FROM customer_client
WHERE customer_client.manager = FALSE
"""


def ensure_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS client_accounts (
            customer_id TEXT PRIMARY KEY,
            descriptive_name TEXT,
            currency_code TEXT,
            time_zone TEXT,
            status TEXT,
            first_seen DATE,
            last_seen DATE
        )
    """)
    conn.commit()


def get_login_customer_id(client: GoogleAdsClient) -> str:
    """
    Extracts login_customer_id (MCC) from google-ads.yaml via the client config.
    """
    login_id = client.login_customer_id
    if not login_id:
        raise RuntimeError(
            "login_customer_id not found. "
            "Ensure google-ads.yaml contains login_customer_id for MCC access."
        )
    return str(login_id)


def sync_client_accounts():
    client = GoogleAdsClient.load_from_storage("google-ads.yaml")
    ga_service = client.get_service("GoogleAdsService")

    mcc_customer_id = get_login_customer_id(client)

    conn = sqlite3.connect(DB_PATH)
    ensure_table(conn)
    cur = conn.cursor()

    today = date.today().isoformat()
    found_ids = set()

    response = ga_service.search_stream(
        customer_id=mcc_customer_id,
        query=QUERY
    )

    for batch in response:
        for row in batch.results:
            cid = str(row.customer_client.id)
            found_ids.add(cid)

            cur.execute("""
                INSERT INTO client_accounts (
                    customer_id,
                    descriptive_name,
                    currency_code,
                    time_zone,
                    status,
                    first_seen,
                    last_seen
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(customer_id) DO UPDATE SET
                    descriptive_name = excluded.descriptive_name,
                    currency_code = excluded.currency_code,
                    time_zone = excluded.time_zone,
                    status = excluded.status,
                    last_seen = excluded.last_seen
            """, (
                cid,
                row.customer_client.descriptive_name,
                row.customer_client.currency_code,
                row.customer_client.time_zone,
                row.customer_client.status.name,
                today,
                today
            ))

    conn.commit()
    conn.close()

    print(f"Synced {len(found_ids)} client accounts from MCC {mcc_customer_id}.")


if __name__ == "__main__":
    sync_client_accounts()
