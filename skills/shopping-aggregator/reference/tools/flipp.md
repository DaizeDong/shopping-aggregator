# Tool: Flipp

- **Domain(s):** mobile-apps-aggregators
- **Barrier route:** ① official aggregator · **Source tier:** L2 · **Ready MCP:** no
- **Cost:** free
- **Repo / Provider:** flipp.com, iOS + Android, US + Canada
- **Top pick for its domain:** yes for **grocery + drugstore weekly circular**

## What it does / when to pick it
Aggregates 2000+ US/CA retailers' weekly circulars + flyers into a searchable app. Great for:
- "Is X on sale this week at <local grocer>?"
- "What's on sale at Target / Walmart / CVS / Walgreens this week?"
- Match-and-stack with coupon apps for grocery deal stacking.

Pick when buy intent is **grocery / drugstore / weekly-deal** category. For tech / appliances use the retailer-direct domains.

## Install
App Store / Google Play "Flipp". v99.1 (Jun 2026), 4.8★ / 518K reviews.

## Auth / keys
Free, optional account for clipping / shopping list sync.

## Usage, call examples
**User-side mostly.** Agent path: WebFetch `https://flipp.com/<region>/search/<query>` for matching flyer items, but the app experience is significantly richer than the web. For grocery price-compare, recommend Flipp + open the user's local zip-code-filtered view.

## General experience & gotchas (踩坑)
- **Geo-filter matters**, flyers are location-specific. Always set the user's zip code first (Flipp asks on first launch).
- **Weekly cycle**, flyers refresh Wednesday/Thursday at most chains; checking Monday = looking at next-week's leaks (sometimes).
- **Weak distance filter**, "near me" radius isn't very tunable; small chains may not be indexed at all.
- **Some grocers run app-only digital coupons** not in the flyer, Flipp won't show those. Pair with the retailer's own app (Kroger app, Target Circle, etc.).
- **Canada coverage** is solid (Flipp originally Canadian).

## Failure signals & fallback
Local grocer not indexed; flyer not yet posted for the upcoming week. **Fallback:** retailer's own app (Kroger / Walmart / Target / CVS / Walgreens), they all show in-app weekly deals.

## Last verified: 2026-06
