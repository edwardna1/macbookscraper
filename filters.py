"""Filter: MacBook Pro M2/M3/M4 Pro 24GB+ OR MacBook Air M4 32GB+."""
import logging
from typing import Any

logger = logging.getLogger(__name__)

TARGET_CHIPS_PRO = ("M4 Pro", "M3 Pro", "M2 Pro")
MIN_RAM_GB_PRO = 24
MIN_RAM_GB_AIR = 32
PREFER_SSD_GB = 1024  # 1TB+


def _chip_label(p: dict[str, Any]) -> str:
    gen = (p.get("chip_generation") or "").strip()
    tier = (p.get("chip_tier") or "").strip()
    if gen and tier:
        return f"{gen} {tier}"
    return gen or ""


def _matches_pro(p: dict[str, Any]) -> bool:
    if not p.get("is_refurbished_macbook_pro"):
        return False
    if _chip_label(p) not in TARGET_CHIPS_PRO:
        return False
    ram = p.get("ram_gb")
    if ram is None:
        return False
    try:
        return int(ram) >= MIN_RAM_GB_PRO
    except (TypeError, ValueError):
        return False


def _matches_air(p: dict[str, Any]) -> bool:
    if not p.get("is_refurbished_macbook_air"):
        return False
    if (p.get("chip_generation") or "").strip() != "M4":
        return False
    ram = p.get("ram_gb")
    if ram is None:
        return False
    try:
        return int(ram) >= MIN_RAM_GB_AIR
    except (TypeError, ValueError):
        return False


def filter_products(products: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Keep: MacBook Pro (M4/M3/M2 Pro, 24GB+ RAM) OR MacBook Air (M4, 32GB+ RAM).
    """
    out = []
    for p in products:
        if _matches_pro(p) or _matches_air(p):
            out.append(p)
    logger.info(
        "Filtered to %s matches (Pro M2/M3/M4 24GB+ or Air M4 32GB+)",
        len(out),
    )
    return out
