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
