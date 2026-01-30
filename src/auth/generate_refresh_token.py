from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/adwords"]

def main():
    # Use o JSON baixado do Google Cloud (OAuth Client: Desktop app)
    flow = InstalledAppFlow.from_client_secrets_file(
        "client_secret.json",
        scopes=SCOPES,
    )

    # Abre o navegador e sobe um servidor local temporário
    creds = flow.run_local_server(port=0, prompt="consent")

    print("\n==== TOKENS GERADOS ====")
    print("refresh_token:")
    print(creds.refresh_token)

if __name__ == "__main__":
    main()
