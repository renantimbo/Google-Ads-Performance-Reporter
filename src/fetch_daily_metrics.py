from google.ads.googleads.client import GoogleAdsClient
from data.db import init_db, connect

QUERY = """
SELECT
  segments.date,
  campaign.id,
  campaign.name,
  metrics.impressions,
  metrics.clicks,
  metrics.cost_micros,
  metrics.conversions,
  metrics.conversions_value
FROM campaign
WHERE segments.date BETWEEN '2025-10-01' AND '2026-01-29'
"""

def main(customer_id: str):
    init_db()
    client = GoogleAdsClient.load_from_storage("google-ads.yaml")
    ga_service = client.get_service("GoogleAdsService")

    rows = ga_service.search_stream(customer_id=customer_id, query=QUERY)

    with connect() as con:
        for batch in rows:
            for row in batch.results:
                d = row.segments.date
                con.execute(
                    """
                    INSERT OR REPLACE INTO campaign_daily
                    (date, customer_id, campaign_id, campaign_name, impressions, clicks,
                     cost_micros, conversions, conversions_value)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(d),
                        customer_id,
                        str(row.campaign.id),
                        row.campaign.name,
                        int(row.metrics.impressions),
                        int(row.metrics.clicks),
                        int(row.metrics.cost_micros),
                        float(row.metrics.conversions),
                        float(row.metrics.conversions_value),
                    ),
                )

if __name__ == "__main__":
    # coloque seu customer id aqui (sem "customers/")
    main("3778262392")
