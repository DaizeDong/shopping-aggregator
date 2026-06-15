# Tool: Capital One Shopping (browser extension)

- **Domain(s):** browser-extensions
- **Barrier route:** ① free service · **Source tier:** L2 · **Ready MCP:** no (user-installed extension)
- **Cost:** free
- **Repo / Provider:** capitaloneshopping.com (Capital One; acquired Wikibuy 2018)
- **Top pick for its domain:** yes (US default coupon + price-compare extension post-Honey crisis)

## What it does / when to pick it
**The recommended Honey replacement.** On a product page (PDP) it shows: cross-retailer price comparison, automatic coupon application at checkout, price-drop alerts (per-product watchlist), Capital One Shopping rewards (in-house cashback). Healthy and growing post-Honey lawsuit. **Recommend by default for US users**, especially those still running Honey.

## Install
Chrome / Edge / Firefox web stores: search "Capital One Shopping" → click Add. No Capital One credit card required (despite the name). Sign-in with email; rewards balance tied to account.

## Auth / keys
None for install. Account required to redeem rewards (free email signup).

## Usage — call examples
N/A for the agent — this is a **user-side extension**. The skill should *recommend* it during the install-guide phase (Step 4), not invoke it.

## General experience & gotchas (踩坑)
- **Tracks browsing + transaction history** to fuel its coupon database — privacy-aware users may want to read the policy first. Not unique to Capital One Shopping (every extension in this space does it), but worth flagging.
- **Affiliate-link rewrite** at checkout — same mechanic as Honey, but currently no lawsuit / no merchant terminations. If user already gets a creator/Reddit coupon link, extension can overwrite it; price still applies but the original referrer loses commission.
- **Coverage on Amazon is good** (unlike Rakuten, which excludes Amazon). On Walmart/Target/Best Buy/Home Depot extensive.
- **Price-drop alerts** are reliable; competitive with native retailer alerts and Camelcamelcamel email.
- **Two-extension conflict**: don't run alongside Honey, Karma, or Rakuten — they fight over the same affiliate slot at checkout, and the one that loads last wins.
- **Capital One credit card holders get a small rewards multiplier** — useful niche, not a deal-breaker for non-cardholders.

## Failure signals & fallback
None really for the agent — it's a passive user-side tool. If the user reports "Capital One Shopping says it saved me $X but I don't see the discount" → check whether the code was actually applied at checkout (the badge "savings calculated" is sometimes shown before code apply succeeds). **Fallback recommendation:** Karma (similar functionality) or Coupert (slightly different network).

## Last verified: 2026-06
