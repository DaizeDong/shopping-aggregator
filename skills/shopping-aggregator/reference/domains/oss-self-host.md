# Domain: oss-self-host

**Triage signals:** "self-host a price tracker", docker-compose, "build my own Keepa", "privacy,
no third party", "company-internal dashboard".

| repo | ★ | last commit | language | coverage | self-host complexity |
|---|---|---|---|---|---|
| **jez500/pricebuddy** ([pricebuddy.md](../tools/pricebuddy.md)) | 962 | 2026-06-13 | PHP/Laravel | Amazon, eBay, Best Buy + custom selectors; **BYO-LLM** (OpenAI/Anthropic/Gemini/Ollama) for scrape repair | docker-compose, plug-and-play |
| **clucraft/PriceGhost** ([priceghost.md](../tools/priceghost.md)) | 641 | 2026-02-03 | TypeScript | Amazon US/UK/DE, Best Buy, Walmart, Target, Costco, eBay, Newegg, Home Depot, AliExpress; multi-strategy scrape (JSON-LD → meta → CSS → headless → LLM fallback) | docker-compose + BYO LLM key |
| **Cybrarist/Discount-Bandit** ([discount-bandit.md](../tools/discount-bandit.md)) | 704 | 2026-06-01 | PHP | Amazon + AliExpress + eBay + custom; multi-region | docker-compose |
| **DAILtech/PriceDive** ([pricedive.md](../tools/pricedive.md)) | 53 | 2025-10-08 | Python | **Taobao + JD + PDD**, only fresh CN multi-platform; tracks 先涨后降 fake-sale | pip + SQLite |
| SpikeHD/AmazonMonitor | 290 | 2026-05-08 | TypeScript | Amazon, multi-region, Discord bot front-end | npm + Puppeteer |
| omkarcloud/amazon-scraper | 221 | 2026-06-15 | Python | Amazon 24 markets, REST API | pip + Puppeteer |
| Crinibus/scraper | 238 | 2025-01-29 | Python | Amazon 6 markets, eBay, Newegg, Shein; CLI + history viz | pip + cron |
| **gokborayilmaz/browseruse-price-tracker-agent** | 13 | recent | Python | LLM agent **live-scrapes** retailers, only credible OSS "AI cheapest finder" | pip + playwright + LLM key (demo-grade) |

**Default pick (West):** **pricebuddy** (most stars, most active, plug-and-play, multi-store).
**Default pick (CN):** **PriceDive** (only fresh multi-platform). Discount-Bandit if user
specifically wants AliExpress.

## Self-host shape

All of these are: docker container or python+SQLite → web UI → per-SKU URL → cron-scheduled
re-scrape → on-drop email/Discord/Telegram alert. They re-create Keepa's core function
(price history + drop alert) **but** the history accrues only from the day you deploy. **They
cannot backfill years of past prices.** This is the hard limit vs paid Keepa.

For consumer use, this is usually fine: install today, in 30 days you have a month of history,
which is enough to know if the current price is below your-personal-window low.

## What OSS WON'T do for you

- **Coupon application** (most OSS trackers just monitor sticker price; coupon stacking is the
  retailer's frontend), use a browser extension or playwright cart test.
- **Anti-bot at scale**, when Amazon ratchets up DataDome, your self-host scraper fails first.
  Mitigation: pin to recent commits, watch for repo issues about anti-bot breaks, swap to
  PriceGhost's LLM-fallback strategy.
- **Mobile App-only prices** (Taobao App "猜你喜欢" prices, JD Plus members-only), same web-only
  limitation as commercial trackers.
- **Cross-currency / cross-region intelligence** (best price across amazon.com vs amazon.de) ,
  you'd have to wire that yourself.

## OSS gap: browser-extension space

There is **no OSS Honey-equivalent with >200★ still maintained**. The Honey/Capital One
Shopping/Karma category is closed-source by economic structure (affiliate revenue hard to share
when open-source). Don't recommend the user "find an open-source Honey", it doesn't really exist.

## OSS gap: Pinduoduo

Only **PriceDive** touches PDD, and even there coverage is thin. PDD's reverse-third-party-compare
posture makes OSS coverage genuinely hard. Realistic: rely on user-manual PDD App check + 慢慢买's
partial coverage; OSS won't fix this.

## When to recommend self-host vs use a SaaS

**Self-host when:**
- User is technical (comfortable with docker-compose).
- Multi-product tracking at low cost (>20 SKUs continuously).
- Privacy / no-cloud-tool requirement (corporate procurement, journalism).
- Building into a workflow (alert into Slack, integrate with own dashboard).

**Skip self-host when:**
- User is shopping for one or two items (overkill).
- User needs deep historical backfill (Keepa wins).
- User wants polish + UX (Camelcamelcamel + Capital One Shopping wins).

**Install guidance:** `../volatile/pricing-install.md` → oss-self-host section + per-tool docs.

## Last verified: 2026-06
