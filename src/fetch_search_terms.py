from google.ads.googleads.client import GoogleAdsClient
from src.data.db import init_db, connect
from src.data.client_accounts import get_active_client_accounts

FETCH_DAYS = 30

QUERY = f"""
SELECT
  segments.date,
  campaign.id,
  ad_group.id,
  search_term_view.search_term,
  metrics.impressions,
  metrics.clicks,
  metrics.cost_micros,
  metrics.conversions,
  metrics.conversions_value
FROM search_term_view
WHERE segments.date DURING LAST_{FETCH_DAYS}_DAYS
"""

def main(customer_id: str):
    init_db()

    client = GoogleAdsClient.load_from_storage("google-ads.yaml")
    ga_service = client.get_service("GoogleAdsService")

    rows = ga_service.search_stream(customer_id=customer_id, query=QUERY)

    with connect() as con:
        cur = con.cursor()

        for batch in rows:
            for row in batch.results:
                cur.execute(
                    """
                    INSERT INTO search_term_daily (
                        date,
                        customer_id,
                        campaign_id,
                        ad_group_id,
                        search_term,
                        impressions,
                        clicks,
                        cost_micros,
                        conversions,
                        conversions_value
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(date, customer_id, campaign_id, ad_group_id, search_term)
                    DO UPDATE SET
                        impressions        = excluded.impressions,
                        clicks             = excluded.clicks,
                        cost_micros        = excluded.cost_micros,
                        conversions        = excluded.conversions,
                        conversions_value  = excluded.conversions_value
                    """,
                    (
                        str(row.segments.date),
                        customer_id,
                        str(row.campaign.id),
                        str(row.ad_group.id),
                        row.search_term_view.search_term,
                        int(row.metrics.impressions),
                        int(row.metrics.clicks),
                        int(row.metrics.cost_micros),
                        float(row.metrics.conversions),
                        float(row.metrics.conversions_value),
                    ),
                )

        con.commit()


if __name__ == "__main__":
    accounts = get_active_client_accounts()
    if not accounts:
        print("No active client accounts found. Run: python -m src.sync_client_accounts")
        raise SystemExit(0)

    for customer_id in accounts:
        print(f"\nFetching search terms for customer {customer_id}")
        main(customer_id)
