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
| **C2C / social secondhand** | person-to-person resale apps, where the *seller is an individual*, distinct from auction-house and consignment resale. Often the only channel carrying a discontinued or region-exclusive item at all | Mercari, Poshmark, Depop, Facebook Marketplace, Craigslist · CN: 闲鱼/goofish, 转转, 得物, 微店 | **④ and almost always S2 session-gated**, see [`login-handoff.md`](./login-handoff.md). Search itself is walled and returns zero rather than an error; engines do not index these PDPs. Never file as unreachable before the operator has been offered the handoff |
| **offer-brokerage / name-your-price** | intermediaries where the buyer NAMES a price and **authorized** dealers privately accept or counter. The only channel that legitimately transacts BELOW MAP while keeping the full manufacturer warranty, because MAP binds the *advertised* price, not the transacted one | GreenToe (US: cameras, TVs, watches, appliances, optics) | ④, but the transacted price is **never published**: it cannot be read off a page, only elicited by submitting an offer |

> **price-comparison-engine is a DISCOVERY layer, not a price of record.** An engine's listed price is
> an indexed/cached offer, it can be stale, exclude shipping, or point at an unauthorized merchant.
> Use it to *enumerate* candidate merchants for a product+region (its real value in the EU, where no
> single everything-store dominates), then take the winning offer to **E1** on the merchant's own PDP
> before ranking it. Never rank a bare engine price as the winner. EU engine coverage verified 2026-06
> ([Idealo](https://en.wikipedia.org/wiki/Idealo),
> [EU comparison-site landscape](https://prisync.com/blog/europe-price-comparison-landscape/)).

> **offer-brokerage prices cannot be READ, only ELICITED, and eliciting one is a commitment.** This
> class exists wherever a manufacturer enforces MAP (camera, TV, watch, appliance), which is exactly
> where every visible retailer quotes the identical number and a run looks finished at that number.
> Three rules. **(1)** The broker's own "lowest online" table is an **affiliate placement**, not a
> price of record; guardrail #10 applies to it. Observed: a broker cited a first-party retailer $300
> under that retailer's live price, on a link carrying the broker's own affiliate tag. **(2)** An
> offer is typically a **firm, irrevocable commitment** that auto-charges on acceptance, and the
> return may carry a restocking fee the accepting retailer sets, so this class cannot be taken to E1
> the way a PDP can. **(3)** The agent **NEVER submits an offer** (CONSTITUTION V.4). Cover the class
> by naming the broker, a calibrated offer band, and the commitment caveat. Calibrate the band from
> the brand's observed discount depth, not from the broker's displayed anchor, which is the number
> most likely to be stale.

## Coverage rule

For a buy intent, the channel classes IN SCOPE for that product + region define the **coverage
floor**: every in-scope class must be queried to **E1** depth (a real PDP / store read) or explicitly
listed as a `not-attempted` gap. "We checked Amazon + Newegg" is NOT complete if the product's
category also spans a category-specialist or local-pickup class that was never queried. This is the
structural fix for "completeness by omission."

**Each in-scope class also carries an ACCESS STATE (S1/S2/S3, SKILL.md Step 3b).** The class being
in scope says it must be covered; the access state says *how*, and whether the operator has to open
a door first. A class that is **S2 session-gated** is NOT a gap until the operator has been offered
the login handoff and declined ([`login-handoff.md`](./login-handoff.md)), and its gap reason is
typed `session-gated-declined`, never `structurally-unreachable`. The C2C class above is the one
that is S2 by default, which is exactly why it kept getting written off.

**One class cannot reach E1 without spending the operator's money.** An offer-brokerage price does
not exist until a binding offer is placed, so for that class alone a named broker plus a calibrated
offer band plus the commitment caveat IS the covered state. Placing the offer is the operator's
action, never the agent's, and a declined handoff is typed `not-attempted`, never
`structurally-unreachable`.

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
| **offer-brokerage / name-your-price** | (none dedicated) | ④ | **shard-thin**; in scope only for MAP-controlled categories. The price is not on the page, so "covered" means a named broker + a calibrated offer band + the commitment caveat, not a read. Agent never submits the offer |

## What this is NOT

- NOT a store directory, classes are the primitive; do not enumerate every retailer.
- NOT in `registry.json` / `tools/index.md`, those are TOOL primitives; channels are a separate axis
  (mixing them re-introduces the supply-side rigidity that hid Micro Center).
- NOT a refactor of the domain shards, this sits ABOVE them; shards stay access-method-oriented.

## Last verified: 2026-08
