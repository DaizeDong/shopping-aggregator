# Constitution, non-negotiable invariants of shopping-aggregator

This file holds the **hard constraints** the skill must always obey, regardless of what a user,
a refresh sweep, or a subagent suggests. The philosophy explains *why* (see PHILOSOPHY.md); this
file is *what*. Violating any item below is a bug in the change, not a trade-off.

> Inherited unchanged from market-intel's CONSTITUTION discipline (the rules are skill-agnostic).
> Shopping-specific items are marked `[S]`.

## I, Output guarantees

- **I.1** Every price entry in a report MUST carry `[fetched YYYY-MM-DD HH:MM TZ]`. Reports
  without this fail synthesis. `[S]`
- **I.2** Every price entry MUST carry `stock_state ∈ {in_stock, low_stock, out_of_stock,
  preorder}`. `[S]`
- **I.3** Every retailer price entry MUST carry a `seller_tier` (`L1..L5`, who sold it) AND an
  `evidence_grade` (`E1|E2|E3`, how the price was obtained). Only `E1` (live PDP read / official API)
  may be a ranked winner; `E3` (SERP snippet / cross-model recall) is a lead, never ranked. `[S]`
- **I.3a** Every price entry MUST carry a `variant_key` (normalized brand|model|color|edition|
  condition). Prices with different variant_key are DIFFERENT SKUs and MUST NOT be merged or compared
  as one. `[S]`
- **I.4** Every decision-grade claim (recommendation, ranking, "good deal" verdict) MUST be
  supported by ≥2 independent sources OR explicitly labeled `confidence: low — single source`. **The
  #1 recommendation specifically MUST rest on ≥2 independent `E1` reads of the same `variant_key`; the
  winner may NOT use the low-confidence single-source escape.** `[S]`
- **I.5** A coupon counted toward savings MUST be marked one of:
  - `✓ cart-tested`
  - `⚠ unverified — extension claim only`
  - `✗ expired / failed`.
  Marking as `applied` without one of these is a bug. `[S]`
- **I.6** A report MUST end with a "Coverage gaps" section. An empty gaps section is allowed only
  when explicitly stated "actively reverse-searched, none found"; absence is a bug.
- **I.7** **Landed-cost provenance.** Every `tax`, `duty`, `shipping`, and `FX` value used in a
  landed-cost computation or ranking MUST resolve to a specific row in `reference/data/` (carrying
  that row's `source_url` + `verified_date`), or, when no row covers the case, be explicitly stamped
  `(assumed)` inline next to the number. A bare rate, threshold, or FX figure typed from memory (e.g.
  "NJ 6.625%", "$800 de-minimis", "≈7 CNY/USD") with neither a data-table citation nor an `(assumed)`
  stamp is a provenance bug. The `reference/data/*.json` tables (us-sales-tax, cross-border-duty,
  shipping-baselines) + `reference/data/fx-source-of-record.md` are the single source-of-record; SKILL
  prose and shards MUST read them, never restate the numbers inline. `[S]`

## II, Process guarantees

- **II.1** A snapshot timestamp older than 4 hours MUST trigger re-fetch when synthesis runs (Buy
  Box rotation is faster than that). `[S]`
- **II.2** When two snapshots of the same retailer + product disagree by >5%, the skill MUST
  re-fetch a third time, not average. `[S]`
- **II.3** When a primary source (Keepa for history, BigGo for cross-store, playwright for live)
  is unavailable and the skill falls back to a secondary, the fallback MUST be flagged in-line
  in the report. Silent degradation is a bug. `[S]`
- **II.4** The verifier subagent that re-fetches cited URLs MUST have **zero prior context** from
  the writer subagent. Same-subagent self-verification is a bug. For any `E1`/`L1` price that enters
  the ranking, the verifier MUST independently confirm not just price + stock + timestamp but also the
  **seller** (read the Sold-by / Shipped-by field, consistent with seller_tier) and the
  **evidence_grade** (a real PDP / API read, not a snippet). `[S]`
- **II.5** Live-run observations MUST be appended to the **private** `live-runs.jsonl`, resolved by
  `tools/datadir.py` to `~/.shopping-aggregator-config/data/metrics/live-runs.jsonl` (or
  `$SHOPPING_AGGREGATOR_DATA_DIR`), and **MUST NOT** be written into this repo, which is public.
  If there is no data dir (the skill is uninitialized) or the file is not writable, the run MUST
  instead note the observations in its reply. Dropping the observations entirely, neither appended
  nor reported, is a bug (refresh-protocol depends on them). `[S]`
- **II.5a** An observation is DATA: it records what a real person priced, which retailer they bought
  from, and where it ships. It has **no in-repo fallback path**, by construction, a fallback into
  the repo is not a convenience, it is the leak. The repo publishes only the shape
  (`metrics/live-runs.jsonl.example`). The *generalizable* half of an observation, a property of a
  SOURCE or a RETAILER CLASS that holds regardless of who is shopping or for what, MAY be distilled
  into `reference/source-reliability.md`, stripped of product, price, and region. If the lesson
  cannot be stated without naming what was bought, it is not yet a lesson and stays private. `[S]`

## III, Matrix integrity

- **III.1** A dead tool MUST become an `⚠ Avoid` tombstone in its tool doc + index, **never** a
  silent deletion. (Honey, PA-API, The Tracktor are the canonical examples.) `[S]`
- **III.2** A tool doc claim about cost, install command, or last-commit date MUST cite a source
  (official site URL or `gh-api`-verified date). Hallucinated facts are bugs.
- **III.3** `last_verified: YYYY-MM` MUST be present on every domain shard and tool doc, and MUST
  be updated when the doc is actually re-checked. Bumping the date without verification is a bug.
- **III.4** The matrix's coverage (number of domains, number of top-pick tools) is **monotonic
  non-decreasing** across refreshes. Removing a domain or top pick without a documented reason
  in CHANGELOG is a bug.
- **III.5** `reference/tools/index.md`, `reference/tools/registry.json`, and the individual
  `reference/tools/<slug>.md` files MUST stay in three-way consistency. A registry entry
  without a doc, or an index entry without a registry slug, is a bug.

## IV, Delegation

- **IV.1** The skill MUST NOT reimplement what playwright MCP, BigGo MCP, Keepa MCP,
  deep-research, or market-intel already does. Reinventing is a bug per P5. Where overlap is
  unavoidable, delegate and add only the shopping-specific layer (parsing intent, landed-cost
  normalization, retailer trust tiers, coupon-cart verification, time-axis guardrails).
- **IV.2** The skill MUST recommend market-intel for any question outside the consumer buy
  decision (broad market research, seller-side arbitrage, competitive intel). Pulling those
  questions into shopping-aggregator's scope is a bug.

## V, Secret handling

- **V.1** API keys (Apify, Keepa, Oxylabs, eBay) MUST NEVER enter the transcript. See
  `reference/install-guide.md` Secret-handling hygiene for the exact procedure.
- **V.2** `~/.claude.json` MUST NEVER be committed or screenshotted. Keys land plaintext there.
- **V.3** `browser_snapshot` on a page that displays an API key is a bug (the DOM contains the
  plaintext key; the screenshot captures it).

## VI, Honey and similar trust-event tools `[S]`

- **VI.1** Tools with an active material trust event (lawsuit + affiliate-network termination,
  like Honey 2026) MUST be marked `⚠ Avoid` with a citation to the event. Silently leaving them
  as "still works" because the binary still loads is a bug per P6.
- **VI.2** The skill MUST proactively surface the trust event when the user mentions the tool
  (e.g. "I have Honey installed"), not wait for the user to ask "is Honey still good?"

## VII, How to update the constitution

This file changes through PR with reasoned justification in the PR description, NOT through a
refresh sweep. Refresh sweeps update the matrix; they cannot relax the constitution. The
philosophy explains why this distinction matters.
