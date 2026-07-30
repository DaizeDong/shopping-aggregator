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
- **Login-walled marketplaces are SESSION-GATED, not unreachable.** This entry previously called the
  class "structurally unreachable," and that framing was the bug: it turned a channel the operator
  could open in ten seconds into a permanent `coverage_gap`. The class is **S2**, one operator login
  away. Run the handoff ([`login-handoff.md`](./login-handoff.md)) before filing any gap, and type
  the gap `session-gated-declined` rather than `structurally-unreachable` when the answer is no.
  Genuinely S3 (no session helps): geo-blocked domains, dead domains, closed APIs, anything needing
  a commercial proxy pool.
- **The wall now reaches search itself, and it returns ZERO rather than an error.** A gated
  marketplace SERP renders its own shell, its filters, and a recommendation carousel, then reports
  "no results" for *everything*, including the bare category noun. **Always run a control query**
  before recording a zero; a zero control voids every zero from that platform for the run. Loading
  the homepage first to collect a full risk-control cookie set has been observed to change nothing,
  so do not spend a round on it. Related and worse: some mainstream commerce sites have extended the
  wall from search to the **PDP**, so holding a SKU id no longer implies you can read its price, and
  their price micro-APIs answer with internal-network addresses or dead endpoints from outside the
  region.
- **Search engines do not index gated commerce PDPs.** The usual bypass, find it on a SERP then open
  the direct URL, does not exist for this class: the major engines carry zero product pages for the
  gated C2C and mainstream-commerce sites. Engine-based discovery works for **content** sites (video,
  blog, wiki, deal-aggregator communities) and systematically fails for gated commerce. Budget
  accordingly instead of re-trying keywords.
- **Forwarding / daigou agents are not a read bypass.** Their product search and their paste-a-URL
  rendering sit behind the same login, and their supported-platform list can exclude a large
  retailer outright, which kills the *purchase* path independently of stock. What is often anonymous
  on those sites is the **freight calculator**, and that is worth reading on its own for landed cost.
- **Price-history sites can inherit the wall** (their own social login required before a curve
  renders for a gated retailer), so they are S2 too rather than a route around it.
- **Auction sold-comps views have moved from open to gated.** "Sold comps are free and open" is an
  expired fact; check it, do not assume it, and do not spend many rounds on bypasses once a first
  one redirects to sign-in.
- **Used-listing titles misstate the spec** (merged into "What a listing page says versus what is
  true" below, kept here as the retailer-class instance). Marketplace and classifieds titles routinely
  name a premium model, size, or material that the listing's own body contradicts. Also watch for
  multi-box products listed as one box: a "(1/2)" in the title means you are buying half of something.
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

## The browser is one shared instance, plan the fan-out around it

Independent of any retailer: the browser MCP is commonly **a single browser shared by every subagent
in the session**, whatever isolation flags are set. Observed with eight parallel agents: tabs
navigated away or closed under each other more than a dozen times over one run.

- **What survives contention:** atomic `newContext()` / `newPage()` per call, open, extract, close.
  Every agent that adopted this pattern reported clean, uncontaminated data.
- **What does not:** addressing tabs by index, and **heavy in-page JS evaluation**. Hand-rolled
  signed API calls from inside the page have been observed to hang **silently until the MCP idle
  timeout** (tens of minutes, zero output, no error). Read the rendered page instead.
- **What is impossible:** a login handoff inside a parallel subagent. A sibling steals the tab
  mid-login and the session is gone. Serialize gated work into the main session.
- **Budget implication:** retries against a contended browser are not free, they are the single
  largest observed time sink in a fan-out run. One control query beats eleven keyword retries.

## Reading a search result page

Absorbed here: the old "a verified ZERO is a finding" entry, plus the paging and endpoint failures
that produce the same symptom. They belong together because **one rendered grid can mean four
different things**, and telling them apart is the whole skill:

| what you see | what it can mean | how to tell |
|---|---|---|
| rows | the market | page until new ids stop |
| rows | **only the top of the market** | diff id sets across pages (#12) |
| "no results" | genuinely nothing for this spec | control query returns rows (#11) |
| "no results" | gated, or a broken endpoint | control query **also** returns zero |

- **A verified ZERO is a finding.** Several classes (refurb / open-box / warehouse, local classifieds,
  resale apps) come back genuinely **empty** for niche, heavy, or high-spec items. That is a real,
  reportable result, "this channel is a dead end for this spec", and it is *not* the same as
  `coverage_gap`, which means "in-scope and I could not reach it." Report the zero; do not quietly
  drop the channel, and do not let an unreachable channel masquerade as an empty one.
- **A brand's own in-store search can be the broken one.** A legacy per-shop search endpoint has been
  observed to **ignore its keyword parameter entirely** and serve the empty state for every term,
  byte-identically, while the shop's full catalogue sat one click away behind its all-products
  listing. Believing it inverts the conclusion, from "the brand still sells this, cheaper than every
  reseller" to "the brand discontinued it." The control query catches it; nothing else does. Same
  family as the query-parameter naming trap (a site whose search needs `query1=` and returns zero for
  `query=`): **the site is healthy, your URL is wrong**, and only a control query distinguishes that
  from out of stock.
- **Paging mechanisms are not guessable, and one of them lies.** Observed in a single run: a URL page
  param that works; a **URL page param that is silently ignored while still rendering a full grid of
  page-one rows**; and paging that only advances by clicking numeric controls. Judge pages by **new
  ids**, never by returned count. Trusting an ignored page param is worse than not paging: it
  manufactures false coverage.
- **Depth payoff varies wildly by site and cannot be predicted.** The same query, same run: one
  marketplace went 30 to 270 unique items across nine pages and surfaced a lower floor price; another
  went 46 to 47 and surfaced nothing. Measure it, do not assume either way, and state the depth
  reached next to any "cheapest" claim.
- **Sorting is part of depth.** A relevance-sorted first page is not a price-sorted one. Either page
  deep enough to reach the band's floor or sort by price, and say which you did.

## What a listing page says versus what is true

- **The stock attribute lies more often than the buy box.** Structured "in stock" parameters and
  search-card stock badges have been observed on listings whose own fulfilment text said preorder,
  30 days. Rank on the fulfilment promise.
- **Reseller spec blocks are frequently copy-pasted from a sibling product**, yielding a 400mm item
  declared as 40mm, the wrong character name, and a 1/1 scale on a 1/12 piece, all on one page. When
  the spec block contradicts the SKU option string, the **option string wins**, and that seller's spec
  block is no longer usable as an independent source anywhere on the page.
- **A SKU can hide inside a multi-SKU collection listing** whose title names entirely different
  products, making it invisible to product-level search and to any results-page scrape. Open the
  collection and enumerate its option strings; **the option list is the real catalogue.** This is how
  a brand flagship can appear to have stopped selling an item it still sells.
- **Promotions: a PDP lists what EXISTS, the order-confirm page shows what STACKS.** Conditional
  offers (new-customer credits, threshold discounts, account-level vouchers) cannot be resolved from
  the PDP. Quote a range with the conditions named, and say when the confirm page was not reached.

## Cross-border

Landed cost is computable end-to-end (source listing + a dated FX source + duty), but the **duty
regime is volatile and litigated**, it has changed materially inside the lifetime of this skill.
Never state a rate from memory: resolve every number to a row in `reference/data/` with its
`verified_date`, and re-verify live when the answer turns on it (CONSTITUTION I.7). The structural
gap worth naming up front: brands sold only through quote/contact-sales channels, or only in another
region, have **no domestic PDP to read**, that is a coverage gap no tool closes.

Three route facts that recur:

- **Volumetric weight, not actual weight, sets the freight.** For anything with an edge over ~30cm,
  compute `L x W x H / divisor` **before** quoting a forwarding cost; a large hollow item bills at
  3 to 5 times its actual weight and the freight can exceed the item price. Divisors differ per
  carrier and per service on the same carrier (5000 / 5500 / 6000 / 8000 have all been observed
  side by side), so read the carrier's own divisor rather than assuming one. Small-parcel intuition
  ("forwarding runs $70 to $110") is the wrong prior for this class and has been observed to
  understate the real quote by 30% to 100%.
- **Box dimensions are a first-class landed-cost input for oversized goods**, and they are usually
  only stated on a retailer PDP, not the brand page. Two plausible box sizes for the same item can
  swing the freight quote by 2x, which is enough to reorder the ranking. Read them at `E1` or stamp
  the freight line `(assumed)`.
- **Sea freight is routinely the cheapest option by a wide margin for bulky, low-value, non-urgent
  goods** and is frequently absent from forwarder marketing. Where a forwarder exposes a rate API,
  it may be **anonymous even when its product pages require login**, so a route can be priced
  exactly while the purchase path is unavailable. Also check the site's own FX rate: a forwarder
  quoting in one currency while charging in another adds a spread on top of the freight.

**Tariff schedules: verify list membership against the primary schedule, never a summary.** Two
independent tariff-summary sites gave two different rates for the same category, and both were
wrong: the goods were on **no** active list, because the list containing them was announced and then
suspended before it ever took effect. Parsing the customs authority's own published mapping settled
it. Secondary tariff sites do not model "announced but never in force," so on any question where the
duty drives the decision, resolve to the primary schedule.

## Feeding this file

`reference/refresh-protocol.md` ranks the private observations with `tools/refresh_priority.py`. When
a sweep finds that a failure has recurred, same signature, different product, **that** is when it
graduates into this file, stripped to the source or retailer-class property. One run is an anecdote;
a repeat is a tool fact. A lesson that cannot be stated without naming what someone bought has not
been distilled yet, and does not belong here.
