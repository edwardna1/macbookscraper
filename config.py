"""Configuration loaded from environment. Uses python-dotenv for .env support."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Apple Canada refurbished store
APPLE_REFURB_BASE_URL = os.getenv("APPLE_REFURB_BASE_URL", "https://www.apple.com/ca/shop/refurbished/mac")
APPLE_REFURB_MACBOOK_PRO_PATH = os.getenv("APPLE_REFURB_MACBOOK_PRO_PATH", "/refurbished/mac/macbook-pro")

# Polling
POLL_INTERVAL_MINUTES = int(os.getenv("POLL_INTERVAL_MINUTES", "12"))
POLL_INTERVAL_SECONDS = POLL_INTERVAL_MINUTES * 60

# Storage
STORAGE_PATH = os.getenv("STORAGE_PATH", str(Path(__file__).parent / "seen_products.json"))

# HTTP
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
RETRY_COUNT = int(os.getenv("RETRY_COUNT", "3"))

# Telegram Bot
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")


def validate_config() -> None:
    """Raise ValueError if required settings are missing (e.g. for alerts)."""
    missing = []
    if not TELEGRAM_BOT_TOKEN:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not TELEGRAM_CHAT_ID:
        missing.append("TELEGRAM_CHAT_ID")
    if missing:
        raise ValueError(
            f"Missing required Telegram config. Set in .env: {', '.join(missing)}"
        )


def telegram_configured() -> bool:
    """True if Telegram bot vars are set (alerts can be sent)."""
    return bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)
