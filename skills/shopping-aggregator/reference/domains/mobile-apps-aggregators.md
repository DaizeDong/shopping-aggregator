# Domain: mobile-apps-aggregators

**Triage signals:** "what app for deals", "barcode scan price", "weekly ads", Slickdeals, Flipp,
什么值得买, DealNews, "什么时候买便宜".

| tool | type | region | status | use case |
|---|---|---|---|---|
| **Slickdeals** ([slickdeals.md](../tools/slickdeals.md)) | community deal forum + app + extension | US | ✓ healthy, ~12M members, Goldman/Hearst-owned | best signal/noise community for **finding deals you weren't looking for**; weak for "compare this specific product" |
| **ShopSavvy** ([shopsavvy.md](../tools/shopsavvy.md)) | mobile app, barcode scanner | US | ✓ healthy (v18.9.40, Jun 2026) | **in-store: scan barcode, see online prices**, physical-store shopper's tool |
| **Flipp** ([flipp.md](../tools/flipp.md)) | weekly-ads aggregator | US + CA | ✓ healthy (v99.1, 4.8★/518k reviews) | **grocery / drugstore weekly circular**, best for SnS-vs-this-week's-deal grocery |
| **DealNews** | editorial-curated deals + app | US | ✓ healthy (app Jun 10 2026) | "Top deals today, editor-vetted"; lower throughput, higher quality |
| **r/deals + r/buildapcsales** | Reddit communities | US-leaning | ✓ active | unmoderated tier; GPU/CPU drops vanish in minutes (bots) |
| **什么值得买 (SMZDM)** ([smzdm.md](../tools/smzdm.md)) | community + app + extension + AI tracker | CN | ✓ healthy | China's Slickdeals-equivalent: 种草 community first, deal aggregation second |
| **慢慢买 App** ([manmanbuy.md](../tools/manmanbuy.md)) | mobile app + 历史价 + 提醒 | CN | ✓ healthy | history-price + per-SKU drop alert, deepest CN historical dataset |
| **小红书 (Xiaohongshu)** | content community, price discussion | CN | ✓ healthy | **not** a deal aggregator, useful for product reviews / 测评 before buying |

**Default pick (US):** **Slickdeals app** (community deals) + **Flipp** (grocery weekly) +
**ShopSavvy** (in-store scan). DealNews if user prefers editorial.
**Default pick (CN):** 什么值得买 (community deals + reviews) + 慢慢买 (history-price + alert).

## When to use which

| User question | Tool |
|---|---|
| "Is there a deal on iPad Pro this week?" | Slickdeals / r/deals (community) + DealNews (editorial) |
| "I'm at Costco, is this TV cheaper at Best Buy?" | ShopSavvy (scan in store) |
| "Grocery prices this week?" | Flipp |
| "What's the best deal of the day?" | DealNews + Slickdeals frontpage |
| "Has this product ever been cheaper?" | NOT these, use Camelcamelcamel (Amazon) or 慢慢买 (CN); see `amazon-us.md` / `taobao-tmall.md` |
| "Should I buy now or wait for Black Friday?" | Slickdeals BF megathread + historical data from Camelcamelcamel |

## Real-run lesson

**These tools are great for DISCOVERY, weak for COMPARISON.** Don't fan out to Slickdeals/Flipp
when the user has a specific SKU in hand and wants a landed-cost table.

> **Grocery hand-off:** When a Flipp result is grocery/CPG (weekly circular, store-card deal, fuel
> points, Instacart markup question), route to **`domains/grocery-cpg.md`** for the banner-specific
> loyalty + Instacart-markup mechanics. Flipp finds the deal; grocery-cpg explains the program,
> the markup trap, and the hyper-regional banner footprint. Always pin the user's ZIP→banner first.

Save them for:
- "I'm thinking of buying X but no rush" → check Slickdeals/SMZDM for any active drop.
- "What's hot right now in <category>" → discovery, not comparison.

For a specific SKU-level price comparison, the heavy lifters are still the retailer-direct routes
(playwright, BigGo MCP, Keepa), these community/aggregator tools are sidekicks.

## Slickdeals algorithm quirks

- **Frontpage threads** are community-voted; **Frontpage Top Deals** are the strongest signal but
  highly time-sensitive (10 min after frontpage = often expired).
- **Slickdeals Email Alerts** can be set per keyword, useful "watch this product" alternative
  to Keepa/Camelcamelcamel native alerts.
- **Forum vs frontpage**: the forum (`forums.slickdeals.net`) has 10× more deals but 50× the
  noise. Stick to frontpage unless deep-diving.

## SMZDM algorithm quirks

- **AI 跟踪** feature lets you submit a SKU and SMZDM AI watches for price drops + community
  posts, similar to Camelcamelcamel email alert.
- **首页好价** + "海淘" + "免税"  栏目 are well-curated.
- **优惠券分类** has reliable code freshness vs 购物党 (which sometimes shows expired).

## Affiliate disclosure

Slickdeals, SMZDM, DealNews all run affiliate links on outbound clicks. **Don't recommend
clicking through the deal page when a public direct link works**, Slickdeals' affiliate redirect
sometimes adds 2-3s redirect lag, occasionally drops to the retailer's homepage instead of the
deal.

**Install guidance:** these are App Store / Google Play apps + browser extensions; open the URLs
in tool docs.

## Last verified: 2026-06
