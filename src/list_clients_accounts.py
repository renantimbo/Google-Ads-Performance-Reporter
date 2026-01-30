from google.ads.googleads.client import GoogleAdsClient

QUERY = """
SELECT
  customer_client.client_customer,
  customer_client.descriptive_name,
  customer_client.level,
  customer_client.manager,
  customer_client.status
FROM customer_client
WHERE customer_client.level <= 1
"""

def main(mcc_customer_id: str):
    client = GoogleAdsClient.load_from_storage("google-ads.yaml")
    ga_service = client.get_service("GoogleAdsService")

    resp = ga_service.search(customer_id=mcc_customer_id, query=QUERY)
    for row in resp:
        print(
            row.customer_client.client_customer,
            "|",
            row.customer_client.descriptive_name,
            "| manager=",
            row.customer_client.manager,
            "| status=",
            row.customer_client.status,
        )

if __name__ == "__main__":
    main("4361105186")  # seu MCC
