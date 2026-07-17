# Tool: Apify price-intelligence-mcp

- **Domain(s):** amazon-us, ebay-walmart-target, claude-mcps
- **Barrier route:** ② resale · **Source tier:** L2 · **Ready MCP:** yes (hosted)
- **Cost:** pay-per-call $0.008,$0.15 per product (varies by retailer); $5/mo free credit on Apify free tier
- **Repo / Provider:** apify.com/onetapstudio/price-intelligence-mcp, actor by onetapstudio on Apify marketplace
- **Top pick for its domain:** yes for **paid US-retailer breadth** (Amazon + Walmart + Target + eBay + Best Buy in one MCP)

## What it does / when to pick it
The **broadest US-retailer coverage in a single MCP**. Pick when:
- You need consistent multi-US-retailer fan-out at scale (>10 products at a time).
- You don't want to maintain 5 separate playwright sessions.
- The cost (~$0.05/product average) is acceptable for the user's use case.

For one-shot single-product compare, **BigGo MCP** is cheaper (free). For just Amazon, **Keepa MCP** is better at history. This is the **middle option** between BigGo (free but narrower) and per-retailer playwright (free but fragile).

## Install
Apify-side: create a free Apify account (apify.com), connect the actor, copy the Apify API token.
Claude-side: `claude mcp add` is **NOT recommended for token-bearing MCPs** (echoes the token to transcript). Instead **edit `~/.claude.json` directly** to add `mcpServers.apify-price-intel.url` + `headers.Authorization: Bearer <token>` (see `reference/install-guide.md` Secret-handling hygiene). Restart session.

## Auth / keys
Apify API token from console.apify.com/account/integrations → personal access token. Pitched at "sellers and shoppers", but the actor is consumer-friendly. **Treat the token as a secret.**

## Usage, call examples
After install + reconnect, in a subagent: `ToolSearch select:apify-price-intel` to load. Call the actor with `{product: "Bose QuietComfort 45", retailers: ["amazon", "walmart", "target", "ebay", "bestbuy"]}` → returns array of price + URL + stock per retailer. Per-call billing, minimize redundant calls.

## General experience & gotchas (踩坑)
- **Per-call cost adds up fast**, each retailer hit is a separate $0.008-0.05 charge. For 5-retailer compare on 10 products = ~$2.50 (acceptable for a big-ticket purchase, wasteful for cheap items).
- **Actor maintenance risk**, Apify actors are maintained by third parties; if `onetapstudio` stops updating, scrapers will break silently. Apify's marketplace shows usage stats; verify in the last 30 days before relying on.
- **Coverage caveats**: Walmart marketplace 3P sellers may not show; Costco needs login (skipped); Best Buy open-box not always captured.
- **No history**, this MCP is **spot-price only**. Pair with Keepa for Amazon history if you need both.
- **Free tier**, Apify gives $5/mo free credit on the Personal plan; enough for low-volume consumer use, runs out fast on a heavy fan-out.

## Failure signals & fallback
Apify-side error response (rate-limited, actor failed, retailer blocked) → return `failed/empty` to skill. **Fallback:** playwright MCP per retailer (free, slower) → BigGo MCP (free, narrower).

## Last verified: 2026-06
