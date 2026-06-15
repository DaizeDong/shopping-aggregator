# Install guide — shopping-aggregator sources & MCP servers (Level 0 / overview)

This is the **top of a three-level install system**. Most shopping-aggregator sources need a
one-time setup (an MCP server, an API key, a browser extension install, or a cloned OSS repo).
This file holds the *mechanics that apply to everything*; the exact per-tool command + price
lives one level down.

> ⚠️ Commands and prices rot. This file holds stable **mechanics**; the volatile exact commands
> live in `reference/volatile/pricing-install.md` (time-stamped — verify against the official
> site before running). **A newly added MCP only takes effect after a session restart / `/mcp`
> reconnect.**

## The three levels — where to look

| level | file | holds |
|---|---|---|
| **L0 overview** (this file) | `reference/install-guide.md` | prerequisites, MCP transport types, the `add` mechanics, secret hygiene, Windows notes, how to verify |
| **L1 per-domain** | `reference/volatile/pricing-install.md` (+ each `domains/<domain>.md` "Install guidance" line) | exact install command + price for every source, grouped by domain |
| **L2 per-tool** | `reference/tools/<slug>.md` → `## Install` | exact steps + auth + gotchas for one specific tool. Find the slug in `reference/tools/index.md` |

Flow: triage the domain → open its shard → for the picked tool, read `tools/<slug>.md` `## Install`
(or the L1 line in `pricing-install.md`) → if it's an MCP, restart/reconnect before using it.

## Tools at THIS layer (specific to shopping-aggregator)

Three categories of "install":

1. **MCP servers** (BigGo, Apify price-intelligence, Keepa, Taobao, Oxylabs) — same `claude mcp
   add` / `~/.claude.json` edit mechanics as market-intel; see "Adding an MCP" below.
2. **Browser extensions** (Capital One Shopping, Karma, Coupert, 购物党, 慢慢买扩展) — user
   installs from Chrome/Edge/Firefox web store. The skill **recommends** them in its output but
   never auto-installs.
3. **Mobile apps** (慢慢买 App, ShopSavvy, Flipp, Slickdeals, SMZDM) — user installs from
   App Store / Google Play. Same recommendation-only flow.
4. **Self-host OSS** (pricebuddy, PriceGhost, PriceDive, Discount-Bandit) — `git clone` +
   `docker compose up -d` or `pip install`; see per-tool docs.

## Prerequisites (install once, reused by everything)

Same as market-intel's:

| prereq | why | check |
|---|---|---|
| **Node.js ≥ 18** (`npx`) | most stdio MCPs ship as npm packages | `node -v` |
| **Python ≥ 3.10 + uv** (`uvx`) | `uvx`-launched MCPs (BigGo) + pip OSS (PriceDive) | `uv --version` |
| **gh CLI** (authenticated) | repo verification (refresh-protocol checks last-commit) | `gh auth status` |
| **git** | clone self-host OSS repos | `git --version` |
| **playwright MCP** | ④ default — almost always connected; primary fan-out tool for live prices | `claude mcp list` |
| **Docker (optional)** | self-host OSS (pricebuddy, PriceGhost, Discount-Bandit) | `docker --version` |

## MCP transport types — which to prefer

- **HTTP (hosted/remote)** — `claude mcp add --transport http <name> <url>`. **Prefer this on
  Windows**: no local Node/uv process, far fewer flakes. Apify price-intelligence and Bright Data
  ship hosted MCP URLs.
- **stdio (local `npx`/`uvx`)** — launches a local process per call. Works but **flaky on
  Windows**. BigGo MCP and Keepa MCPs are stdio — use only when there is no HTTP option.

## Adding an MCP — two ways

1. **`claude mcp add -s user <name> ...`** — convenient. ⚠️ But it **echoes the full command**
   (incl. any key in `--header`/URL) to stdout → the key lands in the transcript.
   **Never use this for a secret-bearing source.** Fine for no-key sources (BigGo MCP).
2. **Direct `~/.claude.json` edit** — for **secret-bearing** MCPs (Apify, Keepa, Oxylabs), write
   `mcpServers.<name>.headers`/`url` straight from the OS clipboard with a tiny no-echo script
   (see hygiene below).

## Secret-handling hygiene — HARD rules

A key must **never enter the transcript** (it can sync to the user's cloud backup). Inherited
directly from market-intel — same operational rules; the consequences (cloud-sync exposure) are
the same.

- **NEVER `browser_snapshot` a page that displays a key.** Provider dashboards render the API key
  in **plaintext in the DOM** (confirmed cases: twitterapi.io rotation page, Bright Data
  API-keys table — both 100% reproducible per the market-intel install-guide). Instead: have the
  user click the page's **copy button**, read the OS clipboard (`powershell Get-Clipboard`), pipe
  it in, and **verify by length only — never print the value**.
- **For secret-bearing MCPs, do NOT use `claude mcp add`** (it echoes the `--header`/URL with the
  key). Edit `~/.claude.json` directly: a tiny python script reads the clipboard and writes
  `mcpServers.<name>.headers.Authorization` (or token-in-URL), with **no echo**.
- **Mask tokens when verifying**: token-in-URL servers print the token in `claude mcp list` → pipe
  through `sed -E 's/token=[^ &]*/token=***/'`.
- **Rotation cooldowns**: if a key leaks, rotate it — but check the provider's cooldown. A truly
  transcript-clean key = the **user** rotates from their own browser, not the agent.
- **Keys land plaintext in `~/.claude.json`** — never commit/screenshot it. The skill holds the
  *procedure*, not the key. Prefer `-e KEY=$VAR` forms the **user** runs themselves.

## Verify an install (always do this after adding)

- `claude mcp list` → parse the three-state health: only **`✓ Connected`** is usable. Treat
  **`✗ Failed`** and **`! Needs authentication`** as not available (they fail at call time).
- Mask any token first: `claude mcp list | sed -E 's/token=[^ &]*/token=***/'`.
- `claude mcp get <name>` for per-server detail.
- **Tool-name prefix matching is unreliable** — use `claude mcp list` as primary signal.

## User-side tool detection (no automation)

For browser extensions / apps / accounts (Capital One Shopping, Honey, 慢慢买 App, Keepa
subscription), the skill **cannot detect**. Ask the user:

> "Do you already have any of these installed: Capital One Shopping / Karma / Honey / 慢慢买 App
> / a Keepa subscription? If yes, I'll use them; if no, I may recommend installing one before
> you continue."

Don't push installs the user hasn't asked for. The "we recommend X" line goes in the report's
coverage-gaps section, not as a mid-flow blocker.

## Install by tool kind

| kind | install looks like | cost shape | restart needed? |
|---|---|---|---|
| MCP (stdio, no key) | `claude mcp add ... -- uvx X@latest` | free | yes |
| MCP (HTTP, with key) | edit `~/.claude.json` directly | pay-per-call or subscription | yes |
| Browser extension | Chrome Web Store → Add | free | no |
| Mobile app | App Store / Google Play → Install | free or freemium | no |
| Self-host OSS | git clone → docker compose / pip install | LLM key + hosting | n/a |
| API account (Keepa) | sign up → get key → wire into MCP | €49/mo+ | yes |

## Windows notes

- Stdio MCPs (`npx`, `uvx`) flake on Windows — prefer HTTP transports when available.
- PowerShell vs Git Bash: this skill defaults to bash style for commands; on PowerShell adapt
  `Get-Content` for `cat`, `Get-Clipboard` for clipboard reads (already used in secret-handling).
- File paths in `~/.claude.json`: use forward slashes or escaped backslashes. Avoid CRLF
  corruption — edit with a real editor or `python` script, not raw `echo >>`.

## Cross-reference with market-intel

This shopping-focused install-guide intentionally re-uses market-intel's secret-handling rules
and MCP transport mechanics verbatim — those are skill-agnostic. For shopping-side-specific
additions (extensions, mobile apps, OSS docker), this file is authoritative.
