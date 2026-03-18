import pickle
import os
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
def login():

    creds = None

    if os.path.exists("token.pickle"):

        with open("token.pickle", "rb") as token:

            creds = pickle.load(token)

    else:

        from google_auth_oauthlib.flow import Flow
        from flask import redirect, request

    CLIENT_SECRETS_FILE = "/etc/secrets/credentials.json"
    SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

    def get_flow():
        return Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri="https://vbeam-1.onrender.com/oauth2callback"
    )

    def login():
        flow = get_flow()

        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )

        return redirect(auth_url)
    def oauth2callback():
        flow = get_flow()
        flow.fetch_token(authorization_response=request.url)
        creds = flow.credentials
        # You can store creds here if needed
        return "Google Login Success ✅"    



        # flow = InstalledAppFlow.from_client_secrets_file(
        #     "credentials.json", SCOPES
        # )

        # creds = flow.run_local_server(
        #     port=0,
        #     open_browser=True
        # )

        with open("token.pickle", "wb") as token:

            pickle.dump(creds, token)

    return build("gmail", "v1", credentials=creds)
