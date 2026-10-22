# Vyonetix household tools

Small browser-only worksheets for everyday household decisions. [Open the tools](https://sudheer-vyo.github.io/vyonetix-household-tools/). No account is needed. Calculations and search inputs stay in your browser; the files contain no analytics, cookies, affiliate links, or retailer price fetches. The printer lookup loads a static, source-reviewed catalog from this repository.

## Tools

- [Four cost calculators](docs/tools.html): appliance electricity, meal cost per serving, bulk unit price, and printer cost per page.
- [Retailer comparison worksheet](docs/retailer_compare.html): explicitly choose AU, US, or UK; enter current prices for the same exact item and compare delivered cost per common unit.
- [Printer Error & Supply Desk](docs/printer/): search exact Australian printer model and error codes against the included manufacturer-sourced catalog; follow its source links before taking action.
- [Top 10 exact-item comparisons](docs/top10.html): a country selector and ranked-results view. Its public feed currently has no qualifying items. A local JSON review preview is available; it does not upload data.

The retailer worksheet uses only observations you enter. It requires a source, a check within 24 hours, and an exact-variant confirmation for each row. A lower calculated cost is not a verified discount or a guarantee of stock or checkout total.

`rank_top10.py` validates exact GTIN, variant, pack, condition, market, current marketplace price and the cheapest checked other retailer before showing at most ten positive differences. It does not pad a list or invent a discount. Run `python rank_top10.py reviewed-records.json --market AU` locally to preview approved records. Do not commit price snapshots to this static site. Amazon rows require an authorised Creators API lowest-new price and a registered Associates Site; the public GitHub Pages view suppresses Amazon price content until those conditions are verified. `awin_feed_inventory.py` lists joined product feeds using `AWIN_PRODUCT_FEED_API_KEY`; `ebay_live_candidates.py` queries eBay Browse by exact GTIN using a production keyset and EPN campaign ID. Both read secrets only from the local environment and return candidates for review, never published savings.

This release does not have live Amazon, eBay or other-retailer price access. Current product-data permissions and exact cross-retailer matches must be verified before a public top-10 list can contain items.

For guides and deals, visit [Vyonetix Deals](https://deals.vyonetixsolutions.com.au/) or subscribe to its [RSS feed](https://deals.vyonetixsolutions.com.au/feed/). Its commercial posts require individual current-offer checks before buying or resharing.

Join the [Vyonetix Deals Discord community](https://discord.gg/Qknnb6Hb3) to discuss tool results and household decisions. Verify any offer at the retailer before purchase.

## Status

This repository contains no private workspace files, API credentials, personal data, partner tags, or automated group posting code. The tools are original Vyonetix prototypes and are supplied without a general reuse licence until the owner chooses one. No live retailer prices or savings are claimed.

Source constraints: [Amazon Associates pricing and comparison rules](https://affiliate-program.amazon.com/help/operating/policies), [eBay Buy API production eligibility](https://developer.ebay.com/api-docs/buy/buy-requirements.html), and [Awin product-feed list access](https://help.awin.com/developers/docs/product-feed-list-download).
