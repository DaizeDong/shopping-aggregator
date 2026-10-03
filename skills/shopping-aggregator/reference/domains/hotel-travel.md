# Domain: hotel-travel

**Triage signals:** "book a hotel", "cheapest hotel near <venue>", "hotel for <these dates>", lodging
price compare, "which site is cheapest for this hotel", 订酒店、差旅住宿、酒店比价、"帮我订酒店".
Rental cars, trains, cruises and package tours are **OUT of scope**. **Flights now have their own shard**,
[`air-travel.md`](./air-travel.md); route airfare intents there, not here.

> **This domain applies to hotel/lodging price comparison + book-to-confirm.** Unlike the product shards
> (read a PDP and stop), the deliverable is: rank the real **total-stay cost** across booking channels for
> specific dates, then **drive the browser to the final confirm page and hand off** name + payment to the
> user. Maps to the **travel-booking / OTA** channel class in [`channel-classes.md`](../channel-classes.md).

| source | route | capability | detect | tier / risk |
|---|---|---|---|---|
| **Booking.com** ([booking.com](https://www.booking.com/)) | ④ playwright | search→property→room-select→Your-Details reads **total + tax + cancellation verbatim**; compare the public rate, then any Genius rate for which the user is eligible | booking.com | **L2** OTA high-trust; check separately for parking payable at the property |
| **Google Hotels** ([google.com/travel](https://www.google.com/travel/search)) | ④ discovery only | aggregates Booking/Expedia/Hotels.com/Priceline/brand-official → use for **RELATIVE channel ordering** only | google.com/travel | **L5** meta-recall; `ts=`/`qs=` URL **LOCKS dates**, on-page date change does NOT apply → never trust its date-specific numbers |
| **Brand-direct** (Hilton/Marriott/IHG) | ④ public rate; login for member rates | always check the **public brand-direct rate without requiring membership**; evaluate loyalty discounts separately after confirming eligibility | brand.com | **L1**; compare live total-stay cost and matching terms against OTAs |
| **Other OTAs** (Expedia/Hotels.com/Priceline) | ④ | check live rates and terms independently; do not assume parity with Booking or brand-direct | the site | **L2 to L3**; watch phantom inventory / opaque bed-banks (treat as L4 if encountered) |
| **Parking research** (hotel site / SpotHero / ParkWhiz / TripAdvisor forums) | ④ web search | fills the fee Booking omits; a WebSearch subagent gathers many hotels in parallel | separate search | material, **reorders rankings** |

**Default comparison:** check Booking.com, the public brand-direct rate, and other relevant OTAs for the
same dates, occupancy, room, board, cancellation and payment terms. Rank by live total-stay cost, including
taxes and mandatory fees; no channel is a standing winner. Membership is not a prerequisite for the
public brand-direct check. Show loyalty or Genius discounts as separate eligible rates, and use them only
after confirming the user's eligibility. If login is needed for a member rate, finish the available public
reads first, then follow the blocking login handoff. Do not assume access to the discount.

## Booking.com route (tested selectors, the spine)

Selectors below are from an illustrative session; Booking churns its DOM. Treat as a starting map, if a
`data-testid` misses, **fall back to a `browser_snapshot` read** of the accessibility tree, and the refresh
pass should re-confirm them live.
1. **Search**, `booking.com/searchresults.html?ss=<place-or-venue>&checkin=YYYY-MM-DD&checkout=YYYY-MM-DD&group_adults=2&no_rooms=1&group_children=0&order=distance_from_search` (or `order=price`) `&nflt=review_score%3D70&selected_currency=USD`. Anchor `order=distance_from_search` on the venue for a drive-time sort.
2. **Result cards**, `[data-testid="property-card"]` → `[data-testid="title"]`, `[data-testid="distance"]`, `[data-testid="price-and-discounted-price"]`, `[data-testid="review-score"]`, `a[data-testid="title-link"]` (href).
3. **Property page**, room rows at `#hprt-table tbody tr`. Room-quantity `<select id="hprt_nos_select_<blockId>">`, options read `"0"`, `"1 ($X)"`, `"2 ($2X)"`… Select **"1"**, click the primary reserve button `.txp-bui-main-pp` ("I'll reserve") (header `#hp_book_now_button` also works) → advances to `secure.booking.com/book.html?...&stage=1` = **Your Details**.
4. **Your Details page** (price-of-record read), total+tax: `Total $X Includes $Y in taxes and fees (NN% Tax)`. Cancellation widget "How much will it cost to cancel? / If you cancel, you'll pay $Z": **$Z == total → NON-REFUNDABLE**; **$Z == $0 → free cancellation**. "No prepayment / pay at the property" → pay-at-hotel.

## TOTAL-STAY COST = the landed-cost analog

**total-stay = nightly × nights + lodging/occupancy tax + cheapest parking + resort/amenity fees − discounts.**
One ranked row per **property|room-type|bed|board(RO/BB/HB)|cancellation-policy** (refundable vs non-ref are
DIFFERENT SKUs, list separately). Rules:
- **Booking's Your-Details Total is already TAX-INCLUSIVE.** The `(NN% Tax)` line is a *breakdown to READ*
  for transparency, **NOT an amount to add on top**, summing Booking-total + the tax line double-counts tax.
  The formula's tax term is the component view; the ranked landed number = **Booking total (tax-incl) +
  cheapest parking + any resort fee not already in the total − discounts.**
- **READ the tax, never hard-code it.** Read the `(NN% Tax)` line off the live page. Do NOT type a lodging-tax
  rate from memory (e.g. a large US metro ~14%); same no-hardcoded-rate guardrail as the rest of the skill
  (#3 / CONSTITUTION I.7). The live-read tax line must carry `snapshot_ts` + the Booking `source_url` so it
  stays auditable under guardrails #1/#3 (it is an E1 live read, not a `data/` row, so it must be stamped).
- **Parking can reorder rankings.** Check whether the quoted total includes parking and add any separate
  charge for the stay. Research the hotel's current parking terms and relevant alternatives (hotel site /
  SpotHero / ParkWhiz / TripAdvisor); do not carry a prior property's fee into a new comparison.
- **Distance filter**, `order=distance_from_search` on the venue; ~10-min drive ≈ ≤4 to 5 mi in a mid-size US city.

## Google Hotels caveat (do not trust its dates)

Google Hotels DOES aggregate channels, but the `ts=`/`qs=` URL params **lock the dates** and the on-page date
picker changes do **NOT** reliably apply (in a real run it stayed stuck on default dates even after clicking new
dates + Done). Use it **only for relative channel ordering**; verify every absolute price on the actual channel
with the correct dates.

## Refundable vs non-refundable tradeoff

Cheapest rates are often **NON-REFUNDABLE**; free-cancellation rates cost a bit more. **Surface BOTH** and
recommend by how firm the user's dates are, firm dates → non-ref saves; soft dates → pay for free cancellation.

## HARD operating rule (mandatory)

**Drive the browser to the selected channel's final review page**, such as Booking's "Your Details"
(room selected; total + tax + cancellation + parking surfaced), then **STOP and hand off** name + payment entry to the user. **NEVER enter
payment card or personal info**, matches the standing principle (agent configures tools; hand off at
login/payment). The deliverable is the ranked total-stay table + the confirm-page URL, not a completed booking.

**Install guidance:** no install, Booking / Google Hotels / OTAs are all ④ playwright live reads; parking via a
WebSearch subagent. Loyalty accounts are the user's; the agent reads the live total and stops before
personal details or payment entry.

## Last verified: 2026-07
