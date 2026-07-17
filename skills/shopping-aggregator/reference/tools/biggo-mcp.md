# Tool: BigGo MCP Server

- **Domain(s):** amazon-us, ebay-walmart-target, taobao-tmall, claude-mcps
- **Barrier route:** ④ act-like-human (provider-side) · **Source tier:** L2 · **Ready MCP:** yes (this is one)
- **Cost:** free
- **Repo / Provider:** github.com/Funmula-Corp/BigGo-MCP-Server (~18★, last commit 2025-04-30), backed by BigGo.com (Taiwan-based multi-platform price-compare site)
- **Top pick for its domain:** yes for consumer cross-store MCP (the only free one with history)

## What it does / when to pick it
The **only free, multi-platform consumer price-compare MCP that includes history**. Wraps BigGo.com's underlying compare engine. Covers Amazon, eBay, AliExpress, Taobao, Shopee. Pick it as default for **any "compare across stores" agent workflow**, especially when the user has not subscribed to Keepa or Apify. It's the single best ROI shopping MCP currently.

## Install
```
uvx BigGo-MCP-Server@latest
```
Or claude-side: `claude mcp add -s user biggo -- uvx BigGo-MCP-Server@latest`. No API key needed. **Restart Claude session / `/mcp` reconnect after add**, newly added MCPs don't take effect mid-session.

## Auth / keys
None. Public service. **Don't `claude mcp add` is safe here**, no secret in the command.

## Usage, call examples
After install, in a subagent: `ToolSearch select:biggo` to load schemas, then call (typical tool names like `search_product`, `get_price_history`, `compare_platforms`). Pass a product name or model number; receive prices across Amazon / eBay / AliExpress / Taobao / Shopee with history graphs.

## General experience & gotchas (踩坑)
- **Small project, watch for drift.** 18★ and last commit 2025-04, single maintainer. If it breaks, repo issues are slow. Verify last-commit date before recommending install; refresh-protocol re-checks monthly.
- **BigGo's underlying coverage is best for Taiwan / SEA / global e-commerce; OK for US MAINSTREAM consumer goods but WEAK for niche / US-specific SKUs** (real-run 2026-06: returned ZERO for a niche US GPU SKU). **An empty BigGo result is NOT evidence the product is unavailable, it is a BigGo coverage gap; fall back to Bright Data SERP + per-retailer scrape and DO NOT report "no results exist."** Weaker for CN domestic too (淘宝/天猫 OK; 京东/拼多多 thin); for deep CN coverage layer 慢慢买 manually.
- **No login required**, but advanced features (price alerts, watchlist) on biggo.com itself need a free account; the MCP doesn't expose those.
- **Rate limits**, BigGo's backend will throttle if you fan out heavily; for >20 SKUs/min consider Apify price-intelligence MCP as the paid scale alternative.
- **Currency / locale**: BigGo defaults to its own locale heuristics. Pass explicit region/currency parameters if the MCP exposes them, or post-process the returned prices to normalize.

## Failure signals & fallback
`✗ Failed` in `claude mcp list` (uvx couldn't fetch), empty results, repeated timeouts (BigGo backend hiccup). On empty, BigGo may suggest its `spec_search` tool, that is a spec lookup, NOT a US live-price source; treat empty as a coverage miss and fall back, don't conclude "no results exist." **Fallback:** playwright MCP per retailer (slower but always works) → Apify price-intelligence (paid, broader US coverage).

## Last verified: 2026-06
