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
- [ScraperAPI](scraperapi.md) — ② paid · budget hosted anti-bot scrape; free 1K credits/mo, Hobby $49/mo (credits≠requests)
- [AliExpress (Open Platform / Affiliate API)](aliexpress.md) — ① free · official signed catalog/affiliate API (⚠ +~35% US duty, 真伪 risk)
- [Bright Data Web Unlocker](bright-data.md) — ② paid · success-based anti-bot unblocker (free 5K/mo, ~$1.3-1.5/1K), Oxylabs peer

## taobao-tmall
- ★ [慢慢买 (manmanbuy)](manmanbuy.md) — ④ free · deepest CN history price data
- ★ [购物党 (gwdang)](gwdang.md) — ④ free · CN browser extension default, 180-day history + coupon
- [什么值得买 (SMZDM)](smzdm.md) — ① free · CN deal community + tracker
- [Taobao MCP](taobao-mcp.md) — ④ · LLM-native Taobao+Tmall (9★, cookie-needed)
- [BigGo MCP](biggo-mcp.md) — ④ free · TW-side multi-platform incl Taobao
- [小红书 (Xiaohongshu / RedNote)](xiaohongshu.md) — ④ free · 评测/种草口碑源，**非价格源**；login-walled + 反爬 + 多软广

## jd-pdd
- ★ [慢慢买 (manmanbuy)](manmanbuy.md) — ④ free · JD coverage strong, PDD thin
- [购物党 (gwdang)](gwdang.md) — ④ free · JD strong; PDD limited
- [什么值得买 (SMZDM)](smzdm.md) — ① free · community deals across JD/PDD
- ★ [京东价保 (JD Price Protection)](jd-price-protection.md) — ① free · 京东自营/三方下单后保价期内自动退差价；非比价工具，是降价兜底
- [小红书 (Xiaohongshu / RedNote)](xiaohongshu.md) — ④ free · 评测/种草口碑源，**非价格源**；login-walled + 反爬 + 多软广

## browser-extensions
- ★ [Capital One Shopping](capital-one-shopping.md) — ① free · US Honey-replacement default
- ★ [Karma](karma-extension.md) — ① free · US wishlist + drop alerts + multi-store
- [Coupert](coupert.md) — ① free · 200K merchants, ~73% coupon success
- ★ [购物党 (gwdang)](gwdang.md) — ④ free · CN extension default
- ★ [慢慢买 (manmanbuy)](manmanbuy.md) — ④ free · CN history + alert
- [什么值得买 (SMZDM)](smzdm.md) — ① free · CN community + insight
- [⚠ Honey](honey.md) — **AVOID 2026** · legal MDL + affiliate network terminations
- [RetailMeNot (ex-Genie)](retailmenot.md) — ① free · coupon + cashback, 20K brands; Genie retired into this listing
- [Cently](cently.md) — ① free · auto-apply codes; ⚠ System1-owned data caveat
- [⚠ InvisibleHand](invisiblehand.md) — **AVOID 2026** · brand retired, rebranded to CNET Shopping (Red Ventures); MV2 sunset risk

## mobile-apps-aggregators
- ★ [Slickdeals](slickdeals.md) — ① free · US community deal aggregator
- ★ [ShopSavvy](shopsavvy.md) — ① free · barcode-scan in-store price compare
- ★ [Flipp](flipp.md) — ① free · US/CA grocery weekly circular
- ★ [什么值得买 (SMZDM)](smzdm.md) — ① free · CN equivalent
- [DealNews](dealnews.md) — ① free · editorial editor-vetted US deals (web/app healthy; API key-gated + stale)
- [Reddit deals (r/buildapcsales + r/deals)](reddit-deals.md) — ④ free · community discovery (E3 lead, not E1 winner); OAuth 100 QPM
- [小红书 (Xiaohongshu / RedNote)](xiaohongshu.md) — ④ free · 生活方式+测评社区（值不值得买）；**非价格源**，多软广需交叉核验

## ai-shopping-assistants
- ★ [Perplexity Shopping](perplexity-shopping.md) — ① Pro $20/mo · conversational AI w/ PayPal checkout (US)

## claude-mcps
- ★ [BigGo MCP](biggo-mcp.md) — ④ free · multi-platform MCP w/ history
- ★ [Apify price-intelligence MCP](apify-price-intelligence.md) — ② paid · broadest US-retailer MCP
- ★ [Keepa MCP](keepa.md) — ① paid · Amazon history MCP
- [Taobao MCP](taobao-mcp.md) — ④ · CN LLM-native (hobby)
- [Oxylabs E-Commerce](oxylabs.md) — ② paid · scrape infrastructure
- [ScraperAPI](scraperapi.md) — ② paid · scrape infrastructure (no first-party MCP; wrap via curl)
- [Bright Data Web Unlocker](bright-data.md) — ② paid · scrape infrastructure (success-CPM anti-bot)

## oss-self-host
- ★ [jez500/pricebuddy](pricebuddy.md) — ④ free · western multi-store, BYO-LLM
- ★ [clucraft/PriceGhost](priceghost.md) — ④ free · multi-strategy scrape, broad coverage
- ★ [DAILtech/PriceDive](pricedive.md) — ④ free · only fresh CN multi-platform (淘/京/拼)
- [Cybrarist/Discount-Bandit](discount-bandit.md) — ④ free · PHP, AliExpress strength
- [AliExpress (Open Platform / Affiliate API)](aliexpress.md) — ① free · official AliExpress data source (5K req/day, ⚠ tariff/counterfeit)
