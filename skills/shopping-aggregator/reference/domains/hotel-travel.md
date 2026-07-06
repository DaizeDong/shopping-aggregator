# Domain: hotel-travel

**Triage signals:** "book a hotel", "cheapest hotel near <venue>", "hotel for <these dates>", lodging
price compare, "which site is cheapest for this hotel", 订酒店、差旅住宿、酒店比价、"帮我订酒店".
Flights / rental cars / trains are **OUT of scope** (messier data sources) — future extension, do NOT build.

> **This domain applies to hotel/lodging price comparison + book-to-confirm.** Unlike the product shards
> (read a PDP and stop), the deliverable is: rank the real **total-stay cost** across booking channels for
> specific dates, then **drive the browser to the final confirm page and hand off** name + payment to the
> user. Maps to the **travel-booking / OTA** channel class in [`channel-classes.md`](../channel-classes.md).

| source | route | capability | detect | tier / risk |
|---|---|---|---|---|
| **Booking.com** ([booking.com](https://www.booking.com/)) | ④ playwright | **the reliable spine.** search→property→room-select→Your-Details reads **total + tax + cancellation verbatim**; Genius member discount often the **lowest PUBLIC** price | booking.com | **L2** OTA high-trust; total **EXCLUDES parking** (pay-at-property) |
| **Google Hotels** ([google.com/travel](https://www.google.com/travel/search)) | ④ discovery only | aggregates Booking/Expedia/Hotels.com/Priceline/brand-official → use for **RELATIVE channel ordering** only | google.com/travel | **L5** meta-recall; `ts=`/`qs=` URL **LOCKS dates**, on-page date change does NOT apply → never trust its date-specific numbers |
| **Brand-direct** (Hilton/Marriott/IHG) | ④ (login) | only beats OTA parity with a **loyalty MEMBER rate** (needs an account/login) | brand.com | **L1**; with no membership it does not beat Booking parity |
| **Other OTAs** (Expedia/Hotels.com/Priceline) | ④ | rate-parity, usually within **~$10** of Booking (session-observed) | the site | **L2–L3**; *general OTA risk, not from session:* watch phantom inventory / opaque bed-banks (treat as L4 if encountered) |
| **Parking research** (hotel site / SpotHero / ParkWhiz / TripAdvisor forums) | ④ web search | fills the fee Booking omits; a WebSearch subagent gathers many hotels in parallel | separate search | material — **reorders rankings** |

**Default pick:** **Booking.com ④** is typically the lowest legitimate channel **with no loyalty membership**
(Genius > public OTA parity); confirm brand-direct only if the user has a loyalty account. Observed
(illustrative single 2026-07 session, not a standing quote): Homewood Suites Booking **$152** < Hilton
official ~$163 < Expedia/Hotels.com/Priceline ~$175. Re-price live every run — never carry these numbers forward.

## Booking.com route (tested selectors — the spine)

Selectors below are from ONE real 2026-07 session; Booking churns its DOM. Treat as a starting map — if a
`data-testid` misses, **fall back to a `browser_snapshot` read** of the accessibility tree, and the refresh
pass should re-confirm them live.
1. **Search** — `booking.com/searchresults.html?ss=<place-or-venue>&checkin=YYYY-MM-DD&checkout=YYYY-MM-DD&group_adults=2&no_rooms=1&group_children=0&order=distance_from_search` (or `order=price`) `&nflt=review_score%3D70&selected_currency=USD`. Anchor `order=distance_from_search` on the venue for a drive-time sort.
2. **Result cards** — `[data-testid="property-card"]` → `[data-testid="title"]`, `[data-testid="distance"]`, `[data-testid="price-and-discounted-price"]`, `[data-testid="review-score"]`, `a[data-testid="title-link"]` (href).
3. **Property page** — room rows at `#hprt-table tbody tr`. Room-quantity `<select id="hprt_nos_select_<blockId>">`, options read `"0"`, `"1 ($X)"`, `"2 ($2X)"`… Select **"1"**, click the primary reserve button `.txp-bui-main-pp` ("I'll reserve") (header `#hp_book_now_button` also works) → advances to `secure.booking.com/book.html?...&stage=1` = **Your Details**.
4. **Your Details page** (price-of-record read) — total+tax: `Total $X Includes $Y in taxes and fees (NN% Tax)`. Cancellation widget "How much will it cost to cancel? / If you cancel, you'll pay $Z": **$Z == total → NON-REFUNDABLE**; **$Z == $0 → free cancellation**. "No prepayment / pay at the property" → pay-at-hotel.

## TOTAL-STAY COST = the landed-cost analog

**total-stay = nightly × nights + lodging/occupancy tax + cheapest parking + resort/amenity fees − discounts.**
One ranked row per **property|room-type|bed|board(RO/BB/HB)|cancellation-policy** (refundable vs non-ref are
DIFFERENT SKUs — list separately). Rules:
- **Booking's Your-Details Total is already TAX-INCLUSIVE.** The `(NN% Tax)` line is a *breakdown to READ*
  for transparency, **NOT an amount to add on top** — summing Booking-total + the tax line double-counts tax.
  The formula's tax term is the component view; the ranked landed number = **Booking total (tax-incl) +
  cheapest parking + any resort fee not already in the total − discounts.**
- **READ the tax, never hard-code it.** Read the `(NN% Tax)` line off the live page. Do NOT type a lodging-tax
  rate from memory (e.g. a large US metro ~14%); same no-hardcoded-rate guardrail as the rest of the skill
  (#3 / CONSTITUTION I.7). The live-read tax line must carry `snapshot_ts` + the Booking `source_url` so it
  stays auditable under guardrails #1/#3 (it is an E1 live read, not a `data/` row, so it must be stamped).
- **Parking reorders rankings.** NOT in Booking's total (paid at property). A **$152 room + $20 self-park beats a $150 room + $55 valet.** Downtown valet observed **$30–65/nt**; some downtown hotels FREE (e.g. Hampton Inn & Suites); suburban usually free. Research separately (hotel site / SpotHero / ParkWhiz / TripAdvisor).
- **Distance filter** — `order=distance_from_search` on the venue; ~10-min drive ≈ ≤4–5 mi in a mid-size US city.

## Google Hotels caveat (do not trust its dates)

Google Hotels DOES aggregate channels, but the `ts=`/`qs=` URL params **lock the dates** and the on-page date
picker changes do **NOT** reliably apply (in a real run it stayed stuck on default dates even after clicking new
dates + Done). Use it **only for relative channel ordering**; verify every absolute price on the actual channel
with the correct dates.

## Refundable vs non-refundable tradeoff

Cheapest rates are often **NON-REFUNDABLE**; free-cancellation rates cost a bit more. **Surface BOTH** and
recommend by how firm the user's dates are — firm dates → non-ref saves; soft dates → pay for free cancellation.

## HARD operating rule (mandatory)

**Drive the browser all the way to the Booking "Your Details" confirm page** (room selected; total + tax +
cancellation + parking surfaced), then **STOP and hand off** name + payment entry to the user. **NEVER enter
payment card or personal info** — matches the standing principle (agent configures tools; hand off at
login/payment). The deliverable is the ranked total-stay table + the confirm-page URL, not a completed booking.

**Install guidance:** no install — Booking / Google Hotels / OTAs are all ④ playwright live reads; parking via a
WebSearch subagent. Loyalty accounts are the user's; the agent prices the live cart and stops at Your-Details.

## Last verified: 2026-07