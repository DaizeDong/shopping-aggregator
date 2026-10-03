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
Or claude-side: `claude mcp add -s user -e BIGGO_MCP_SERVER_REGION=US biggo -- uvx BigGo-MCP-Server@latest` (set the region to the buyer's market; see gotchas). No API key needed. **Restart Claude session / `/mcp` reconnect after add**, newly added MCPs don't take effect mid-session.

## Auth / keys
None. Public service. **Don't `claude mcp add` is safe here**, no secret in the command.

## Usage, call examples
After install, in a subagent: `ToolSearch select:biggo` to load schemas, then call (typical tool names like `search_product`, `get_price_history`, `compare_platforms`). Pass a product name or model number; receive prices across Amazon / eBay / AliExpress / Taobao / Shopee with history graphs.

## General experience & gotchas (踩坑)
- **Small project, watch for drift.** 18★ and last commit 2025-04, single maintainer. If it breaks, repo issues are slow. Verify last-commit date before recommending install; refresh-protocol re-checks monthly.
- **The region is a server setting, and upstream defaults it to `TW`.** `BIGGO_MCP_SERVER_REGION` picks which BigGo site every search hits; unset, that is biggo.com.tw, so a US product query returns only TWD-priced Taiwan merchants, or nothing. A control query such as `iphone` still returns rows, so neither the health line nor a control catches this; the `currency` field on the returned rows does. Measured 2026-10: one US product query returned 10 USD rows from US merchants under `US` and a single TWD row under `TW`. The earlier reading that BigGo is "weak for niche / US-specific SKUs" (zero rows for a niche US GPU in 2026-06, Taiwan-only rows for another US SKU in 2026-07) was taken under the default and says nothing about US coverage.
- **Correctly configured, it is still a partial index.** Under `US` the measured query came back dominated by one marketplace, with no rows from several mass-market retailers that carried the item. **An empty or thin BigGo result is NOT evidence the product is unavailable; fall back to per-retailer reads and DO NOT report "no results exist."** CN domestic coverage (淘宝/天猫 OK; 京东/拼多多 thin) needs its own region; for deep CN coverage layer 慢慢买 manually.
- **No login required**, but advanced features (price alerts, watchlist) on biggo.com itself need a free account; the MCP doesn't expose those.
- **Rate limits**, BigGo's backend will throttle if you fan out heavily; for >20 SKUs/min consider Apify price-intelligence MCP as the paid scale alternative.
- **One server holds one region.** The region is read once at server start, so a run that needs two markets needs a reconnect with a different `BIGGO_MCP_SERVER_REGION`, or a second server entry. Read the `currency` field before converting or ranking anything: a TWD price read as dollars is off by roughly 30x.

## Failure signals & fallback
`✗ Failed` in `claude mcp list` (uvx couldn't fetch), empty results, repeated timeouts (BigGo backend hiccup). On empty, BigGo may suggest its `spec_search` tool, that is a spec lookup, NOT a US live-price source; treat empty as a coverage miss and fall back, don't conclude "no results exist." **Fallback:** playwright MCP per retailer (slower but always works) → Apify price-intelligence (paid, broader US coverage).

## Last verified: 2026-10
