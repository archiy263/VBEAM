import base64
import re
from bs4 import BeautifulSoup


def strip_html(html_text: str) -> str:
    """Convert HTML email body to clean readable plain text."""
    soup = BeautifulSoup(html_text, "html.parser")
    # Remove script/style noise
    for tag in soup(["script", "style", "meta", "head", "noscript"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    # Collapse blank lines
    lines = [ln.strip() for ln in text.splitlines()]
    clean_lines = []
    prev_blank = False
    for ln in lines:
        if ln == "":
            if not prev_blank:
                clean_lines.append("")
            prev_blank = True
        else:
            clean_lines.append(ln)
            prev_blank = False
    return "\n".join(clean_lines).strip()


def extract_body(payload) -> str:
    """Recursively extract the best plain-text body from a Gmail message payload."""
    # Direct body data (simple messages)
    if 'body' in payload and payload['body'].get('data'):
        data = payload['body']['data']
        raw = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        mime = payload.get('mimeType', '')
        if 'html' in mime:
            return strip_html(raw)
        return raw.strip()

    # Multi-part: prefer text/plain, fallback to text/html
    if 'parts' in payload:
        plain_text = None
        html_text = None
        for part in payload['parts']:
            mime = part.get('mimeType', '')
            body_data = part.get('body', {}).get('data')
            if body_data:
                decoded = base64.urlsafe_b64decode(body_data).decode('utf-8', errors='ignore')
                if mime == 'text/plain':
                    plain_text = decoded.strip()
                elif mime == 'text/html':
                    html_text = strip_html(decoded)
            # Recurse into nested parts
            elif 'parts' in part:
                nested = extract_body(part)
                if nested:
                    return nested
        if plain_text:
            return plain_text
        if html_text:
            return html_text
    return ""


def clean_sender(sender: str) -> str:
    """Return just the display name or email from 'Name <email@example.com>'."""
    m = re.match(r'^"?([^"<]+)"?\s*<', sender)
    if m:
        return m.group(1).strip()
    return sender.strip()


def format_email_output(sender: str, subject: str, body: str, preview_chars: int = 600) -> str:
    """
    Format email as clean, readable plain text — no HTML tags.
    Visually structured using Unicode separators.
    """
    body_preview = body[:preview_chars].strip()
    if len(body) > preview_chars:
        body_preview += "..."

    return (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"  📧  Latest Email\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"  From    : {clean_sender(sender)}\n"
        f"  Subject : {subject or '(No Subject)'}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{body_preview}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )


def read_latest_email(service) -> str:
    if service is None:
        return "Please login with Google first."

    results = service.users().messages().list(userId="me", maxResults=1).execute()
    messages = results.get("messages", [])
    if not messages:
        return "Your inbox is empty."

    msg = service.users().messages().get(userId="me", id=messages[0]["id"], format="full").execute()
    headers = msg["payload"]["headers"]

    sender = subject = ""
    for h in headers:
        if h["name"] == "From":
            sender = h["value"]
        if h["name"] == "Subject":
            subject = h["value"]

    body = extract_body(msg["payload"])
    return format_email_output(sender, subject, body)


def get_email_count(service) -> int:
    if service is None:
        return 0
    results = service.users().messages().list(userId='me').execute()
    return len(results.get('messages', []))
