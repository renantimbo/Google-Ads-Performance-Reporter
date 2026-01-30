from google.ads.googleads.client import GoogleAdsClient

def main():
    client = GoogleAdsClient.load_from_storage("google-ads.yaml")
    customer_service = client.get_service("CustomerService")
    resp = customer_service.list_accessible_customers()
    print("Accessible customers:")
    for r in resp.resource_names:
        print(" -", r)  # formato: customers/1234567890

if __name__ == "__main__":
    main()
