"""Rank exact, current retailer comparisons; never fetch or invent prices.

Input records must come from approved product-data sources or reviewed local
observations. This module deliberately has no credentials, scraper or cache.
Amazon comparison rows need API-derived lowest-new pricing; the current
Vyonetix Creators API adapter does not yet establish that field, so it must
not populate such rows until that gap is resolved.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from math import isfinite
from urllib.parse import parse_qs, urlparse

CURRENCY = {"AU": "AUD", "US": "USD", "UK": "GBP"}
AMAZON_HOST = {"AU": "amazon.com.au", "US": "amazon.com", "UK": "amazon.co.uk"}
EBAY_MARKET = {"AU": "EBAY_AU", "US": "EBAY_US", "UK": "EBAY_GB"}
SHORT_HOSTS = {"amzn.to", "bit.ly", "tinyurl.com", "t.co", "ebay.to"}


def _money(value: object) -> Decimal | None:
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None
    return amount if amount.is_finite() and amount >= 0 else None


def _time(value: object, now: datetime, minutes: int) -> bool:
    if not isinstance(value, str):
        return False
    try:
        checked = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    if checked.tzinfo is None:
        return False
    age = (now - checked.astimezone(timezone.utc)).total_seconds()
    return 0 <= age <= minutes * 60


def _host(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = urlparse(value)
    except ValueError:
        return None
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        return None
    host = parsed.hostname.lower()
    return None if host in SHORT_HOSTS else host.removeprefix("www.")


def _total(row: dict) -> Decimal | None:
    amounts = [_money(row.get(key)) for key in ("price", "shipping", "membership")]
    if any(value is None for value in amounts) or row.get("tax_included") is not True:
        return None
    return sum(amounts, Decimal("0"))


def _same_product(product: dict, row: dict, market: str) -> bool:
    return all((product.get(key) == row.get(key)) for key in ("gtin", "variant", "quantity", "unit")) and (
        row.get("market") == market and row.get("currency") == CURRENCY[market]
        and row.get("condition") == "NEW" and row.get("available") is True
    )


def _valid_offer(product: dict, row: dict, market: str, now: datetime) -> bool:
    if not isinstance(row, dict) or row.get("exact_match_reviewed") is not True or not _same_product(product, row, market) or _total(row) is None:
        return False
    network = row.get("network")
    host = _host(row.get("url"))
    affiliate_host = _host(row.get("affiliate_url"))
    if network == "amazon":
        # Amazon requires its lowest new price in cross-retailer comparisons.
        # A featured-offer price alone is insufficient. Used price is shown if
        # the authorised product-data method provides it.
        return (
            row.get("source_type") == "amazon_creators_api"
            and row.get("lowest_new_verified") is True
            and _money(row.get("lowest_new_price")) == _money(row.get("price"))
            and (row.get("used_price_provided") is False or
                 (row.get("used_price_provided") is True and _money(row.get("lowest_used_price")) is not None))
            and host == AMAZON_HOST[market]
            and affiliate_host == host
            and isinstance(row.get("asin"), str) and len(row["asin"]) == 10
            and f"/dp/{row['asin']}" in urlparse(row["url"]).path
            and f"/dp/{row['asin']}" in urlparse(row["affiliate_url"]).path
            and bool(parse_qs(urlparse(row["affiliate_url"]).query).get("tag"))
            and _time(row.get("checked_at"), now, 15)
        )
    if network == "ebay":
        return (
            row.get("source_type") == "ebay_browse_api"
            and row.get("marketplace") == EBAY_MARKET[market]
            and row.get("buying_option") == "FIXED_PRICE"
            and row.get("listing_status") == "ACTIVE"
            and host == f"ebay.com{'.au' if market == 'AU' else '.uk' if market == 'UK' else ''}"
            and affiliate_host in {host, "ebay.com", "rover.ebay.com"}
            and row.get("affiliate_url_from_api") is True
            and _time(row.get("checked_at"), now, 15)
        )
    return False


def _valid_baseline(product: dict, row: dict, market: str, now: datetime) -> bool:
    return (
        isinstance(row, dict) and _same_product(product, row, market)
        and row.get("exact_match_reviewed") is True
        and row.get("source_type") in {"licensed_retailer_feed", "reviewed_observation"}
        and isinstance(row.get("retailer"), str) and len(row["retailer"].strip()) >= 2
        and row["retailer"].strip().lower() not in {"amazon", "ebay"}
        and _host(row.get("url")) is not None
        and _total(row) is not None
        and _time(row.get("checked_at"), now, 24 * 60)
    )


def rank_top10(records: list[dict], market: str, now: datetime | None = None) -> dict:
    """Return at most 10 genuine positive same-item comparisons for a market.

    Empty/invalid input returns an empty list. It is never padded to ten.
    The returned payload is ephemeral and must be served with no-store headers.
    """
    if market not in CURRENCY:
        raise ValueError("market must be AU, US or UK")
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    ranked = []
    for product in records:
        if not isinstance(product, dict) or not isinstance(product.get("gtin"), str) or not product["gtin"].isdigit() or len(product["gtin"]) not in {8, 12, 13, 14}:
            continue
        if product.get("exact_match_reviewed") is not True:
            continue
        if not isinstance(product.get("label"), str) or not product["label"].strip() or not isinstance(product.get("variant"), str) or not product["variant"].strip():
            continue
        if not isinstance(product.get("quantity"), (int, float)) or isinstance(product["quantity"], bool) or not isfinite(product["quantity"]) or product["quantity"] <= 0 or product.get("unit") not in {"each", "g", "ml", "sheet", "page"}:
            continue
        baselines = [r for r in (product.get("baselines") if isinstance(product.get("baselines"), list) else []) if _valid_baseline(product, r, market, now)]
        if not baselines:
            continue
        # The comparison is against the cheapest verified non-marketplace
        # retailer, not a selectively high reference price.
        baseline = min(baselines, key=_total)
        base_total = _total(baseline)
        for offer in (product.get("offers") if isinstance(product.get("offers"), list) else []):
            if not _valid_offer(product, offer, market, now):
                continue
            offer_total = _total(offer)
            if offer_total >= base_total:
                continue
            saving = base_total - offer_total
            ranked.append({
                "market": market, "currency": CURRENCY[market], "gtin": product["gtin"],
                "label": product["label"], "variant": product["variant"],
                "quantity": product["quantity"], "unit": product["unit"],
                "network": offer["network"], "offer_price": str(_money(offer["price"])),
                "offer_total": str(offer_total), "other_retailer": baseline["retailer"],
                "other_total": str(base_total), "saving": str(saving),
                "saving_percent": str((saving / base_total * 100).quantize(Decimal("0.1"))),
                "offer_checked_at": offer["checked_at"], "other_checked_at": baseline["checked_at"],
                "offer_url": offer["url"], "other_url": baseline["url"],
                "affiliate_url": offer["affiliate_url"],
                "amazon_lowest_used_price": str(offer["lowest_used_price"]) if offer.get("used_price_provided") is True else None,
            })
    # Keep the best offer for each exact product, then rank by actual saving.
    ranked.sort(key=lambda r: (Decimal(r["saving"]), Decimal(r["saving_percent"])), reverse=True)
    unique = {}
    for row in ranked:
        unique.setdefault((row["gtin"], row["variant"], row["quantity"], row["unit"]), row)
    return {"market": market, "generated_at": now.isoformat(), "status": "verified" if unique else "no_verified_comparisons", "items": list(unique.values())[:10]}


if __name__ == "__main__":
    import argparse
    import json
    from pathlib import Path

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="reviewed local records JSON; never commit price snapshots")
    parser.add_argument("--market", choices=("AU", "US", "UK"), default="AU")
    args = parser.parse_args()
    data = json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        parser.error("input must be a JSON array")
    print(json.dumps(rank_top10(data, args.market), indent=2))
