# Domain: browser-extensions

**Triage signals:** "best coupon extension", "cashback", "Honey", "自动找券", "返利插件".

> **⚠ Critical 2026 update, DO NOT recommend PayPal Honey.** Active MDL (*In Re PayPal Honey
> Browser Extension Litigation*) in discovery; **Rakuten terminated Honey from its 2000+ merchant
> network on 2026-01-12**; Impact / Awin followed; arbitration motion denied 2025-11. The product
> still loads but its actual coupon coverage has been gutted, and it may overwrite the user's own
> affiliate links, installing it can REDUCE earned rewards.

| extension | status (2026-06) | what it does | watch out for |
|---|---|---|---|
| **Capital One Shopping** (ex-Wikibuy) ([capital-one-shopping.md](../tools/capital-one-shopping.md)) | ✓ healthy default | multi-retailer coupon + price-compare on PDP + price-drop alerts; works on Amazon | tracks browsing/transaction history (privacy trade-off) |
| **Karma** ([karma-extension.md](../tools/karma-extension.md)) | ✓ healthy (v10.88 May 2026) | wishlist + price-drop + multi-store; works on Amazon | cashback lower than Rakuten |
| **Coupert** ([coupert.md](../tools/coupert.md)) | ✓ healthy, ~8M users | 200K+ merchants, 70K cashback, ~73% coupon success rate | freemium nudges; sometimes silent affiliate-link rewrite |
| **Rakuten extension** | ✓ healthy | 3500+ stores cashback; **NOT Amazon** | quarterly payout delay; Amazon not covered |
| **Cently** ([cently.md](../tools/cently.md)) | ✓ healthy (v7.36, ~100K users, updated 2026-03) | auto-apply codes at checkout | owned by System1 ad-tech (NextGen Shopping LLC), data concerns |
| **Slickdeals extension** | ✓ healthy (v3.9.1, Jun 2026) | community-deal alerts on PDP | notification noise from forum activity |
| **RetailMeNot** (ex-Genie) ([retailmenot.md](../tools/retailmenot.md)) | ✓ healthy (v4.23.x, Apr 2026; Genie name retired into this listing) | coupon apply + cashback, 20K brands | smaller catalog post-Vericast cuts; last-click affiliate rewrite; intrusive popups |
| **PayPal Honey** | ⚠⚠ **AVOID 2026** | coupon + Honey Gold cashback; covers Amazon | legal MDL active; Rakuten/Impact/Awin terminations gutted catalog Jan 2026; suspected affiliate-link hijack; uninstall recommended |
| **InvisibleHand** ([invisiblehand.md](../tools/invisiblehand.md)) | ⚠ **AVOID, brand retired** | (was 20k+ US/UK + travel) | rebranded to CNET Shopping (Red Ventures); old ID now serves CNET Shopping; MV2 sunset risk, shrinking base, tombstone (D-SUPERSEDED) |
| **PriceBlink** | ✗ EoL announced | 11k+ retailers incl Amazon | migrating to CNET Shopping, sunset planned |

## CN-side extensions

| extension | status | notes |
|---|---|---|
| **购物党扩展** ([gwdang.md](../tools/gwdang.md)) | ✓ healthy (v5.16+, 2025-04, Manifest V3) | 100+ CN+ overseas platforms, 180-day history, auto-coupon |
| **慢慢买 Chrome 扩展** ([manmanbuy.md](../tools/manmanbuy.md)) | ✓ healthy | history price + alert; companion to App |
| **什么值得买插件** ([smzdm.md](../tools/smzdm.md)) | ✓ healthy | 导购社区 + 180-day history |

**Default pick (US user):** Capital One Shopping + Karma. Skip Honey.
**Default pick (CN user):** 购物党 + 慢慢买 (cover overlap is fine, different strengths).
**Don't install >2 coupon extensions**, they conflict, slow the browser, and the second-installed
one usually loses the affiliate hijack race anyway.

## Honey 2026 status, what we know (sources cited so don't paraphrase from memory)

- **MegaLag video (Dec 2024)** broke the original last-click affiliate hijacking allegation +
  suppressed-coupons accusation.
- **Class actions consolidated** into MDL (*In Re PayPal Honey Browser Extension Litigation*),
  active discovery as of Jun 2026 (cohenmilstein.com case page).
- **PayPal's arbitration motion DENIED Nov 2025**, case proceeds in court.
- **Rakuten terminated Honey from its affiliate network on 2026-01-12** (ppc.land report);
  Impact.com and Awin followed within weeks, coverage on those merchants effectively gutted.
- No product-behavior changes announced by PayPal. Most creators / personal finance press now
  recommend uninstalling.

If the user already has Honey installed, **proactive recommendation: uninstall**, even if the
user doesn't care about the lawsuit, the Rakuten/Impact/Awin terminations mean the catalog you
think Honey covers has shrunk silently. They're paying CPU + browsing-data cost for a worse list.

## Affiliate-hijack mechanic (why this domain is fraught)

These extensions earn revenue by **rewriting the affiliate link on checkout** so the extension
publisher gets the commission (instead of the YouTuber / blogger / Reddit thread that referred
the user). For the user this is *usually* neutral on price, the discount they see is real, but
it can:
- Strip a "your code 5% off" link a friend / creator sent.
- Disqualify a cashback-portal rebate the user was about to claim (Rakuten Portal vs Honey vs
  Capital One vying for the same checkout).
- Stack falsely, extension shows "savings calculated" but actually only re-applied a public
  code anyone could use without the extension.

**Guardrail in this skill:** when recommending an extension-driven price, always state the source
clearly and don't double-count "extension savings" + "public coupon savings", they're often the
same dollar.

## Two-extension limit

If user has any extension already, don't recommend a second from the same category (coupon-apply
vs coupon-apply). Compatible pairings: one cashback-portal extension + one price-history alert
(e.g. Camelizer for Amazon + Capital One Shopping), these don't fight over the same checkout
affiliate slot.

**Install guidance:** these are Chrome Web Store / Edge / Firefox add-ons, open the store link
and click install. URLs in tool docs.

## Last verified: 2026-06
