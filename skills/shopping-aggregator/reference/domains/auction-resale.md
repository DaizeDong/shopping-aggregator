# Domain: auction-resale

**Triage signals:** secondhand / resale / "what's it actually worth", **eBay sold comps** ("how
much do these sell for", fair-market value, "is this a good resale price"), sneakers/streetwear
resale (StockX, GOAT), live-auction commerce (Whatnot), peer-to-peer used marketplaces (Poshmark,
Mercari, Depop, ThredUp). Also: "should I buy used", "what's the going rate", "comps for <item>".

> This domain is about **realized market value of used/collectible goods**, the price something
> *actually changed hands for*, not the sticker price of new retail (that's `amazon-us` /
> `ebay-walmart-target`). The signature read here is a **sold-comp distribution**, not a single
> Buy-It-Now number.

| source | route | capability | detect | risk |
|---|---|---|---|---|
| **eBay public Sold SERP** (`?LH_Sold=1&LH_Complete=1`) | ④ | the only **free, no-approval** path to realized eBay sale prices; 90-day window; same page markup as active search | append `&LH_Sold=1&LH_Complete=1` to any `ebay.com/sch/i.html?_nkw=` URL; playwright/scrape the SERP | low at consumer scale; **green price = sold, red = ended unsold**; ToS gray, anti-bot at scale (keep <20 req/min/IP) |
| **eBay Marketplace Insights API** | ① | structured sold/realized-price comps via API | **Limited Release**, production access gated, per-vertical approval, frequently DENIED to independents | **✗ for most builds**, not generally available; default to the public Sold SERP instead |
| **StockX Public API v2** | ① | catalog search + sell + product market data; OAuth2 + `x-api-key`; base `api.stockx.com/v2` | apply at developer.stockx.com, app review (can be declined for thin sites) | gated approval + browser-based auth (PerimeterX) makes token automation hard; **has an official API, contrary to common belief** |
| **GOAT** | ① | n/a | no official public API (GitHub org is internal tooling only) | **✗ no official API**, only 3P scrapers (Retailed.io, Apify) or unofficial reverse-eng libs (Sneaks-API), all break-prone |
| **Whatnot Seller API** | ① | seller inventory mgmt + sale notifications | developers.whatnot.com, **Developer Preview, NOT accepting new applicants** | **✗ closed** + seller-only (no buyer/market-data scope); for market reads use playwright or 3P Apify scraper |
| **Poshmark** | ④ | live listings + sold flag; brand/size/condition in unstructured seller text | no official API at all; playwright the marketplace | **✗ no official API**; sold shown but not a clean field; moderate anti-bot; condition free-text (NWT/EUC/"like new") |
| **Goofish / 闲鱼** (CN, Alibaba) | ④ | China's largest C2C resale market; also the default channel for grey/virtual goods (API quota, accounts, kuji prizes). Search needs a logged-in session; the web SPA renders **only the first 30 rows**, deeper pages come from its own mtop endpoint (see below) | `goofish.com`; playwright +阿里系 cookies in the context | medium; login-walled search, per-seller listing spam distorts page 1 |
| **Mercari** | ④ | live US listings; client-side rendered + Cloudflare | **Mercari Shops API** is contract-only (assigned `API_CLIENT_NAME`); no public consumer API | **✗ no public consumer API**; needs browser automation (CSR + Cloudflare); unofficial libs get AWS IPs blacklisted |
| **Depop Selling API** | ① | official Selling API (API-key / OAuth2) | **private**, partner approval via partnerapi.depop.com only | **✗ not self-serve**; for reads, playwright or 3P scraper (ScrapingBee/Oxylabs) |
| **ThredUp** | ④ | live thrift listings | no public dev API; **RaaS** is B2B-only (raas.thredup.com) | **✗ no public API**; obfuscated CSS classes; scrape via playwright |

**Default pick:**
- **"What's it worth" / fair-market comps (the most common ask)** → **eBay public Sold SERP**
  (`&LH_Sold=1&LH_Complete=1`) via playwright. It is the single free, no-approval, broadest realized
  -price source in the whole matrix. Report the **distribution** (low/median/high of last-90-day
  solds), not one number; drop reds (ended-unsold).
- **Sneakers/streetwear** → **StockX Public API v2** if you have an approved key (it IS public,
  unlike GOAT); otherwise playwright StockX/GOAT product pages for last-sale + bid/ask.
- **Poshmark / Mercari / Depop / ThredUp / Whatnot** → **playwright MCP, one subagent per
  platform**, none has a usable public read API; treat sold/condition as parsed-from-page, low
  structured-trust.

## Real-run lesson

The recurring trap is treating an **asking price as a market price**. A live listing (eBay BIN,
StockX ask, Poshmark listing) is what a seller *wants*; the only decision-grade number is a
**realized sale**. Always anchor on sold comps:
- eBay: the Sold SERP green prices.
- StockX/GOAT: "last sale" field, not the lowest ask.
- Poshmark/Mercari: the sold/SOLD-tagged listings, not active ones.

A single sold comp is noise, pull the **last-90-day distribution** and report median + range.
Condition stratifies value heavily on these platforms (new/NWT vs used vs parts), never blend a
deadstock comp with a beat-up one.

## Per-platform gotchas

- **eBay Sold SERP**: 90-day window only, older sales vanish. ~10,000-result cap (~42 pages at
  `_ipg=240`). `_sop=13` sorts newest. **Green = confirmed sale, red = ended without selling**,
  filter reds out or your "median" is fiction. The Marketplace Insights API would give this
  structured but production access is gated/denied to most, do **not** assume you can get it.
- **StockX**: it genuinely has an official v2 API (many guides wrongly say "no public API"), but
  app review can reject thin/new sites, and PerimeterX bot detection makes headless token refresh
  painful. "Lowest ask" ≠ market; use **last sale**. Prices already net of StockX's buyer/seller
  fees in some views, state which.
- **GOAT**: no official API. 3P scrapers (Retailed.io, Apify) and unofficial libs (Sneaks-API)
  exist but ride GOAT's private endpoints and break on their changes, flag staleness risk.
- **Whatnot**: live-auction; prices are bid-driven and ephemeral. Seller API is preview-closed and
  buyer-blind. For "what did X sell for in a Whatnot stream" there is no clean source, playwright
  the past-stream/listing or use a 3P Apify scraper, mark evidence low.
- **Poshmark**: heavy social/feed layer; "offers" and bundle discounts mean the listed price often
  isn't the transaction price. Sold tag exists but condition is free-text, normalize NWT/EUC/etc.
- **Mercari**: client-side rendered + Cloudflare → plain HTTP/WebFetch fails, **must** use
  playwright (browser that waits for DOM). Unofficial Python lib warns AWS IPs are blocked.
- **Depop**: Gen-Z fashion; official Selling API is partner-gated (email approval), not for reads.
  Listings skew vintage/one-of-a-kind, so "comps" are weak, similar-item bands, not exact matches.
- **ThredUp**: managed-consignment thrift (ThredUp owns the inventory, not P2P), so listings are
  one-off SKUs, there's rarely a comp set; treat as single-unit pricing. RaaS is B2B only.

## Trust & evidence note

Realized-resale value is **inherently noisy**, wide variance by condition, authentication,
season, and hype cycle. Per CONSTITUTION III.2, any specific "it's worth $X" claim MUST cite the
sold-comp source (the eBay Sold SERP URL / StockX last-sale read) + date; never assert a resale
value from memory. When only asking prices are reachable (no sold data), mark **evidence low** and
say so explicitly ("asks only, no realized comps") rather than implying a market price. Sneaker
authenticity/condition fraud is real, StockX/GOAT authenticate, P2P platforms (Poshmark, Mercari,
Depop) do not; flag that gap when a high-value used buy routes through an unauthenticated P2P seller.

## Goofish (闲鱼) deep pagination, the mtop route

The web SPA is a **coverage trap**: `goofish.com/search?q=` renders exactly **30 rows**, has no
pagination control, does not infinite-scroll, and **silently ignores `&page=N`** (page 2 returns a
byte-identical result set). Scrolling to the bottom adds nothing. A run that stops there reports
30 of what are often thousands of listings while looking complete.

The page itself pages through its own mtop endpoint. Drive that instead:

```
api : mtop.taobao.idlemtopsearch.pc.search   v: 1.0
data: { pageNumber, keyword, rowsPerPage: 30, fromFilter: false,
        sortField: "", sortValue: "", propValueStr: {}, extraFilterValue: "{}",
        customDistance: "", gps: "", customGps: "", userPositionJson: "{}",
        searchReqFromPage: "pcSearch" }
```

Three things decide whether this works:

1. **`type: 'POST'`, not `method: 'POST'`.** In `lib-mtop`, `type` is the HTTP-verb slot. Any other
   spelling fails with `UNEXCEPT_REQUEST::错误的请求类型`, which reads like a payload problem and
   sends you debugging the wrong thing.
2. **Call it from the page context** (`window.lib.mtop.request`) so the library signs the request.
   Hand-rolling the `sign` means reproducing the token-plus-timestamp MD5 scheme; borrowing the
   page's own library avoids that entirely.
3. **Session cookies must be in the context.** Anonymous search returns a login modal over the
   results, not results.

Paging control lives in `data.resultInfo.searchResControlFields`: `numFound` (total hits, use it to
state real coverage) and `nextPage` (stop condition). Items are under `data.resultList[]`, with the
useful fields at `.data.item.main.exContent` (`itemId`, `title`, `price`, `userNickName`, `area`).
`price` is sometimes an array of segments, join them.

### Throttling: a per-API quota, not a rate limit, and not a ban

Measured, and the distinction changes what you do about it:

- **It is a quota on cumulative calls, not a rate.** ~0.45s spacing was fine for the first ~136
  calls; past roughly 200 in one session *every* search call failed. Slowing to 2.5s afterwards did
  **not** restore it, so "space the requests out" alone does not buy more depth.
- **The punishment is a black hole, not an error code.** The call hangs until your own client
  timeout fires (`TIMEOUT::接口超时` at exactly the configured ms). There is no 429 and no retry
  header, so retry-with-backoff burns wall-clock and recovers nothing.
- **It is scoped to this one API, not the session.** While search was black-holed,
  `mtop.idle.web.user.page.nav` and `mtop.taobao.idlemessage.pc.loginuser.get` both returned
  `SUCCESS` in **244 to 497ms** on the same context. Cookies, login and IP were fine. So do NOT
  respond by rotating profile, re-logging-in, or assuming the account is flagged, none of that is
  the problem and re-logging a risk-controlled account has its own cost.
- **Recovery is slow.** Still black-holed tens of minutes later.

**Use latency as the early-warning signal.** A healthy search call answers in a few hundred ms in
the same range as those other endpoints. Track a rolling latency; when a call crosses ~5s, you are
at the edge of the quota, **stop immediately and bank what you have** rather than pushing into the
penalty window. Budget **under ~100 search pages per session** with 2 to 3s spacing, and when a
sweep needs more coverage than that, split it across sessions or time windows instead of going
deeper in one run. Prefer few keywords deep over many keywords shallow when the two compete.

`sortField` / `sortValue` are exposed by the same call, so server-side sorting (e.g. by price) is
available without client-side re-ranking.

## Coverage lesson: page 1 is not a sample, it is a biased one

A single-seller listing spam is normal on C2C marketplaces, and it concentrates on page 1. In a real
run, one price point looked like multi-seller consensus across the first page; deep paging showed
**two accounts had posted 14+ near-identical listings**. Ranking off page 1 would have reported a
manufactured price as the market rate.

So: **never infer a market rate from one page**, and always group by seller before treating repeated
prices as corroboration. Two listings from the same nickname are one data point, not two. Where a
platform hides its pagination (as above), finding the real pager is part of the job, not an optional
extra, and `numFound` belongs in the report so the reader can see coverage as a fraction.

**Install guidance:** `../volatile/pricing-install.md` → auction-resale section.

## Last verified: 2026-07
