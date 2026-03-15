"""Main loop: poll Apple refurb listing, filter, rank, dedupe, alert, persist."""
import logging
import sys
import time

import config
import filters
import parser
import ranker
import storage
import alerts

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


def run_once() -> None:
    """Single cycle: fetch, parse, filter, rank, compare to seen, alert, save."""
    try:
        products = parser.fetch_all(
            listing_url=config.APPLE_REFURB_BASE_URL,
            fetch_details_for_macbook_pro=True,
        )
    except Exception as e:
        logger.exception("Fetch/parse failed: %s", e)
        return

    if not products:
        logger.warning("No products parsed")
        return

    matched = filters.filter_products(products)
    if not matched:
        logger.info("No matches (M2/M3/M4 Pro, 36GB+ RAM)")
        return

    ranked = ranker.rank_by_value(matched)
    logger.info("Ranked %s matches", len(ranked))

    data = storage.load(config.STORAGE_PATH)
    new_products, price_drops = storage.get_new_and_price_drops(data, ranked)
    storage.mark_seen(data, ranked)
    to_alert_new = new_products
    to_alert_drops = price_drops

    if to_alert_new or to_alert_drops:
        if config.telegram_configured():
            alerts.alert_new_and_price_drops(to_alert_new, to_alert_drops)
            storage.mark_alerted(data, to_alert_new + [p for p, _ in to_alert_drops])
        else:
            logger.warning("Telegram not configured; would have alerted %s new, %s drops",
                          len(to_alert_new), len(to_alert_drops))
    else:
        logger.info("No new matches or price drops to alert")

    storage.save(config.STORAGE_PATH, data)


def main() -> None:
    """Run loop every POLL_INTERVAL_SECONDS, or once if --once."""
    if "--once" in sys.argv:
        run_once()
        return

    try:
        config.validate_config()
    except ValueError as e:
        logger.error("%s", e)
        sys.exit(1)

    logger.info("Starting monitor (poll every %s s)", config.POLL_INTERVAL_SECONDS)
    while True:
        run_once()
        time.sleep(config.POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
