import os
import pickle
from flask import redirect, request, session
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from modules.database import get_connection

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
CLIENT_SECRETS_FILE = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def get_flow(state=None):
    redirect_uri = os.getenv("REDIRECT_URI", "http://localhost:5000/oauth2callback")
    return Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        state=state,
        redirect_uri=redirect_uri,
        autogenerate_code_verifier=False
    )

def login():
    flow = get_flow()
    auth_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent', # Force refresh token generation every time for stability
        code_challenge_method=None
    )
    session['oauth_state'] = state
    return redirect(auth_url)

def oauth2callback():
    state = session.get('oauth_state')
    flow = get_flow(state=state)
    flow.fetch_token(authorization_response=request.url)
    return flow.credentials

def save_user_credentials(email, creds):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET google_token = ? WHERE email = ?", (pickle.dumps(creds), email.lower()))
    conn.commit()
    conn.close()

def load_user_credentials(email):
    if not email: return None
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT google_token FROM users WHERE email = ?", (email.lower(),))
    row = c.fetchone()
    conn.close()
    if row and row[0]:
        return pickle.loads(row[0])
    return None

def get_gmail_service(email):
    creds = load_user_credentials(email)
    if not creds:
        return None
        
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                save_user_credentials(email, creds)
            except Exception as e:
                print(f"Failed to refresh token for {email}: {e}")
                return None
        else:
            return None
            
    return build("gmail", "v1", credentials=creds)