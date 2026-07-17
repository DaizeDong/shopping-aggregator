# Source reliability, what actually works, learned from real runs

> **WHY this file exists.** `tools/registry.json` says which sources EXIST. The domain shards say
> which ones to *try*. Neither says which ones **hold up when you pull on them**, that is only
> learned by running, and until now it was learned over and over. Real runs append observations to
> `live-runs.jsonl`, but that file is DATA: its lines record what a specific person priced, which
> retailer they bought from, and where it shipped, so it lives in the private data dir and never in
> this repo (`.dataclass.json`). This file is the half of it that *is* the tool: the failure modes,
> their signatures, and the fallback each one demands, with the shopping list removed.
>
> Read it at **Step 3/4** (route selection) and again at **Step 7** (before you write a
> `coverage_gap`, check whether it is a known structural gap or a new one).
>
> **What may be written here:** properties of a SOURCE or a RETAILER CLASS that hold regardless of who
> is shopping or for what. **What may never:** a product, a price, a region, a ZIP, an order, the
> things that make an observation *someone's*. If you cannot state the lesson without naming what was
> bought, it is not a lesson yet; leave it in the private file.

`last_verified: 2026-07`

## The one-paragraph version

Prefer a **live PDP read** over anything that summarizes one. Every source that *summarizes* prices
(cross-model web search, SERP snippets, cross-store aggregators) was observed to disagree with the
live authorized listing, always in the same direction, always *cheaper*, because summaries outlive
the prices they quote. Treat them as leads (`L5`/`E3`), never as the ranked answer. The
authoritative read is the retailer's own product page, fetched now.

## Route reliability, by source

| source | route | holds up for | fails at | do this instead |
|---|---|---|---|---|
| **Bright Data** (SERP + retailer scrape) | ③ scrape | The workhorse. Reaches live authorized PDP prices at `E1` across mainstream and niche retail alike. First choice when a listing must enter the ranking. | Pages that render the price in JS (see below), it returns the empty DOM, not the price. | Nothing; it *is* the fallback for most other sources. When it hits a JS page, drop to the retailer's own category/SERP listing + a price-history source and mark the row `E2`. |
| **Bright Data PDP read** on a marketplace | ③ scrape | Returns the **Sold-by / Shipped-by** field, which is what lets you settle `seller_tier` (first-party vs 3P) instead of guessing from the price. Read it every time, it is the input to the seller-identity gate. |, |, |
| **BigGo MCP** | ② MCP | Commodity SKUs with broad multi-store presence. | **Niche or low-volume SKUs: it returns ZERO.** An empty result is the same shape as "nobody sells this," and it is not the same fact. | Never read empty as *unavailable*. Fall back to a direct SERP + retailer scrape before concluding a product has no listings. |
| **Cross-model web search** (Codex `web_search` crossval) | ② MCP | A cheap breadth sweep, surfacing channels or retailers you did not think to check. | **Prices.** Observed on independent runs, in unrelated categories, to quote well *below* the live authorized listings. Model-summarized prices are stale by construction. | Fold results in as `L5` leads and re-verify each one at the PDP. Never let a crossval price enter the ranking or set the "cheapest" claim. |
| **Codex MCP** (as a call) | ② MCP |, | **It can hang indefinitely** (observed: a single call still open after ~2h, run abandoned). | Give it a wall-clock budget and treat it as **fail-soft**: crossval is a nice-to-have, never a blocking dependency. A run that cannot finish is worth less than a run with one fewer cross-check, say so in Coverage gaps and move on. |
| **Price-history sources** (Keepa / camelcamelcamel / 慢慢买) | ②/③ | The time axis, and a serviceable `E2` price when the live PDP is unreachable. | They are history, not stock. | Pair with a live read; never answer "is it in stock" from history. |

## Retailer-class access facts

These are properties of the storefront, not of any one product.

- **JS-rendered prices.** A number of brand-direct storefronts (and some manufacturer stores) inject
  the price client-side. A plain scrape returns **`$0` or an empty price node**, and `$0` is not a
  price, it is a failed read. Detect that signature explicitly, never let it into a table, and fall
  back to the retailer's category/SERP listing plus a price-history source, marking the row `E2`
  rather than `E1`. Silently reporting `$0` is the worst available outcome: it ranks #1.
- **Big-box sites host 3P marketplace sellers.** A conspicuously cheap listing on a major retailer's
  own domain is, more often than not, a third-party marketplace seller rather than the retailer's
  first-party stock, sometimes a poorly-rated one. Price alone will rank it #1 and be wrong. Read
  Sold-by/Shipped-by and apply the seller-identity gate before ranking, every time.
- **Pickup-only retailers key stock per store.** For store-only chains, the national product page can
  show nothing while a specific branch has units on the shelf. Availability is only answerable by
  scraping the **store-specific page** for the buyer's region. "Not available" from the national page
  is not a finding; it is a query you have not run yet.
- **Login-walled marketplaces.** Social/local marketplaces gate item pages behind a session, and
  accounts can be marketplace-ineligible on top of that. Without an authenticated session this class
  is **structurally unreachable**, a recurring, *known* `coverage_gap`. Declare it up front rather
  than re-discovering it; do not pretend the class was covered by a national estimate.
- **Used-listing titles misstate the spec.** Marketplace and classifieds titles routinely name a
  premium model or material that the listing's own body contradicts (a lookalike variant, a
  veneer-for-solid substitution, a lower model number). Confirm `variant_key` against the listing's
  **spec text and photos**, never the title. Also watch for multi-box products listed as one box ,
  a "(1/2)" in the title means you are buying half of something.
- **Manufacturer-official refurb is its own channel class** and reads cleanly at `E1` from the
  manufacturer's own outlet. It is *not* interchangeable with third-party remanufacturers, whose
  rebuild quality varies widely by shop; treat their trust tier as an open question to research, not
  an equivalence to assume.
- **Foreign brands are often rebadged for the domestic market.** A brand that appears to be
  grey-import-only may be licensed and sold in-market under a domestic partner's name, with a real
  domestic warranty. Search for the rebadged name before concluding "no authorized domestic channel."
- **Brand-direct is the authority on what is even sellable.** Aggregators and marketplaces will list
  configurations, sizes, and component combinations the manufacturer does not actually sell, or that
  are not physically compatible. When a cheaper combination depends on parts fitting together, the
  brand's own PDP is what settles it.

## A verified ZERO is a finding

Several classes (refurb / open-box / warehouse, local classifieds, resale apps) come back genuinely
**empty** for niche, heavy, or high-spec items. That is a real, reportable result, "this channel is a
dead end for this spec", and it is *not* the same as `coverage_gap`, which means "in-scope and I
could not reach it." Report the zero; do not quietly drop the channel from the table, and do not let
an unreachable channel masquerade as an empty one.

## Cross-border

Landed cost is computable end-to-end (source listing + a dated FX source + duty), but the **duty
regime is volatile and litigated**, it has changed materially inside the lifetime of this skill.
Never state a rate from memory: resolve every number to a row in `reference/data/` with its
`verified_date`, and re-verify live when the answer turns on it (CONSTITUTION I.7). The structural
gap worth naming up front: brands sold only through quote/contact-sales channels, or only in another
region, have **no domestic PDP to read**, that is a coverage gap no tool closes.

## Feeding this file

`reference/refresh-protocol.md` ranks the private observations with `tools/refresh_priority.py`. When
a sweep finds that a failure has recurred, same signature, different product, **that** is when it
graduates into this file, stripped to the source or retailer-class property. One run is an anecdote;
a repeat is a tool fact. A lesson that cannot be stated without naming what someone bought has not
been distilled yet, and does not belong here.
