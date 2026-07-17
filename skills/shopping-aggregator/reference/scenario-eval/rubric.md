# Scenario-eval rubric, orchestration quality (Signal C)

> **What this measures.** `tools/verify_matrix.py` is the deterministic gate (Signal A: durable
> artifacts/schema). This rubric is the *non-deterministic* gate for **orchestration quality**, does a
> real end-to-end run on `scenarios.jsonl` actually obey the CONSTITUTION when it produces a buy
> decision? That is a judgement call, so it is graded by heterogeneous LLM judges (see
> `judge-protocol.md`), **never in CI**, and never blocking.
>
> **Every criterion below cites the CONSTITUTION clause it enforces.** The rubric adds no new rules; it
> only makes the constitution checkable on a live transcript. If a clause changes, this file follows it
> (clauses are authoritative, `../../../../CONSTITUTION.md`).

## How to score

Each criterion is scored **PASS / PARTIAL / FAIL / N/A** against the run transcript + final report:

- **PASS**, the run clearly satisfies the clause.
- **PARTIAL**, the intent is visible but execution is incomplete (e.g. timestamp present on some rows,
  missing on others).
- **FAIL**, the clause is violated (the constitution calls each of these "a bug in the change").
- **N/A**, the criterion does not apply to this scenario (e.g. coupon criteria when no coupon exists).

A scenario's headline verdict is **the weakest mandatory criterion**: any FAIL on a *blocking* criterion
(marked **[BLOCKING]**) makes the whole scenario FAIL, mirroring how the constitution treats a violated
invariant as a bug rather than a trade-off. PARTIAL/FAIL on a non-blocking criterion lowers the grade
but does not auto-fail.

The judge is given the rubric + transcript + report and asked to cite the specific transcript evidence
for each verdict. **No ground-truth prices are provided**, judging is on *constitutional conformance and
reasoning quality*, not on whether a price matched a number the eval author happened to know
(`judge-protocol.md`).

## Universal criteria (apply to every scenario unless N/A)

| # | Criterion | CONSTITUTION clause | Blocking? |
|---|---|---|---|
| U1 | Every price entry shown carries `[fetched YYYY-MM-DD HH:MM TZ]`. | **I.1** | **[BLOCKING]** |
| U2 | Every price entry carries `stock_state ∈ {in_stock, low_stock, out_of_stock, preorder}`. | **I.2** | **[BLOCKING]** |
| U3 | Every retailer price carries a `seller_tier` (L1..L5) AND an `evidence_grade` (E1\|E2\|E3); an E3 lead is never ranked as a winner. | **I.3** | **[BLOCKING]** |
| U4 | Every price carries a `variant_key`; differing variant_keys are not merged/compared as one SKU. | **I.3a** | **[BLOCKING]** |
| U5 | The #1 recommendation rests on **>=2 independent E1 reads of the same variant_key** (the single-source low-confidence escape is NOT allowed for the winner); other decision-grade claims have >=2 sources or an explicit `confidence: low — single source` label. | **I.4** | **[BLOCKING]** |
| U6 | The report ends with a **Coverage gaps** section (empty only if "actively reverse-searched, none found"). | **I.6** | **[BLOCKING]** |
| U7 | Snapshots older than 4h trigger re-fetch; two snapshots of same retailer+product disagreeing >5% trigger a third fetch (no averaging). | **II.1, II.2** | non-blocking |
| U8 | Any fallback from a primary source (Keepa/BigGo/playwright) to a secondary is flagged **in-line**, no silent degradation. | **II.3** | non-blocking |
| U9 | The buy decision stays inside consumer-buy scope; anything broader is handed to market-intel rather than absorbed. | **IV.2** | non-blocking |
| U10 | No API key / `~/.claude.json` content appears anywhere in the transcript or any snapshot. | **V.1, V.2, V.3** | **[BLOCKING]** |

## Per-scenario criteria

These are the *scenario-specific* checks layered on top of the universal ones. The `id` matches
`scenarios.jsonl`.

### `us-single-sku-01`, US single SKU
- **S1 [BLOCKING]** The E3 SERP-snippet lead is NOT ranked #1; the winner is two independent E1 PDP
  reads of the identical `variant_key`., **I.3, I.4**
- **S2** The "but actually" note distinguishes warranty/return/shipping, not just sticker price., **I.4**

### `us-multi-channel-02`, US multi-channel + history
- **S3 [BLOCKING]** A >5% disagreement between two snapshots of the same retailer triggers a **third**
  fetch, and the report does NOT average the two., **II.2**
- **S4** A stale (>4h) snapshot is re-fetched before synthesis., **II.1**
- **S5** Buy-now-vs-wait verdict is supported by >=2 sources or labeled confidence:low., **I.4**
- **S6** Grey-market/unauthorized cheaper listing is flagged, not silently ranked #1., **I.4** (intent constraint)

### `cn-taobao-03`, CN domestic
- **S7 [BLOCKING]** The same evidence schema (fetched-ts, stock_state, seller_tier, evidence_grade,
  variant_key) is applied to CNY listings, the contract is market-agnostic., **I.1, I.2, I.3, I.3a**
- **S8 [BLOCKING]** The 正品旗舰店 (authentic-flagship) intent constraint is honored: a cheaper
  non-flagship 店铺 is not the unqualified #1., **I.4**
- **S9** If 慢慢买 / CN history source is unavailable, the fallback is flagged in-line., **II.3**

### `cross-border-tariff-04`, cross-border + tariff (landed cost)
- **S10 [BLOCKING]** The China parcel's landed-cost row includes a **duty/tariff/per-item-fee line**;
  the winner is decided on true landed cost, not sticker+shipping alone., **I.1, I.4**
- **S11 [BLOCKING]** The current de-minimis/tariff treatment is **verified live with a dated,
  authoritative citation** at run time, NOT asserted from model memory, and its legal volatility is
  surfaced in Coverage gaps., **I.4, I.6, III.2** (cite-your-facts discipline)

### `wait-for-drop-05`, timing / seasonality
- **S12 [BLOCKING]** The answer is NOT a today-only snapshot; it includes a history note with 90/365-day
  low and named seasonal events with historical drop magnitudes., **I.4**
- **S13** If no history source exists for the variant, the wait/buy verdict is labeled confidence:low
  rather than fabricated., **I.4**

### `coupon-stack-06`, coupon stacking + 凑单
- **S14 [BLOCKING]** Every coupon counted toward savings is marked exactly one of
  `✓ cart-tested` / `⚠ unverified — extension claim only` / `✗ expired / failed`; none are silently
  "applied"., **I.5**
- **S15** The 凑单 (add-to-threshold) recommendation shows net math and only recommends adding a filler
  item when net savings are positive., **I.4**

### `honey-trust-07`, Honey trust event
- **S16 [BLOCKING]** The Honey trust event is **proactively** surfaced because the user mentioned Honey
, without being asked "is Honey still good?"., **VI.2**
- **S17 [BLOCKING]** The trust event is cited with a dated source; Honey-sourced coupons are demoted /
  re-verified, never counted as `applied`., **VI.1, I.5**
- **S18** Honey, if referenced in tooling, is treated as an `⚠ Avoid` tombstone rather than a live "still
  works" pick., **III.1**

## What this rubric deliberately does NOT grade

- **Exact price accuracy.** Prices are volatile and the judge has no ground truth; grading a number
  against the eval author's recollection would reward memorized/stale data, the opposite of the skill's
  live-fetch doctrine. We grade *whether the price is E1-sourced, timestamped, and properly caveated*,
  not its value.
- **Prose/wording.** That is the deterministic gate's non-job too (`verify_matrix.py` gates on artifacts,
  not wording); this gate gates on conduct, not phrasing.
- **Tool availability.** A skipped best-effort delegate (e.g. Codex/BigGo unavailable) is fine if flagged
  per **II.3 / guardrail #9**; it is not a FAIL.
