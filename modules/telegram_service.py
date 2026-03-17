import os
import asyncio
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

# Provide valid API ID / HASH from my.telegram.org in your .env
# We fallback to defaults if not provided for testing.
API_ID = os.getenv("TELEGRAM_API_ID", "2040") 
API_HASH = os.getenv("TELEGRAM_API_HASH", "b18441a1ff607e10a989891a5462e627")

def _get_client_and_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    # Using the same 'assistant_session.session' sqlite file
    client = TelegramClient('assistant_session', API_ID, API_HASH, loop=loop)
    return client, loop

def send_telegram_message(username, text):
    """Sends a telegram message to a username (e.g. '@dev') natively."""
    client, loop = _get_client_and_loop()
    try:
        loop.run_until_complete(client.connect())
        if not loop.run_until_complete(client.is_user_authorized()):
            return "Telegram is not set up. Please run python telegram_setup.py in your terminal first."
        
        # Telethon allows string usernames directly: client.send_message('@username', 'text')
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

def read_latest_telegram():
    """Reads the latest message received"""
    client, loop = _get_client_and_loop()
    try:
        loop.run_until_complete(client.connect())
        if not loop.run_until_complete(client.is_user_authorized()):
            return "Telegram is not set up. Please connect Telegram from the dashboard."
        
        # Get the latest message from the first dialog (most recent chat)
        dialogs = loop.run_until_complete(client.get_dialogs(limit=1))
        
        if dialogs and len(dialogs) > 0:
            last_message_obj = dialogs[0].message
            return last_message_obj.message if last_message_obj else None
        return None
    except Exception as e:
        print("Telegram Read Error:", e)
        return None
    finally:
        client.disconnect()
        loop.close()

def telegram_send_code(phone):
    client, loop = _get_client_and_loop()
    try:
        loop.run_until_complete(client.connect())
        result = loop.run_until_complete(client.send_code_request(phone))
        return {"success": True, "phone_code_hash": result.phone_code_hash}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        client.disconnect()
        loop.close()

def telegram_verify_code(phone, code, phone_code_hash):
    client, loop = _get_client_and_loop()
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

def telegram_verify_password(password):
    client, loop = _get_client_and_loop()
    try:
        loop.run_until_complete(client.connect())
        loop.run_until_complete(client.sign_in(password=password))
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        client.disconnect()
        loop.close()

def is_telegram_authorized():
    client, loop = _get_client_and_loop()
    try:
        loop.run_until_complete(client.connect())
        return loop.run_until_complete(client.is_user_authorized())
    except Exception:
        return False
    finally:
        client.disconnect()
        loop.close()
