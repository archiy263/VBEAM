import os
from flask import redirect, request, session
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

import os
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
CLIENT_SECRETS_FILE = os.getenv(
    "GOOGLE_CREDENTIALS_PATH",
    "credentials.json"
)
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def get_flow(state=None):
    redirect_uri = os.getenv(
        "REDIRECT_URI",
        "http://localhost:5000/oauth2callback"
    )

    return Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        state=state,
        redirect_uri=redirect_uri,
        autogenerate_code_verifier=False
    )
# redirect to Google login

def login():
    flow = get_flow()

    auth_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        code_challenge_method=None
    )

    session['oauth_state'] = state

    return redirect(auth_url)

def oauth2callback():
    state = session.get('oauth_state')

    flow = get_flow(state=state)

    flow.fetch_token(authorization_response=request.url)

    creds = flow.credentials

    return build("gmail", "v1", credentials=creds)
