# Tool: Taobao MCP (JeremyDong22/taobao_mcp)

- **Domain(s):** taobao-tmall, claude-mcps
- **Barrier route:** ④ scrape with cookie · **Source tier:** L4 (single-source, hobby grade) · **Ready MCP:** yes (this is one)
- **Cost:** free
- **Repo / Provider:** github.com/JeremyDong22/taobao_mcp (~9★, last commit 2025-11-17)
- **Top pick for its domain:** yes for **LLM-native CN access** (only one in this niche)

## What it does / when to pick it
The **only LLM-native MCP for Taobao + Tmall**, pulls title, price, specs, reviews of a Taobao/Tmall product into a Claude agent. Pick when you want an agent to compare/extract structured info from Taobao listings without manual browser orchestration. For consumer-side ad-hoc lookups, **慢慢买 App** is more reliable; this tool earns its keep when scripting agentic workflows.

## Install
`git clone https://github.com/JeremyDong22/taobao_mcp && cd taobao_mcp && pip install -r requirements.txt` → start the MCP per repo README. Or wire it as a stdio MCP in `~/.claude.json`. Restart session.

## Auth / keys
Requires a **valid Taobao login cookie** (extracted from a logged-in browser session). This is the chief operational burden, cookies expire every few days to weeks; the scraper breaks silently when stale. Repo README has cookie-extraction instructions.

## Usage, call examples
After install + cookie injection: `ToolSearch select:taobao_mcp`, then call `get_product` with item ID or share URL. Returns title, price (web-public price, see Taobao 实际到手价 caveat in `domains/taobao-tmall.md`), reviews, seller info.

## General experience & gotchas (踩坑)
- **Cookie maintenance is the real cost.** Plan to refresh every 1-2 weeks; automated headless login is fragile (Taobao's slider-captcha is hard).
- **9★, single-author repo**, high abandonment risk. Pin to a specific commit if relying on it; refresh-protocol re-checks monthly.
- **App-only prices invisible** (see `domains/taobao-tmall.md` real-run lesson 1). Web-public price ≠ user-actual price. Always state this caveat in the output.
- **Detection risk**: persistent scraping from one Taobao account → account safety verification → cookie invalidation. Use a throwaway account, not your main.
- **No Tmall flagship store special pricing** (店铺会员价 / 88VIP) shown, same web-public-only limitation.
- **No history**, spot-price only.

## Failure signals & fallback
Empty/garbled response, "请重新登录" embedded in product description (cookie expired), Taobao风控页 (account verification triggered). **Fallback:** ask user to refresh cookie → if persistent, route to **慢慢买 web fetch** via playwright (no auth required) or **BigGo MCP** (lower CN coverage but auth-free).

## Last verified: 2026-06
