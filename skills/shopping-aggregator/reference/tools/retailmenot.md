# Tool: RetailMeNot (browser extension, ex-Genie)

- **Domain(s):** browser-extensions
- **Barrier route:** ① free service · **Source tier:** L2 · **Ready MCP:** no (user-installed extension)
- **Cost:** free (cashback redeemable via PayPal / Venmo)
- **Repo / Provider:** retailmenot.com, RetailMeNot, Inc. (Austin TX; Vericast/Valassis-owned)
- **Top pick for its domain:** no (secondary coupon/cashback option behind Capital One Shopping + Karma)

## What it does / when to pick it
Auto-finds, tests, and applies the best promo codes + RetailMeNot Cash Back offers at checkout, stacking cashback on top of an eligible code. Covers 20,000+ brands (Target, Sephora, Macy's, Best Buy). The **"Genie"** extension RetailMeNot launched in 2017 was retired into the current consolidated listing, the Chrome Web Store extension is now named **"RetailMeNot: Codes, Cash Back and Coupons"** (same ID `jjfblogammkiefalfpafidabbnamoknm`). Pick when a user specifically wants RetailMeNot's coupon DB / cashback portal; otherwise the default pair (Capital One Shopping + Karma) covers the same ground with fewer popups.

## Install
Chrome / Edge / Firefox web stores: search "RetailMeNot" → Add. Free account for cashback redemption (PayPal / Venmo payout).
- Chrome Web Store: `chromewebstore.google.com/detail/retailmenot-codes-cash-ba/jjfblogammkiefalfpafidabbnamoknm`
- Firefox: `addons.mozilla.org/en-US/firefox/addon/retailmenot/`

## Auth / keys
None for install. Email account for cashback payout.

## Usage, call examples
N/A for the agent, **user-side extension.** Recommend during install-guide phase, do not invoke.

## General experience & gotchas (踩坑)
- **Survival check (2026-06):** ✓ alive. Chrome listing v4.23.x, last updated **Apr 2026** (build history shows steady 2025-2026 releases: v4.17.x Oct 2025, v4.20.0 Jan 2026); publisher RetailMeNot, Inc. (per chrome-stats / Chrome Web Store).
- **Last-click affiliate trust event, FLAG.** Like Honey, RetailMeNot's extension rewrites the affiliate link / sets its own cashback attribution at checkout. It is **not** under the Honey lawsuit, but it is the same mechanic: it can overwrite a creator/Reddit coupon-link referral or disqualify a competing cashback-portal rebate (Rakuten / Capital One vying for the same checkout slot). State the savings source clearly and never double-count "extension savings" + "public coupon savings", usually the same dollar.
- **Catalog narrowed post-Vericast cuts**, smaller working coupon set than peak; the in-extension "X codes available" badge over-counts working codes, same caveat as every tool in this domain.
- **Intrusive UX**, reviews flag popups + an overlay icon that can't be hidden.
- **Privacy**, requests tabs/all-sites permission (tracks browsing); typical for the category, still worth flagging.
- **Two-extension conflict**, do not run alongside Capital One Shopping / Karma / Honey; they fight over the same checkout affiliate slot and the last-loaded wins.

## Failure signals & fallback
If RetailMeNot reports "saved $X" but no discount lands → verify the code actually applied at checkout (badge shows "calculated" before apply succeeds). **Fallback:** Capital One Shopping or Karma (overlapping function, fewer popups), or Coupert (different coupon network).

## Last verified: 2026-06
