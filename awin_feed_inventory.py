"""Read joined Awin product-feed availability without printing secret feed URLs.

Uses Awin's included publisher Product Feed List Download service. Set the
separate AWIN_PRODUCT_FEED_API_KEY in the process environment; never add it to
this repository. This inventories feeds only and makes no price claim.
"""

from __future__ import annotations

import csv
import io
import json
import os
from urllib.request import urlopen


def joined_feeds(csv_text: str, market: str) -> list[dict[str, str]]:
    if market not in {"AU", "US", "UK"}:
        raise ValueError("market must be AU, US or UK")
    region = {"AU": "AU", "US": "US", "UK": "GB"}[market]
    reader = csv.DictReader(io.StringIO(csv_text))
    rows = []
    for item in reader:
        if (item.get("Primary Region") or "").strip().upper() != region:
            continue
        if (item.get("Membership Status") or "").strip().lower() != "joined":
            continue
        feed_id = (item.get("Feed ID") or "").strip()
        advertiser_id = (item.get("Advertiser ID") or "").strip()
        if not feed_id.isdigit() or not advertiser_id.isdigit():
            continue
        rows.append({
            "feed_id": feed_id, "advertiser_id": advertiser_id,
            "advertiser": (item.get("Advertiser Name") or "").strip(),
            "feed_name": (item.get("Feed Name") or "").strip(),
            "last_imported": (item.get("Last Imported") or "").strip(),
        })
    return rows


def fetch_inventory(market: str) -> list[dict[str, str]]:
    key = os.getenv("AWIN_PRODUCT_FEED_API_KEY", "").strip()
    if not key or not key.isalnum():
        raise RuntimeError("AWIN_PRODUCT_FEED_API_KEY is missing or malformed")
    url = "https://productdata.awin.com/datafeed/list/apikey/" + key
    try:
        with urlopen(url, timeout=20) as response:
            body = response.read(5_000_001)
    except Exception as exc:
        # The request URL carries the API key, so never surface exception text.
        raise RuntimeError("Awin feed inventory request failed") from None
    if len(body) > 5_000_000:
        raise RuntimeError("Awin feed inventory exceeded the size limit")
    return joined_feeds(body.decode("utf-8-sig"), market)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--market", choices=("AU", "US", "UK"), default="AU")
    args = parser.parse_args()
    try:
        print(json.dumps({"market": args.market, "joined_feeds": fetch_inventory(args.market)}, indent=2))
    except RuntimeError as exc:
        parser.exit(2, str(exc) + "\n")
