"""One-off: print your Telegram chat ID from getUpdates. Message your bot first, then run this."""
import os
import sys

from dotenv import load_dotenv

load_dotenv()
token = os.getenv("TELEGRAM_BOT_TOKEN")
if not token:
    print("Set TELEGRAM_BOT_TOKEN in .env", file=sys.stderr)
    sys.exit(1)

import httpx
r = httpx.get(f"https://api.telegram.org/bot{token}/getUpdates", timeout=10)
data = r.json()
if not data.get("ok"):
    print("API error:", data, file=sys.stderr)
    sys.exit(1)
for u in data.get("result", []):
    chat = u.get("message", {}).get("chat") or u.get("callback_query", {}).get("message", {}).get("chat")
    if chat:
        print("Your TELEGRAM_CHAT_ID:", chat["id"])
        break
else:
    print("No messages found. Send a message to your bot in Telegram first, then run this again.")
