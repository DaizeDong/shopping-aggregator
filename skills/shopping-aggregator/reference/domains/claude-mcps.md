# Domain: claude-mcps

**Triage signals:** "I want a Claude agent to do this", MCP-driven price compare, "auto-compare in
Claude Code", "make Claude do the shopping".

> This is the **MCP-server domain** — purpose-built MCPs that the shopping-aggregator skill itself
> delegates to. The user-facing skill answers; this domain provides the plumbing.

| MCP | route | coverage | install | risk |
|---|---|---|---|---|
| **BigGo MCP** ([biggo-mcp.md](../tools/biggo-mcp.md)) | ④ free | Amazon, eBay, AliExpress, Taobao, Shopee — multi-platform price compare + **history**; **weak for niche/US-specific SKUs — empty ≠ unavailable, fall back to Bright Data SERP + retailer scrape** | `uvx BigGo-MCP-Server@latest` | low; **18★ small project — watch for drift**, last update 2025-04 |
| **Apify price-intelligence MCP** ([apify-price-intelligence.md](../tools/apify-price-intelligence.md)) | ② paid | Amazon, Walmart, Target, eBay, Best Buy — broadest US-retailer | Apify MCP config + token | low; pay-per-call $0.008–$0.15; relies on Apify actor maintenance |
| **Keepa MCP** ([keepa.md](../tools/keepa.md)) | ① paid | Amazon all 11 markets — **full price/BSR/Buy Box history** | KEEPA_API_KEY + `cosjef/Keepa_MCP` or `BWB03/keepa-adapter` (.mcpb) | low; **€49/mo+** real cost; tokens stall large sweeps |
| **Taobao MCP** ([taobao-mcp.md](../tools/taobao-mcp.md)) | ④ | Taobao + Tmall title/price/specs/reviews | git clone + cookie injection | medium; 9★ small project, requires manual cookie maintenance |
| **BuyWhere MCP** | ② paid | Lazada, Shopee, Amazon (SG/SEA/US, 11M+ SKUs) | `npx -y @buywhere/mcp-server` + API key | low; **SE Asia focus** — limited US relevance |
| **playwright MCP** | ④ free | bespoke page fetch on ANY retailer | usually pre-installed in Claude Code | low; the fallback that always works |
| **firecrawl MCP / skill** | ② paid | general scrape, OK for static product pages | already in user's setup if firecrawl skill present | **fails on Amazon/Taobao anti-bot** — don't use for those |
| **Bright Data Web Unlocker MCP** ([brightdata.md via market-intel](../../../market-intel/skills/market-intel/reference/tools/brightdata.md)) | ② paid | beats Cloudflare/DataDome on hard targets at scale | hosted HTTP MCP | $1.50/1k req; 5k req/mo free tier |

**Default pick:** **playwright MCP + BigGo MCP** for free / general; layer Keepa MCP for Amazon
history; layer Apify price-intelligence MCP for paid US-retailer scale.

## Single-retailer MCPs (NOT cross-store, listed for completeness)

| MCP | covers | use |
|---|---|---|
| rigwild/mcp-server-amazon (31★) | Amazon | search/cart/checkout — no price compare |
| Fewsats/amazon-mcp | Amazon | search+buy via L402 — no compare |
| devlimelabs/amazon-shopping-mcp | Amazon | search/buy — no compare |
| sachinparyani/mcp-server-shopping | Amazon + Target orders | limited |

These don't replace BigGo / Apify for cross-store comparison. Useful only when the buy decision
is already made and you want Claude to actually execute the purchase.

## How shopping-aggregator delegates to MCPs

The orchestration logic in `SKILL.md` Step 5 decides per fan-out:
1. **One product, multiple retailers, no history needed** → BigGo MCP (one call).
2. **Amazon-only, need history** → Keepa MCP if subscribed, else Camelcamelcamel page fetch.
3. **Need cart-test for coupons or login-walled prices** → playwright MCP per retailer.
4. **Broad US retailer sweep + reliability** → Apify price-intelligence MCP (cost trade).
5. **Hard target with anti-bot** → playwright fails → Bright Data Web Unlocker MCP.
6. **CN platforms** → Taobao MCP (if cookies fresh) → playwright → 慢慢买 web fetch.

Each subagent is told via the prompt: "you have access to <MCP name> via ToolSearch — load its
schema with `ToolSearch select:<mcp_name>` before calling it." Subagents inherit MCPs in
**deferred form only** — they must explicitly load schemas before calling, or the call fails
with InputValidationError.

## Why so few MCPs exist for consumer price compare

The plumbing for consumer price compare requires either:
(a) an **upstream commercial API** (Keepa, Rainforest, PriceAPI) — paid, gated, often with
    affiliate/seller-app requirements; or
(b) a **scraping infrastructure** (Apify, Bright Data, custom playwright) — pays for
    anti-bot/proxy at scale.

Free indie MCPs ((a) or hand-rolled (b)) tend to be **hobby-grade** (BigGo at 18★, Taobao MCP at
9★) because consumer shopping has no obvious monetization for the MCP author. This is the
opposite of seller-side MCPs (Apollo, Hunter, Apify business actors) which have a clear
subscription target.

**Real-run lesson:** treat any indie consumer-shopping MCP as **at-risk for silent drift /
abandonment** — verify the repo's last-commit date in the tool doc's `Last verified` line before
recommending an install. Refresh-protocol re-checks these monthly.

**Install guidance:** `../volatile/pricing-install.md` → claude-mcps section + per-tool docs.

## Last verified: 2026-06
