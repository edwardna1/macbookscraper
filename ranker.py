"""Rank matches by best value: price, chip priority, SSD. Assign value score and best-deal flag."""
from typing import Any

CHIP_PRIORITY = {"M4 Pro": 3, "M3 Pro": 2, "M2 Pro": 1, "M4": 1}


def _chip_label(p: dict[str, Any]) -> str:
    gen = (p.get("chip_generation") or "").strip()
    tier = (p.get("chip_tier") or "").strip()
    if gen and tier:
        return f"{gen} {tier}"
    return gen or ""


def _price_value(p: dict[str, Any]) -> float:
    price = p.get("price")
    if price is None:
        return float("inf")
    if isinstance(price, str):
        try:
            price = float(price.replace(",", "").replace("$", "").strip())
        except (ValueError, AttributeError):
            return float("inf")
    return float(price)


def _value_score(p: dict[str, Any], max_price: float) -> float:
    """
    Higher is better. Base from lower price, bonus for newer chip, bonus for larger SSD.
    """
    price = _price_value(p)
    if price <= 0 or max_price <= 0:
        return 0.0
    # Base: inverse of normalized price (0..1 scale)
    base = 1.0 - (price / max_price)
    chip_label = _chip_label(p)
    chip_bonus = CHIP_PRIORITY.get(chip_label, 0) * 0.1
    ssd = p.get("ssd_gb") or 0
    try:
        ssd = int(ssd)
    except (TypeError, ValueError):
        ssd = 0
    ssd_bonus = min(0.2, ssd / 2048 * 0.2)  # cap at 2TB
    return base + chip_bonus + ssd_bonus


def rank_by_value(products: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Sort by: (1) price asc, (2) chip priority M4 > M3 > M2, (3) SSD desc.
    Add value_score, rank (1-based), and is_best_deal for rank 1.
    """
    if not products:
        return []

    max_price = max(_price_value(p) for p in products) or 1.0
    for p in products:
        p["value_score"] = _value_score(p, max_price)

    def sort_key(p: dict[str, Any]) -> tuple:
        price = _price_value(p)
        chip_label = _chip_label(p)
        chip_ord = -CHIP_PRIORITY.get(chip_label, 0)
        ssd = p.get("ssd_gb") or 0
        try:
            ssd = int(ssd)
        except (TypeError, ValueError):
            ssd = 0
        return (price, chip_ord, -ssd)

    sorted_list = sorted(products, key=sort_key)
    for i, p in enumerate(sorted_list):
        p["rank"] = i + 1
        p["is_best_deal"] = i == 0
    return sorted_list
