# Tool: Reddit deal subs (r/buildapcsales + r/deals)

- **Domain(s):** mobile-apps-aggregators
- **Barrier route:** ④ community/scrape · **Source tier:** L3 (unmoderated community) · **Ready MCP:** no
- **Cost:** free for low volume (OAuth) · commercial high-usage **$0.24 / 1K calls**
- **Repo / Provider:** reddit.com/r/buildapcsales · reddit.com/r/deals · API docs reddit.com/dev/api
- **Top pick for its domain:** **no**, this is a **DISCOVERY / E3 lead** tier, never an E1 ranked winner

## What it does / when to pick it
Two community deal feeds: **r/buildapcsales** (US PC/GPU/CPU/SSD drops, the canonical signal for parts deals) and **r/deals** (general US-leaning deals). Pick for **discovery of deals the user wasn't searching for**, especially fast-moving tech drops. **Weakest verification tier of the aggregators**, unmoderated relative to Slickdeals' vote-curation and DealNews' editor-vetting; GPU/CPU drops are gone in minutes (bot resellers). Anything found here is a **lead (E3)** to re-fetch at the retailer to **E1** before it can be a ranked winner, never quote a Reddit post as the live price.

## Install
- **Web/app**: just browse the subs; sort by **New** for live drops, **Hot** for vetted-by-upvote.
- **Public JSON (no key, fragile)**: append `.json` to any listing URL, e.g. `https://www.reddit.com/r/buildapcsales/new.json?limit=25`. Unauthenticated traffic is throttled/blocked, fine for an occasional WebFetch, not for polling.
- **OAuth API (for repeated reads)**: register an app at reddit.com/prefs/apps → get client ID/secret → OAuth2 → call `oauth.reddit.com/r/<sub>/new`.

## Auth / keys
- Public `.json`: none, but **heavily rate-limited / may be rejected** (Reddit blocks unidentified Data API traffic).
- OAuth (recommended for any repeat use): client ID + secret + Bearer token. Treat as secret; env var only.
- **Since 2023 Reddit also requires app pre-approval for API access**, a registered, identified client is effectively mandatory.

## Usage, call examples
**agent (default)**: WebFetch `https://www.reddit.com/r/buildapcsales/new.json?limit=25` or `https://www.reddit.com/r/deals/hot.json?limit=25`; parse `data.children[].data` for `title`, `url`, `created_utc`, `score`. For a single thread add `.json` to the permalink to read comments (deal-validation: "code dead", "OOS").

## General experience & gotchas (踩坑)
- **DISCOVERY / E3 only, not an E1 winner.** A Reddit post is a *lead*. Re-fetch the linked retailer PDP to E1 before ranking or quoting price; the post title price is often stale within minutes.
- **2023 rate-limit regime (still in force):** **100 QPM per OAuth client ID** (averaged over a 10-min window for bursts) · **10 QPM unauthenticated** · high-usage commercial billed **$0.24/1K calls**. Over the cap → **HTTP 429**.
- **OAuth effectively mandatory**, unauthenticated `.json` is throttled/blocked and enforcement is *erratic* (real behavior doesn't match the documented numbers; build defensive retry/backoff).
- **Bot resellers gut GPU/CPU drops in minutes**, r/buildapcsales is the signal, not the buying floor. Sort **New** + act fast, or just use it to know a sale exists.
- **Unmoderated noise**, lower curation than Slickdeals/DealNews; read comments for "is this live" before clicking.
- **Affiliate / referral links** appear in some posts, extract the underlying retailer URL.

## Failure signals & fallback
HTTP 429 (rate-limited; back off), 403 (unauthenticated blocked), stale/expired linked deal, empty `.json`. **Fallback:** Slickdeals (vote-curated, stronger signal), DealNews (editor-vetted), SMZDM (CN equivalent); for the actual price always re-fetch the retailer to E1.

## Last verified: 2026-06
