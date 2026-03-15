"""Fetch and parse Apple Canada refurbished Mac listing into structured products."""
import json
import logging
import re
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

import config

logger = logging.getLogger(__name__)

BASE_URL = "https://www.apple.com"
CANADA_REFURB_MAC = getattr(
    config, "APPLE_REFURB_BASE_URL", "https://www.apple.com/ca/shop/refurbished/mac"
)


def _normalize_price(raw: str) -> float | None:
    """Extract numeric price from string like '$2,699.00' or 'Now $2,699.00'."""
    if not raw:
        return None
    m = re.search(r"\$[\d,]+(?:\.\d{2})?", raw.replace("\u00a0", " "))
    if not m:
        return None
    s = m.group(0).replace("$", "").replace(",", "").strip()
    try:
        return float(s)
    except ValueError:
        return None


def _parse_chip(title: str) -> tuple[str | None, str | None]:
    """Return (generation, tier) e.g. ('M4', 'Pro'). Tier can be Pro, Max, etc."""
    if not title:
        return None, None
    # M4 Pro, M3 Pro, M2 Pro, M4 Max, etc.
    m = re.search(r"Apple\s+(M\d+)\s+(Pro|Max|Ultra)\s+", title, re.I)
    if m:
        return m.group(1).upper(), m.group(2).capitalize()
    m = re.search(r"(M\d+)\s+(Pro|Max|Ultra)\s+", title, re.I)
    if m:
        return m.group(1).upper(), m.group(2).capitalize()
    return None, None


def _parse_screen(title: str) -> float | None:
    """Extract screen size in inches from title."""
    if not title:
        return None
    m = re.search(r"(\d+(?:\.\d+)?)\s*[-‑]\s*inch", title, re.I)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass
    return None


def _parse_color(title: str) -> str | None:
    """Extract color from end of title (after last – or -)."""
    if not title:
        return None
    # Split on en-dash or hyphen before color
    parts = re.split(r"\s*[–\-]\s*", title, maxsplit=1)
    if len(parts) >= 2:
        return parts[-1].strip()
    return None


def _parse_ram_from_text(text: str) -> int | None:
    """Extract RAM in GB from page text (e.g. '36 GB', '36GB', 'unified memory')."""
    if not text:
        return None
    # Prefer "XX GB unified memory" or "XXGB"
    m = re.search(r"(\d+)\s*GB\s+unified\s+memory", text, re.I)
    if m:
        return int(m.group(1))
    m = re.search(r"(\d+)\s*GB\s+memory", text, re.I)
    if m:
        return int(m.group(1))
    m = re.search(r"memory[:\s]+(\d+)\s*GB", text, re.I)
    if m:
        return int(m.group(1))
    return None


def _parse_ssd_from_text(text: str) -> int | None:
    """Extract SSD in GB from page text (e.g. '1 TB SSD', '512GB')."""
    if not text:
        return None
    m = re.search(r"(\d+)\s*TB\s+SSD", text, re.I)
    if m:
        return int(m.group(1)) * 1024
    m = re.search(r"(\d+)\s*TB\s+storage", text, re.I)
    if m:
        return int(m.group(1)) * 1024
    m = re.search(r"(\d+)\s*GB\s+SSD", text, re.I)
    if m:
        return int(m.group(1))
    m = re.search(r"(\d+)\s*GB\s+storage", text, re.I)
    if m:
        return int(m.group(1))
    return None


def _is_refurbished_macbook_pro(title: str) -> bool:
    if not title:
        return False
    t = title.lower()
    return "refurbished" in t and "macbook pro" in t


def _build_product(
    title: str,
    price: float | str | None,
    url: str,
    ram_gb: int | None = None,
    ssd_gb: int | None = None,
) -> dict[str, Any]:
    gen, tier = _parse_chip(title)
    return {
        "title": title,
        "price": price,
        "url": url,
        "chip_generation": gen,
        "chip_tier": tier,
        "ram_gb": ram_gb,
        "ssd_gb": ssd_gb,
        "screen_inches": _parse_screen(title),
        "color": _parse_color(title),
        "is_refurbished_macbook_pro": _is_refurbished_macbook_pro(title),
    }


def fetch_listing_page(url: str | None = None) -> str:
    """Fetch listing HTML with retries. Returns raw HTML."""
    url = url or CANADA_REFURB_MAC
    timeout = getattr(config, "REQUEST_TIMEOUT", 30)
    retries = getattr(config, "RETRY_COUNT", 3)
    last_error = None
    for attempt in range(retries):
        try:
            with httpx.Client(timeout=timeout, follow_redirects=True) as client:
                r = client.get(url)
                r.raise_for_status()
                return r.text
        except Exception as e:
            last_error = e
            logger.warning("Fetch attempt %s failed: %s", attempt + 1, e)
    raise last_error  # type: ignore


def _extract_products_from_html(html: str, base: str = BASE_URL) -> list[dict[str, Any]]:
    """Parse listing HTML into product dicts. Uses script JSON first, then DOM."""
    products: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    soup = BeautifulSoup(html, "html.parser")

    # Strategy 1: __NEXT_DATA__ or application/json script
    for script in soup.find_all("script", type="application/json"):
        try:
            data = json.loads(script.string or "{}")
            items = _extract_products_from_json(data)
            for p in items:
                url = p.get("url") or ""
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    products.append(p)
        except (json.JSONDecodeError, TypeError):
            continue
    script_next = soup.find("script", id="__NEXT_DATA__")
    if not products and script_next and script_next.string:
        try:
            data = json.loads(script_next.string)
            items = _extract_products_from_json(data)
            for p in items:
                url = p.get("url") or ""
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    products.append(p)
        except (json.JSONDecodeError, TypeError):
            pass

    # Strategy 2: product links in HTML
    if not products:
        for a in soup.find_all("a", href=True):
            href = a.get("href", "")
            if "/shop/product/" not in href:
                continue
            # Allow if refurbished in URL or in link/heading text
            link_text = (a.get_text(strip=True) or "").lower()
            if "refurbished" not in href.lower() and "refurbished" not in link_text:
                parent = a.find_parent(["li", "div", "section", "article"])
                if parent:
                    pt = (parent.get_text() or "").lower()
                    if "refurbished" not in pt:
                        continue
                else:
                    continue
            full_url = urljoin(base, href)
            if full_url in seen_urls:
                continue
            # Title: link text or nearby heading
            title = (a.get_text(strip=True) or "").strip()
            if not title or len(title) < 10:
                parent = a.find_parent(["li", "div", "section"])
                if parent:
                    h = parent.find(["h2", "h3", "h4"])
                    if h:
                        title = h.get_text(strip=True) or title
            if not title:
                continue
            # Price: sibling or parent text with $
            price = None
            parent = a.find_parent(["li", "div", "article", "section"])
            if parent:
                text = parent.get_text()
                price = _normalize_price(text)
            if price is None and title:
                # Try "Now $X" or "$X" in title area
                price = _normalize_price(title)
            if price is None:
                price = _normalize_price(a.get_text())
            products.append(
                _build_product(title, price, full_url)
            )
            seen_urls.add(full_url)

    # Strategy 3: regex on raw HTML for title + price + link blocks
    if not products:
        # Pattern: link to product, then nearby title and price
        link_pattern = re.compile(
            r'href="(/ca/shop/product/[^"]+)"[^>]*>([^<]*(?:<[^>]+>[^<]*)*?)</a>',
            re.S,
        )
        price_pattern = re.compile(r"\$[\d,]+(?:\.\d{2})?")
        for m in link_pattern.finditer(html):
            path, inner = m.group(1), m.group(2)
            if "refurbished" not in path.lower() and "refurbished" not in inner.lower():
                continue
            full_url = urljoin(base, path)
            if full_url in seen_urls:
                continue
            # Strip tags for title
            title = re.sub(r"<[^>]+>", " ", inner).strip()
            title = re.sub(r"\s+", " ", title)[:200]
            if not title or len(title) < 15:
                continue
            # Find price in surrounding context
            start = max(0, m.start() - 500)
            end = min(len(html), m.end() + 500)
            block = html[start:end]
            prices = price_pattern.findall(block)
            price = None
            for p in prices:
                v = _normalize_price(p)
                if v and 100 < v < 100000:
                    price = v
                    break
            products.append(_build_product(title, price, full_url))
            seen_urls.add(full_url)

    return products


def _extract_products_from_json(data: Any) -> list[dict[str, Any]]:
    """Recursively find product-like objects in JSON (titles, prices, URLs)."""
    out: list[dict[str, Any]] = []
    if isinstance(data, dict):
        title = data.get("title") or data.get("name") or data.get("displayName")
        price = data.get("price") or data.get("currentPrice") or data.get("listPrice")
        url = data.get("url") or data.get("href") or data.get("link")
        if title and (price is not None or url):
            if isinstance(price, (int, float)):
                pass
            elif isinstance(price, str):
                price = _normalize_price(price)
            else:
                price = None
            if url and not url.startswith("http"):
                url = urljoin(BASE_URL, url)
            if title and url and "refurbished" in (title + url).lower():
                out.append(_build_product(str(title), price, url or ""))
        for v in data.values():
            out.extend(_extract_products_from_json(v))
    elif isinstance(data, list):
        for item in data:
            out.extend(_extract_products_from_json(item))
    return out


def fetch_product_detail(url: str) -> tuple[int | None, int | None]:
    """Fetch product detail page and return (ram_gb, ssd_gb)."""
    timeout = getattr(config, "REQUEST_TIMEOUT", 30)
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            r = client.get(url)
            r.raise_for_status()
            text = r.text
    except Exception as e:
        logger.debug("Detail fetch failed for %s: %s", url, e)
        return None, None
    ram = _parse_ram_from_text(text)
    ssd = _parse_ssd_from_text(text)
    return ram, ssd


def fetch_all(
    listing_url: str | None = None,
    fetch_details_for_macbook_pro: bool = True,
) -> list[dict[str, Any]]:
    """
    Fetch listing, parse products, and optionally fetch detail pages for MacBook Pro
    M2/M3/M4 Pro to get RAM/SSD. Returns list of normalized product dicts.
    """
    html = fetch_listing_page(listing_url)
    products = _extract_products_from_html(html)
    logger.info("Parsed %s products from listing", len(products))

    if fetch_details_for_macbook_pro:
        for p in products:
            if not p.get("is_refurbished_macbook_pro"):
                continue
            chip = (p.get("chip_generation") or "") + " " + (p.get("chip_tier") or "")
            if "Pro" not in chip or p.get("chip_generation") not in ("M2", "M3", "M4"):
                continue
            if p.get("ram_gb") is not None:
                continue
            url = p.get("url")
            if not url:
                continue
            ram, ssd = fetch_product_detail(url)
            p["ram_gb"] = ram
            p["ssd_gb"] = ssd

    return products
