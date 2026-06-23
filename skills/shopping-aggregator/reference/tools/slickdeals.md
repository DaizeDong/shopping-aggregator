# Tool: Slickdeals

- **Domain(s):** mobile-apps-aggregators, browser-extensions
- **Barrier route:** ① community-curated · **Source tier:** L2 · **Ready MCP:** no
- **Cost:** free (ad + affiliate funded)
- **Repo / Provider:** slickdeals.net — Goldman Sachs / Hearst-owned, ~12M members
- **Top pick for its domain:** yes for **US deal discovery + community signal**

## What it does / when to pick it
The strongest US deal-aggregation community. Members post deals, others vote / comment / verify; frontpage = top-voted active deals. Best for **discovery** ("is there a deal on iPad Pro this week") and **community verification** ("is this Costco TV deal a real markdown or fake-sale"). Weak for SKU-level live comparison (use the price-fetch domain shards for that).

## Install
- **Web**: slickdeals.net, browse Frontpage.
- **iOS/Android app**: v6.26+ Jun 2026 — same content, alerts.
- **Chrome extension**: shows deal flags on PDPs across retailers.
- **Email alerts**: keyword-based "watch for deals on X" — alternative to Camelcamelcamel.

## Auth / keys
Browsing anonymous; commenting/posting/alerts need a free account.

## Usage — call examples
**agent**: WebFetch `https://slickdeals.net/?s=<keyword>` for search results, or `https://slickdeals.net/<deal-slug>/` for a single deal page (votes, comments, expiration). Frontpage at `slickdeals.net/forums/forumdisplay.php?f=9`. **Affiliate redirects** are added to outbound retailer links — agent can ignore or extract the underlying URL.

## API / feed access — verification (checked 2026-06)
Question: does Slickdeals expose a public RSS / undocumented JSON / affiliate feed an agent can hit without a partnership? Answer below; **no free public developer API** — use RSS for the agent, the partner API only if the user is a syndication partner.

- **RSS feeds — yes, free, the agent route.** Slickdeals provides built-in RSS (and RSS v2) for the **frontpage** and for **forum threads** (where the forum admin enabled syndication). Front-page feed is the one third-party deal sites poll. Convert RSS→JSON with a generic tool if needed. This is the no-auth path for an agent — use it instead of scraping HTML when you just want the top-deals stream. (Source: Slickdeals Help Center "How to Use RSS feeds"; RSS.app Slickdeals feed generator.)
- **Official API — exists, but partner-only, not a public dev API.** Slickdeals runs a **token-based syndication/affiliate API** (`corp-site.slickdeals.net/api-sales/`, `/api-resources/`) serving **deals, coupons, and articles** from 10,000+ merchants, with **social signals** (likes, comments, views, popular flags) and **filters** (store, category, sale/final price). Access = "grab a token from the Slickdeals team" → **you must contact their sales team**; it is positioned as a **monetization/partner program (they pay you)**, not a self-serve paid API. No public signup, no published rate card. Use only if the user is/becomes a syndication partner. (Source: corp-site.slickdeals.net/api-sales/ + /api-resources/.)
- **Internal search API** (`search.sd-disco-prod-cluster…slickdeals.net/api`) returns `json|html` and has Swagger/GraphiQL docs, but it is an **undocumented internal endpoint** — not a stable contract, may change/break without notice; do not depend on it for production. Prefer RSS or the partner API.
- **Net:** for an autonomous agent → **RSS front-page feed** (free, no key). For monetized affiliate/syndication → **partner API via sales contact**. There is **no public free JSON developer API**; structured-JSON-without-partnership falls back to third-party scrapers (Apify Slickdeals actors, ScrapingBee) — outside official channels.

## General experience & gotchas (踩坑)
- **Frontpage = signal; Forum = noise.** The frontpage is community-curated by votes; the wider forum has 10-50× more deals but most are mediocre or expired. Default to frontpage for triage.
- **Frontpage Top Deals expire fast** — 10 min after frontpage = often stock-out or pulled.
- **GPU / CPU drops vanish in minutes** (bot resellers). Slickdeals is the canonical signal but not the buying floor.
- **Affiliate links** — outbound clicks via Slickdeals redirect for revenue. Most users don't care; for clean tracking strip the redirect.
- **Deal-validation in comments**: "is this code working" / "got error 503" — read top comments before clicking. The community surfaces failed deals fast.
- **Email keyword alerts** are reliable — set them when user is in "wait for sale" mode.
- **Black Friday megathread** is the canonical year-by-year tracker — better than retailer compilations.

## Failure signals & fallback
Empty search, dead deal links (expired), affiliate redirect breakage. **Fallback:** DealNews (editorial-curated), r/buildapcsales for tech, r/deals for general; SMZDM for CN equivalent.

## Last verified: 2026-06
