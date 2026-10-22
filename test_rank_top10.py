"""Focused checks for unsupported and genuine same-item price claims."""

import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from rank_top10 import rank_top10
from awin_feed_inventory import joined_feeds
from ebay_live_candidates import fetch_candidates


NOW = datetime(2026, 10, 22, 3, 0, tzinfo=timezone.utc)


def row(**overrides):
    data = {
        "market": "AU", "currency": "AUD", "gtin": "9312345678901",
        "variant": "500 ml, blue", "quantity": 500, "unit": "ml",
        "condition": "NEW", "available": True, "exact_match_reviewed": True,
        "price": "10.00", "shipping": "0", "membership": "0", "tax_included": True,
        "checked_at": (NOW - timedelta(minutes=5)).isoformat(),
        "url": "https://www.ebay.com.au/itm/123456789012",
    }
    data.update(overrides)
    return data


class RankingChecks(unittest.TestCase):
    def test_ebay_probe_fails_closed_without_approved_keyset(self):
        with patch.dict("os.environ", {"EBAY_APP_ID": "", "EBAY_CERT_ID": "", "EBAY_EPN_CAMPAIGN_ID": ""}):
            with self.assertRaisesRegex(RuntimeError, "production keyset"):
                fetch_candidates("9312345678901", "AU")

    def test_awin_inventory_keeps_only_joined_market_feeds_without_urls(self):
        csv_text = ("Advertiser ID,Advertiser Name,Primary Region,Membership Status,Feed ID,Feed Name,Last Imported,URL\n"
                    "10,Shop A,AU,Joined,20,Main,2026-10-22,https://secret.example/key\n"
                    "11,Shop B,AU,Not Joined,21,Main,2026-10-22,https://secret.example/key\n"
                    "12,Shop C,GB,Joined,22,Main,2026-10-22,https://secret.example/key\n")
        result = joined_feeds(csv_text, "AU")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["advertiser"], "Shop A")
        self.assertNotIn("url", result[0])

    def test_empty_and_unverified_are_not_padded(self):
        self.assertEqual(rank_top10([], "AU", NOW)["items"], [])
        self.assertEqual(rank_top10([{"gtin": "9312345678901"}], "AU", NOW)["items"], [])

    def test_current_exact_ebay_offer_beats_cheapest_other_retailer(self):
        offer = row(network="ebay", source_type="ebay_browse_api", marketplace="EBAY_AU",
                    buying_option="FIXED_PRICE", listing_status="ACTIVE",
                    affiliate_url="https://www.ebay.com.au/itm/123456789012?campid=1234567890",
                    affiliate_url_from_api=True)
        expensive = row(retailer="Shop B", source_type="reviewed_observation", price="20.00",
                        url="https://shop-b.example/item")
        cheapest = row(retailer="Shop A", source_type="licensed_retailer_feed", price="15.00",
                       url="https://shop-a.example/item")
        product = {"gtin": offer["gtin"], "label": "Sample bottle", "variant": offer["variant"],
                   "quantity": offer["quantity"], "unit": offer["unit"], "exact_match_reviewed": True,
                   "offers": [offer], "baselines": [expensive, cheapest]}
        item = rank_top10([product], "AU", NOW)["items"][0]
        self.assertEqual(item["saving"], "5.00")
        self.assertEqual(item["other_retailer"], "Shop A")
        product["offers"][0]["checked_at"] = (NOW - timedelta(minutes=16)).isoformat()
        self.assertEqual(rank_top10([product], "AU", NOW)["items"], [])
        product["offers"][0]["checked_at"] = (NOW - timedelta(minutes=5)).isoformat()
        product["baselines"][1]["variant"] = "750 ml, blue"
        self.assertEqual(rank_top10([product], "AU", NOW)["items"][0]["other_retailer"], "Shop B")

    def test_amazon_featured_price_is_insufficient(self):
        amazon = row(network="amazon", source_type="amazon_creators_api", asin="B012345678",
                     url="https://www.amazon.com.au/dp/B012345678",
                     affiliate_url="https://www.amazon.com.au/dp/B012345678?tag=example-22",
                     lowest_new_verified=False, lowest_new_price="10.00", used_price_provided=False)
        other = row(retailer="Shop A", source_type="reviewed_observation", price="20.00",
                    url="https://shop-a.example/item")
        product = {"gtin": amazon["gtin"], "label": "Sample bottle", "variant": amazon["variant"],
                   "quantity": amazon["quantity"], "unit": amazon["unit"], "exact_match_reviewed": True,
                   "offers": [amazon], "baselines": [other]}
        self.assertEqual(rank_top10([product], "AU", NOW)["items"], [])


if __name__ == "__main__":
    unittest.main()
