# Tool docs index (thin)

One line per tool. The domain shard (`domains/<domain>.md`) decides **which** tool to use; this
index points to the **how-to**. To use a tool, find its slug here and read **only** its doc
`reference/tools/<slug>.md` (per-tool install + auth + usage + 踩坑). **Never read the whole
`tools/` directory** — that breaks progressive loading. Install mechanics overview:
`reference/install-guide.md`.

★ = current top pick for its domain. Routes: ① official · ② resale · ③ self-host scrape · ④ browser/scrape.

## amazon-us
- ★ [Keepa (+ Keepa MCP)](keepa.md) — ① paid · full Amazon price/BSR/Buy Box history; €49/mo
- ★ [Camelcamelcamel](camelcamelcamel.md) — ① free · Amazon history web + Camelizer extension
- [BigGo MCP](biggo-mcp.md) — ④ free · multi-platform MCP incl. Amazon w/ history
- [Apify price-intelligence MCP](apify-price-intelligence.md) — ② paid · broad US-retailer MCP

## ebay-walmart-target
- ★ [eBay Browse API](ebay-api.md) — ① free · 5000 calls/day, only free cross-seller catalog API
- ★ [Apify price-intelligence MCP](apify-price-intelligence.md) — ② paid · Amazon+Walmart+Target+eBay+Best Buy
- [BigGo MCP](biggo-mcp.md) — ④ free · covers eBay + AliExpress + more
- [Oxylabs E-Commerce](oxylabs.md) — ② paid · scale anti-bot Walmart/eBay/Target/+100

## taobao-tmall
- ★ [慢慢买 (manmanbuy)](manmanbuy.md) — ④ free · deepest CN history price data
- ★ [购物党 (gwdang)](gwdang.md) — ④ free · CN browser extension default, 180-day history + coupon
- [什么值得买 (SMZDM)](smzdm.md) — ① free · CN deal community + tracker
- [Taobao MCP](taobao-mcp.md) — ④ · LLM-native Taobao+Tmall (9★, cookie-needed)
- [BigGo MCP](biggo-mcp.md) — ④ free · TW-side multi-platform incl Taobao

## jd-pdd
- ★ [慢慢买 (manmanbuy)](manmanbuy.md) — ④ free · JD coverage strong, PDD thin
- [购物党 (gwdang)](gwdang.md) — ④ free · JD strong; PDD limited
- [什么值得买 (SMZDM)](smzdm.md) — ① free · community deals across JD/PDD

## browser-extensions
- ★ [Capital One Shopping](capital-one-shopping.md) — ① free · US Honey-replacement default
- ★ [Karma](karma-extension.md) — ① free · US wishlist + drop alerts + multi-store
- [Coupert](coupert.md) — ① free · 200K merchants, ~73% coupon success
- ★ [购物党 (gwdang)](gwdang.md) — ④ free · CN extension default
- ★ [慢慢买 (manmanbuy)](manmanbuy.md) — ④ free · CN history + alert
- [什么值得买 (SMZDM)](smzdm.md) — ① free · CN community + insight
- [⚠ Honey](honey.md) — **AVOID 2026** · legal MDL + affiliate network terminations

## mobile-apps-aggregators
- ★ [Slickdeals](slickdeals.md) — ① free · US community deal aggregator
- ★ [ShopSavvy](shopsavvy.md) — ① free · barcode-scan in-store price compare
- ★ [Flipp](flipp.md) — ① free · US/CA grocery weekly circular
- ★ [什么值得买 (SMZDM)](smzdm.md) — ① free · CN equivalent

## ai-shopping-assistants
- ★ [Perplexity Shopping](perplexity-shopping.md) — ① Pro $20/mo · conversational AI w/ PayPal checkout (US)

## claude-mcps
- ★ [BigGo MCP](biggo-mcp.md) — ④ free · multi-platform MCP w/ history
- ★ [Apify price-intelligence MCP](apify-price-intelligence.md) — ② paid · broadest US-retailer MCP
- ★ [Keepa MCP](keepa.md) — ① paid · Amazon history MCP
- [Taobao MCP](taobao-mcp.md) — ④ · CN LLM-native (hobby)
- [Oxylabs E-Commerce](oxylabs.md) — ② paid · scrape infrastructure

## oss-self-host
- ★ [jez500/pricebuddy](pricebuddy.md) — ④ free · western multi-store, BYO-LLM
- ★ [clucraft/PriceGhost](priceghost.md) — ④ free · multi-strategy scrape, broad coverage
- ★ [DAILtech/PriceDive](pricedive.md) — ④ free · only fresh CN multi-platform (淘/京/拼)
- [Cybrarist/Discount-Bandit](discount-bandit.md) — ④ free · PHP, AliExpress strength
