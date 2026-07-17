# Shopping source index (thin)

One line per domain. At triage, match the buy intent to 1 to N domains, then read ONLY the matched
shard(s) in `domains/`. Do not read shards you didn't match.

> **These domains are organized by ACCESS METHOD (supply-side), they do NOT enumerate the buyer's
> channel universe.** After matching domains here, ALSO map the product to its demand-side **channel
> classes** in `channel-classes.md`. That is what surfaces tool-less authorized retailers (e.g. Micro
> Center, website only) which this access-method index structurally omits.

| domain | triage signals | top pick (barrier route) | shard |
|---|---|---|---|
| amazon-us | "Amazon", ASIN, US Amazon shopping, "Amazon 历史价" | playwright ④ live + Camelcamelcamel ① history (Keepa ① if subscribed) | `domains/amazon-us.md` |
| ebay-walmart-target | eBay, Walmart, Target, Best Buy, Costco, multi-store US compare | eBay Browse API ① free + playwright ④ for others | `domains/ebay-walmart-target.md` |
| auction-resale | resale/used value, eBay sold comps, "what's it worth", StockX/GOAT sneakers, Whatnot/Poshmark/Mercari/Depop/ThredUp | eBay Sold SERP ④ (`?LH_Sold=1`) free + StockX API ① (if approved) / playwright ④ for the rest | `domains/auction-resale.md` |
| taobao-tmall | 淘宝, 天猫, taobao, tmall | 慢慢买 App ④ + 购物党扩展 ④ (Taobao MCP ④ for agent use) | `domains/taobao-tmall.md` |
| jd-pdd | 京东, 拼多多, JD.com, Pinduoduo | 慢慢买 ④ + JD 自带价保 ① + 购物党 ④ (PDD coverage thin) | `domains/jd-pdd.md` |
| **cross-border** | 海淘, 代购, daigou, parallel/grey import, package forwarder/转运, "ship to US from CN/KR", customs/duty on my order | Superbuy ④ (CN→US haul) · Stackry/MyUS ④ (US-addr reship) · YesStyle ④ (K-beauty, absorbs tariff), **duty by default**, numbers from `data/cross-border-duty.json` | `domains/cross-border.md` |
| browser-extensions | "Honey", coupon extension, cashback, 自动找券 | Capital One Shopping ① + Karma ① (⚠ Honey: 卸载推荐) | `domains/browser-extensions.md` |
| mobile-apps-aggregators | ShopSavvy / Flipp / Slickdeals / 什么值得买 / DealNews | Slickdeals 社区 ① + Flipp 周报 ① + 什么值得买 ① | `domains/mobile-apps-aggregators.md` |
| **grocery-cpg** | groceries/CPG/staples, Instacart markup, Kroger fuel points, Target Circle, ShopRite/Wegmans/Costco, Amazon Fresh/WFM, weekly circular | Flipp ① circular discovery + banner app ① loyalty truth (playwright ④ for live Instacart cart), **hyper-regional, pin ZIP+banner** | `domains/grocery-cpg.md` |
| ai-shopping-assistants | "Perplexity Shopping", "ChatGPT shopping", Rufus, Klarna AI | Perplexity Pro ① (in-app PayPal) | `domains/ai-shopping-assistants.md` |
| **claude-mcps** | "want a Claude agent to compare for me", MCP-driven price compare | BigGo MCP ④ free · Apify price-intelligence MCP ② paid | `domains/claude-mcps.md` |
| oss-self-host | "self-host", docker, "自己跑一个", privacy-first | pricebuddy ④ (US/EU) · PriceDive ④ (CN, only fresh multi-platform) | `domains/oss-self-host.md` |
| hotel-travel | "book a hotel", "cheapest hotel near", lodging price compare, hotel + dates, 订酒店, 差旅住宿, 酒店比价 (flights/cars/trains OUT) | Booking.com playwright ④ (Genius often lowest public; drive to Your-Details, then hand off pay) | `domains/hotel-travel.md` |

Barrier-route legend (same scheme as `market-intel`):
① official API / official site, compliant, often paid/limited, no ban risk
② resale API, provider absorbs the barrier, pay-per-use, gray-area
③ self-host scrape (reverse-engineered API), free, you supply accounts+proxies, ban risk
④ **browser automation / act-like-human**, real logged-in browser (playwright MCP + OSS repos);
   FIRST-CLASS for live consumer prices. The Amazon/Taobao real-run lesson (in shard), playwright
   reads the rendered page in one shot; firecrawl/WebFetch return 500 / login-wall. Reach for paid
   ①/② only for history (Keepa) or scale.

## Non-US/CN regional routing (no dedicated shard, route to ④)

The shards above are deliberately US- and CN-centric (where the access-method ecosystem is richest).
Major **non-US/CN regional marketplaces have no dedicated shard and no usable consumer price API** ,
they are reached via **playwright ④** (live PDP read), with the EU price-comparison engines as the
discovery layer on top (see [`channel-classes.md`](./channel-classes.md) price-comparison-engine row +
the X1 map). Do not invent a shard for these prematurely; route to ④ and confirm at E1.

| region | marketplace(s) | route | note |
|---|---|---|---|
| Latin America | **Mercado Libre** (18 LATAM countries: MX/BR/AR/CL/CO/PE/UY/…) | ④ | no public price API; per-country site, prices in local currency + installments ("cuotas") |
| South Korea | **Coupang** (+ Naver Shopping) | ④ | login/anti-bot heavy; Rocket-delivery price ≠ marketplace 3P price |
| Japan | **Rakuten** (rakuten.co.jp) | ④ | point-economy distorts effective price (楽天ポイント); read cart, not sticker. Amazon JP → `amazon-us` JP-locale section instead |
| India | **Flipkart** (+ region: Amazon.in via Keepa) | ④ | no public price API; bank-card instant-discount coupons distort checkout, price the cart |

Verified 2026-06 ([Mercado Libre 18-country scope](https://apify.com/trudax/mercadolibre-scraper),
[no public price APIs → scraping ecosystem for ML/Rakuten/Flipkart](https://pricesapi.io/)). These are
④ browser reads because, exactly as the Amazon/Taobao real-run lesson shows, the rendered PDP is the
only reliable consumer-price source and no compliant API exists for these markets.

## Sister-skill cross-reference

For broad commercial research, competitor analysis, market sizing, X/Twitter sentiment, SEO
intel, frontier-research, or seller-side ecommerce-arbitrage, use **market-intel**
([github.com/DaizeDong/market-intel](https://github.com/DaizeDong/market-intel)). This skill is
the consumer-purchase specialization.

| Question shape | Use |
|---|---|
| "Should I buy X, where, when, for how much" | shopping-aggregator (here) |
| "Should I sell X, sourced from where, with what margin" | market-intel `ecommerce-arbitrage` |
| "What's the market for X-category products, who are the players" | market-intel general |
