# Tool: Camelcamelcamel (+ Camelizer extension)

- **Domain(s):** amazon-us
- **Barrier route:** ① free site · **Source tier:** L1 · **Ready MCP:** no (web fetch via playwright)
- **Cost:** free; no API; no paid tier
- **Repo / Provider:** camelcamelcamel.com (maintained by Cosmic Shovel Inc.) · Camelizer Chrome/Firefox extension
- **Top pick for its domain:** yes (for free history)

## What it does / when to pick it
The **free Amazon history** workhorse. 90-day / 365-day / all-time low + history chart, ASIN-level, for Amazon US / CA / UK / DE / ES / FR / IT / AU. Pick it whenever the user wants "is this a good deal" without paying for Keepa. For programmatic batch sweeps Keepa wins; for one-shot consumer lookups Camelcamelcamel is plenty.

## Install
Web: just `camelcamelcamel.com/product/<ASIN>` (or paste URL on the site). Browser extension: search "Camelizer" on the Chrome Web Store / Firefox Add-ons. Mobile: **Android app exists, no iOS app** (long-standing gap; iOS users use the web).

## Auth / keys
None. Free, anonymous. Optional account for email price-drop alerts.

## Usage — call examples
- **From the skill**: instruct a playwright subagent to fetch `https://camelcamelcamel.com/product/<ASIN>` and extract the 90d/365d/all-time low spans + the in-line price-history chart. The page renders server-side; rate-limit politely (don't smash with concurrent fan-out).
- **From the user**: install Camelizer; on any Amazon PDP a small icon shows the price chart inline.

## General experience & gotchas (踩坑)
- **Data update lag**: history typically refreshes daily, not real-time. For "right now" use playwright on amazon.com; use Camel for context.
- **3P-seller listings** sometimes have sparse data — main coverage is amazon-direct + warehouse + major sellers.
- **No public API** — the company has not offered one historically. If you need batch, use Keepa.
- **Price-drop email alerts** are free and reliable; recommend to user as "watch this product" alternative to a paid Keepa subscription.
- **Coverage on lightly-trafficked SKUs** can be patchy (few datapoints).
- **The site uses cloudfront + may rate-limit aggressively from datacenter IPs** — use playwright with residential / consumer-tier proxy if hitting it from a server. For ad-hoc consumer queries, fine.

## Failure signals & fallback
404 / "we don't have this product" → either Amazon de-listed the ASIN or Camel hasn't indexed it. **Fallback:** Keepa for deeper coverage (paid), or accept "no history available" and flag the gap.

## Last verified: 2026-06
