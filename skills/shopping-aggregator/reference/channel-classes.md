# Channel classes, the demand-side coverage primitive

> **WHY this file exists.** The rest of the matrix (`sources-index.md`, `tools/registry.json`) is
> organized SUPPLY-SIDE, around data-access tools (MCPs / APIs / scrapers). A retailer with no tool
> (e.g. **Micro Center**: website only, no API/MCP/extension) is therefore structurally invisible to
> triage and to the refresh loop, it can only survive as prose buried in a shard, which no gate or
> sweep can see. This file is the DEMAND-SIDE counterweight: for a product, enumerate the **channel
> classes** a knowledgeable buyer would check, independent of whether a tool exists. A tool-less class
> is still a first-class channel; it just routes to the browser/scrape (④), and for store-only
> retailers to a **store-specific** scrape.
>
> This is a PRIMITIVE (channel *classes*), NOT a store directory. Add a row only for a distinct
> buyer-channel TYPE, never just because a new store exists.

## Step 2 use

At triage, after matching the access-method domains in `sources-index.md`, ALSO map the product to
the channel classes below and enumerate the concrete authorized retailers per class for the region.
A class with no connected tool is **not skipped**, it is covered via playwright / Bright Data (and,
for store-pickup retailers, a store-specific scrape for the buyer's ZIP). Any in-scope class you do
not actually take to a real read becomes a `not-attempted` coverage gap (guardrail #9).

## Classes (region = US; CN / cross-border analogues in parentheses)

| class | what it is | example retailers (NOT exhaustive) | typical route |
|---|---|---|---|
| mass-market marketplace | the everything-stores | Amazon, Walmart, Target, eBay | API/MCP + playwright |
| category-specialist authorized retail | deep-catalog authorized dealers for a category | **PC/parts: Micro Center, Newegg, B&H, Adorama, Central Computer** · beauty: Sephora, Ulta · audio: Crutchfield · outdoor: REI | mostly browser/scrape (few expose a tool) |
| brand-direct / DTC | the maker's own store / official Amazon storefront | brand.com · "Sold by `<brand>` Official" | browser; confirm it's the brand, not a 3P |
| warehouse / membership | member-priced bulk | Costco, Sam's Club, BJ's (CN: 山姆) | login-walled playwright or skip |
| local-pickup-only | per-store stock, no shipping | **Micro Center store**, Best Buy / Target / Walmart store pickup | **store-specific scrape by ZIP** (the chain page lies about local stock) |
| cross-border / import | overseas authorized or grey | YesStyle, Stylevana, AliExpress, Olive Young (US→CN: 海淘) | browser; flag customs + slow ship + authenticity |
| refurb / open-box | manufacturer / authorized refurbished | Amazon WHD, Best Buy Open-Box, brand-refurb | only if user said refurb-OK |
| price-comparison engine | meta-aggregators that index many merchants' offers for one product (esp. **EU**, where this is the dominant discovery layer) | **EU: Idealo (pan-EU: DE/AT/FR/ES/IT/UK), Geizhals (DACH, electronics/specs), PriceRunner (UK + Scandinavia)** · pan-region: Google Shopping (free listings) · (US analogue: BigGo / Google Shopping) | browser ④ (none expose a consumer price API); read the engine, then E1-confirm the winning merchant's own PDP |
| travel-booking / OTA | booking intermediaries + brand-direct for **lodging** (a distinct buyer-channel TYPE, not a store) | Booking, Expedia, Hotels.com, Priceline · brand.com (Hilton/Marriott/IHG) · Google Hotels (discovery only) | browser ④ (rate/availability live; **verify dates on the actual channel**, Google Hotels locks dates) |

> **price-comparison-engine is a DISCOVERY layer, not a price of record.** An engine's listed price is
> an indexed/cached offer, it can be stale, exclude shipping, or point at an unauthorized merchant.
> Use it to *enumerate* candidate merchants for a product+region (its real value in the EU, where no
> single everything-store dominates), then take the winning offer to **E1** on the merchant's own PDP
> before ranking it. Never rank a bare engine price as the winner. EU engine coverage verified 2026-06
> ([Idealo](https://en.wikipedia.org/wiki/Idealo),
> [EU comparison-site landscape](https://prisync.com/blog/europe-price-comparison-landscape/)).

## Coverage rule

For a buy intent, the channel classes IN SCOPE for that product + region define the **coverage
floor**: every in-scope class must be queried to **E1** depth (a real PDP / store read) or explicitly
listed as a `not-attempted` gap. "We checked Amazon + Newegg" is NOT complete if the product's
category also spans a category-specialist or local-pickup class that was never queried. This is the
structural fix for "completeness by omission."

## X1, channel-class ↔ shard coverage map

The two axes are orthogonal: classes (here) are DEMAND-side; shards (`domains/`) are SUPPLY/access-side.
This table is the bridge, for each class it names which shard(s) actually carry the read instructions,
and flags classes whose coverage is **tool-less / shard-thin** (must be taken via ④ browser, and counted
as a `not-attempted` gap if skipped). Use it to confirm an in-scope class is not silently uncovered.

| channel class | primary shard(s) | where it routes | coverage note |
|---|---|---|---|
| mass-market marketplace | `amazon-us` (+ EU/UK/JP locale section), `ebay-walmart-target` | API/MCP + ④ | best-covered axis |
| category-specialist authorized retail | (none dedicated) | ④ store-specific scrape | **shard-thin**, most expose no tool; read PDP directly |
| brand-direct / DTC | (none dedicated) | ④ | confirm it's the brand, not a 3P; shard-thin |
| warehouse / membership | `ebay-walmart-target` (Costco) | login-walled ④ or skip | partial |
| local-pickup-only | `grocery-cpg` (banner pickup) partial | ④ store-by-ZIP scrape | **shard-thin**, chain page lies on local stock |
| cross-border / import | `cross-border` (border layer) + origin shard (`taobao-tmall`/`jd-pdd`/`amazon-us`) | ④ + duty JSON | well-owned; dutiable by default |
| refurb / open-box | `amazon-us` (WHD), `ebay-walmart-target` | ④ | only if refurb-OK |
| **price-comparison engine** | `claude-mcps` (BigGo, US), `oss-self-host` (pricebuddy EU) partial; **EU Idealo/Geizhals/PriceRunner have NO dedicated shard** | ④ | **shard-thin for EU**, read the engine via browser, then E1 the merchant PDP. Non-US/CN regional routing → [`../sources-index.md`](../sources-index.md) regional note |
| **travel-booking / OTA** | `hotel-travel` | ④ | Booking.com is the spine; total-stay cost READ off the Your-Details `(NN% Tax)` line (never hard-coded) + separate parking research; Google Hotels discovery-only (date-lock). Flights/cars/trains OUT of scope |

## What this is NOT

- NOT a store directory, classes are the primitive; do not enumerate every retailer.
- NOT in `registry.json` / `tools/index.md`, those are TOOL primitives; channels are a separate axis
  (mixing them re-introduces the supply-side rigidity that hid Micro Center).
- NOT a refactor of the domain shards, this sits ABOVE them; shards stay access-method-oriented.

## Last verified: 2026-07
