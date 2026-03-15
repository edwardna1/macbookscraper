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

# Twilio SMS
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER", "")
TWILIO_TO_NUMBER = os.getenv("TWILIO_TO_NUMBER", "")


def validate_config() -> None:
    """Raise ValueError if required settings are missing (e.g. for alerts)."""
    missing = []
    if not TWILIO_ACCOUNT_SID:
        missing.append("TWILIO_ACCOUNT_SID")
    if not TWILIO_AUTH_TOKEN:
        missing.append("TWILIO_AUTH_TOKEN")
    if not TWILIO_FROM_NUMBER:
        missing.append("TWILIO_FROM_NUMBER")
    if not TWILIO_TO_NUMBER:
        missing.append("TWILIO_TO_NUMBER")
    if missing:
        raise ValueError(
            f"Missing required Twilio config. Set in .env: {', '.join(missing)}"
        )


def twilio_configured() -> bool:
    """True if all Twilio vars are set (alerts can be sent)."""
    return bool(
        TWILIO_ACCOUNT_SID
        and TWILIO_AUTH_TOKEN
        and TWILIO_FROM_NUMBER
        and TWILIO_TO_NUMBER
    )
