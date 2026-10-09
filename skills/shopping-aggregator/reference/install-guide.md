# Install guide, shopping-aggregator (Level 0 / overview)

Use this guide for shopping-specific source setup. Shared installation mechanics
remain in the market-intel guide linked below.

> **Shared L0 installation mechanics:**
> The three install levels below, prerequisites, MCP transport types, the `claude mcp add`
> mechanics, secret-handling hygiene, and Windows-specific notes are documented authoritatively
> at:
>
> [market-intel install-guide](https://github.com/DaizeDong/market-intel/blob/main/skills/market-intel/reference/install-guide.md)
>
> Read it first for shared mechanics, then use the shopping-specific instructions below.

## The three levels, where to look

Same scheme as market-intel:

| level | file | holds |
|---|---|---|
| **L0 overview** (this file + market-intel's install-guide) | mechanics inherited + shopping-specific deltas below | how to install anything in general (market-intel's) + the shopping-specific tool kinds (here) |
| **L1 per-domain** | `reference/volatile/pricing-install.md` + each `domains/<domain>.md` "Install guidance" line | exact install command + price per shopping source |
| **L2 per-tool** | `reference/tools/<slug>.md` → `## Install` | install + auth + usage + gotchas for one specific tool. Find the slug in `reference/tools/index.md`. |
| **L3 ops state (recommended)** | your config root in a private companion repo ([CONFIG.md](../../../CONFIG.md)): `registry.json` and `profile.json` | which tools *you* installed, *your* memberships and store credit, which retailers the agent may check out at |

## Shopping tool categories

Shopping sources use four installation routes:

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
subscription), the skill **cannot detect**. Read the selected config root first (`registry.json`
tools, `profile.json` memberships and accounts) and ask only about what it does not list:

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

## Shopping-specific routing

Use the shared secret-handling, transport and Windows procedures. Shopping adds
these source-selection and configuration rules:

- **`firecrawl` skill is NOT enough for Amazon/Taobao** (anti-bot / login-wall). Always route
  to **playwright** for those two retailers. Other JS-static retailer pages (Best Buy, Home
  Depot) firecrawl handles fine.
- **playwright MCP is the default for live e-commerce price reads**; market-intel's matrix
  also favors it but for different reasons (acting human / cookie state).
- The **L3 config root** has its own schema here, not market-intel's: [CONFIG.md](../../../CONFIG.md)
  defines `profile.json` (memberships, ship-to, accounts, purchase defaults), `registry.json`
  (installed tools) and the run ledgers, and `python scripts/init_config.py` creates one.

## Cross-reference with market-intel

| Need | Where |
|---|---|
| Secret-handling requirements | market-intel install-guide § Secret-handling hygiene |
| MCP transport preference (HTTP vs stdio, Windows flakiness) | market-intel install-guide § MCP transport types |
| `claude mcp add` two-ways procedure (with vs without key) | market-intel install-guide § Adding an MCP |
| Verifying an install (current-session operation, authentication and content) | market-intel install-guide § Verify an install |
| Windows-specific gotchas | market-intel install-guide § Windows-specific notes |
| Bootstrap a private config root | `python scripts/init_config.py`, then [CONFIG.md](../../../CONFIG.md); the companion contract is [guards/COMPANION.md](../../../guards/COMPANION.md) |
| Shopping-tool categories (browser ext, mobile app, OSS) | this file ↑ |
| Per-retailer install entry points (Amazon / Taobao / JD / etc.) | `domains/<domain>.md` |
| Per-tool install + gotchas | `tools/<slug>.md` (slug in `tools/index.md`) |
