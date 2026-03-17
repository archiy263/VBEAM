import os
import asyncio
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

# Provide valid API ID / HASH from my.telegram.org in your .env
# We fallback to defaults if not provided for testing.
API_ID = os.getenv("TELEGRAM_API_ID", "2040") 
API_HASH = os.getenv("TELEGRAM_API_HASH", "b18441a1ff607e10a989891a5462e627")

def _get_client_and_loop(session_name='assistant_session'):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    # Use the provided session_name (e.g. 'user_email_session')
    client = TelegramClient(session_name, API_ID, API_HASH, loop=loop)
    return client, loop

def send_telegram_message(username, text, session_name='assistant_session'):
    """Sends a telegram message to a username (e.g. '@dev') natively."""
    client, loop = _get_client_and_loop(session_name)
    try:
        loop.run_until_complete(client.connect())
        if not loop.run_until_complete(client.is_user_authorized()):
            return "Telegram is not set up. Please connect Telegram from the dashboard first."
        
        # If it's a phone number, ensure it has '+' and no '@'
        if username.startswith('+') or username.isdigit():
            target = username if username.startswith('+') else f"+{username}"
        else:
            target = username if username.startswith('@') else f"@{username}"
            
        loop.run_until_complete(client.send_message(target, text))
        return "Telegram message sent successfully."
    except ValueError as ve:
        print("Telegram Send Error:", ve)
        return "Could not find that Telegram user."
    except Exception as e:
        print("Telegram Send Error:", e)
        return "Telegram sending failed."
    finally:
        client.disconnect()
        loop.close()

def read_latest_telegram(session_name='assistant_session'):
    """Reads the latest message received"""
    client, loop = _get_client_and_loop(session_name)
    try:
        loop.run_until_complete(client.connect())
        if not loop.run_until_complete(client.is_user_authorized()):
            return "NOT_CONNECTED"
        
        # Get the latest dialogues to find a real message (skips empty/service messages)
        dialogs = loop.run_until_complete(client.get_dialogs(limit=15))
        
        for d in dialogs:
            m = d.message
            if not m:
                continue
            
            text = getattr(m, 'message', '') or getattr(m, 'text', '')
            sender = d.name or "Unknown"
            
            if text:
                return f"Message from {sender}: {text}"
            elif getattr(m, 'media', None):
                return f"Media message from {sender}"
                
        return "NO_MESSAGES"
    except Exception as e:
        print("Telegram Read Error:", e)
        return "ERROR"
    finally:
        client.disconnect()
        loop.close()

def telegram_send_code(phone, session_name='assistant_session'):
    client, loop = _get_client_and_loop(session_name)
    try:
        loop.run_until_complete(client.connect())
        result = loop.run_until_complete(client.send_code_request(phone))
        return {"success": True, "phone_code_hash": result.phone_code_hash}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        client.disconnect()
        loop.close()

def telegram_verify_code(phone, code, phone_code_hash, session_name='assistant_session'):
    client, loop = _get_client_and_loop(session_name)
    try:
        loop.run_until_complete(client.connect())
        loop.run_until_complete(client.sign_in(phone=phone, code=code, phone_code_hash=phone_code_hash))
        return {"success": True}
    except SessionPasswordNeededError:
        return {"success": False, "needs_password": True}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        client.disconnect()
        loop.close()

def telegram_verify_password(password, session_name='assistant_session'):
    client, loop = _get_client_and_loop(session_name)
    try:
        loop.run_until_complete(client.connect())
        loop.run_until_complete(client.sign_in(password=password))
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        client.disconnect()
        loop.close()

def is_telegram_authorized(session_name='assistant_session'):
    client, loop = _get_client_and_loop(session_name)
    try:
        loop.run_until_complete(client.connect())
        return loop.run_until_complete(client.is_user_authorized())
    except Exception:
        return False
    finally:
        client.disconnect()
        loop.close()
