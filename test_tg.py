import asyncio
from modules.telegram_service import telegram_send_code

print("Testing send code...")
res = telegram_send_code("+919327526633", "test_session_123")
print("Result:", res)
