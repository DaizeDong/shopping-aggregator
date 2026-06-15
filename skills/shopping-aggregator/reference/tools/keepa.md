# Tool: Keepa (+ Keepa MCP)

- **Domain(s):** amazon-us, claude-mcps
- **Barrier route:** ① official · **Source tier:** L1 · **Ready MCP:** yes — `cosjef/Keepa_MCP` or `BWB03/keepa-adapter` (.mcpb one-click)
- **Cost:** ~€49/mo @ 20 tokens/min start, scales with token burn [keepa.com/#!api — site 403s bots; confirm at keepa.com]
- **Repo / Provider:** github.com/cosjef/Keepa_MCP (~28★, MIT) · alt `BWB03/keepa-adapter` (~11★, MIT, .mcpb). Data provider: keepa.com (paid key)
- **Top pick for its domain:** yes (for history)

## What it does / when to pick it
The one irreplaceable Amazon source: full historical **price curve + BSR/sales-rank history + Buy Box / stock history** for any ASIN, going back years. Pick Keepa whenever the question needs *history* (price seasonality, BSR trend, was-it-ever-this-cheap) — no free/scrape route can backfill that. For live spot prices only, the free ④ route (playwright, BigGo MCP) is cheaper; reach for Keepa specifically because the OSS route can only accrue history from *its own deploy day*, never the past.

## Install
KEEPA_API_KEY from keepa.com → install MCP. Both MCPs are stdio (local `uvx`/node) — on Windows test in a plain shell first per `reference/install-guide.md` (Windows notes). `.mcpb` one-click via `BWB03/keepa-adapter` is the lowest-friction path. No hosted HTTP MCP.

## Auth / keys
Key from keepa.com dashboard after subscribing (no free tier for the API — the website's product graphs are free, the *API* is not). Key-bearing → one-line hygiene: never `browser_snapshot` the key page (renders plaintext in DOM); have the user copy → clipboard, edit `~/.claude.json` directly, verify by length only. Full rules in `reference/install-guide.md` (Secret-handling hygiene).

## Usage — call examples
MCP exposes ASIN/product lookups (e.g. `query_product` / `get_product` by ASIN + domain code: 1=US, 3=DE, 4=FR…). Minimal: ask MCP for ASIN `B0XXXXXXXX`, domain US, with history=1 → returns price/BSR/BuyBox CSV arrays. Direct REST alt: `https://api.keepa.com/product?key=KEY&domain=1&asin=B0...&history=1`.

## General experience & gotchas (踩坑)
- **Token economy is the real cost, not the €49.** Each product pull burns tokens; history + offers + Buy Box cost more. Pull narrow, batch, watch the per-minute refill — large sweeps stall.
- Sales numbers everywhere in ecom are **estimates** — Keepa's BSR→sales conversion can differ from Helium 10 / Jungle Scout by *multiples*. Cross-check, never quote a single tool's figure as fact.
- keepa.com is **bot-hardened** (pricing page 403s WebFetch) — you cannot scrape it as a workaround; paid API is the only programmatic path.
- Domain code is mandatory and easy to get wrong (US vs DE diverge); a missing `history=1` silently returns spot-only.

## Failure signals & fallback
Failure: MCP `✗ Failed` / `! Needs authentication` in `claude mcp list`, HTTP 401 (bad key), or empty history arrays (token-starved / wrong domain). **Fallback for live prices:** playwright MCP or Camelcamelcamel page fetch — but accept you lose all back-history. There is no equivalent for deep history; flag the gap in the report.

## Last verified: 2026-06
