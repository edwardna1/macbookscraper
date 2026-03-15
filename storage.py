"""Persist seen product IDs/URLs and track price for new vs price-drop alerts."""
import json
import logging
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Product id is URL or stable identifier
ENTRY_LAST_PRICE = "last_price"
ENTRY_FIRST_SEEN_TS = "first_seen_ts"
ENTRY_LAST_SEEN_TS = "last_seen_ts"
ENTRY_LAST_ALERTED_TS = "last_alerted_ts"
ENTRY_LAST_ALERTED_PRICE = "last_alerted_price"


def _product_id(p: dict[str, Any]) -> str:
    return p.get("url") or p.get("title") or ""


def load(path: str) -> dict[str, dict[str, Any]]:
    """Load seen products from JSON file. Returns dict id -> entry."""
    filepath = Path(path)
    if not filepath.exists():
        return {}
    try:
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Could not load storage %s: %s", path, e)
        return {}


def save(path: str, data: dict[str, dict[str, Any]]) -> None:
    """Write seen products to JSON file."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def mark_seen(
    current: dict[str, dict[str, Any]],
    products: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Update current state with products (last_seen_ts, last_price). Returns updated dict."""
    now = time.time()
    for p in products:
        pid = _product_id(p)
        if not pid:
            continue
        price = p.get("price")
        if isinstance(price, str):
            try:
                price = float(price.replace(",", "").replace("$", "").strip())
            except (ValueError, AttributeError):
                price = None
        entry = current.get(pid) or {
            ENTRY_FIRST_SEEN_TS: now,
            ENTRY_LAST_ALERTED_TS: None,
            ENTRY_LAST_ALERTED_PRICE: None,
        }
        entry[ENTRY_LAST_SEEN_TS] = now
        if price is not None:
            entry[ENTRY_LAST_PRICE] = price
        if ENTRY_FIRST_SEEN_TS not in entry:
            entry[ENTRY_FIRST_SEEN_TS] = now
        current[pid] = entry
    return current


def get_new_and_price_drops(
    current: dict[str, dict[str, Any]],
    ranked_matches: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[tuple[dict[str, Any], float]]]:
    """
    Returns (new_products, price_drops).
    - new_products: never seen before (no entry in current).
    - price_drops: list of (product, previous_price) for items we've seen and alerted
      before but current price is lower than last_alerted_price or last_price.
    """
    now = time.time()
    new_products: list[dict[str, Any]] = []
    price_drops: list[tuple[dict[str, Any], float]] = []

    for p in ranked_matches:
        pid = _product_id(p)
        if not pid:
            continue
        price = p.get("price")
        if isinstance(price, str):
            try:
                price = float(price.replace(",", "").replace("$", "").strip())
            except (ValueError, AttributeError):
                price = None
        if price is None:
            continue

        entry = current.get(pid)
        if not entry:
            new_products.append(p)
            continue

        last_alerted = entry.get(ENTRY_LAST_ALERTED_PRICE)
        last_price = entry.get(ENTRY_LAST_PRICE)
        # Consider it a price drop if we have a previous price and current is lower
        prev = last_alerted if last_alerted is not None else last_price
        if prev is not None and price < prev:
            price_drops.append((p, prev))

    return new_products, price_drops


def mark_alerted(
    current: dict[str, dict[str, Any]],
    products: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Set last_alerted_ts and last_alerted_price for given products."""
    now = time.time()
    for p in products:
        pid = _product_id(p)
        if not pid or pid not in current:
            continue
        price = p.get("price")
        if isinstance(price, str):
            try:
                price = float(price.replace(",", "").replace("$", "").strip())
            except (ValueError, AttributeError):
                price = None
        current[pid][ENTRY_LAST_ALERTED_TS] = now
        if price is not None:
            current[pid][ENTRY_LAST_ALERTED_PRICE] = price
    return current
