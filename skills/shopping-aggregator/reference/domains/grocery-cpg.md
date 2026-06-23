# Domain: grocery-cpg

**Triage signals:** groceries / CPG / household staples, "is Instacart marked up", "Kroger fuel
points worth it", "Target Circle vs in-store", "ShopRite / Wegmans / Costco grocery deal",
"cheapest place for <pantry item> near me", "Amazon Fresh vs Whole Foods delivery", weekly
grocery circular, EBT/SNAP delivery. **Demand-side, hyper-local:** grocery economics are dominated
by *which banner operates in the user's ZIP* and *which loyalty/fuel program they're enrolled in* —
NOT a single national price. Always pin the user's region before quoting a number.

> **HYPER-REGIONAL WARNING.** Unlike amazon-us (one national marketplace), grocery is a patchwork of
> regional cooperatives and banners. ShopRite (NJ/NY/PA/CT/MD/DE), Wegmans (Mid-Atlantic/Northeast),
> Kroger family (~35 states under 20+ banner names), H-E-B (TX only), Publix (Southeast) etc. do NOT
> overlap. A price/program quoted for one banner is **invalid** outside its footprint. Confirm the
> banner+ZIP before any number leaves your mouth. Loyalty mechanics (fuel points, circulars, digital
> coupons) are also banner-specific.

## Routing

| source | route | capability | detect | risk |
|---|---|---|---|---|
| **Flipp** ([flipp.md](../tools/flipp.md)) | ① free | local weekly circulars + cross-store matchup for ANY US/CA grocery banner by ZIP; loyalty-card + coupon clip | app / app.flipp.com, enter ZIP | low; discovery tool, weak for live cart total |
| **playwright MCP** | ④ | live banner price + Instacart storefront badge + cart-test delivery fee + digital-coupon state (logged in) | `claude mcp list` → `playwright ✓` | low; needs user's loyalty login for personalized prices |
| Instacart storefront (per-retailer) | ④/① | each retailer's posted pricing-policy badge + live marked-up price | open retailer page on instacart.com | low; price ≠ in-store (see below) |
| Banner native app/site (Kroger, ShopRite, Wegmans, Target) | ① | authoritative loyalty balance, fuel points, digital coupons, weekly ad for the user's store | banner app, logged in | low; the source of truth for that banner |

**Default pick:** **Flipp ① for cross-banner weekly-deal discovery** (it already knows the user's
ZIP→banner map) + **the banner's own app ① for loyalty/fuel/coupon truth** + **playwright ④** only
when you need a live Instacart cart total or to verify a markup badge. Do NOT quote Instacart prices
as if they were shelf prices.

---

## Instacart — per-retailer markup policy (the big trap)

**Retailers set their own Instacart prices; some add a markup, some don't.** There is no single
"Instacart markup %." Each storefront shows a **pricing-policy badge** under the retailer logo:
- **"In-store Prices" / "Everyday Store Prices"** badge → no in-app markup (price matches shelf).
- **"View pricing policy"** / markup disclosed → retailer (or Instacart, within an agreed range)
  marks items up above shelf price.
[instacart.com/help item-pricing](https://www.instacart.com/help/section/360007902791/360039572851);
[Truth About Pricing Tests](https://www.instacart.com/company/updates/the-truth-about-pricing-tests-on-instacart).

- Markup is **on top of** Instacart's separate delivery + service fees + tip — landed cost stacks.
- **Late-2025 change:** Instacart **ended item price tests** (Eversight) — same store/time/items now
  shows the **same price to all users** (no more per-user A/B price discrimination).
  [Ending Item Price Tests](https://www.instacart.com/company/updates/ending-item-price-tests-on-instacart). VERIFIED 2026-06.
- Third-party reporting (The Markup, ~11 retailers) found avg markup ~17.5%, up to ~25%; Costco-via-
  Instacart cases ~34%. **evidence: medium** (journalism, not Instacart's official figure — Instacart
  does not publish a headline markup number). Treat as order-of-magnitude, verify the live badge.
- **Action:** read the badge on the user's actual retailer storefront; if marked-up, surface
  in-store / pickup as the cheaper alternative.

## Kroger Fuel Points (Kroger family of stores — multi-banner)

Applies across the Kroger family (Kroger, Ralphs, Fred Meyer, King Soopers, Smith's, Fry's, QFC,
Harris Teeter, etc. — **banner names differ by region**).
[Fuel Points Program](https://www.kroger.com/d/fuel-points-program) ·
[Fuel Program FAQs](https://www.kroger.com/o/fuel/faqs). VERIFIED 2026-06.
- **Earn:** 1 point / $1 on most groceries (pre-tax, before fees; pickup/delivery fees don't earn).
- **Gift cards:** 2x points (4th-party-funded; a classic stacking lever).
- **Boost membership:** 2x points on every purchase.
- **Bonus fuel events:** up to 4x points.
- **Redeem:** 100 points = 10¢/gal off, in 100-pt increments, up to 1,000 pts = $1/gal off, on up
  to 35 gallons per fill. Redeemable at Kroger fuel centers + participating Shell (Shell capped at
  100 pts = 10¢/gal). Shopper's-card swipe also gives a base ~3¢/gal even with 0 points.
- **Expiry (the gotcha):** points expire the **last day of the month AFTER** they're earned (May
  points die June 30). Balances do NOT roll/combine across months. Burn before month-end.

## Target Circle (national; not regional)

[About Target Circle](https://www.target.com/help/articles/target-circle/about-target-circle) ·
[Target Circle Bonus](https://help.target.com/help/subcategoryarticle?childcat=Target+Circle+Bonus&parentcat=Target+Circle%E2%84%A2&searchQuery=). VERIFIED 2026-06.
- **The flat 1% earnings/cashback is DISCONTINUED** (removed after the Apr-2024 relaunch). Do NOT
  tell users they earn 1% back — that model is dead. **evidence: high** (Target help + multiple
  trade reports; exact final-removal date for all accounts not pinned — note if user has a legacy
  balance, it expires 1 yr after earning).
- **Now:** free membership → auto-applied deals + **personalized "Circle Bonus" offers** (e.g.
  "spend $100 get $15") that must be **activated** on the Deals page before checkout (not automatic).
- Bonuses can pay out as **Target Circle Rewards** (formerly "earnings") → apply to a future
  purchase; **expire 1 year** if unredeemed.
- Free-tier perks: 5% birthday discount (valid 30 days), community-giving votes, brand partner deals.
- **Circle 360** = paid tier (~$99/yr, was the Shipt-backed same-day): unlimited same-day delivery
  from Target + 100+ Shipt-network retailers. **evidence: medium on exact 2026 price — VERIFY live
  at target.com/circle-360 before quoting the fee** (pricing/promo has shifted; not re-confirmed this pass).

## Amazon Fresh / Whole Foods (national, Prime-gated)

[Amazon Fresh & WFM Delivery help](https://www.amazon.com/gp/help/customer/display.html?nodeId=GB4P4BZ9FYDGRV6X) ·
[WFM Amazon benefits](https://www.wholefoodsmarket.com/amazon). VERIFIED 2026-06.
- **Prime:** $14.99/mo or $139/yr (Young Adult/student: 6-mo free trial → $7.49/mo or $69/yr).
- **WFM / Fresh 2-hour delivery (Prime):** free over $100; under $100 a service fee applies
  ($6.95 for $50–$100, $9.95 under $50, per the help page). Non-Prime ~$4.95–$13.95 by basket size.
- **Same-Day (Prime):** free over $25, else $2.99; non-Prime $12.99 flat.
- **Grocery delivery subscription (add-on):** ~$9.99/mo or ~$99.99/yr → free delivery over $25 from
  WFM, Fresh, and partner retailers. **Prime Access / EBT-registered: discounted ~$4.99/mo.**
- WFM-specific annual: ~$59.99 intro for a year of $0-fee deliveries (auto-renews ~$99.99/yr).
  **evidence: medium on the $59.99 intro / exact add-on fee — promo-priced, VERIFY live at checkout
  for the user's market before quoting.** Pickup is free for all.
- Prime members: extra **10% off sale items** in-store at Whole Foods.

## Regional banners (HYPER-REGIONAL — footprint-pin before quoting)

| banner | footprint (VERIFY ZIP) | loyalty | notes |
|---|---|---|---|
| **ShopRite** | NJ, NY, PA, CT, MD, DE only (Wakefern co-op, Keasbey NJ) | **Price Plus Club** (free): instant in-store cash discounts + personalized digital coupons clipped to card; "Digital Price Plus Perks" | offers vary by store; circular is per-store, not regional. [Price Plus Club](https://www.shoprite.com/priceplusclub) · [Digital coupons](https://www.shoprite.com/digital-coupon). VERIFIED 2026-06 |
| **Wegmans** | Mid-Atlantic/Northeast, ~112 stores; **2026: Atlanta GA entry planned** | **Shoppers Club** (free): clip digital coupons, auto member discounts, aisle-sorted lists, recipes | two apps: **Wegmans app** (grocery) vs **Meals 2GO** (prepared food, separate). [Shoppers Club](https://www.wegmans.com/service/shoppers-club). VERIFIED 2026-06 (store count "as of Jul 2025" per Wegmans — evidence: high; Atlanta-2026 from 3rd-party analysis — evidence: medium, not Wegmans official) |
| **Costco** | national warehouse (membership-gated) | **Gold Star $65/yr**; **Executive $130/yr** = +$65 upgrade → **2% annual reward, cap raised to $1,250** | reward excludes gas/tobacco/alcohol/gift cards/fees; break-even ~$3,250/yr spend (refund guarantee if reward < $65). Executive: $10/mo Instacart credit (orders >$150) since 2025-06-30. [Membership types](https://customerservice.costco.com/app/answers/answer_view/a_id/857/) · [Executive Rewards](https://www.costco.com/executive-rewards.html). VERIFIED 2026-06 |

**General regional-banner method:** (1) get the user's ZIP, (2) confirm which banner(s) operate
there (Flipp's ZIP map or a quick web check), (3) read THAT banner's loyalty/circular page, (4)
never carry a number across banner boundaries.

## Grocery-specific gotchas

- **Instacart price ≠ shelf price** — always check the storefront badge; pickup usually avoids markup.
- **Loyalty card required** — most "sale" prices on ShopRite/Wegmans/Kroger need the card scanned;
  digital coupons must be **clipped before checkout**, not auto-applied.
- **Fuel points expire monthly** (Kroger) — a balance is worthless if the fill-up is next month.
- **Target's 1% is gone** — don't quote it; bonuses must be activated, rewards expire in 1 yr.
- **Membership math** — Costco Executive / Amazon grocery-sub only pay off above a spend threshold;
  compute break-even for the user's volume, don't assume.
- **Footprint mismatch** — the #1 grocery error is quoting a banner the user can't actually visit.

## When you'd switch off this domain

Non-grocery durable goods (electronics, apparel) → route to amazon-us / ebay-walmart-target /
browser-extensions instead. Chinese grocery/CPG → taobao-tmall / jd-pdd. Pure deal *discovery*
across all categories → mobile-apps-aggregators (Flipp/Slickdeals), then come back here for the
grocery loyalty/markup mechanics.

## Last verified: 2026-06
