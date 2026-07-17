# Tool: Bright Data Web Unlocker

- **Domain(s):** ebay-walmart-target, claude-mcps (as scrape infrastructure)
- **Barrier route:** ② resale · **Source tier:** L2 · **Ready MCP:** no (REST API + Web Unlocker proxy endpoint; Bright Data also ships an MCP server, verify status)
- **Cost:** **free tier 5K requests/mo** (no card) · pay-as-you-go **~$1.5/1K successful** · Scale **$499/mo → 383K included, then $1.3/1K** · Enterprise custom (volume-discounted), **success-based CPM**
- **Repo / Provider:** brightdata.com/products/web-unlocker (pricing: brightdata.com/pricing/web-unlocker · docs: docs.brightdata.com/scraping-automation/web-unlocker/features)
- **Top pick for its domain:** no, peer alternative to **Oxylabs** as higher-tier anti-bot scrape when Apify price-intelligence MCP / playwright stall

## What it does / when to pick it
Hosted "unblocker" proxy+API that takes a target URL and returns the unblocked page (handles Cloudflare / DataDome / PerimeterX / CAPTCHA / fingerprinting automatically). Same job class as Oxylabs E-Commerce: pick when the user needs **reliable scale on heavily-protected US retailers** (Best Buy, Walmart, Target, Footlocker) past what playwright MCP can sustain. Web Unlocker returns **raw HTML you parse yourself**, it is not a structured-product API (that's Bright Data's separate "Web Scraper API" / dataset products). Choose Web Unlocker for breadth (any URL), choose a structured scraper when you want pre-parsed price fields.

## Install
1. Sign up at brightdata.com → start the free trial (5K req/mo, no card).
2. In the dashboard create a **Web Unlocker** zone → get the zone name + API token.
3. Call via the proxy endpoint or the REST `request` API (see below).
4. (Optional) Bright Data publishes an MCP server, wire via `~/.claude.json` and verify with `claude mcp list` before fan-out.

## Auth / keys
API token (Bearer) + zone name from the dashboard. **Treat as secret**, pass via env var, never echo to transcript; agent reads `process.env.BRIGHTDATA_TOKEN` only.

## Usage, call examples
```
curl https://api.brightdata.com/request \
  -H "Authorization: Bearer $BRIGHTDATA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"zone":"web_unlocker1","url":"https://www.bestbuy.com/site/<id>.p","format":"raw"}'
```
Returns the unblocked HTML of the target page; parse price/title/availability yourself.

## General experience & gotchas (踩坑)
- **⚠ Billed for SOME failures, the success-only promise has an exception.** Standard Web Unlocker bills only **successful** requests, but when any **Custom Web Unlocker** feature is enabled (custom config), you are billed for **100% of requests, successful AND failed**. Don't assume free retries; check whether your zone has custom features on. (docs.brightdata.com features page.)
- **Premium domains cost more.** A predefined list of hard targets (bestbuy.com, footlocker.com, …) is billed at a higher per-1K rate when premium unlocking is enabled, only requests to those domains get the higher rate, others stay at base.
- **PAYG is the most expensive tier (~$1.5/1K)**; committing to Scale drops marginal cost to ~$1.3/1K. For one-off comparisons the free 5K/mo is usually enough, don't auto-upgrade.
- **You parse the HTML.** Unlike Oxylabs `source:walmart` structured mode, plain Web Unlocker hands back raw HTML; budget parsing effort or use Bright Data's structured products instead.
- **Geo / residential pools**, requests egress from Bright Data IPs; member-login walls (Costco) aren't solved by unblocking.
- **Scraping at scale is ToS-violating** for most retailers, Bright Data absorbs IP-ban risk; legal exposure still shifts to the user per their agreement. Read per-retailer ToS before commercial use.

## Failure signals & fallback
HTTP 4xx/5xx from the `request` API; returned page still showing a challenge/block; budget exhausted. **Fallback:** Oxylabs E-Commerce Scraper, Apify price-intelligence MCP, playwright MCP.

## Last verified: 2026-06
