"""Filter products: MacBook Pro, M2/M3/M4 Pro, RAM >= 36GB. Optional: prefer 1TB+ SSD."""
import logging
from typing import Any

logger = logging.getLogger(__name__)

TARGET_CHIPS = ("M4 Pro", "M3 Pro", "M2 Pro")
MIN_RAM_GB = 36
PREFER_SSD_GB = 1024  # 1TB+


def _chip_label(p: dict[str, Any]) -> str:
    gen = (p.get("chip_generation") or "").strip()
    tier = (p.get("chip_tier") or "").strip()
    if gen and tier:
        return f"{gen} {tier}"
    return ""


def _matches_chip(p: dict[str, Any]) -> bool:
    label = _chip_label(p)
    return label in TARGET_CHIPS


def _matches_ram(p: dict[str, Any]) -> bool:
    ram = p.get("ram_gb")
    if ram is None:
        # Not known from listing/detail - exclude (we require 36GB+)
        return False
    try:
        return int(ram) >= MIN_RAM_GB
    except (TypeError, ValueError):
        return False


def filter_products(products: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Keep only: MacBook Pro, chip in (M4 Pro, M3 Pro, M2 Pro), RAM >= 36GB.
    Optional: prefer 1TB+ SSD (we don't exclude smaller, just rank lower later).
    """
    out = []
    for p in products:
        if not p.get("is_refurbished_macbook_pro"):
            continue
        if not _matches_chip(p):
            continue
        if not _matches_ram(p):
            continue
        out.append(p)
    logger.info("Filtered to %s matches (MacBook Pro, M2/M3/M4 Pro, 36GB+ RAM)", len(out))
    return out
