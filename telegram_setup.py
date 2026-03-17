import os
import asyncio
from telethon import TelegramClient

# Make sure these match the ones in telegram_service.py
API_ID = os.getenv("TELEGRAM_API_ID", "2040")
API_HASH = os.getenv("TELEGRAM_API_HASH", "b18441a1ff607e10a989891a5462e627")

async def main():
    print("="*50)
    print("    VOICEMAIL AI - TELEGRAM SETUP")
    print("="*50)
    print("This will link your Telegram account so the assistant can send/read messages on your behalf.\n")
    print("Please enter your Telegram Phone Number (with country code, e.g., +919000000000):")
    phone = input("> ")

    # This creates or uses 'assistant_session.session' in the same folder
    client = TelegramClient('assistant_session', API_ID, API_HASH)
    
    try:
        # Client start will automatically prompt for OTP in the terminal
        await client.start(phone=phone)

        print("\n✅ Successfully connected to Telegram!")
        print("You can now close this script and restart your Flask app (python main.py).")
        print("The assistant will use the new auth file to send messages automatically.")
    except Exception as e:
        print(f"\n❌ Error during setup: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
