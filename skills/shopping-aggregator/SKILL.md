---
name: shopping-aggregator
description: "Triggers: compare prices, cheapest to buy, good deal, should I wait for a sale, book a hotel, cheapest hotel, cheapest flight, is this ticket a good deal, 比价, 查历史价, 全网最低价, X 在哪里买便宜, 凑单, 订酒店, 差旅住宿, 酒店比价, 机票比价, 查机票, 这个机票值不值, buy it for me, place the order, 帮我买, 帮我下单."
---

# shopping-aggregator

Compare purchases using current evidence and the price/coverage rules below.
Delegate retrieval, history and side research to available tools. Follow
[PHILOSOPHY](../../PHILOSOPHY.md) and [CONSTITUTION](../../CONSTITUTION.md).

Resolve `reference/` relative to this file; run `tools/` and `scripts/` commands
from the package root two levels above its real path (resolve a linked skill
directory first). Discover and probe tools on the current host.

## Scope

Use this for comparison, deal value or buy/wait decisions. Preserve the metadata
triggers. A chosen retailer or policy lookup needs only a direct read.
Route supplier discovery, arbitrage/FBA sourcing, market
sizing, category competition, SEO and social sentiment to `market-intel`. When
a request combines a purchase with research, own the purchase and delegate the
research question.

Flights use [air travel](reference/domains/air-travel.md). Hotels use
[lodging](reference/domains/hotel-travel.md): reach a selected confirmation page
only to verify total, taxes, cancellation and parking, then hand off. Stop before
entering personal/payment data, reserving inventory, or completing a purchase.
Rental cars, rail, cruises and package tours need a separate workflow.

## Step 1: Parse the buy intent

Capture these fields before delegating; resolve material ambiguities with the user.

Start from the buyer's config root ([CONFIG.md](../../CONFIG.md)). Run `python scripts/verify_config.py`; it prints the root it selected. When buying for someone else, select their root (usually `<companion>/people/<id>/`) and keep it selected for the whole run: environment variables do not carry from one tool call to the next, so pass the same `--config-dir <root>` to every `scripts/` command and put `SHOPPING_AGGREGATOR_CONFIG=<root>` on the command line of every `tools/` command (`$env:SHOPPING_AGGREGATOR_CONFIG='<root>'; python ...` in PowerShell; quote Windows paths or use forward slashes). If its `profile.json conforms` check passes, read `<root>/profile.json` and prefill Region from `market` and `ship_to`, Existing access from `memberships`, `not_held`, `store_credit`, `accounts` and `home_stores`, the run defaults from `purchase_defaults`, `risk` and `travel`, the platforms to leave alone from `off_limits`, and category tastes from `preferences`; ask only for what it leaves open, and report any other failing doctor check. An instruction in the conversation overrides the profile for this run without editing it. If no root resolves or the profile check fails, ask for every field below. Change a profile only when its owner states a new fact (CONFIG.md, Changing a profile), never by inference. Name the `profile_id` in the report header.

| Field | Required detail |
|---|---|
| Product | Brand, model, specification, quantity and condition |
| Region | Buying/shipping market; cross-border origin and destination where relevant |
| Budget and urgency | Spending limit, delivery deadline, willingness to wait |
| Sensitivity | Warranty, returns, refurbishment, seller reputation and authenticity needs |
| Existing access | Accounts, memberships and their perks (member price, cash back, free shipping), store credit, extensions and connected sources that can be used |

For flights also capture airport sets, travel-date windows, cabin, passenger
count, baggage needs, stop/duration limits, refund needs and payment currency.
Ask only for transit-eligibility facts required by the proposed route; never
request a passport number for comparison. Hotel dates, occupancy, room/rate
type and cancellation needs must be fixed before comparing totals.

## Step 2: Triage and depth

Produce `[matched domains | in-scope channel classes | depth cap]`.
Use [the source index](reference/sources-index.md) to select from the 14 domains,
then read only the matching `reference/domains/<domain>.md` files. Flight
intents always load the air-travel shard before the first fetch.

Read [channel classes](reference/channel-classes.md) to enumerate in-scope channels.
Even a channel without a domain shard needs its listed route and caveats;
never drop it or create a shard during a purchase.

Choose a depth and maintain its running counts. Stop fan-out and synthesize at
any hard cap. Quick is the default for a mainstream in-stock SKU in one region.

| Depth | Max subagents | Max rounds | Max verifiers | Use |
|---|---|---|---|---|
| quick | 3 | 1 | 1 | One mainstream SKU without history needs |
| standard | 6 | 2 | 3 | Multiple retailers and material channel spread |
| deep | 12 | 3 | 5 | Explicit comprehensive research or a purchase of at least `risk.deep_depth_usd` (default $500) |

Declare the chosen scope before collection and achieved coverage in the report. A limited
search cannot justify an unqualified market-wide minimum. Use unique listing
and seller counts, not page counts alone, to measure coverage.

## Step 3: Probe sources and classify access

Discover tools on the current host; a connected health indicator is insufficient.
Run a small functional read. Failed or authentication-needed tools are unavailable.
Read [source reliability](reference/source-reliability.md) when choosing a route.

| State | Evidence | Action |
|---|---|---|
| S1 anonymous | A real anonymous read succeeds | Collect and grade |
| S2 session-gated | A user-provided session could expose the content | Main-session login handoff |
| S3 structural | A session cannot fix the block, dead source or closed API | Typed coverage gap; stop retries |

Before treating a marketplace's empty search as no inventory, run the control
query in rule #11. An empty response may instead indicate gating or a broken
route. Never infer S1 or S3 merely from HTTP status or a tool's name.

## Step 4: Choose routes and offer installation when useful

Prefer the free ④ browser route when it can answer the question. Paid APIs earn
their cost for needed history, scale or access. The ①②③④ route legend is in the
source index. Read [tool index](reference/tools/index.md), then only the selected
`reference/tools/<slug>.md`. Read
[installation guidance](reference/install-guide.md) and
[current pricing/install details](reference/volatile/pricing-install.md) only
when setup is necessary; verify current official instructions and cost first.

A missing source does not stop all research: use an available alternative and
state the gap. Respect the host's install/reconnect requirements. Never expose
keys, credential files or authentication state in transcripts or reports.

## Step 5: Collect and verify evidence

Use connected browser/source tools for selected retailer reads, available
aggregates for discovery, and Keepa/Camelcamelcamel or regional tools for history.

For model/agent work, use `llmcall.call(prompt, mode="agent")`; text judgments
use its default judge mode. Follow installed routing and policy without provider
pins. [Review guidance](reference/codex-crossval.md) explains evidence limits and
actual independence. A missing reviewer is a declared gap. Its recalled prices
are E3 leads requiring a live selected-offer read before ranking.

Workers return bounded structured evidence units described in
[evidence schema](reference/evidence-schema.md): status; retailer; matched title,
SKU and `variant_key`; price/currency/shipping/tax/discount stack (#16)/landed cost;
stock, seller, condition, timestamp, source URL, seller tier and evidence grade;
history source and range; coupon attempts; and notes. Reduce those units instead
of copying raw pages into the main context. Add a combiner if more than about
five workers are collecting evidence.

A fresh verifier with no prior verdict must re-open every cited selected offer
supporting a ranked E1/L1 claim and confirm price, variant, stock, seller,
timestamp and evidence grade. A worker's self-check is insufficient. Fresh
context is not proof of a different backend: disclose any unestablished model
independence. Browser work must be coordinated sequentially unless isolated
contexts are actually verified; never concurrently navigate a shared page or
address tabs by index.

### Login handoff for S2 channels

Read [login handoff](reference/login-handoff.md). Finish anonymous S1 work first,
then batch all S2 channels into one main-session request. Keep exclusive browser
ownership, open the login page, explain what each login unlocks and the resume
signal, then pause browser interaction until the user resumes. The agent never
enters credentials or codes, scans QR codes, or creates accounts; the user handles
authentication directly. A timeout is neither consent nor refusal. Re-run the
control query after login before trusting content. If the user declines, record `session-gated-declined`; unattended execution
records `session-gated-unattended`. Retry a non-login failure once with a revised
query. Never fill a blocked channel with another channel's prices. Post-login
reads must avoid snapshots of account, order, address and payment views. Ordering,
bidding, offers, messaging or settings changes need a fresh per-action instruction.
If a cart was changed to reveal charges, restore it and verify the restoration.

## Step 6: Normalize landed cost

Compare identical variants and condition on the actual fulfillment promise.
Landed cost includes sticker, shipping, tax and duty, less verified checkout
discounts. Delayed cashback is shown separately and never deducted from the ranked
checkout total. Every tax/duty/shipping/FX input needs dated source provenance
from the applicable reference table or an explicit `(assumed)` label. Assumptions
cannot support an unqualified verified-lowest-total claim.

Read [sales tax](reference/data/us-sales-tax.json),
[shipping](reference/data/shipping-baselines.json), and
[cross-border duty](reference/data/cross-border-duty.json) as relevant; the tax
row is the profile's `ship_to.state` unless the buyer names another destination. When the profile
names a forwarder for the route, price its leg from that forwarder's private rate table
(`forwarders[].rate_table`, CONFIG.md); `duty_inclusive: true` means no duty line on top. Confirm
current legal treatment and selected checkout charges; do not infer duty-free
status from a remembered threshold. Missing region or HTS treatment remains an
explicit uncertainty. Follow [FX sourcing](reference/data/fx-source-of-record.md)
for provider precedence and effective rate timestamp. If no rate is verified,
retain source currency and mark conversion UNVERIFIED.

For flights include taxes, checked/cabin bags, seats and actual payment/FX
fees. Read [baggage collection requirements](reference/data/airline-baggage.json);
it supplies no verified fee defaults. Unknown brand, baggage, tax, refund or
payment terms make offers non-comparable. Verify the selected fare's terms and
use `python tools/flight_cost.py <private-quote-path>` to check declared evidence
and total completeness. A successful arithmetic check still requires the fresh
selected-source verification described in the flight shard.

Rank each offer at its best achievable discount stack (#16), not at its sticker. Eligible means available to this buyer now without joining or signing up for anything; list the rest as conditional rows. Look where discounts live, not only on the product page: after selecting each purchase path (some coupons render only then), the retailer's coupon or deals page, the cart and checkout, and the retailer's current codes on coupon and deal sites, cart-testing each. Enumerate: a subscription or auto-replenish price cancellable without fee, clip coupons, first-order offers, codes, member pricing, loyalty rewards and cashback portals. A member price shown only when signed in is S2 content for the login handoff, or a typed gap beside that offer, never the anonymous price. Record in `discount_checked` where you looked, so an empty stack means none found rather than not checked. A multi-pack is its own row with total and per-unit price, only when the buyer's quantity covers it. Keep the one-time sticker path as its own row.

Rank on the amount charged at checkout: subtract only lines confirmed there in a tested combination (#4), and show product-page-only lines as a labelled "if applied" figure. Value paid later (cash back, portal cashback, rewards earned) sits beside the total with its form and expiry and is never subtracted; count at most one portal or extension per order, and say so if it would change the #1. Store credit, gift-card balances and rewards already earned are the buyer's money, never a discount.

Test coupons in the cart/confirmation flow without submitting an order; state
what was actually applied and any stacking conditions. Exclude marketplace
offers below the profile's `risk` cutoffs (default 95 percent rating or 500
ratings) unless the user accepts the risk.
Show the sorted verified totals, differentiators for the top two (warranty,
returns, shipping), and a sourced history note. A wait recommendation requires
history evidence or an explicit low-confidence label.

## Quality guardrails

Keep these IDs stable; the rubric and evidence schema cite them.

- **#1 Snapshot timestamp:** every entry has `[fetched YYYY-MM-DD HH:MM TZ]`;
  an undated entry is unverified. State the report snapshot time.
- **#2 Stock/fulfillment:** label in-stock, low-stock, out-of-stock or preorder.
  Rank deliverable stock first; others are footnotes. Check the actual promise.
- **#3 Landed cost:** rank verified complete costs. Otherwise label sticker-only
  or an assumed range; never hide unknown additions as zero.
- **#4 Coupons:** cart-test savings and stacking, or label the claim unverified.
  State if the confirmation page could not be reached.
- **#5 Seller tier:** assign L1 only after reading Sold-by/Shipped-by. Unknown
  seller is L3, never L1. Identify every tier; L4/L5 winners require user override.
  A domain name does not establish the seller.
- **#5b Evidence grade:** E1 is a live selected PDP/official API read; E2 is an
  aggregate; E3 is a snippet, recall or lead. E3 never ranks. E2 needs same-variant
  E1 corroboration; two E2 reads do not upgrade it. The top recommendation needs
  at least two independent E1 reads of the same `variant_key`; other material
  claims need two sources or `confidence: low - single source`.
- **Variant identity:** use specification, selected option or manufacturer ID,
  not a title alone. If selected option and generic specification disagree,
  the option controls and that generic spec is no longer independent evidence.
- **#6 Degradation:** disclose each fallback inline. A tool that returns empty
  results has not demonstrated functional availability.
- **#7 Disagreement:** re-fetch snapshots older than four hours. Same-page
  snapshots differing by over 5 percent need a third read, never an average.
  For cross-source disagreement first check variants, then record cause
  (`different seller`, `stale/aggregated (E2/E3)`, or `coverage-gap`) and resolve
  using E1 evidence. If unresolved, show both dated observations.
- **#8 Disconfirmation:** have a fresh reviewer reverse-search the cheapest
  option for scam, counterfeit, seller and condition risks. Report Risks &
  counter-evidence. An empty search means none found, never proof of safety.
- **#9 Coverage:** list failed and never-attempted in-scope channels. After one
  query rewrite/retry, retain the gap with reason `session-gated-declined`,
  `session-gated-unattended`, `structurally-unreachable`, `tool-outage`, or
  `not-attempted`. Never substitute evidence from a different channel.
- **#10 Affiliate claims:** compare affiliate savings against the merchant's
  public selected price. Non-merchant notifications and release calendars are
  E3 at best; their numbers do not establish a payable price.
- **#11 Control query:** every marketplace zero-result needs a query for a
  known-stocked control. A failed control voids that platform's zero-results
  for the run. Cite the control and result, including brand-store searches.
- **#12 Search depth:** report pages, unique items/sellers, sort order and how
  paging worked. Compare new IDs across pages; duplicates do not prove progress.
  Stop on zero new IDs or the declared floor. Report read/total coverage when
  available. Multiple listings by one seller are one seller observation.
- **#13 Card attribution:** read a price only from its own offer card or API
  record. Preserve `price_unavailable`; never borrow a nearby price. Run
  `python tools/flight_probe.py selftest` before using the flight parser.
- **#14 Flight corroboration:** require a second independent transport for a
  ranked fare. Repeated endpoint/cache reads count once. Reconcile disagreement
  under #7; absence on one transport is not evidence of no available flight.
- **#15 Fare product:** state fare brand, needed bag allowance and refund/change
  restrictions. An identical flight number does not imply equivalent fares.
  Unknown terms remain unverified and cannot support a lowest-total claim.
- **#16 Discount stack:** the headline answer and every purchase use the purchase path whose own stack charges the least at checkout, with every eligible discount stacked and each condition stated. Try every top candidate's stack at the confirmation page; a sticker headline is acceptable only after the stack was tried and failed, could not be tested (label it under #3), or the buyer declined the commitment, never because it was not tried. A discount advertised on the product page but absent from the confirmation page has not been applied.

## Purchasing on instruction

Retail product orders only; lodging and flights stay hand-off-only per their shards. Buy only on the buyer's explicit, per-action instruction, and read [purchase execution](reference/purchase-execution.md) first. Buy the #16 stack, not the sticker; with no report covering the offer, build its stack first. Activate every portal, offer and code the stack needs, select the discounted path, clip the coupons that render after it, and stop on the final page to confirm each expected discount line before the single submitting click. A fee-free cancellable subscription may be bought on announcement; any other added commitment, quantity change or sign-up needs the buyer's yes. Read logged-in pages by scoped extraction of named fields, never snapshots. Confirm the order in order history, restore cart side effects, and handle a later correction as that file says.

The selected profile supplies the buyer's standing answers: `purchase_defaults.subscriptions` (`accept-fee-free` keeps the announcement rule above, `ask` turns it into a question, `decline` leaves subscriptions out of the stack) and `subscription_interval`, and the retailer's `accounts[]` entry for who may submit. Only `checkout: agent` lets the agent click; `owner-browser`, a missing entry or a run without a conforming profile means prepare the cart and hand the final click to the owner, and `none` means no order through that account at all. Record every order action (placed, cancelled, replaced, returned) by piping one row to `python scripts/ledger.py append purchases --row-file - --config-dir <root>`; the row carries that root's `profile_id` and the fields in purchase execution. An invalid row is fixed and appended again; any other refusal is reported in the reply, never written elsewhere.

## Output and final check

Use [the report template](reference/report-template.md) for intent, timestamp,
ranking, history, coupons, Risks & counter-evidence, sources and final Coverage gaps.
The headline price is the #16 stack; show the discount lines that produce it.
Check each applicable guardrail before delivery. Claims of booking, model
execution or source verification require evidence that the action occurred.

## Step 7: Keep real observations private

Append each source outcome and every in-scope channel gap by piping one JSON row to `python scripts/ledger.py append live-runs --row-file - --config-dir <root>` (never a row file inside this repository). It validates the row against [the published schema](metrics/live-runs.jsonl.example), checks the selected root against the shared [resolver](../../guards/tools/datadir.py) and proves it PRIVATE before writing; the [refresh protocol](reference/refresh-protocol.md) defines the fields. An invalid row is fixed and appended again. Any other refusal is a writer failure: report it and keep the observations in the reply pending private initialization. Never fall back to the public tool tree. The companion is versioned; real run history belongs in its private commits.
Every `outcome: coverage_gap` record requires an enum `gap_reason` from the
[refresh protocol](reference/refresh-protocol.md#feedback-loop). Preserve the same
reason in the report and private record; explanatory `detail` does not replace it.

Public code/docs contain general rules and generated synthetic examples only.
Do not copy a real order, route, transcript, quote, prompt or verdict into them.
For transcript evaluation read
[judge protocol](reference/scenario-eval/judge-protocol.md). The default plan is
`not_run`; `--judge` is an explicit model submission with strict private preflight.

## Progressive loading and maintenance

Load the source index first, then selected domain/tool shards. Read CONFIG.md
for configuration and retention changes; each person uses the same per-kind rules
from [CONFIG.md](../../CONFIG.md). Step 1 needs just the doctor and the profile. Load channel
classes for coverage, reliability for retrieval trouble, login guidance for S2,
the evidence schema for worker results, and only applicable cost tables. Load
purchase execution only when the buyer has instructed a purchase. Never
load an entire reference directory. For recurring alerts recommend an existing
price tracker with its current verified setup; this one-shot workflow does not
create an unattended purchase loop; a subscription bought on instruction is the one exception, and its next charge date is always reported.

For a requested source refresh, follow the refresh protocol and monthly cadence.
Update evidence and versions together, preserve source tombstones/death codes,
and run the repository's deterministic checks. Packaging verification uses
Git's delivery index: a locally present untracked resource is not shipped.
