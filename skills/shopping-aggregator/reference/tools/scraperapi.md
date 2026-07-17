# Tool: ScraperAPI

- **Domain(s):** ebay-walmart-target, claude-mcps (as scrape infrastructure)
- **Barrier route:** ② resale · **Source tier:** L2 · **Ready MCP:** no (REST/SDK; no first-party MCP as of 2026-06)
- **Cost:** **free tier 1,000 credits/mo** (5 concurrent); paid from **Hobby $49/mo = 100K credits** (≈$0.49/1K credits, but credits ≠ requests, see gotchas)
- **Repo / Provider:** scraperapi.com, acquired Traject Data (announced on their site 2026)
- **Top pick for its domain:** budget alternative to Oxylabs / Apify price-intelligence when the user wants the cheapest hosted anti-bot scrape and can tolerate lower success rates

## What it does / when to pick it
Hosted scrape API that rotates proxies + bypasses bot protection (Cloudflare/DataDome/PerimeterX) and returns raw HTML or, for some sites, structured JSON. Pick it as the **②-route budget option** when the user explicitly wants low cost over reliability, or for one-off / low-volume fan-out. For high-volume reliability prefer **Oxylabs**; for per-actor structured extraction prefer **Apify price-intelligence MCP**. Independent benchmark context: Scrapeway's **Jun 2026** run measured ScraperAPI at **~34% overall success across 12 sites (#6 of 8), ~5.5s avg, ~$3.23/1K requests effective**, so it is cheap-per-credit but the *effective* cost-per-success on hard targets is much higher.

## Install
1. Sign up at scraperapi.com → free 1,000 credits/mo (no card), or 7-day trial = 5,000 credits.
2. Get the API key from the dashboard.
3. Call the REST endpoint directly (no SDK required); Python/Node SDKs exist if wanted.
4. No first-party MCP, if you want it inside Claude, wrap the REST call yourself or call via Bash/WebFetch.

## Auth / keys
Single `api_key` from dashboard. **Treat as secret**, pass via env var, never inline in committed code.

## Usage, call examples
```
curl 'https://api.scraperapi.com/?api_key=APIKEY&url=https://www.walmart.com/ip/<id>&render=true&country_code=us'
```
- `render=true` runs JS (needed for Walmart/Target PDPs), costs extra credits.
- `country_code` for geotargeting (country-level geo only on Business $299+).
- Structured-data endpoints exist for a few sites (e.g. Amazon) returning JSON instead of HTML.

## Pricing (official pricing page, verified 2026-06)
- **Free**, 1,000 credits/mo, 5 concurrent, no card.
- **Hobby**, **$49/mo**, 100,000 credits, 20 concurrent, US & EU regions only.
- **Startup**, **$149/mo**, US & EU only.
- **Business**, **$299/mo**, all country-level geotargeting.
- **Scaling**, **$475/mo**, all geo + pay-as-you-go overage.
- **Enterprise**, contact sales, 5M+ credits, 200+ concurrent.
- Annual billing ≈ 10% off (Hobby ≈ $44/mo). Credits **do not roll over** (reset on renewal).

## General experience & gotchas (踩坑)
- **CREDITS ≠ REQUESTS, this is the trap.** 1 standard page = 1 credit, but **Amazon = 5**, **Google/Bing = 25**, **LinkedIn = 30**; **Cloudflare/DataDome/PerimeterX bypass = +10**; **JS render = +5 to 10**. An Amazon PDP with JS render = ~15 credits → the $49/100K-credit plan is only ~6,667 Amazon requests. **Always multiply credits by the per-site multiplier before quoting the user a budget.**
- **Low success on hard targets**, ~34% in the Jun 2026 Scrapeway benchmark. For Walmart/Target/Costco at scale, Oxylabs is more reliable; ScraperAPI is the cost-first, not reliability-first, pick.
- **Effective $/1K-success can dwarf the $/1K-credit headline**, cheap per credit, but retries on failures burn credits. Budget upward for protected sites.
- **Geo is gated**, only US/EU on Hobby+Startup; full country-level geotargeting needs Business ($299+).
- **No first-party MCP**, don't expect `claude mcp list` to show it; wire it as a Bash/curl call.
- **Scraping retailers is ToS-violating** for most targets, same legal caveat as Oxylabs; ScraperAPI absorbs IP-ban risk, not your legal exposure.

## Failure signals & fallback
HTTP 500 / `{"error": ...}` payloads, credit exhaustion (402), repeated empty HTML on protected sites. **Fallback:** Oxylabs E-Commerce (higher reliability), Apify price-intelligence MCP (structured per-actor), playwright MCP (free, low volume).

## Last verified: 2026-06
