# Tool: Oxylabs E-Commerce Scraper API

- **Domain(s):** ebay-walmart-target, claude-mcps (as scrape infrastructure)
- **Barrier route:** ② resale · **Source tier:** L2 · **Ready MCP:** no (REST API + their own MCP wrapper in private preview)
- **Cost:** $49/mo trial / ~24.5K requests; +$1.25/1K for JS render; pay-as-you-go available
- **Repo / Provider:** oxylabs.io/products/scraper-api/ecommerce
- **Top pick for its domain:** alternative to Apify price-intelligence MCP for higher-volume US retailer scrapes

## What it does / when to pick it
Hosted scrape API that handles anti-bot (Cloudflare/PerimeterX/DataDome) for Walmart, eBay, Target, Wayfair, Costco, Home Depot, Best Buy + 100 e-commerce sites. Pick when the user's use case needs **reliable scale** beyond what playwright MCP can give (>50 retailers fan-out, or repeated polling). Cost trade vs Apify: Oxylabs more reliable at high volume, narrower per-actor flexibility.

## Install
1. Sign up at oxylabs.io, take the $49/mo trial.
2. Get API username + password from dashboard.
3. Use REST endpoint: `https://realtime.oxylabs.io/v1/queries` with HTTP basic auth.
4. (Optional) Wire as a custom MCP via `~/.claude.json` (Oxylabs publishes their own MCP wrapper in preview; check status).

## Auth / keys
Username + password from Oxylabs dashboard. **Treat as secret** — pass via env var.

## Usage — call examples
```
curl -u 'USERNAME:PASSWORD' \
  'https://realtime.oxylabs.io/v1/queries' \
  -H 'Content-Type: application/json' \
  -d '{"source":"walmart","url":"https://www.walmart.com/ip/<id>","render":"html"}'
```
Returns rendered HTML + structured fields (price, title, availability).

## General experience & gotchas (踩坑)
- **Cost adds up with JS render** — +$1.25/1K. Walmart's product page is JS-heavy, so plan for JS-render-budget.
- **The free trial credits go fast** — $49 / ~24.5K requests at base price; ~10-15K at JS-render. For testing OK; for production budget upward.
- **Their MCP wrapper is newer** than Apify's — verify it's connected via `claude mcp list` before fan-out.
- **Geo-IP**: requests come from Oxylabs proxies (datacenter + residential pools); some retailers (Costco) require member login that proxies don't fix.
- **Scraping at scale is ToS-violating** for most retailers — Oxylabs absorbs the ban-risk on their proxy IPs but legal exposure shifts depending on user-agreement terms. Read the per-retailer ToS clauses before deploying for commercial work.

## Failure signals & fallback
HTTP 5xx on Oxylabs side (rare); 200 with `error: anti_bot_detected` payload; budget exhausted. **Fallback:** Apify price-intelligence MCP, Bright Data Web Unlocker, playwright MCP.

## Last verified: 2026-06
