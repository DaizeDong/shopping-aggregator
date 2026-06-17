# Domain: amazon-us

**Triage signals:** Amazon (.com), ASIN provided or implied, "Amazon 历史价", "is this Amazon
deal good", "wait for Prime Day?", "should I get Amazon WHD vs new".

| source | route | capability | detect | risk |
|---|---|---|---|---|
| **playwright MCP** | ④ | live Buy Box + sticker + Prime ship + WHD section + variant SKUs | `claude mcp list` → `playwright ✓ Connected` (almost always on) | low; ToS gray but consumer-scale fine |
| **Camelcamelcamel** ([camelcamelcamel.md](../tools/camelcamelcamel.md)) | ① free | 90d / 365d / all-time low + history chart, free, no key | open camelcamelcamel.com/product/<ASIN> | low; free site, slow rate-limit |
| **Keepa MCP** ([keepa.md](../tools/keepa.md)) | ① paid | full price + BSR + Buy Box history CSV, deepest dataset | `claude mcp list` → `keepa ✓` + `KEEPA_API_KEY` | low; **€49/mo+** the real cost |
| **BigGo MCP** ([biggo-mcp.md](../tools/biggo-mcp.md)) | ④ free | multi-platform incl Amazon w/ history, MCP-native | `claude mcp list` → `biggo ✓ Connected` | low; covers Amazon as one of many |
| **Apify price-intelligence MCP** ([apify-price-intelligence.md](../tools/apify-price-intelligence.md)) | ② paid | broadest US-retailer coverage incl Amazon | `claude mcp list` + Apify token | low; pay-per-call $0.008–$0.15 |
| Rainforest API | ② resale | real-time ASIN, Buy Box detection | trajectdata.com key | $23/mo Hobbyist; history weaker than Keepa |
| Amazon PA-API 5.0 | ① | — | — | **✗ DEAD 2026-05-15** — replaced by Creators API (10 sales/30d gate); skip for new builds |

**Default pick:** **playwright MCP for live price** (one-shot Amazon read) + **Camelcamelcamel
free** for history (decision-grade "is this a good deal"). Pay for Keepa only when the question
needs deep history (year-over-year, BSR trend) or batched ASIN sweeps.

## Real-run lesson (don't waste a fan-out round)

**Firecrawl / WebFetch return HTTP 500 on Amazon product pages** (anti-bot). Skip them entirely
for amazon.com. Route order for live price:
1. playwright MCP — works in one shot, rendered page, all variants visible.
2. BigGo MCP if connected (covers Amazon, no playwright cost).
3. Apify price-intelligence if paid.
4. Bright Data Web Unlocker as scale fallback ($1.50/1k req).

For history:
1. Camelcamelcamel free (open URL in browser or fetch via playwright — they don't block heavily).
2. Keepa if subscribed (programmatic, batch-safe, paywall on API access).
3. **Do not** try to scrape Keepa's pricing page (`keepa.com/#!api` 403s bots — paid API is the
   only programmatic path).

## Amazon-specific gotchas

- **Buy Box rotates.** Two fetches 5 minutes apart can disagree by 20%+ if a third-party seller
  flipped in. Guardrail: re-fetch on >5% drift, or note "Buy Box volatility — price band $X–$Y."
- **Amazon Warehouse Deals (WHD)** is a separate listing tucked on the right rail — often the
  cheapest in-stock option but ships only direct. Always check.
- **"Available from these sellers" deal section** is 3rd-party; condition (new/used) and seller
  rating filter aggressively.
- **The main Buy Box itself can be a 3rd-party seller**, not Amazon — read "Ships from / Sold by".
  Only "Sold by Amazon.com" (or the brand's official store) is L1; anything else is a marketplace
  seller → tier per guardrail #5. Do not assume amazon.com = first-party.
- **Coupons**: Amazon offers in-page "$X off" tick-box coupons. Most need a click to apply.
  playwright cart-test to verify.
- **Prime vs non-Prime ship**: $0 vs $5.99 ship for a small order can flip rankings — always price
  shipping into landed cost.
- **Amazon Fresh / Subscribe & Save** prices differ from spot prices. Spot price ≠ S&S price.
- **Renewed (refurb)** has a separate listing chain; if user said "refurb OK" expand to renewed.

## Cross-region note

amazon.com vs amazon.ca vs amazon.de prices diverge significantly. Default to user's
region-localized Amazon (US user → amazon.com). For cross-border (US user wants amazon.co.jp
price), state both + currency-convert + flag international shipping/duties.

## When you'd switch off this domain

If the product is obviously not on Amazon (private-label DTC, brand-direct only, used-only on
eBay), drop amazon-us from fan-out early to save budget. Confirm with a quick BigGo or Google
Shopping check before pruning.

**Install guidance:** `../volatile/pricing-install.md` → amazon-us section.

## Last verified: 2026-06
