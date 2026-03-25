import re

def extract_telegram_raw(raw: str) -> str:
    words = raw.split()
    for i, w in enumerate(words):
        if w.startswith("@"):
            if w == "@" and i + 1 < len(words):
                return "@" + words[i+1]
            return w
        if w.startswith("+"):
            return w
    
    if "username is" in raw.lower():
        idx = raw.lower().find("username is") + 11
        parts = raw[idx:].strip().split()
        if parts:
            val = parts[0]
            if val == "@" and len(parts) > 1:
                return "@" + parts[1]
            if not val.startswith("@") and not val.startswith("+"):
                return "@" + val
            return val
    return None

def speak_response(text: str, language: str) -> str:
    _TRANSLATIONS = {
        "hi": {
            "Contact not found": "संपर्क नहीं मिला",
            "What should I name this contact?": "मुझे इस संपर्क का क्या नाम रखना चाहिए?",
        }
    }
    if language == "en" or not language:
        return text
    lang = language.split("-")[0]
    local = _TRANSLATIONS.get(lang, {})
    
    if text in local:
        return local[text]
        
    if lang == "hi":
        if text.startswith("Do you want to save ") and " to your contacts? Say yes or no." in text:
            uname = text.replace("Do you want to save ", "").replace(" to your contacts? Say yes or no.", "")
            return f"क्या आप {uname} को अपने संपर्कों में सहेजना चाहते हैं? हाँ या ना कहें।"

        if text.startswith("Saved contact ") and ". What message should I send?" in text:
            cname = text.replace("Saved contact ", "").replace(". What message should I send?", "")
            return f"{cname} संपर्क सहेजा गया। क्या संदेश भेजूं?"

        if text.startswith("Contact '") and text.endswith("' not found. Please say their Telegram @username directly."):
            cname = text.split("'")[1]
            return f"संपर्क '{cname}' नहीं मिला। कृपया सीधे उनका टेलीग्राम @username बताएं।"

        if text.startswith("Sending to ") and ": '" in text and "'. Say yes to confirm." in text:
            parts = text.split(": '")
            uname = parts[0].replace("Sending to ", "")
            msg = parts[1].replace("'. Say yes to confirm.", "")
            return f"{uname} को भेज रहे हैं: '{msg}'। पुष्टि के लिए हाँ कहें।"

        if text.startswith("Sending email to "):
            match = re.search(r"Sending email to (.+?)\. Subject: (.+?)\. Message: (.+?)\. Say yes to confirm or no to cancel\.", text)
            if match:
                to_part, subj_part, msg_part = match.groups()
                return f"{to_part} को ईमेल भेज रहे हैं। विषय: {subj_part}। संदेश: {msg_part}। पुष्टि के लिए हाँ, रद्द के लिए नहीं।"
    return text

print("Testing Telegram Extraction:")
print(f"my username is @ dev -> {extract_telegram_raw('my username is @ dev')}  (Expected: @dev)")
print(f"send to +91900 -> {extract_telegram_raw('send to +91900')}  (Expected: +91900)")
print(f"my username is dev -> {extract_telegram_raw('my username is dev')}  (Expected: @dev)")
print(f"@archi -> {extract_telegram_raw('@archi')}  (Expected: @archi)")

print("\nTesting Speak Response Hindi Translations:")
print("Save prompt:", speak_response("Do you want to save @dev to your contacts? Say yes or no.", "hi"))
print("Saved prompt:", speak_response("Saved contact Rahi. What message should I send?", "hi"))
print("Not found prompt:", speak_response("Contact 'XYZ' not found. Please say their Telegram @username directly.", "hi"))
print("Sending prompt:", speak_response("Sending to @dev: 'hello'. Say yes to confirm.", "hi"))
print("Sending email prompt:", speak_response("Sending email to test@gmail.com. Subject: urgent. Message: call me. Say yes to confirm or no to cancel.", "hi"))
