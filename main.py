
from dotenv import load_dotenv
import os
load_dotenv()

import time as time_module
from click import command
from flask import Flask, redirect, request, jsonify, render_template, session
from flask_cors import CORS
from modules.gmail_auth import login
from modules.telegram_service import send_telegram_message, read_latest_telegram
from modules.gemini_ai import summarize_text, suggest_reply, translate_text
from modules.command_parser import normalize_command 
from modules.database import get_connection

app = Flask(__name__)
# Enable CORS for React Dev Server
CORS(app, supports_credentials=True)


# ── Local translations (no Gemini API needed) ──────────────────────────────
_TRANSLATIONS = {
    "hi": {
        "Which service do you want to use? Email or Telegram?": "आप कौन सी सेवा उपयोग करना चाहते हैं? ईमेल या टेलीग्राम?",
        "Tell recipient contact name or email address": "प्राप्तकर्ता का नाम या ईमेल बताएं",
        "Got it. Now tell me the subject.": "ठीक है। अब विषय बताएं।",
        "Tell subject": "विषय बताएं",
        "Tell message": "संदेश बताएं",
        "You are sending email to": "आप ईमेल भेज रहे हैं", 
        "Say yes to confirm or no to cancel.": "पुष्टि के लिए हाँ कहें या रद्द के लिए नहीं।",
        "Please say your 4-digit PIN": "अपना 4-अंकीय पिन बताएं",
        "Email sent successfully": "ईमेल सफलतापूर्वक भेजा गया",
        "Email cancelled": "ईमेल रद्द किया गया",
        "Invalid PIN. Message not sent.": "गलत पिन। संदेश नहीं भेजा गया।",
        "Contact not found in your directory.": "संपर्क नहीं मिला।",
        "Please login with Google first to read emails.": "कृपया पहले Google से लॉगिन करें।",
        "Assistant stopped": "असिस्टेंट बंद किया गया",
        "Reply cancelled": "जवाब रद्द किया गया",
        "Tell your reply message": "अपना जवाब बताएं",
        "Say yes to confirm or no to cancel": "पुष्टि के लिए हाँ, रद्द के लिए नहीं",
        "Reply sent successfully": "जवाब सफलतापूर्वक भेजा गया",
        "Which contact should I send Telegram to?": "किस संपर्क को टेलीग्राम भेजूं?",
        "What message should I send?": "क्या संदेश भेजूं?",
        "Telegram message sent.": "टेलीग्राम संदेश भेजा गया।",
        "Telegram message cancelled.": "टेलीग्राम संदेश रद्द किया गया।",
        "Contact not found": "संपर्क नहीं मिला",
        "No contacts saved": "कोई संपर्क सहेजा नहीं गया",
    }
}

def speak_response(text: str, language: str) -> str:
    """Translate a response using local dict first, dynamic patterns next."""
    if language == "en" or not language:
        return text
    lang = language.split("-")[0]  # 'hi-IN' → 'hi'
    local = _TRANSLATIONS.get(lang, {})
    
    if text in local:
        return local[text]
        
    if lang == "hi":
        if text.startswith("You have ") and "emails" in text:
            count = text.replace("You have ", "").replace(" emails", "").strip()
            return f"आपके पास {count} ईमेल हैं।"
            
        if text.startswith("What is your reply to "):
            name = text.replace("What is your reply to ", "").replace("?", "").strip()
            return f"{name} को आपका क्या जवाब है?"
            
        if text.startswith("Contact ") and "added successfully" in text:
            name = text.replace("Contact ", "").replace(" added successfully", "").strip()
            return f"संपर्क {name} सफलतापूर्वक जोड़ा गया"
            
        if text.startswith("Contact ") and "deleted" in text:
            name = text.replace("Contact ", "").replace(" deleted", "").strip()
            return f"संपर्क {name} हटा दिया गया"
            
        if text.startswith("Your contacts are: "):
            return text.replace("Your contacts are: ", "आपके संपर्क हैं: ")
            
        if text.startswith("Latest Telegram message summary: "):
            return text.replace("Latest Telegram message summary: ", "टेलीग्राम संदेश का सार: ")

    return text


app.secret_key = "voice_email_secret"


service = None
email_state = {}
reply_state = {}
telegram_state = {}
total_emails_sent = 0  # Fix: was missing, caused NameError crash in command_handler

user_pin = "1234"

def get_activity_logs():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT user_sub, message FROM activity_logs ORDER BY timestamp DESC LIMIT 20")
    rows = c.fetchall()
    conn.close()
    return [{"user": r[0], "message": r[1]} for r in rows]

def add_log(activity):
    user_email = session.get('user_email', 'System')
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO activity_logs (user_sub, message) VALUES (?, ?)", (user_email, activity))
    conn.commit()
    conn.close()

def extract_pin(text):
    import re
    word_to_num = {
        "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
        "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9"
    }
    for word, num in word_to_num.items():
        text = text.replace(word, num)
    digits = re.sub(r'\D', '', text)
    return digits

@app.route("/api/auth/status", methods=["GET"])
def auth_status():
    global service
    if service:
        # User is logged in
        try:
            profile = service.users().getProfile(userId="me").execute()
            return jsonify({"authenticated": True, "email": profile.get("emailAddress")})
        except:
            service = None
            return jsonify({"authenticated": False})
    return jsonify({"authenticated": False})


@app.route("/login/oauth")
def oauth_login():
    global service
    service = login()
    if not service:
        return redirect("/")
        
    try:
        profile = service.users().getProfile(userId="me").execute()
        email = profile.get("emailAddress")
        name = email.split("@")[0]
        
        from modules.auth import get_or_create_google_user
        user = get_or_create_google_user(email, name)
        
        if user and "error" in user:
            service = None
            return render_template("login.html", error="Your account has been blocked by the admin.")
    except Exception as e:
        service = None
        return redirect("/")

    add_log("User logged in with Google Auth successfully.")
    session['logged_in'] = True
    session['auth_type'] = 'google'
    session['user_email'] = email
    return redirect("/dashboard")

@app.route("/api/auth/manual/signup", methods=["POST"])
def manual_signup():
    from modules.auth import create_user
    data = request.json
    success = create_user(data.get("email"), data.get("name"), data.get("password"))
    if success:
        return jsonify({"success": True})
    return jsonify({"error": "User already exists or missing data"}), 400

@app.route("/api/auth/manual/login", methods=["POST"])
def manual_login():
    from modules.auth import verify_user
    data = request.json
    user = verify_user(data.get("email"), data.get("password"))
    if user:
        if "error" in user:
            return jsonify({"error": user["error"]}), 403
            
        session['logged_in'] = True
        session['auth_type'] = 'manual'
        session['user_email'] = user["email"]
        session['user_name'] = user["name"]
        add_log(f"User {user['name']} logged in manually.")
        return jsonify({"success": True})
    return jsonify({"error": "Invalid credentials"}), 401

# --- TELEGRAM WEB AUTH ROUTES ---
telegram_login_state = {}

@app.route("/api/telegram/status")
def telegram_status():
    from modules.telegram_service import is_telegram_authorized
    return jsonify({"connected": is_telegram_authorized()})

@app.route("/api/telegram/send_code", methods=["POST"])
def telegram_send_code_route():
    data = request.json
    phone = data.get("phone")
    from modules.telegram_service import telegram_send_code
    res = telegram_send_code(phone)
    if res.get("success"):
        telegram_login_state["phone"] = phone
        telegram_login_state["phone_code_hash"] = res.get("phone_code_hash")
        return jsonify({"success": True})
    return jsonify({"success": False, "error": res.get("error")})

@app.route("/api/telegram/verify_code", methods=["POST"])
def telegram_verify_code_route():
    data = request.json
    code = data.get("code")
    phone = telegram_login_state.get("phone")
    phone_code_hash = telegram_login_state.get("phone_code_hash")
    
    if not phone or not phone_code_hash:
        return jsonify({"success": False, "error": "Session expired, please request code again."})
        
    from modules.telegram_service import telegram_verify_code
    res = telegram_verify_code(phone, code, phone_code_hash)
    if res.get("success"):
        telegram_login_state.clear()
        return jsonify({"success": True})
    elif res.get("needs_password"):
        return jsonify({"success": False, "needs_password": True})
    return jsonify({"success": False, "error": res.get("error")})

@app.route("/api/telegram/verify_password", methods=["POST"])
def telegram_verify_password_route():
    data = request.json
    password = data.get("password")
    
    from modules.telegram_service import telegram_verify_password
    res = telegram_verify_password(password)
    if res.get("success"):
        telegram_login_state.clear()
        return jsonify({"success": True})
    return jsonify({"success": False, "error": res.get("error")})

# --- HTML TEMPLATE ROUTES ---

@app.route("/")
def login_page():
    if session.get('logged_in'):
        return redirect("/dashboard")
    return render_template("login.html")

@app.route("/dashboard")
def dashboard_page():
    if not session.get('logged_in'):
        return redirect("/")
    return render_template("dashboard.html")

@app.route("/profile")
def profile_page():
    if not session.get('logged_in'):
        return redirect("/")
    return render_template("profile.html")

@app.route("/inbox")
def inbox_page():
    if not session.get('logged_in'):
        return redirect("/")
    return render_template("inbox.html")

@app.route("/contacts")
def contacts_page():
    if not session.get('logged_in'):
        return redirect("/")
    return render_template("contacts.html")

@app.route("/admin")
def admin_page():
    if not session.get('logged_in'):
        return redirect("/")
    return render_template("admin.html")

@app.route("/api/admin/metrics")
def admin_metrics():
    global service, total_emails_sent
    if service is None:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        gmail_profile = service.users().getProfile(userId="me").execute()
        email = gmail_profile.get("emailAddress", "")
        if email != "archiyadav262003@gmail.com":
            return jsonify({"error": "Access Denied: You are not an Admin"}), 403
    except:
        return jsonify({"error": "Unauthorized"}), 401
    
    logs = get_activity_logs()
    
    from modules.auth import get_all_users
    users = get_all_users()
    total_users = len(users) if users else 0

    return jsonify({
        "recent_activity": logs,
        "total_users": total_users,
        "total_emails_sent": total_emails_sent
    })

@app.route("/api/admin/users", methods=["GET"])
def admin_get_users():
    global service
    if service is None:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        gmail_profile = service.users().getProfile(userId="me").execute()
        email = gmail_profile.get("emailAddress", "")
        if email != "archiyadav262003@gmail.com":
            return jsonify({"error": "Access Denied: You are not an Admin"}), 403
    except:
        return jsonify({"error": "Unauthorized"}), 401
        
    from modules.auth import get_all_users
    users = get_all_users()
    return jsonify({"users": users})

@app.route("/api/admin/users/delete", methods=["POST"])
def admin_delete_user():
    global service
    if service is None:
        return jsonify({"error": "Unauthorized"}), 401
    try:
        gmail_profile = service.users().getProfile(userId="me").execute()
        if gmail_profile.get("emailAddress") != "archiyadav262003@gmail.com":
            return jsonify({"error": "Access Denied"}), 403
    except:
        return jsonify({"error": "Unauthorized"}), 401
        
    data = request.json
    email = data.get("email")
    if not email:
        return jsonify({"error": "Missing email"}), 400
        
    from modules.auth import delete_user
    if delete_user(email):
        return jsonify({"success": True})
    return jsonify({"error": "User not found"}), 404

@app.route("/api/admin/users/update", methods=["POST"])
def admin_update_user():
    global service
    if service is None:
        return jsonify({"error": "Unauthorized"}), 401
    try:
        gmail_profile = service.users().getProfile(userId="me").execute()
        if gmail_profile.get("emailAddress") != "archiyadav262003@gmail.com":
            return jsonify({"error": "Access Denied"}), 403
    except:
        return jsonify({"error": "Unauthorized"}), 401
        
    data = request.json
    current_email = data.get("current_email")
    new_name = data.get("name")
    new_email = data.get("email")
    if not current_email or not new_name or not new_email:
        return jsonify({"error": "Missing data"}), 400
        
    from modules.auth import update_user
    if update_user(current_email, new_name, new_email):
        return jsonify({"success": True})
    return jsonify({"error": "Update failed (email may already exist)"}), 400

@app.route("/api/admin/users/block", methods=["POST"])
def admin_block_user():
    global service
    if service is None:
        return jsonify({"error": "Unauthorized"}), 401
    try:
        gmail_profile = service.users().getProfile(userId="me").execute()
        if gmail_profile.get("emailAddress") != "archiyadav262003@gmail.com":
            return jsonify({"error": "Access Denied"}), 403
    except:
        return jsonify({"error": "Unauthorized"}), 401
        
    data = request.json
    email = data.get("email")
    block_status = data.get("block", True)
    if not email:
        return jsonify({"error": "Missing email"}), 400
        
    from modules.auth import toggle_block_user
    if toggle_block_user(email, block_status):
        return jsonify({"success": True})
    return jsonify({"error": "User not found"}), 404

@app.route("/api/profile")
def profile():
    global service
    from modules.contacts import get_all_contacts

    if service is None:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        gmail_profile = service.users().getProfile(userId="me").execute()
        
        credentials = service._http.credentials
        import requests
        headers = {"Authorization": f"Bearer {credentials.token}"}
        user_info = requests.get("https://www.googleapis.com/oauth2/v2/userinfo", headers=headers).json()

        contacts = get_all_contacts()

        return jsonify({
            "email": gmail_profile.get("emailAddress"),
            "name": user_info.get("name"),
            "contacts": contacts
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/inbox")
def inbox():
    global service
    if service is None:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        results = service.users().messages().list(userId="me", maxResults=10).execute()
        messages = results.get("messages", [])
        emails = []

        for msg in messages:
            full_msg = service.users().messages().get(userId="me", id=msg["id"], format="full").execute()
            headers = full_msg["payload"]["headers"]

            sender, subject = "", ""
            for h in headers:
                if h["name"] == "From":
                    sender = h["value"]
                if h["name"] == "Subject":
                    subject = h["value"]

            emails.append({"id": msg["id"], "sender": sender, "subject": subject})

        return jsonify({"emails": emails})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/logout")
def logout():
    global service
    service = None
    session.clear()          # ← clears 'logged_in', 'auth_type', etc.
    add_log("User logged out.")
    return redirect("/")

@app.route("/api/contacts", methods=["GET"])
def view_contacts():
    from modules.contacts import get_all_contacts
    return jsonify(get_all_contacts())

@app.route("/api/contacts/add", methods=["POST"])
def add_new_contact():
    from modules.contacts import add_contact
    data = request.get_json()
    name = data.get("name")
    email = data.get("email")
    telegram_username = data.get("telegram_username")

    if not name or not email:
        return jsonify({"status": "error", "message": "Missing data"})

    add_contact(name, email, telegram_username)
    return jsonify({"status": "success", "message": "Contact added"})


@app.route("/api/contacts/delete", methods=["POST"])
def delete_existing_contact():
    from modules.contacts import delete_contact
    data = request.get_json()
    name = data.get("name")

    if delete_contact(name):
        return jsonify({"status": "success", "message": "Contact deleted"})
    else:
        return jsonify({"status": "error", "message": "Contact not found"})

@app.route("/api/contacts/update", methods=["POST"])
def update_existing_contact():
    from modules.contacts import update_contact
    data = request.get_json()
    name = data.get("name")
    email = data.get("email")
    telegram_username = data.get("telegram_username")

    if update_contact(name, email, telegram_username):
        return jsonify({"status": "success", "message": "Contact updated"})
    else:
        return jsonify({"status": "error", "message": "Contact not found"})

@app.route("/api/command", methods=["POST"])
def command_handler():

    global service, email_state, reply_state, telegram_state, total_emails_sent, recent_activity

    from modules.contacts import get_email
    from modules.email_sender import send_email, normalize_email, reply_latest_email, reply_to_contact
    from modules.gmail_reader import read_latest_email, get_email_count

    data = request.get_json()
    if not data or "command" not in data:
        return jsonify({"response": "No command received", "language": "en"}), 400

    raw_command = data["command"]
    language = data.get("language", "en")
    
    # normalize_command may return 'cmd|entity:name' for Gemini-resolved commands
    full_cmd = normalize_command(raw_command)
    entity = ""
    if "|entity:" in full_cmd:
        command, entity = full_cmd.split("|entity:", 1)
        entity = entity.strip()
    else:
        command = full_cmd
        # Also try to extract entity from raw command using smart extractor
        from modules.command_parser import extract_entity
        entity = extract_entity(raw_command)
    
    print(f"[VOICE CMD] raw='{raw_command}' → cmd='{command}' entity='{entity}' lang={language}")

    if "start assistant" in command or "start" in command:
        return jsonify({
        "response": speak_response(
            "Which service do you want to use? Email or Telegram?",
            language
        ),
        "language": language
    })


    # GLOBAL STOP
    if "stop" in command:
        email_state = {}
        reply_state = {}
        return jsonify({"response": translate_text("Assistant stopped", language),
        "language": language
            })


    # NEW COMMANDS (always before state)

    if command.startswith("Start assistant"):
        response = "Which service do you want to use? Email or Telegram?"
        response = translate_text(response, language)
        return jsonify({
    "response": response,
    "language": language
    })

    if "read email" in command:
        if service is None:
            return jsonify({"response": "Please login with Google first to read emails.", "language": language})
        email_state = {}
        reply_state = {}
        try:
            result = read_latest_email(service)
        except Exception as e:
            result = f"Could not read email: {str(e)[:80]}. Please restart the app and try again."
        return jsonify({"response": result, "language": language})

    if "count" in command and "email" in command:
        if service is None:
            return jsonify({
    "response": speak_response("Please login first", language),
    "language": language
})
        email_state = {}
        reply_state = {}
        count = get_email_count(service)
        return jsonify({"response": speak_response(f"You have {count} emails", language), "language": language  })

    if "send email" in command:
        if service is None:
            return jsonify({
    "response": speak_response("Please login first", language),
    "language": language
})
        reply_state = {}
        email_state = {"step": "recipient"}
        return jsonify({
    "response": speak_response(
        "Tell recipient contact name or email address",
        language
    ),
    "language": language
})

    if "reply latest" in command or "reply email" in command:
        if service is None:
            return jsonify({
    "response": speak_response("Please login first", language),
    "language": language
})
        email_state = {}
        reply_state = {"step": "latest_body"}
        return jsonify({"response": speak_response("Tell your reply message", language), "language": language})

    if "reply to" in command:
        if service is None:
            return jsonify({
    "response": speak_response("Please login first", language),
    "language": language
})
        email_state = {}
        name = command.replace("reply to", "").strip()
        if not name:
            reply_state = {"step": "ask_contact"}
            return jsonify({"response": speak_response("Tell contact name or email", language), "language": language})
        reply_state = {"step": "contact_body", "contact": name}
        return jsonify({"response": speak_response(f"What is your reply to {name}?", language), "language": language})


    # EMAIL STATE FLOW

    if email_state.get("step") == "recipient":
        from modules.command_parser import extract_entity
        from modules.email_sender import normalize_email
        from modules.contacts import get_email

        # Try contact name from entity extraction (handles 'send to X', 'contact name is X' etc)
        candidate = entity if entity else extract_entity(command)
        contact_email = get_email(candidate) or get_email(command)

        if not contact_email:
            # Maybe they spoke a raw email address
            email = normalize_email(command)
            if email:
                contact_email = email
            else:
                # Stay on recipient step & ask again
                return jsonify({"response": speak_response(
                    f"Contact '{candidate}' not found in your directory. Say a name from your contacts or an email address.",
                    language
                ), "language": language})
                
        email_state["to"] = contact_email
        
        # If it was an unsaved raw email, ask to save it
        if not get_email(candidate) and not get_email(command):
            email_state["step"] = "ask_save_contact"
            return jsonify({"response": speak_response(f"Do you want to save {contact_email} to your contacts? Say yes or no.", language), "language": language})

        email_state["step"] = "subject"
        return jsonify({"response": speak_response(f"Got it. Now tell me the subject.", language), "language": language})

    if email_state.get("step") == "ask_save_contact":
        if any(word in command for word in ["yes", "yeah", "ok", "sure", "ha", "हाँ", "हां"]):
            email_state["step"] = "save_contact_name"
            return jsonify({"response": speak_response("What should I name this contact?", language), "language": language})
        else:
            email_state["step"] = "subject"
            return jsonify({"response": speak_response("Got it. Now tell me the subject.", language), "language": language})

    if email_state.get("step") == "save_contact_name":
        from modules.command_parser import extract_entity
        from modules.contacts import add_contact
        contact_name = extract_entity(command)
        if not contact_name:
            contact_name = command.strip()
        add_contact(contact_name, email=email_state["to"])
        email_state["step"] = "subject"
        return jsonify({"response": speak_response(f"Saved contact {contact_name}. Now tell me the subject.", language), "language": language})

    if email_state.get("step") == "subject":
        email_state["subject"] = command
        email_state["step"] = "body"
        return jsonify({"response": speak_response("Tell message", language), "language": language})

    if email_state.get("step") == "body":
        email_state["body"] = command
        email_state["step"] = "confirm"
        to = email_state.get('to', '')
        subj = email_state.get('subject', '')
        body_preview = command[:80]
        confirm_text = f"Sending email to {to}. Subject: {subj}. Message: {body_preview}. Say yes to confirm or no to cancel."
        return jsonify({"response": confirm_text, "language": language})

    if email_state.get("step") == "confirm":
        if any(word in command for word in ["yes", "yeah", "confirm", "conform", "send", "okay", "ok", "sure", "haan", "हाँ", "हां", "ha"]):
            email_state["step"] = "pin_auth"
            return jsonify({"response": speak_response("Please say your 4-digit PIN", language), "language": language})
        else:
            email_state = {}
            add_log("Email sending cancelled.")
            return jsonify({"response": speak_response("Email cancelled", language), "language": language})

    if email_state.get("step") == "pin_auth":
        entered_pin = extract_pin(command)
        if entered_pin == user_pin:
            try:
                send_email(service, email_state["to"], email_state["subject"], email_state["body"])
            except Exception as e:
                email_state = {}
                return jsonify({"response": f"Email failed: {str(e)[:60]}", "language": language})
            email_state = {}
            total_emails_sent += 1
            add_log("Email sent successfully.")
            return jsonify({"response": speak_response("Email sent successfully", language), "language": language})
        else:
            email_state = {}
            add_log("Failed PIN attempt.")
            return jsonify({"response": speak_response("Invalid PIN. Message not sent.", language), "language": language})


 
    # REPLY STATE FLOW

    if reply_state.get("step") == "latest_body":
        reply_state["body"] = command
        reply_state["step"] = "latest_confirm"
        return jsonify({"response": translate_text("Say yes to confirm or no to cancel", language), "language": language})

    if reply_state.get("step") == "latest_confirm":

        if any(word in command for word in [
            "yes", "yeah", "confirm", "conform",
            "send", "okay", "ok", "sure"
        ]):
            reply_state["step"] = "latest_pin_auth"
            return jsonify({"response": translate_text("Please say your 4-digit PIN", language), "language": language})
        else:
            reply_state = {}
            add_log("Latest email reply cancelled.")
            return jsonify({"response": translate_text("Reply cancelled", language), "language": language})

    if reply_state.get("step") == "latest_pin_auth":
        entered_pin = extract_pin(command)
        if entered_pin == user_pin:
            reply_latest_email(service, reply_state["body"])
            reply_state = {}
            total_emails_sent += 1
            add_log("Replied to latest email.")
            return jsonify({"response": translate_text("Reply sent successfully", language), "language": language})
        else:
            reply_state = {}
            add_log("Failed PIN attempt for email reply.")
            return jsonify({"response": translate_text("Invalid PIN. Reply not sent.", language), "language": language})


    if reply_state.get("step") == "ask_contact":
        reply_state = {"step": "contact_body", "contact": command}
        return jsonify({"response": translate_text(f"What is your reply to {command}?", language), "language": language})

    if reply_state.get("step") == "contact_body":
        reply_state["body"] = command
        reply_state["step"] = "contact_confirm"
        return jsonify({"response": translate_text(f"Send reply to {reply_state['contact']}? Say yes or no.", language), "language": language})

    if reply_state.get("step") == "contact_confirm":

        if any(word in command for word in [
            "yes", "yeah", "confirm", "conform",
            "send", "okay", "ok", "sure"
        ]):
            reply_state["step"] = "contact_pin_auth"
            return jsonify({"response": translate_text("Please say your 4-digit PIN", language), "language": language})
        else:
            reply_state = {}
            add_log("Contact email reply cancelled.")
            return jsonify({"response": translate_text("Reply cancelled", language), "language": language})

    if reply_state.get("step") == "contact_pin_auth":
        entered_pin = extract_pin(command)
        if entered_pin == user_pin:
            reply_to_contact(
                service,
                reply_state["contact"],
                reply_state["body"]
            )
            reply_state = {}
            total_emails_sent += 1
            add_log(f"Replied to contact {reply_state.get('contact', 'unknown')}.")
            return jsonify({"response": translate_text("Reply sent successfully", language), "language": language})
        else:
            reply_state = {}
            add_log("Failed PIN attempt for contact email reply.")
            return jsonify({"response": translate_text("Invalid PIN. Reply not sent.", language), "language": language})


    # CONTACT MANAGEMENT

    # Add Contact by Voice
    if command.startswith("add contact"):
        parts = command.replace("add contact", "").strip().split()
        if len(parts) < 2:
            return jsonify({"response": speak_response("Say add contact name email", language), "language": language})

        name = parts[0]
        email = parts[1]

        from modules.contacts import add_contact
        add_contact(name, email)
        return jsonify({"response": speak_response(f"Contact {name} added successfully", language), "language": language})

    # Delete Contact by Voice
    if command.startswith("delete contact"):
        name = command.replace("delete contact", "").strip()

        from modules.contacts import delete_contact
        if delete_contact(name):
            return jsonify({"response": speak_response(f"Contact {name} deleted", language), "language": language})
        else:
            return jsonify({"response": speak_response("Contact not found", language), "language": language})

    # Show Contacts by Voice
    if "all contact" in command:
        from modules.contacts import get_all_contacts
        contacts = get_all_contacts()

        if not contacts:
            return jsonify({"response": speak_response("No contacts saved", language), "language": language})

        response = "Your contacts are: "
        for name in contacts:
            response += name + ", "

        return jsonify({"response": speak_response(response, language), "language": language})

    # ── TELEGRAM STATE MACHINE (now fully guided) ─────────────────────────
    if telegram_state.get("step") == "recipient":
        from modules.command_parser import extract_entity, extract_telegram_raw
        from modules.contacts import get_telegram
        candidate = entity if entity else extract_entity(command)
        username = get_telegram(candidate) or get_telegram(command)
        
        if not username:
            raw_username = extract_telegram_raw(command)
            if raw_username:
                username = raw_username
            elif command.startswith("@") or len(command.split()) == 1:
                username = command.strip()
                
        if not username:
            return jsonify({"response": speak_response(
                f"Contact '{candidate}' not found. Please say their Telegram @username directly.",
                language), "language": language})
                
        telegram_state["username"] = username
        
        if not get_telegram(candidate) and not get_telegram(command):
            telegram_state["step"] = "ask_save_contact"
            return jsonify({"response": speak_response(f"Do you want to save {username} to your contacts? Say yes or no.", language), "language": language})
            
        telegram_state["step"] = "message"
        return jsonify({"response": speak_response("What message should I send?", language), "language": language})

    if telegram_state.get("step") == "ask_save_contact":
        if any(w in command for w in ["yes", "haan", "ok", "sure", "हाँ", "ha", "yeah"]):
            telegram_state["step"] = "save_contact_name"
            return jsonify({"response": speak_response("What should I name this contact?", language), "language": language})
        else:
            telegram_state["step"] = "message"
            return jsonify({"response": speak_response("What message should I send?", language), "language": language})

    if telegram_state.get("step") == "save_contact_name":
        from modules.command_parser import extract_entity
        from modules.contacts import add_contact
        contact_name = extract_entity(command)
        if not contact_name:
            contact_name = command.strip()
        # Fallback email is required by schema, use a local placeholder
        add_contact(contact_name, email=contact_name.replace(" ", "") + "@tg.local", telegram_username=telegram_state["username"])
        telegram_state["step"] = "message"
        return jsonify({"response": speak_response(f"Saved contact {contact_name}. What message should I send?", language), "language": language})

    if telegram_state.get("step") == "message":
        telegram_state["pending_message"] = command
        telegram_state["step"] = "confirm"
        uname = telegram_state.get("username", "")
        return jsonify({"response": f"Sending to {uname}: '{command}'. Say yes to confirm.", "language": language})

    if telegram_state.get("step") == "confirm":
        if any(w in command for w in ["yes", "haan", "ok", "confirm", "sure", "हाँ"]):
            telegram_state["step"] = "pin_auth"
            telegram_state["timestamp"] = time_module.time()
            return jsonify({"response": speak_response("Please say your 4-digit PIN", language), "language": language})
        else:
            telegram_state = {}
            return jsonify({"response": speak_response("Telegram message cancelled.", language), "language": language})

    if telegram_state.get("step") == "pin_auth":
        entered_pin = extract_pin(command)
        if entered_pin == user_pin:
            msg = telegram_state.get("pending_message", "")
            uname = telegram_state.get("username", "")
            response = send_telegram_message(uname, msg)
            telegram_state = {}
            add_log("Telegram message sent.")
            return jsonify({"response": speak_response("Telegram message sent.", language), "language": language})
        else:
            telegram_state = {}
            add_log("Failed PIN for Telegram.")
            return jsonify({"response": speak_response("Invalid PIN. Message not sent.", language), "language": language})

    # ── SEND TELEGRAM: Initiate guided flow ───────────────────────────────
    if "send telegram" in command:
        telegram_state = {"step": "recipient"}
        return jsonify({"response": speak_response(
            "Which contact should I send Telegram to?", language), "language": language})

    # ── READ TELEGRAM ─────────────────────────────────────────────────────
    if "read telegram" in command:
        msg = read_latest_telegram()
        if msg:
            return jsonify({"response": msg, "language": language})
        return jsonify({"response": "No Telegram messages found or not connected.", "language": language})

    # ── FALLBACK ──────────────────────────────────────────────────────────
    return jsonify({"response": "Command not understood", "language": language})



if __name__ == "__main__":
    print("Starting Flask server...")
    app.run(debug=True, port=5000, use_reloader=False)
