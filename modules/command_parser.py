"""
Command parser - local keyword-based, no external APIs required.
Supports English and Hindi (हिंदी).
"""
import re


# Original command map - exact phrase/substring matching
_AI_CACHE = {}

COMMAND_MAP = {

    # START ASSISTANT
    "start assistant": [
        "start assistant", "start",
        "स्टार्ट असिस्टेंट", "असिस्टेंट शुरू करो", "शुरू करो"
    ],

    # STOP
    "stop": [
        "stop", "exit", "quit",
        "रुको", "बंद करो"
    ],

    # READ EMAIL
    "read email": [
        "read email", "read mail", "read my email",
        "ईमेल पढ़ो", "मेल पढ़ो", "latest email"
    ],

    # COUNT EMAIL
    "count email": [
        "count email", "how many emails", "email count",
        "कितने ईमेल"
    ],

    # SEND EMAIL  ← NOTE: must NOT contain "telegram"
    "send email": [
        "send email", "compose email", "write email",
        "ईमेल भेजो", "मेल भेजो"
    ],

    # REPLY EMAIL
    "reply email": [
        "reply email", "reply latest", "reply to email",
        "ईमेल का जवाब"
    ],

    # READ TELEGRAM  ← must come BEFORE send telegram
    "read telegram": [
        "read telegram", "check telegram",
        "टेलीग्राम पढ़ो"
    ],

    # SEND TELEGRAM
    "send telegram": [
        "send telegram", "telegram message send",
        "टेलीग्राम भेजो"
    ],

    # SUMMARIZE TELEGRAM
    "summarize telegram": [
        "summarize telegram", "telegram summary",
        "टेलीग्राम सार"
    ],

    # SUGGEST TELEGRAM REPLY
    "suggest telegram reply": [
        "suggest telegram reply", "telegram reply suggestion",
        "टेलीग्राम जवाब सुझाव", "टेलीग्राम जवाब दो"
    ],

    # ADD CONTACT
    "add contact": [
        "add contact", "add new contact",
        "नया संपर्क जोड़ो", "संपर्क जोड़ो"
    ],

    # DELETE CONTACT
    "delete contact": [
        "delete contact", "remove contact",
        "संपर्क हटाओ", "संपर्क डिलीट करो"
    ],

    # SHOW CONTACTS
    "all contact": [
        "all contact", "show contacts", "list contacts",
        "सभी संपर्क"
    ],
}

# Filler words to strip when extracting a contact name from a spoken phrase
_FILLER_PATTERNS = [
    r"(?:my\s+)?(?:contact|recipient)\s+(?:name\s+)?(?:is\s+)?",
    r"^(?:send\s+(?:email\s+)?(?:to\s+)?|email\s+to\s+)",
    r"\s+(?:ko|को|ne|ने|nu|ane|ને)\s*$",
    r"^(?:name\s+is\s+|is\s+|the\s+)",
]


def normalize_command(text: str) -> str:
    """
    Map spoken text to a canonical command key.
    Pure local matching — no external API.
    """
    t = text.lower().strip()
    if not t:
        return ""

    # 1. Exact local matching (Fast path)
    for key, phrases in COMMAND_MAP.items():
        for phrase in phrases:
            if phrase in t:
                return key
    return t


def extract_entity(raw: str) -> str:
    """
    Pull the meaningful contact name from messy spoken input.
    'contact name is yadav'  →  'yadav'
    'send email to mahadev'  →  'mahadev'
    'mahadev ko bhejo'       →  'mahadev'
    """
    raw = raw.lower().strip()
    for pat in _FILLER_PATTERNS:
        raw = re.sub(pat, "", raw, flags=re.IGNORECASE).strip()
    # Take last remaining word (the actual name)
    words = raw.split()
    if words:
        # Prefer the LAST meaningful word (avoids "email" leftover from "send email to X")
        stopwords = {"email", "mail", "send", "to", "the", "my", "is", "name", "contact"}
        for w in reversed(words):
            if w not in stopwords:
                return w
    return raw

def extract_telegram_raw(raw: str) -> str:
    """
    Extract @username or phone number from spoken text like 'my username is @dev' and 'send to +919000'
    """
    if "@" in raw:
        idx = raw.find("@")
        part = raw[idx:].replace(" ", "")
        return part
        
    words = raw.split()
    for w in words:
        if w.startswith("+"):
            return w
    
    if "username is" in raw.lower():
        idx = raw.lower().find("username is") + 11
        part = raw[idx:].strip().replace(" ", "")
        if part:
            if not part.startswith("@") and not part.startswith("+"):
                return "@" + part
            return part
            
    return None