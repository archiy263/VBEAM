import os
from flask import redirect, request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

import os
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
CLIENT_SECRETS_FILE = os.getenv(
    "GOOGLE_CREDENTIALS_PATH",
    "credentials.json"
)
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def get_flow():
    # auto switch between local and production
    redirect_uri = os.getenv(
        "REDIRECT_URI",
        "http://localhost:5000/oauth2callback"
    )

    return Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=redirect_uri
    )

# redirect to Google login
def login():
    flow = get_flow()

    auth_url, _ = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )

    return redirect(auth_url)

# STEP 2 → Google callback → create Gmail service
def oauth2callback():
    flow = get_flow()
    flow.fetch_token(authorization_response=request.url)

    creds = flow.credentials

    service = build("gmail", "v1", credentials=creds)

    return service
