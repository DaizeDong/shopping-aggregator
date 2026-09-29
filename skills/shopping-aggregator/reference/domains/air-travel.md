# Air travel: compare the selected itinerary and fare terms

Last verified: 2026-09 (workflow structure only; no live fare or baggage rate verified).

Use this shard for flight comparison, airfare value, or a ticket seller's quote.
Read it before collecting prices. Rental cars, rail, cruises, and package tours
require a different workflow. Stop before entering personal or payment details,
reserving inventory, or purchasing a ticket.

## Collect the decision inputs

Record airport sets, travel-date windows, one-way/return/multi-city structure,
cabin, passenger count and ages where pricing requires them, stop and duration
limits, required checked and cabin bags, refund/change needs, and payment currency.
Ask only for transit-eligibility facts needed for the actual itinerary; do not
request passport numbers or other booking identity data.

The variant key must include the complete itinerary, operating carrier, cabin,
fare brand, baggage entitlement, and relevant change/refund restrictions. A flight
number alone cannot establish that two offers sell the same product.

## Source selection and attribution

| Source | Route | What it can establish |
|---|---|---|
| Airline's selected booking page or official offer API | ④ browser / official API | E1 selected fare, tax, bags and restrictions when the exact offer is visible |
| Google Flights | ④ browser; repository flight probe | E2 discovery and itinerary options; advance to the selected seller for terms |
| Skiplagged | ④ browser / available public response | E2 corroboration; a hidden-city itinerary requires explicit disclosure of its restrictions |
| Ticket agency or consolidator | ④ selected written quote / booking page | Seller-specific E1 only for its own offer; independently verify ticketing, refunds and fees |

The repository's `tools/flight_probe.py` parses prices inside their own offer
cards. An unpriced card remains `price_unavailable`; it must never receive a
neighboring price. Run `python tools/flight_probe.py selftest` before relying on
its parser. This checks parser behavior, not live site availability.

Confirm ranked fares with a second independent transport. Two reads of the same
endpoint or cached payload count as one observation. Save the endpoint, selected
offer, retrieval time, and actual transport identity with each observation.
Metasearch output remains E2; two E2 reads do not become E1. Re-fetch when matched
offers disagree by more than 5 percent, and do not average away the disagreement.

## Comparable total and unknown terms

Use `reference/data/airline-baggage.json` as a collection checklist. It deliberately
contains no verified airline fees. It cannot supply a default bag allowance or
price. Obtain the selected fare's allowance and fees from the airline or seller,
including each direction, codeshare/operating-carrier rules, and the buyer's needs.

Total cost includes the fare, taxes, checked and cabin bags, necessary seat fees, and the
actual payment conversion/fees. When tax is included in the fare, the separate
tax addition is a verified zero with that inclusion cited. Never assume that all
displayed airfares include tax. A mid-market FX rate does not prove a card or
transfer service's payable amount.

Before ranking, collect explicit fare-brand and refund/change terms. Unknown
tax, baggage, seat, payment, or refund terms produce `not_comparable`, not zero.
Show an indicative quote or a clearly assumed range separately from verified
totals. Do not call it the lowest total or equivalent to another fare.

`tools/flight_cost.py` checks a private quote JSON with `variant_key`, `currency`,
`terms`, and selected-source observations. Each term has `status` and `value`;
cost terms are `fare`, `tax`, `checked_bags`, `cabin_bags`, `seat_selection`, `payment_fx`, with
`fare_brand` and `refund_terms` as text. Sources carry `source_url`, `fetched_at`,
`variant_key`, `evidence_grade`, `selected`, and `transport_id`. The generated
`reference/scenario-eval/flight-quote-fixture.json` illustrates the shape only.
Included or unneeded baggage requires a verified zero cost, not an omitted term.

Run `python tools/flight_cost.py <private-quote-path>` from the repository root.
The checker validates declared evidence and arithmetic. It does not fetch the
sources or establish that transport labels are honest. A fresh verifier must
re-open the selected offers and substantiate those declarations. Only then may
`comparable_total` support ranking among the selected verified offers; it never
proves a global market minimum.

## Report and retain evidence

Show the airport/date search coverage, itinerary and variant, selected seller,
fare brand, bag allowance, restrictions, currency, total, dated source links,
independent verification, and unresolved gaps. A missing price is an option with
an unknown price. A blocked source is a coverage gap, not evidence of no seats.

Real queries, quotes, screenshots, transcripts and evaluations are private DATA.
Keep them in the versioned PRIVATE companion. Public examples must come from
`tools/make_fixtures.py`. This shard supplies generic workflow instructions and
contains no observed travel prices or personal itinerary history.
