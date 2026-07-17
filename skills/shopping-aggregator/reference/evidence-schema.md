# Evidence unit + tiering / grade rules (read at Step 5)

This is the on-demand detail behind SKILL.md Step 5 (the structured evidence unit) and guardrails
**#5 / #5b / #7 / #9**. SKILL.md carries the bare schema + one-line imperatives; the long rules,
field commentary, and the real-run war-stories live here so the always-loaded file stays thin.

## The structured evidence unit (annotated)

Every subagent returns this, not free prose. Field-by-field commentary:

```jsonc
{
  status: ok|partial|empty|failed,
  retailer: "amazon.com" | "ebay" | ...,
  product_match: { title, asin/itemId/skuId, variant_key, confidence: high/med/low },
  // variant_key (REQUIRED) = normalized "brand|model|color|edition|condition" read off the PDP;
  // prices with a DIFFERENT variant_key are DIFFERENT SKUs — list separately, never compared as one (guardrail #7).
  prices: [{
    sticker, currency,
    shipping, tax_estimate, coupon_applied, cashback_estimate,
    landed_cost,
    stock_state: in_stock|low_stock|out_of_stock|preorder,
    seller_name,      // REQUIRED for L1–L4 retailer units — see #5
    seller_rating, condition: new|refurb|used,
    snapshot_ts: "YYYY-MM-DD HH:MM TZ",
    source_url,
    seller_tier: L1|L2|L3|L4|L5,   // WHO sold it (first-party … unverifiable) — see #5
    evidence_grade: E1|E2|E3        // HOW the price was obtained: E1 = live PDP read / official API ·
                                    // E2 = aggregator field (BigGo/Keepa/SERP-with-price) · E3 = SERP
                                    // snippet / cross-model recall = a LEAD. Ranking checks this FIRST (#5b).
  }],
  history: { 90d_low, 90d_high, 365d_low, "now_vs_low": "$X above", source_url } | null,
  coupon_attempts: [{ code, applied: yes|no, savings }],
  notes: "..."
}
```

Apply a length cap per field. The main agent **reduces** these units, it does NOT read raw page
dumps. If fan-out exceeds ~5 retailers, insert a combiner layer (each combiner merges 3 to 4 workers)
so the main context never holds N long page dumps.

## #5, Seller tiers (L1 to L5): WHO sold it

- **L1** first-party retailer (or the brand itself)
- **L2** marketplace seller with high rating
- **L3** marketplace seller with low rating or thin history, also the default when seller is unconfirmed
- **L4** unknown / dropshipper
- **L5** unverifiable (codex / BigGo leads legitimately lack a seller field)

A retailer **DOMAIN is not proof of first-party.** Best Buy Marketplace, Walmart Marketplace,
Newegg 3P and Amazon 3P all render under the retailer's own domain. Stamp **L1 ONLY after reading
the listing's `Sold by` / `Shipped by` field** and confirming it is the retailer or the brand. If
that field was not read, the unit is **L3 (seller unconfirmed)**, never L1. So `seller_name` is
required on every L1 to L4 retailer live-fetch unit, but a **missing seller_name degrades the tier to
L3, it does NOT reject the unit** (L5 leads legitimately lack a seller field). Don't rank L4/L5 as
winners without explicit user override. Mark every retailer's tier in the output.

> **War-story:** a conspicuously cheap listing on a big-box retailer's own domain was actually a
> 3.7★ Marketplace 3P seller, caught only by reading the Sold-by field. Domain alone would have
> mis-stamped it L1, and price alone would have ranked it #1.

## #5b, Evidence grade (E1/E2/E3): HOW the price was obtained, gates ranking FIRST

Evidence grade is **ORTHOGONAL to seller tier and gates ranking FIRST.** Tag every price:

- **E1** live PDP read / official API
- **E2** aggregator field, BigGo / Keepa / a SERP result carrying a price
- **E3** SERP snippet / cross-model recall = a *lead*

Rules:
- **Only `E1` may be a ranked winner.**
- `E2` may enter the ranking only with a corroborating `E1` of the **same `variant_key`**.
- `E3` is never ranked, it must be re-fetched to `E1` first.
- A clean first-party domain does **NOT** upgrade an E3 snippet, evidence_grade is checked before
  seller_tier.

> **Run B war-story:** the "$1,450" figure was an E3 SERP snippet; the real E1 PDP was
> $1,199.99, neither the same number nor the same SKU.

## #7, Disagreement handling (cross-snapshot AND cross-source)

- **(a) Cross-snapshot (same page, two pulls):** if two playwright pulls of the same page disagree
  by >5%, re-fetch a 3rd time and either resolve or surface both with timestamps, prices can
  genuinely change mid-fan-out (Buy Box rotation).
- **(b) Cross-source recon (different sources, same product):** FIRST confirm the prices share the
  **same `variant_key`**, mismatched variants are two SKUs, listed separately, NOT a disagreement.
  If two same-`variant_key` sources differ by >5%, write a Disagreement-matrix row with a cause from
  the closed set `{different seller, stale/aggregated (E2/E3), coverage-gap}`, and resolve by
  evidence grade (E1 wins; an E2/E3 that can't be lifted to E1 corroborates or is discarded, **never
  averaged**).

> **Run B war-story:** codex ~$1.0 to 1.3k vs Newegg E1 PDP $1,199.99 vs a $1,450 E3 snippet were
> never reconciled, that is exactly the (b) gap this rule closes.

## #8, Disconfirmation mandate (esp. for cheapest-source recommendations)

Run a dedicated reverse-search subagent against the negative space of the cheapest pick: scam /
counterfeit / "X is a fake reseller" / refurb-not-as-advertised / shipping-from-China-charged-as-US /
dead-on-arrival reviews. The report MUST include a "Risks & counter-evidence" section. An empty result
is written as **"actively reverse-searched, none found, not proof of safety"**, never silence. If the
Codex MCP is connected, also run this reverse-search through it as an independent cross-model check ,
treat its findings as **L5 corroboration, not proof** (see `reference/codex-crossval.md`).

## #10, Affiliate disclosure tracking (read-only)

Many extensions / sites (Honey, Karma, Slickdeals, smzdm) run on affiliate hijacking. This is fine
for the *user* to know, but it MUST NOT bias the ranking: when an extension claims "save $X via our
exclusive link," cross-check against the same retailer's public price before crediting the saving.

## #9, Failures AND never-tried become explicit gaps (coverage floor)

- **(a) Failures:** any subagent that returns `failed/empty` triggers one query rewrite + retry; if
  still empty, list it in an explicit "Not covered" section.
- **(b) Coverage floor (never-tried):** a channel class that is IN SCOPE per `channel-classes.md`
  but was **never attempted** is also a gap, record it `status: not-attempted` with a reason, emit a
  `coverage_gap` line (Step 7), and the report's "Coverage gaps" section MUST list every in-scope
  class not taken to `E1` depth. Completeness-by-omission (silence about a channel you never queried
, e.g. a category-specialist or local-pickup class) is a bug. A report may not look complete while
  a buyer channel was never checked.
