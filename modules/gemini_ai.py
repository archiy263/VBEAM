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

        {text}
        """

        response = model.generate_content(prompt)
        return response.text.strip()

    except:
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