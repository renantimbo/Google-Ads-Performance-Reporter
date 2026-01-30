from google.ads.googleads.client import GoogleAdsClient
from data.db import init_db, connect

QUERY = """
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
                con.execute(
                    """
                    INSERT OR REPLACE INTO search_term_daily
                    (date, customer_id, campaign_id, ad_group_id, search_term,
                     impressions, clicks, cost_micros, conversions, conversions_value)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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

if __name__ == "__main__":
    main("6269083523")
