# Three household tools: methods and limits

The [Vyonetix tool hub](https://deals.vyonetixsolutions.com.au/tools/) groups three free browser tools. Each begins with a household question and works without a retailer feed. This note makes the arithmetic and purchasing boundaries reviewable.

## Laptop battery part search

The [battery finder](https://deals.vyonetixsolutions.com.au/tools/battery-checker/) builds a retailer search from a laptop model, battery part number, or keyword. It does **not** infer a compatible battery from the text entered. Before buying, compare the exact part number, voltage, connector, physical dimensions and manufacturer guidance. A retail search result is a candidate, not proof of fit.

## Appliance electricity cost

The [electricity tool](https://deals.vyonetixsolutions.com.au/tools/electricity-cost/) uses the visitor's own power draw, daily use and tariff:

```text
daily kWh = watts × hours per day ÷ 1,000
monthly cost = daily kWh × days used in month × AUD per kWh
annual cost = daily kWh × 365 × AUD per kWh
```

For example, 100 W used for four hours each day for 30 days at A$0.30/kWh uses 12 kWh and costs an estimated A$3.60 for that month. This ignores standing charges, variable tariffs, solar exports and devices whose actual average draw differs from their label. A suitably rated plug-in meter may help measure actual use.

## Meal cost per serving

The [meal tool](https://deals.vyonetixsolutions.com.au/tools/meal-cost/) adds the cost of ingredients *used*, optional other meal costs, then divides by servings:

```text
cost per serving = (sum of ingredient costs used + other costs) ÷ servings
```

For example, A$2 of one ingredient plus A$3 of another divided into four servings gives A$1.25 per serving. If a recipe consumes half of a A$4 pack, the cost used is A$2. It does not fetch supermarket prices or account automatically for delivery, waste or time.

## Merchant links and data

The hosted pages may offer an optional, directly visible Amazon product search with an adjacent Associate disclosure. The live price and stock are shown by Amazon after the visitor clicks. A product-search link is not a verified deal, cheapest-price claim, compatibility guarantee or automated Amazon price feed. No merchant purchase is needed to use the calculators.

The GitHub Pages worksheets in this repository have no affiliate links or price fetches. The [hosted tools' RSS feed](https://deals.vyonetixsolutions.com.au/tools/feed.xml) announces useful page updates; subscribing does not create a browser push notification or a price alert.
