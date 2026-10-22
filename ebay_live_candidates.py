"""Fetch fresh eBay fixed-price candidates by GTIN for human exact-match review.

Requires an eBay production Browse API keyset and EPN campaign approval. Search
results alone never prove an exact variant, shipping total or a discount. No
response is cached, published or turned into a top-10 entry by this command.
"""

from __future__ import annotations

import base64
import json
import os
from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx

MARKETS = {"AU": "EBAY_AU", "US": "EBAY_US", "UK": "EBAY_GB"}
HOSTS = {"AU": "ebay.com.au", "US": "ebay.com", "UK": "ebay.co.uk"}


def _safe_host(value: object, expected: str) -> bool:
    try:
        parsed = urlparse(str(value))
        return parsed.scheme == "https" and parsed.hostname in {expected, "www." + expected} and not parsed.username and not parsed.password
    except ValueError:
        return False


def _safe_affiliate(value: object, expected: str) -> bool:
    try:
        parsed = urlparse(str(value))
        return parsed.scheme == "https" and parsed.hostname in {expected, "www." + expected, "ebay.com", "www.ebay.com", "rover.ebay.com"} and not parsed.username and not parsed.password
    except ValueError:
        return False


def fetch_candidates(gtin: str, market: str = "AU", limit: int = 10) -> list[dict]:
    if market not in MARKETS or not gtin.isdigit() or len(gtin) not in {8, 12, 13, 14} or not 1 <= limit <= 20:
        raise ValueError("use AU/US/UK, an 8/12/13/14-digit GTIN and limit 1–20")
    app_id = os.getenv("EBAY_APP_ID", "").strip()
    cert_id = os.getenv("EBAY_CERT_ID", "").strip()
    campaign = os.getenv("EBAY_EPN_CAMPAIGN_ID", "").strip()
    if not app_id or not cert_id or not campaign.isdigit() or len(campaign) != 10:
        raise RuntimeError("approved eBay production keyset and 10-digit EPN campaign ID are required")
    basic = base64.b64encode(f"{app_id}:{cert_id}".encode()).decode()
    try:
        with httpx.Client(timeout=15, follow_redirects=False) as client:
            auth = client.post("https://api.ebay.com/identity/v1/oauth2/token",
                               headers={"Authorization": "Basic " + basic},
                               data={"grant_type": "client_credentials", "scope": "https://api.ebay.com/oauth/api_scope"})
            auth.raise_for_status()
            token = auth.json().get("access_token")
            if not isinstance(token, str) or not token:
                raise ValueError("invalid token")
            response = client.get("https://api.ebay.com/buy/browse/v1/item_summary/search",
                                  params={"gtin": gtin, "filter": "buyingOptions:{FIXED_PRICE}", "limit": str(limit)},
                                  headers={"Authorization": "Bearer " + token,
                                           "X-EBAY-C-MARKETPLACE-ID": MARKETS[market],
                                           "X-EBAY-C-ENDUSERCTX": "affiliateCampaignId=" + campaign,
                                           "Accept": "application/json"})
            response.raise_for_status()
            data = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        # URLs, response bodies and token-bearing headers are never logged.
        raise RuntimeError("eBay Browse API request failed") from None
    checked_at = datetime.now(timezone.utc).isoformat()
    rows = []
    for item in data.get("itemSummaries", []):
        if not isinstance(item, dict) or not _safe_host(item.get("itemWebUrl"), HOSTS[market]):
            continue
        price = item.get("price") or {}
        affiliate = item.get("itemAffiliateWebUrl")
        rows.append({"market": market, "gtin_searched": gtin, "marketplace": MARKETS[market],
                     "item_id": item.get("itemId"), "title_for_review": item.get("title"),
                     "price_for_review": price.get("value"), "currency": price.get("currency"),
                     "item_url": item.get("itemWebUrl"),
                     "api_affiliate_url": affiliate if _safe_affiliate(affiliate, HOSTS[market]) else None,
                     "condition": item.get("condition"),
                     "checked_at": checked_at,
                     "review_status": "candidate_not_exact_match_or_delivered_total"})
    return rows


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("gtin")
    parser.add_argument("--market", choices=("AU", "US", "UK"), default="AU")
    args = parser.parse_args()
    try:
        print(json.dumps({"candidates": fetch_candidates(args.gtin, args.market)}, indent=2))
    except (ValueError, RuntimeError) as exc:
        parser.exit(2, str(exc) + "\n")
