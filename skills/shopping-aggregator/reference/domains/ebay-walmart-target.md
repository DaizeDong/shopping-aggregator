# Domain: ebay-walmart-target

**Triage signals:** US multi-retailer compare beyond Amazon, eBay, Walmart, Target, Best Buy,
Costco, Home Depot, Newegg, Micro Center. Also: "anywhere besides Amazon", "is there a better deal elsewhere".

| source | route | capability | detect | risk |
|---|---|---|---|---|
| **eBay Browse API** ([ebay-api.md](../tools/ebay-api.md)) | ① free | 5000 calls/day free; item search, lowest-price, Best Offer, condition filter | dev key + EPN signup for production | low; **only free cross-seller catalog API in the matrix** |
| **playwright MCP** | ④ | live page fetch for Walmart/Target/Best Buy/Costco, none of which expose a usable consumer API | almost always connected | low; consumer-scale OK |
| **BigGo MCP** ([biggo-mcp.md](../tools/biggo-mcp.md)) | ④ free | covers eBay + AliExpress + Amazon + Shopee + Taobao via single MCP | `claude mcp list` → `biggo ✓` | low; star count only 18, small project, watch for drift |
| **Apify price-intelligence MCP** ([apify-price-intelligence.md](../tools/apify-price-intelligence.md)) | ② paid | Amazon + Walmart + Target + eBay + Best Buy in one MCP | Apify token | $0.008,$0.15/call; **broadest paid coverage** |
| **Oxylabs E-Commerce Scraper** ([oxylabs.md](../tools/oxylabs.md)) | ② | Walmart/eBay/Target/Wayfair/Costco/HomeDepot/BestBuy +100 anti-bot scrape | API key | $49/mo trial, +$1.25/1k for JS render |
| Walmart Open API | ① |, | walmart.io closed to non-sellers | **✗ no consumer API**, only path is Impact.com affiliate (≤4%) for catalog feeds |
| eBay Finding API | ① |, |, | **✗ DECOMMISSIONED 2025-02-05**, use Browse API |
| Google Shopping (via SerpApi) | ② | cross-merchant SERP, 195 geos | SerpApi key | $25/mo 1k calls; SERP-level only (no SKU detail) |

**Default pick:**
- **eBay** → eBay Browse API (free) for catalog/lowest; playwright for the actual listing page.
- **Walmart / Target / Best Buy / Costco** → playwright MCP one subagent per retailer; if scale or
  reliability matters, switch to Apify price-intelligence MCP or Oxylabs.
- **For "is there a better deal anywhere" surveys** → BigGo MCP one call (covers 5+ retailers
  cheaply), then drill in with playwright on the winners.

## Real-run lesson

These retailers don't anti-bot as aggressively as Amazon. firecrawl/WebFetch sometimes work for
static product pages (Best Buy, Home Depot) but **fail on cart/coupon pages** (JS-heavy). For
anything beyond a sticker-price read, use playwright. Walmart and Target specifically use
DataDome (Walmart) / PerimeterX (Target), Bright Data Web Unlocker if you need scale.

## Per-retailer gotchas

- **eBay**: filter by condition (new/used/refurb/parts) + Best Offer + Buy-It-Now vs auction. A
  Buy-It-Now price the user thinks is "the price" may have a hidden Best Offer accepted at much
  lower for similar listings, check sold-listings filter for true market price.
- **Walmart marketplace**: 3rd-party sellers on walmart.com look identical to walmart-direct.
  Tier them by who sold-and-shipped. Some marketplace sellers are "ships from China" dropshippers
  with multi-week delivery and Chinese-quality knockoffs, explicit trust filter.
- **Target Circle**: requires login; in-store-only deals don't show online. Acknowledge gap.
- **Best Buy**: open-box deals are a separate page (bestbuy.com/site/open-box), often the best
  price for a specific store's stock; geo-restricted (only the store with the unit ships). **Best Buy
  Marketplace 3P**: a listing under bestbuy.com can be "Sold & shipped by <third party>" (a low-rated
  reseller), NOT Best Buy first-party, read the Sold-by field and tier per guardrail #5 (observed: a
  conspicuously cheap listing turned out to be a 3.7★ marketplace seller, not Best Buy first-party;
  price alone would have ranked it #1).
- **Costco**: requires membership; member-only prices behind login. playwright with logged-in
  session or skip.
- **Home Depot / Lowe's**: prices vary by zip code (regional pricing). Default to user's zip;
  state assumption.
- **Newegg**: marketplace dropshippers same issue as Walmart; trust filter mandatory.
- **Micro Center**: major US authorized PC-parts retailer, often the cheapest in-store on
  GPUs/CPUs/components. **PICKUP-ONLY (no shipping) + PER-STORE stock**, the chain-level page lies
  about local availability; query the SPECIFIC store page for the user's ZIP (the `storeid` goes in
  the URL, resolve it from the user's ZIP at run time, never assume a branch). codex web_search and
  BigGo both MISS per-store stock, a store-specific playwright / Bright Data scrape is the only
  reliable read. Landed cost has no shipping line but is gated on the user being near a store, flag
  if they aren't. (Observed on a scarce, high-demand GPU: the chain page showed nothing, while the
  store page for the buyer's own branch showed units on the shelf. "Not available" from the national
  page is not a finding, it is a query you have not run yet.)

## Affiliate hijack alert

Honey-style extensions can rewrite checkout affiliate links on Walmart/Target/eBay. If you're
giving the user "click this and save $X via referrer," verify the user wasn't already eligible
for the same price (extension claims a discount that was already public). See
`domains/browser-extensions.md` for the Honey 2026 trust crisis.

**Install guidance:** `../volatile/pricing-install.md` → ebay-walmart-target section.

## Last verified: 2026-06
