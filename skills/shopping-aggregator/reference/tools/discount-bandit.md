# Tool: Cybrarist/Discount-Bandit

- **Domain(s):** oss-self-host
- **Barrier route:** ④ self-host · **Source tier:** L4 · **Ready MCP:** no
- **Cost:** free OSS
- **Repo / Provider:** github.com/Cybrarist/Discount-Bandit (~704★, last commit 2026-06-01, MIT), PHP
- **Top pick for its domain:** alternative to pricebuddy especially when AliExpress matters

## What it does / when to pick it
PHP-based self-host tracker. Covers Amazon (multi-region) + AliExpress + eBay + custom stores via configurable selectors. Pick over pricebuddy when **AliExpress** is a primary target, Discount-Bandit's AliExpress selectors have been better-maintained.

## Install
```bash
git clone https://github.com/Cybrarist/Discount-Bandit.git
cd Discount-Bandit
docker compose up -d
```
Web UI for adding products + setting alerts.

## Auth / keys
None for basic use. Optional retailer accounts via session cookies for region-locked prices.

## Usage, call examples
N/A, external service.

## General experience & gotchas (踩坑)
- **PHP/Laravel stack**, slightly older feel than pricebuddy/PriceGhost; matures slower but is stable.
- **AliExpress coverage** is the differentiator. Other OSS sometimes leave AE for users to wire.
- **No LLM repair**, when a site changes layout, selectors must be updated manually; check repo issues.
- **Multi-region Amazon** is well-supported (US/UK/DE/IT/ES/CA etc.).
- **Notifications**: email, Discord, Telegram out of box.
- 704★ + active commits = healthy + low drift risk relative to PriceDive / BigGo.

## Failure signals & fallback
Layout-change breaks → manual selector fix or raise issue. **Fallback:** pricebuddy (LLM repair) or PriceGhost (multi-strategy).

## Last verified: 2026-06
