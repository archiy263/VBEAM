import google.generativeai as genai
import os

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-2.5-flash")


def summarize_text(text):
    try:
        prompt = f"""
        Summarize the following message in a short and clear way:

        {text}
        """

        response = model.generate_content(prompt)
        return response.text.strip()

    except Exception as e:
        print("Summarization Error:", e)
        return "Could not generate summary."


def suggest_reply(text):
    try:
        prompt = f"""
        Generate a short professional reply suggestion for this message:

        {text}

        Reply:
        """

        response = model.generate_content(prompt)
        return response.text.strip()

    except Exception as e:
        print("Reply Suggestion Error:", e)
        return "Noted. I will respond soon."

def detect_language(text):
    try:
        prompt = f"""
        Detect the language of this text.
        Reply only with language code like:
        en, hi, gu, etc.

        Text:
        {text}
        """

        response = model.generate_content(prompt)
        return response.text.strip().lower()

    except:
        return "en"
    
def translate_text(text, target_lang):
    try:
        prompt = f"""
        Translate this text into {target_lang} language:
        '{text}'
        Provide ONLY the translated text, no quotes or extra words.
        CRITICAL RULE: DO NOT translate any email addresses or usernames (like example@domain.com or @username), leave them exactly as they are in English.
        """

        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Translation error: {e}")
        return text

def normalize_phonetic(text: str) -> str:
    """Uses Gemini to convert Hindi phonetic STT (like एआरसीएचएटदरेटgmail.com) into proper English email/username."""
    try:
        prompt = f"""
        You are fixing speech-to-text formatting.
        Convert the following spoken text (which may contain Hindi phonetics of English spelling) into a valid English email address, telegram username, or contact name.
        Rules:
        - "एट द रेट" -> "@"
        - "डॉट कॉम" -> ".com"
        - Convert spelled-out letters in Hindi (e.g. "ए", "बी", "सी") into English letters (A, B, C).
        - If it's just a name like "देव उपाध्याय ऑफिशियल", convert it to English spelling like "Dev Upadhyay Official".
        - If it has an "@" symbol, keep it exactly (don't add extra spaces).
        - Return ONLY the final converted string, without quotes or extra explanation.
        
        Input: '{text}'
        """
        response = model.generate_content(prompt)
        res = response.text.strip().lower()
        return res
    except Exception as e:
        print(f"Phonetic normalization error: {e}")
        return text
    
def analyze_command(text):
    try:

        prompt = f"""
You are an AI assistant for a voice command system.

Detect the language and translate the command to English.

Return JSON ONLY like this:

{{
"language":"gu",
"translated_command":"read email"
}}

User command:
{text}
"""

        response = model.generate_content(prompt)

        import json, re

        clean = re.search(r'\{.*\}', response.text, re.S)

        if clean:
            result = json.loads(clean.group())
            return result["language"], result["translated_command"]

        return "en", text.lower()

    except Exception as e:
        print("Gemini command analysis error:", e)
        return "en", text.lower()


