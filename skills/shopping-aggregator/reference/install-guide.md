# Install guide, shopping-aggregator (Level 0 / overview)

This is the **top of a three-level install system** for `shopping-aggregator`'s tool stack.

> 🔗 **Most of L0 install mechanics is inherited from the sister skill, market-intel.**
> The three install levels below, prerequisites, MCP transport types, the `claude mcp add`
> mechanics, secret-handling hygiene, and Windows-specific notes are documented authoritatively
> at:
>
> [market-intel install-guide](https://github.com/DaizeDong/market-intel/blob/main/skills/market-intel/reference/install-guide.md)
>
> Read that FIRST. This document only records the **delta** that's specific to
> shopping-aggregator's tool stack.

## The three levels, where to look

Same scheme as market-intel:

| level | file | holds |
|---|---|---|
| **L0 overview** (this file + market-intel's install-guide) | mechanics inherited + shopping-specific deltas below | how to install anything in general (market-intel's) + the shopping-specific tool kinds (here) |
| **L1 per-domain** | `reference/volatile/pricing-install.md` + each `domains/<domain>.md` "Install guidance" line | exact install command + price per shopping source |
| **L2 per-tool** | `reference/tools/<slug>.md` → `## Install` | install + auth + usage + gotchas for one specific tool. Find the slug in `reference/tools/index.md`. |
| **L3 ops state (recommended)** | per-user private companion repo (see market-intel's [companion-config-repo.md](https://github.com/DaizeDong/market-intel/blob/main/skills/market-intel/reference/companion-config-repo.md)) | which tools *you* installed, *your* tier, *your* key rotation history |

## Tools at THIS layer (shopping-specific kinds)

The four install categories users will hit when configuring shopping-aggregator (different
from market-intel's mix because consumer shopping has more retail-specific tooling):

1. **MCP servers** (BigGo, Apify price-intelligence, Keepa, Taobao, Oxylabs), same
   `claude mcp add` / `~/.claude.json` edit mechanics as market-intel; see market-intel's
   "Adding an MCP" section.
2. **Browser extensions** (Capital One Shopping, Karma, Coupert, 购物党, 慢慢买扩展), user
   installs from Chrome/Edge/Firefox web store. The skill **recommends** them in its output
   but never auto-installs.
3. **Mobile apps** (慢慢买 App, ShopSavvy, Flipp, Slickdeals, SMZDM), user installs from
   App Store / Google Play. Same recommendation-only flow.
4. **Self-host OSS** (pricebuddy, PriceGhost, PriceDive, Discount-Bandit), `git clone` +
   `docker compose up -d` or `pip install`; see per-tool docs.

## User-side tool detection (no automation)

For browser extensions / apps / accounts (Capital One Shopping, Honey, 慢慢买 App, Keepa
subscription), the skill **cannot detect**. Ask the user:

> "Do you already have any of these installed: Capital One Shopping / Karma / Honey / 慢慢买
> App / a Keepa subscription? If yes, I'll use them; if no, I may recommend installing one
> before you continue."

Don't push installs the user hasn't asked for. The "we recommend X" line goes in the report's
coverage-gaps section, not as a mid-flow blocker.

## Install by tool kind (shopping-specific)

| kind | install looks like | cost shape | restart needed? |
|---|---|---|---|
| MCP (stdio, no key) | `claude mcp add ... -- uvx X@latest` | free | yes |
| MCP (HTTP, with key) | edit `~/.claude.json` directly | pay-per-call or subscription | yes |
| Browser extension | Chrome Web Store → Add | free | no |
| Mobile app | App Store / Google Play → Install | free or freemium | no |
| Self-host OSS | git clone → docker compose / pip install | LLM key + hosting | n/a |
| API account (Keepa) | sign up → get key → wire into MCP | €49/mo+ | yes |

## What `shopping-aggregator` deviates from market-intel on

Almost nothing, secret-handling, MCP transport choice, `claude mcp list` health states,
Windows notes are all identical. The few differences:

- **`firecrawl` skill is NOT enough for Amazon/Taobao** (anti-bot / login-wall). Always route
  to **playwright** for those two retailers. Other JS-static retailer pages (Best Buy, Home
  Depot) firecrawl handles fine.
- **playwright MCP is the default for live e-commerce price reads**; market-intel's matrix
  also favors it but for different reasons (acting human / cookie state).
- The **L3 companion repo** pattern works for shopping-aggregator too: replicate the
  market-intel companion-repo layout with a `shopping-aggregator-config/` companion holding Keepa
  subscription, browser-extension install state, etc.

Everything else: read market-intel's install-guide.

## Cross-reference with market-intel

| Need | Where |
|---|---|
| Secret-handling hygiene (the HARD rules learned the hard way) | market-intel install-guide § Secret-handling hygiene |
| MCP transport preference (HTTP vs stdio, Windows flakiness) | market-intel install-guide § MCP transport types |
| `claude mcp add` two-ways procedure (with vs without key) | market-intel install-guide § Adding an MCP |
| Verifying an install (`claude mcp list` parsing) | market-intel install-guide § Verify an install |
| Windows-specific gotchas | market-intel install-guide § Windows-specific notes |
| Bootstrap a private companion config repo | market-intel [companion-config-repo.md](https://github.com/DaizeDong/market-intel/blob/main/skills/market-intel/reference/companion-config-repo.md) |
| Shopping-tool categories (browser ext, mobile app, OSS) | this file ↑ |
| Per-retailer install entry points (Amazon / Taobao / JD / etc.) | `domains/<domain>.md` |
| Per-tool install + gotchas | `tools/<slug>.md` (slug in `tools/index.md`) |
