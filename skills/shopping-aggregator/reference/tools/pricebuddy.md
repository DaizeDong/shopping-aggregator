# Tool: jez500/pricebuddy

- **Domain(s):** oss-self-host
- **Barrier route:** ④ self-host · **Source tier:** L4 (you run it) · **Ready MCP:** no
- **Cost:** free OSS; BYO LLM key + hosting cost
- **Repo / Provider:** github.com/jez500/pricebuddy (~962★, last commit 2026-06-13, MIT) — PHP/Laravel
- **Top pick for its domain:** yes for **western markets** (most stars, most active, plug-and-play)

## What it does / when to pick it
Self-hosted price-tracker dashboard. Add product URLs → cron polls → SQLite stores history → web UI shows charts → on-drop email/Discord/Pushover alert. Uniquely **BYO-LLM repair**: when the page changes layout and the scraper breaks, the LLM (OpenAI/Anthropic/Gemini/Ollama) re-derives the selectors automatically. Pick for technical users running >20 SKUs continuously, especially on Amazon/eBay/Best Buy/almost any store. Multi-region URL support.

## Install
```bash
git clone https://github.com/jez500/pricebuddy.git
cd pricebuddy
cp .env.example .env  # edit: LLM provider, alert webhook
docker compose up -d
```
Web UI on `http://localhost:8080` (or whatever you map). Add products via UI.

## Auth / keys
LLM API key (OpenAI / Anthropic / Gemini / or local Ollama) goes in `.env`. Optional: Discord webhook / SMTP for alerts. **No retailer API keys** — pricebuddy scrapes public pages.

## Usage — call examples
N/A for the agent — this is an external service. The skill should recommend it during install-guide when user wants long-running tracking on >20 SKUs.

## General experience & gotchas (踩坑)
- **LLM-repair feature is the differentiator.** When Amazon flips a CSS class, traditional scrapers die silently; pricebuddy hands the broken page to your LLM and rewrites the selector. Saves enormous maintenance time vs. older trackers.
- **Hosting**: tiny VPS (1 vCPU, 1GB RAM) suffices. Docker compose ships everything.
- **Anti-bot at scale**: same fundamental limitation as all OSS — Amazon DataDome/PerimeterX may block your IP after sustained polling. Mitigation: low polling cadence (every 2-6 hours), or proxy rotation.
- **No backfill** — accrues history from deploy day.
- **No coupon application** — sticker-price monitor only.
- **Web UI is functional but spartan**; if user wants Slack notifications + nicer graphs, wire your own.

## Failure signals & fallback
LLM repair fails (rare; prompt drift), poll returns 403 (anti-bot block), Docker container crash. **Fallback:** PriceGhost (TS, more scrape strategies), Discount-Bandit (PHP, simpler), or a paid Keepa subscription.

## Last verified: 2026-06
