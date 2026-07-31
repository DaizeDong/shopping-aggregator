---
name: shopping-aggregator
description: "Use to compare a product's price across retailers (Amazon/eBay/Taobao) + price-history/coupons, or a hotel/lodging's total-stay cost across booking channels. Triggers: compare prices, cheapest to buy, good deal, book a hotel, cheapest hotel, 比价, 查历史价, 全网最低价, 凑单, 订酒店, 差旅住宿, 酒店比价."
Base directory for this skill: ${CLAUDE_PLUGIN_ROOT}/skills/shopping-aggregator
---

# shopping-aggregator

A thin orchestration layer for consumer shopping price comparison. It does **only three things nothing
else does**: (1) parse a buy intent into a triage of the right shopping domains + channel classes; (2)
detect which specialized shopping MCP / extension / OSS tool is connected and guide installing missing
ones; (3) enforce **price-specific** guardrails (snapshot timestamp, stock state, landed-cost
normalization, coupon-cart verification, retailer trust tiers). The heavy lifting, live page fetch,
history backfill, adversarial verification, citation synthesis, is **delegated** to playwright / BigGo
/ Keepa MCPs / `deep-research` / `market-intel`. Do not re-implement those.

> **Design philosophy (governs all changes): root-cause design, not incremental patching**, fix the
> assumption underneath a problem, not the symptom on top. Full statement in `PHILOSOPHY.md`; every
> change must pass "does it fix the framing, or just patch a symptom?"

## Scope, when this skill applies, and when to stop

**Use this skill** for the consumer buy decision: "compare prices / find the cheapest place to buy X",
"is this a good deal / should I wait for a sale / what's the historical low". **Stop and delegate**
otherwise, before doing anything, route away these non-buy-decision asks:
- **Single retailer + already picked** ("just check Amazon for Bose QC45") → open the page, no workflow.
- **Bulk arbitrage / FBA sourcing / supplier discovery** → `market-intel` `ecommerce-arbitrage` shard
  (different sources, Keepa, Helium 10, alibaba, and a seller-side verifier mindset).
- **Category research / market sizing / competitive landscape / X-Twitter sentiment / SEO intel** (no
  specific product, e.g. "how big is the smart-lock market") → `market-intel`.
- **Single-fact lookup** ("what's Costco's return policy") → plain web search, no workflow.

If both apply ("buying X, also tell me what reviewers think / whether the category is declining"),
own the buy decision here and **delegate the side-research to market-intel as a sub-task**.

**Lodging (`hotel-travel`) is the one domain that intentionally goes past "read a PDP and stop":** it drives the browser to the Booking "Your Details" confirm page (total + tax + cancellation + parking surfaced) and then **stops at the payment/PII hand-off**. This is still the decision-layer identity above, it never enters card or personal info; the confirm-page URL + ranked total-stay table is the deliverable, not a completed booking. Flights / rental cars / trains stay OUT of scope.

## Workflow
### Step 1, Parse the buy intent (BLOCKING)

Capture all five before fanning out. **For ambiguous asks, ask the user for the missing fields first.**
Skipping this is the most common failure mode, it yields a generic landscape report instead of a buy
decision.
| field | why it changes routing |
|---|---|
| **Product** (brand+model+spec+condition) | controls SKU-level matching (new/refurb/used) |
| **Region** (US / CN / cross-border) | switches domain set: US → Amazon/eBay/Walmart/Best Buy; CN → Taobao/JD/PDD; cross-border → both + customs |
| **Budget / urgency** | "wait for sale" → Keepa/Camelcamelcamel historical-low; "need Wed" → hard-filter shipping speed |
| **Sensitivity** (warranty, refurb-OK, rating cutoff, returns) | drives trust tiers (AliExpress rating, Amazon WHD vs marketplace) |
| **Existing accounts / extensions** | use what's installed; don't recommend new tooling unless clearly worth it |

If the user said only "find me the cheapest", confirm region + condition first, cheapest "new from
authorized US seller" ≠ cheapest "any condition + any AliExpress seller."

### Step 2, Triage (domains → channel classes → depth)

**Step 2 output you MUST produce: `[matched domains | in-scope channel classes | depth cap]`.**

#### 2a, Triage to domains
Read `reference/sources-index.md` (thin index); match the buy intent to 1 to N of the 13 domains
(full list there). **Do not read full domain shards yet.** US typically → `amazon-us`,
`ebay-walmart-target`, `browser-extensions`, `mobile-apps-aggregators`, `ai-shopping-assistants`,
`claude-mcps`; CN → `taobao-tmall`, `jd-pdd`, `claude-mcps`, maybe `oss-self-host`. Historical-low
queries always add `amazon-us` (Camelcamelcamel/Keepa) or `taobao-tmall` (慢慢买).

**Hotel / lodging** intents ("book a hotel", "cheapest hotel near", 订酒店/差旅住宿/酒店比价) → `hotel-travel` (Booking.com ④ is the spine). For lodging the "landed cost" is **total-stay cost**; the shard owns the full formula, only remember here that the lodging tax is **READ off Booking's Your-Details page, never hard-coded**, and parking is separate (NOT in Booking's total) and materially reorders rankings. Flights / rental cars / trains stay OUT of scope.

#### 2b, Map to channel classes
Read `reference/channel-classes.md` and enumerate the authorized-retailer classes the product spans
(mass-market · category-specialist · brand-direct · warehouse · local-pickup-only · cross-border ·
refurb). This is the **demand-side** counterweight to 2a: a tool-less channel (e.g. Micro Center,
website only) is still in scope, routes to playwright / a store-specific scrape, **not skipped**. The
in-scope classes are the **coverage floor**, each must reach a real read (E1) or be a `not-attempted`
gap (guardrail #9).

#### 2c, Depth budget
Pick a depth and hold its hard caps:
| depth | max subagents | max rounds | max verifiers | use when |
|---|---|---|---|---|
| **quick (default)** | 3 | 1 | 1 | a single mainstream in-stock SKU, one region, no history needed |
| standard | 6 | 2 | 3 | multi-retailer "best price right now" with real channel spread |
| deep | 12 | 3 | 5 | explicit "comprehensive / 全面" or high-ticket ($500+) where execution cost > research cost |

For a single mainstream SKU the value is **landed-cost + timestamp + seller-identity check, not a full
fan-out**, `quick` is the honest default; escalate only when channel spread or ticket size earns it.
Maintain a running count; at a cap, stop fanning out and synthesize.

### Step 3, Detect available sources (do NOT guess by tool name)

Run `claude mcp list` and parse the three-state health, usable only if `✓ Connected`; treat
`✗ Failed` / `! Needs authentication` as **not available**. Tool-name prefix matching (`mcp__*shopping*`)
is unreliable (deferred tools, plugin prefixes, dead connections distort it). Detect: **playwright MCP**
(default ④ live-fetch); **firecrawl** (static fallback, **NOT enough for Amazon/Taobao** anti-bot, use
playwright, see `reference/domains/amazon-us.md`); **BigGo MCP** (`reference/tools/biggo-mcp.md`); **Keepa MCP** (Amazon
history); **Apify price-intelligence MCP** (paid, broadest US). Also ask the user (can't auto-detect):
Camelcamelcamel bookmark, Keepa account, browser extensions (Capital One Shopping / Karma / 购物党 / 慢慢买 App).

#### 3b, Classify each in-scope CHANNEL by access state (NOT the same axis as tool health)

Tool health answers "can I drive a browser." It does not answer "will that browser see anything."
Classify every in-scope channel class into one of three states, full rules in
[`reference/login-handoff.md`](./reference/login-handoff.md):

| state | meaning | action |
|---|---|---|
| **S1 anonymous** | a real read lands with no session | fetch, grade normally |
| **S2 session-gated** | page loads, content needs a logged-in session the operator could supply | **login handoff (Step 5b)**, NOT a gap until asked and declined |
| **S3 structural** | no operator session helps (geo-block, dead domain, closed API, proxy pool needed) | genuine `coverage_gap`, declare up front, stop retrying |

**A session-gated marketplace search returns "no results", not an error.** That is the same shape as
"nobody sells this." Guardrail #11 makes the control query mandatory before any zero is recorded.
Classifying S2 as S3 silently discards a reachable channel; classifying it as S1 fabricates a zero.

### Step 4, Select sources + guide install (non-blocking)

For each triaged domain read **only** its shard `reference/domains/<domain>.md`, pick the best
**available** source, and **prefer the free browser-automation route (④) over paid APIs when it
fits**, playwright reads the real Amazon / Taobao page in one shot; paid APIs (Keepa, Rainforest,
PriceAPI) earn their cost only for what playwright can't (deep history, scale, compliance). **A channel class with NO domain shard**
(brand-direct, cross-border/import, non-PC category-specialists e.g. Sephora/Crutchfield/REI) has no
shard to read, run it directly via the route in `reference/channel-classes.md` (usually ④ playwright +
that class's caveat); do NOT create a shard for it. **Never
block on install:** if the decision depends on a missing source, recommend it (command + cost in
`reference/volatile/pricing-install.md`) but **proceed this turn with a fallback + flag the gap** (a
new MCP only works after a session restart / `/mcp` reconnect). Prefer HTTP-transport on Windows
(stdio `npx`/`uvx` MCPs are flaky). L0 mechanics + secret hygiene (keys NEVER in transcript):
`reference/install-guide.md`.

### Step 5, Delegate execution

Hand the selected sources + sub-questions to the heavy harness:
- **Per-retailer live price** → playwright MCP (one subagent/retailer; each loads the MCP via
  ToolSearch first, subagents inherit MCPs only in deferred form).
- **Multi-retailer one-shot** → BigGo MCP, else Apify price-intelligence MCP, else fan out playwright.
- **History query** → Keepa MCP / Camelcamelcamel web fetch (Amazon free) / 慢慢买 (CN).
- **Adjacent research** (reviews, brand reliability, "wait for Prime Day?") → `market-intel` /
  `deep-research`.
- **Independent cross-model crossval + channel discovery** → **Codex MCP** (`mcp__codex__*`, GPT +
  own search): discover missed channels, cross-check the cheapest pick, sanity-check authenticity.
  **Codex prices are L5 *leads***, re-pass the live-fetch + citation gate (#1) before ranking.
  Best-effort: skip + note the gap (#9) if absent. Setup + how-to: `reference/codex-crossval.md`.

Require every subagent to return a **structured evidence unit**, not free prose, bare fields below;
full annotated schema + tiering/grade rules: `reference/evidence-schema.md` (read at Step 5):
```
status, retailer, product_match{ title, asin/itemId/skuId, variant_key, confidence },
prices[{ sticker, currency, shipping, tax_estimate, coupon_applied, cashback_estimate, landed_cost,
         stock_state, seller_name, seller_rating, condition, snapshot_ts, source_url,
         seller_tier, evidence_grade }],
history{ 90d_low, 90d_high, 365d_low, now_vs_low, source_url }|null, coupon_attempts[{ code, applied, savings }], notes
```
Length-cap each field. The main agent **reduces** these units, never reads raw page dumps; if fan-out
exceeds ~5 retailers, insert a combiner layer (each merges 3 to 4 workers). Then, before synthesis, spawn
the **zero-context verifier** (CONSTITUTION II.4): a fresh subagent with NO prior context that
re-fetches every cited URL backing an `E1`/`L1` price entering the ranking and independently confirms
price + stock + timestamp + **seller** (Sold-by/Shipped-by) + **evidence_grade** (a real PDP/API read,
not a snippet). Same-subagent self-verification is a bug.

**Browser concurrency.** The browser MCP is commonly **ONE shared instance across every subagent**,
whatever the isolation flags claim. Subagents MUST use atomic `newContext()`/`newPage()` per call
(open, extract, close), MUST NOT address tabs by index, and MUST NOT hand-roll signed API calls
in-page (heavy JS eval deadlocks silently under contention). Detail: `source-reliability.md`.

### Step 5b, Login handoff for S2 channels (BLOCKING, main session only)

If Step 3b marked any in-scope channel **S2**, that channel is one human login away, not a gap. Run
[`reference/login-handoff.md`](./reference/login-handoff.md); the shape is:

1. **Finish all S1 work first**, so a declined handoff still ships a complete report.
2. **Batch every S2 channel into ONE ask.** Asking once per platform is the failure this prevents.
3. **Main session, exclusive browser, never inside a parallel subagent** (see concurrency above); a
   sibling agent stealing the tab mid-login destroys the session.
4. **Open the login page and STOP.** Emit no further tool calls against that browser, state which
   platforms need login and what each unlocks, give the resume signal, then **end the turn.** Waiting
   means ending the turn, not polling.
5. **The agent NEVER authenticates**: no credentials, no codes, no QR scans, no account creation, not
   even if the operator pastes a password (tell them to type it into the browser instead).
6. **On resume, re-run the control query** to prove the session is live before trusting any read; a
   still-empty control means the channel was S3 after all, say so.
7. **Post-login is read-only + a PII surface**: no ordering, bidding, offers, messaging, or settings
   changes without a fresh per-action instruction; never snapshot account / order / address /
   payment views (CONSTITUTION V.4). A cart added to reveal a tax line MUST be emptied and re-read.

Declined or unattended is a normal outcome: record `session-gated-declined` (or
`session-gated-unattended`), which is a **different** gap fact from `structurally-unreachable`, and
never backfill the missing cell with another channel's numbers.

### Step 6, Normalize and rank by LANDED COST

The most-skipped step and the most decision-relevant. **Every tax / duty / shipping / FX number used
here MUST resolve to a row in `reference/data/` (carrying `source_url` + `verified_date`) or be stamped
`(assumed)` inline, CONSTITUTION I.7. Do NOT hard-code a rate or threshold from memory.**
- **Currency**: convert all to the user's region currency using the provider precedence + provenance
  schema in `reference/data/fx-source-of-record.md` (Frankfurter primary → ExchangeRate-API fallback).
  Cite the FX rate + provider + the rate's effective timestamp (not fetch time); never round silently,
  never invent a rate, if neither provider answers, leave the price in its source currency and mark
  the conversion `UNVERIFIED`.
- **Landed cost = sticker + shipping + tax + duty + (− coupon) + (− cashback).** Sticker alone is a
  ranking trap (Prime free-ship vs eBay $15 ship flips winners).
  - **Tax (US):** look up the buyer's state in `reference/data/us-sales-tax.json` (do NOT type a rate
    from memory, e.g. NJ resolves to the `NJ` row, 6.625%). Cite the row's `source_url` +
    `verified_date`. If the state is unknown, compute with the row anyway once region is confirmed at
    Step 1, or stamp the tax line `(assumed)`.
  - **Shipping:** check the retailer's free-ship baseline in `reference/data/shipping-baselines.json`
    (Amazon/Walmart/Target/Best Buy $35 non-member; eBay/AliExpress = seller-set, no platform
    baseline) before assuming "free", sub-threshold carts add a real fee that flips rankings.
  - **Cross-border duty:** look up `reference/data/cross-border-duty.json`. **The legacy $800 US
    Section 321 de-minimis is SUSPENDED for ALL origins (EO 14324, eff 2025-08-29), do NOT treat any
    sub-$800 cross-border parcel as duty-free.** Read the de-minimis status row + the relevant HTS
    category rate, estimate duty, and cite both rows; where no category row fits, flag `duty likely
    owed, confirm exact HTS rate at checkout` rather than assuming $0.
- **Coupons**: verify by **playwright cart test** (badges lie); mark each `code, applied?, $`.
- **Trust-adjust**: drop marketplace listings < 95% rating or < 500 ratings unless user OK'd it
  (AliExpress especially).
- **Output** the table sorted by landed cost, a "but actually" footnote on the top-2 (warranty /
  returns / shipping-speed differentiators), and an explicit history note ("$X above 90-day low / at
  365-day low / NEW LOW"; cite the Camelcamelcamel/Keepa chart when recommending "wait for sale").

**Before you emit the report, self-check** (cheap substitute for an executable gate):
- [ ] Every ranked row carries `variant_key` + `snapshot_ts` + `seller_tier` + `evidence_grade`?
- [ ] The #1 recommendation rests on ≥2 `E1` reads of the **same `variant_key`** (not single-source)?
- [ ] A "Coverage gaps" section is present, including every in-scope channel class `not-attempted`?
- [ ] `Sold by` was read for every unit stamped `L1` (else it is `L3`, not `L1`)?
- [ ] The zero-context verifier (Step 5) actually re-confirmed each ranked `E1`/`L1` price?
- [ ] No `E3` lead is sitting in the ranking, and no two snapshots were silently averaged?
- [ ] Every in-scope channel got an access state (S1/S2/S3), and **every S2 one was either handed
      off or explicitly declined**, not quietly filed as unreachable?
- [ ] Every zero-result from a marketplace search carries its **control query** (#11)?
- [ ] Every "cheapest" declares its **search depth** and how paging was driven, judged by NEW ids (#12)?
- [ ] Every `coverage_gap` carries a **typed reason**, not prose (#9c)?

## Quality guardrails (HARD rules, apply during synthesis)

Price-data-specific extensions of the market-intel guardrails, read both together. Long-form
rationale + war-stories for #5/#5b/#7/#8/#9/#10/#12: `reference/evidence-schema.md`.

They group into **five questions**, asked in order. The grouping is presentation; the numbered IDs
are the contract (`evidence-schema.md`, `report-template.md` and CONSTITUTION cite them), so they are
kept stable rather than renumbered.

| ask | rules | one-line test |
|---|---|---|
| **A. Can this row be ranked at all?** | #5b, #5, #1 | is its provenance complete |
| **B. Is this number comparable?** | #3, #2 | is it landed and in-stock |
| **C. Did I test the claim or repeat it?** | #4, #7 | did I re-fetch rather than trust |
| **D. Is absence posing as a finding?** | #11, #12, #9, #6 | can I tell empty from unreached |
| **E. What would make this wrong?** | #8, #10 | did I argue against myself |

### A. Provenance, four fields or it does not rank

- **#5b Evidence grade (E1/E2/E3, HOW obtained). Gates FIRST, before seller_tier.** Only `E1` (live
  PDP / official API) may be a ranked winner; `E2` (aggregator) enters only with a corroborating `E1`
  of the **same `variant_key`**; `E3` (SERP / cross-model recall) is never ranked, re-fetch to `E1`.
  A first-party domain does NOT upgrade an E3 snippet. (`evidence-schema.md` #5b)
- **#5 Seller tier (L1 to L5, WHO sold it).** A DOMAIN is not proof of first-party. Stamp **L1 ONLY
  after reading `Sold by` / `Shipped by`**; unread → **L3, never L1**. Missing `seller_name`
  **degrades to L3, does NOT reject**. Don't rank L4/L5 winners without override; mark every tier.
  Sold-by is also **channel discovery**: a 3P seller on a big-box domain can be the product's own
  exclusive source, whose first-party storefront sells it for less. (`evidence-schema.md` #5)
- **#1 Snapshot timestamp.** Every entry carries `[fetched YYYY-MM-DD HH:MM TZ]`; one without is
  "unverified". State the snapshot date at report top.
- **`variant_key`.** Confirmed from **spec text, SKU option strings, or a manufacturer id (EAN/MPN),
  never the title**. When a spec block and an option string disagree the **option string wins**, and
  that spec block stops counting as an independent source (`source-reliability.md`).

### B. Comparability, a sticker is not a price

- **#3 Landed cost, not sticker.** See Step 6. No computable landed cost → label `⚠ sticker only,
  actual landed cost may be higher.` Every tax/duty/shipping/FX value MUST resolve to a
  `reference/data/` row (`source_url` + `verified_date`) or be stamped `(assumed)`; a rate typed from
  memory is a provenance bug (CONSTITUTION I.7). For oversized goods freight and packaging can
  dominate to where item price stops deciding the ranking (`source-reliability.md` cross-border).
- **#2 Stock state is part of the price.** In-stock ranks first; OOS / preorder is a footnote.
  **Rank on the fulfilment promise, not the stock attribute**, which is the one that lies.

### C. Verification, test the claim instead of repeating it

- **#4 Coupon and promo gate.** Badges are not evidence: verify via a playwright cart test or label
  `coupon claims unverified` (Honey 2026 status in `domains/browser-extensions.md`). A PDP lists what
  promos **exist**; only the order-confirm page shows what **stacks**. Quote a range with conditions
  named, and say when the confirm page was not reached.
- **#7 Disagreement = re-fetch / reconcile, never average** (`evidence-schema.md` #7):
  - (a) **Cross-snapshot** (same page, two pulls >5% apart): re-fetch a 3rd time; resolve or surface
    both with timestamps.
  - (b) **Cross-SOURCE recon** (different sources): FIRST confirm same `variant_key` (mismatched =
    two SKUs, separate, NOT a disagreement); if same-key and >5% apart, write a Disagreement-matrix
    row (cause ∈ `{different seller, stale/aggregated (E2/E3), coverage-gap}`) and resolve by grade,
    E1 wins; an E2/E3 that can't be lifted corroborates or is discarded, never averaged.

### D. Absence is not a finding, and this is where runs go wrong

**A search result page looks identical whether the market is empty, the query was gated, or you only
read the top of it.** These four rules tell those apart. Signatures, failure modes and war-stories:
`source-reliability.md` "Reading a search result page".

- **#11 Control-query gate: a zero is not a zero until a control says so.** Before recording ANY
  zero-result from a marketplace search, re-query a term that platform certainly stocks. Control also
  zero → **every zero from that platform this run is void** (an access-state signal, not a stock
  signal). Cite the control + its result beside the finding. Applies to a brand's own in-store search.
- **#12 Depth gate: the first page is not the market.** Any ranked "cheapest" MUST declare pages read,
  unique items, and **how paging was driven**. Test the mechanism, never assume it. Judge pages by
  **new ids, not returned count** (a full grid of duplicates is a broken pager, and trusting an
  ignored page param manufactures false coverage). Stop at zero new ids or once the band's floor is
  covered. Sort order is part of depth: say whether you paged to the floor or sorted by price.
  - **A silently-ignored page param is the common failure**, and it fails *quietly*: the page still
    returns 200 with a full grid. Diff item ids across pages before believing any pager. When a web
    UI has no pager at all, the SPA's own XHR endpoint usually does, capture it from the network log
    and drive that (worked example: `domains/auction-resale.md` → Goofish mtop).
  - **Report coverage as a fraction.** Most search backends return a total-hits field; quote it
    (`read 300 of 3,564`). "Scanned N items" hides whether N is the market or a rounding error.
  - **Dedupe by SELLER before treating repeated prices as agreement.** Listing spam concentrates on
    page 1, so a price repeated by one account reads as multi-seller consensus exactly where the
    evidence is thinnest. Observed in a real run: two accounts had posted 14+ near-identical
    listings, and the "consensus" price was one seller talking to itself. N listings from one
    nickname is **one** data point.
- **#9 Failures AND never-tried become explicit gaps** (`evidence-schema.md` #9):
  - (a) **Failures:** subagent returns `failed/empty` → one query rewrite + retry; still empty → an
    explicit "Not covered" entry.
  - (b) **Coverage floor:** an in-scope channel class (`channel-classes.md`) never attempted is also a
    gap. "Coverage gaps" MUST list every in-scope class not taken to `E1`; completeness-by-omission
    is a bug.
  - (c) **Typed reason, not prose:** `session-gated-declined` / `session-gated-unattended` /
    `structurally-unreachable` / `tool-outage` / `not-attempted`. Collapsing "one login away" into
    "no login helps" is what makes a reachable channel look permanently dead. Never backfill a gapped
    cell with another channel's numbers.
- **#6 No silent degradation.** Any fallback is stated in-line (`⚠ historical data unavailable, only
  live price shown...`). **A tool's health line is not evidence it works**: probe it functionally, a
  server can report Connected while every call returns empty.

### E. Adversarial, what would make this wrong

- **#8 Disconfirmation mandate.** Run a dedicated reverse-search subagent (scam / counterfeit /
  fake-reseller / refurb-not-as-advertised / DOA) against the cheapest pick; report a "Risks &
  counter-evidence" section. Empty = "actively reverse-searched, none found, not proof of safety,"
  never silence. Taxonomy + Codex option: `evidence-schema.md` (#8).
- **#10 Affiliate and non-merchant prices MUST NOT bias the ranking.** Cross-check any "save $X via
  our link" claim (Honey, Karma, Slickdeals, smzdm) against the retailer's public price. A price shown
  by a notification or release-calendar site that is **not itself the merchant** is not reproducible
  at checkout, `E3` at best. Detail: `evidence-schema.md` (#10).

## Output

Synthesize per `reference/report-template.md`: snapshot timestamp, parsed buy intent (for the user to
confirm), landed-cost ranked table, history note, coupon-applied list, risks & counter-evidence,
explicit coverage gaps + "configure source X for deeper data" lines, full source list.

## Close the feedback loop (Step 7, write what you observed)

At the end of a real run, append one line per source touched to the **private** `live-runs.jsonl`
(reuses guardrail verdicts, tells the next refresh which matrix entries the world just proved
right/wrong), plus one `coverage_gap` line per IN-SCOPE channel class
(`reference/channel-classes.md`) NOT taken to E1, this is how a missing CHANNEL (not just a dead
tool) reaches the refresh loop (`reference/refresh-protocol.md`).

**WHERE:** `~/.shopping-aggregator-config/data/metrics/live-runs.jsonl` (or
`$SHOPPING_AGGREGATOR_DATA_DIR/metrics/live-runs.jsonl`). Resolve it with
`tools/datadir.py`; if there is no data dir, the skill is UNINITIALIZED, report the observations in
your reply and stop. **NEVER write it into the repo.** These lines record what a real person priced,
which retailer they bought from, and where it ships; the repo is public, and no content scan can see
the difference between that and a schema. The repo carries the shape only:
`metrics/live-runs.jsonl.example`.

```jsonc
{ "ts":"<UTC>", "domain":"amazon-us", "source":"keepa",
  "outcome":"verified|unverifiable|dead|fallback_used|price_mismatch|coupon_fake|coverage_gap",
  "detail":"<what diverged>", "user_correction": null }  // user_correction = highest-weight truth
```

Per CONSTITUTION II.5: if you can't write the file (no data dir / not writable), note the
observations in your reply instead, dropping them entirely is a bug.

**The generalizable half goes public.** When an observation is a fact about a SOURCE or a RETAILER
CLASS rather than about this shopper (a scrape route that returns `$0`, a retailer that hides
per-store stock), it also belongs in `reference/source-reliability.md`, stripped of the product,
price, and region. That doc is how the tool gets smarter without the repo learning anyone's life.

## Recurring / monitoring use

**One-shot**, "should I buy this now and where." For "watch this and alert me below $X", point the
user to `/schedule` (cron re-run) or a native Keepa / Camelcamelcamel / 慢慢买 price alert; monitoring
+ distribution is out of scope for this thin layer (market-intel P5).

## Progressive loading rules

SKILL.md (this file) is always loaded, keep it the only frequently-loaded content. Read on-demand,
**never a whole directory**: `reference/login-handoff.md` at Step 3b whenever a channel looks
session-gated, and again before writing any `coverage_gap` whose reason starts `session-gated`;
`reference/sources-index.md` + `reference/channel-classes.md` at triage; only the matched
`reference/domains/<domain>.md`; `reference/tools/index.md` then only the picked
`reference/tools/<slug>.md`; `reference/source-reliability.md` at Step 3/4 when choosing a route and
again at Step 7 before writing a `coverage_gap` (which sources hold up, which fail and how to detect
it); `reference/install-guide.md` when setting up a source;
`reference/evidence-schema.md` at Step 5; the relevant `reference/data/*.json` table(s) at Step 6
landed-cost (us-sales-tax / cross-border-duty / shipping-baselines) + `reference/data/fx-source-of-record.md`
for FX; `reference/volatile/pricing-install.md` only when guiding an install (time-stamped, verify
against the official site first).

## Maintenance

The matrix decays. To "refresh the source matrix / 刷新比价工具库" or on a scheduled sweep, follow
`reference/refresh-protocol.md` (per-domain fan-out for new/changed/dead tools since each shard's
`last_verified`, apply guardrails, edit shards incrementally, diff in `CHANGELOG.md`, bump version).
Cadence: **monthly** (faster than market-intel, promo cycles + browser-extension policy churn).
