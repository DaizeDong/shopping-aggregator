# Tool: clucraft/PriceGhost

- **Domain(s):** oss-self-host
- **Barrier route:** ④ self-host · **Source tier:** L4 · **Ready MCP:** no
- **Cost:** free OSS; BYO LLM key + hosting
- **Repo / Provider:** github.com/clucraft/PriceGhost (~641★, last commit 2026-02-03, MIT), TypeScript
- **Top pick for its domain:** alternative to pricebuddy for **broadest retailer coverage**

## What it does / when to pick it
Self-hosted price tracker with **multi-strategy scraping**: tries JSON-LD → meta tags → CSS selectors → headless browser → LLM fallback, in that order. Pick when user has a wide retailer mix (Amazon US/UK/DE, Best Buy, Walmart, Target, Costco, eBay, Newegg, Home Depot, AliExpress) and wants the system to figure out the right scrape approach per site.

## Install
```bash
git clone https://github.com/clucraft/PriceGhost.git
cd PriceGhost
cp .env.example .env  # configure LLM, retailers, alerts
docker compose up -d
```

## Auth / keys
LLM key (OpenAI/Anthropic/Gemini/Ollama). Optional alert webhooks.

## Usage, call examples
N/A for agent, external service.

## General experience & gotchas (踩坑)
- **The multi-strategy fallback chain is the killer feature.** JSON-LD works on most modern e-com sites (no scraping needed); CSS selectors on older sites; headless+LLM on hostile sites. Less manual selector tuning vs pricebuddy.
- **TypeScript stack**, easier to extend if user is JS-native.
- **Slightly less active than pricebuddy** (Feb vs Jun last commit), watch for staleness.
- **Same anti-bot limit at scale** as all OSS, pace your polling.
- **Wider default retailer support out-of-box**, pricebuddy is more "BYO selectors with LLM help"; PriceGhost ships more pre-wired.

## Failure signals & fallback
Strategies all fail (site genuinely changed structure) → LLM repair takes over; if persistent, raise GitHub issue. **Fallback:** pricebuddy.

## Last verified: 2026-06
