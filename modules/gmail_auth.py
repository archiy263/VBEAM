from flask import redirect, request, session
import os
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

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
        redirect_uri=redirect_uri
    )


# STEP 1
def login():
    flow = get_flow()

    auth_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )

    # store state in session
    session['oauth_state'] = state

    return redirect(auth_url)


# STEP 2
def oauth2callback():
    state = session.get('oauth_state')

    flow = get_flow(state=state)

    flow.fetch_token(authorization_response=request.url)

    creds = flow.credentials

    service = build("gmail", "v1", credentials=creds)

    return service
