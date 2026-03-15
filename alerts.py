"""Send alerts via Twilio SMS. Format: title, price, specs, value rank, link."""
import logging
from typing import Any

import config

logger = logging.getLogger(__name__)

MAX_SMS_LENGTH = 1600  # Keep under to avoid excessive segments


def _format_price(p: dict[str, Any]) -> str:
    price = p.get("price")
    if price is None:
        return "?"
    if isinstance(price, (int, float)):
        return f"${price:,.0f} CAD"
    return str(price)


def _format_product_line(p: dict[str, Any], rank_label: str) -> str:
    title = (p.get("title") or "")[:80]
    price = _format_price(p)
    chip = (p.get("chip_generation") or "") + " " + (p.get("chip_tier") or "")
    ram = p.get("ram_gb")
    ram_s = f"{ram}GB" if ram is not None else "?"
    ssd = p.get("ssd_gb")
    if ssd and ssd >= 1024:
        ssd_s = f"{ssd // 1024}TB"
    else:
        ssd_s = f"{ssd}GB" if ssd is not None else "?"
    url = p.get("url") or ""
    return f"{title} — {price} — {chip} {ram_s} RAM {ssd_s} SSD — {rank_label}\n{url}"


def _format_message(
    new_products: list[dict[str, Any]],
    price_drops: list[tuple[dict[str, Any], float]],
) -> str:
    parts = []
    for p in new_products:
        rank_label = "Best current value" if p.get("is_best_deal") else f"#{p.get('rank', '?')} value"
        line = "MATCH: " + _format_product_line(p, rank_label)
        parts.append(line)
    for p, prev_price in price_drops:
        line = f"PRICE DROP: {p.get('title', '')[:60]} — was ${prev_price:,.0f}, now {_format_price(p)} — {p.get('url', '')}"
        parts.append(line)
    msg = "\n\n".join(parts)
    if len(msg) > MAX_SMS_LENGTH:
        msg = msg[: MAX_SMS_LENGTH - 20] + "\n…(truncated)"
    return msg


def send_sms(body: str) -> bool:
    """Send one SMS via Twilio. Returns True on success."""
    if not config.twilio_configured():
        logger.warning("Twilio not configured; skipping SMS")
        return False
    try:
        from twilio.rest import Client

        client = Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=body,
            from_=config.TWILIO_FROM_NUMBER,
            to=config.TWILIO_TO_NUMBER,
        )
        logger.info("SMS sent to %s", config.TWILIO_TO_NUMBER)
        return True
    except Exception as e:
        logger.exception("Twilio SMS failed: %s", e)
        return False


def alert_new_and_price_drops(
    new_products: list[dict[str, Any]],
    price_drops: list[tuple[dict[str, Any], float]],
) -> bool:
    """Format and send one SMS for all new matches and price drops. Returns True if sent."""
    if not new_products and not price_drops:
        return False
    msg = _format_message(new_products, price_drops)
    return send_sms(msg)
