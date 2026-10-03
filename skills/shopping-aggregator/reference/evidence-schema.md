# Evidence unit + tiering / grade rules (read at Step 5)

Use this schema and the rules below to reduce source observations into comparable evidence.

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
    discount_stack: [{ type: subscription|coupon|first_order|code|member|loyalty|portal,
                       value, condition, path,
                       mark: cart_tested|unverified|expired_failed|paid_later }],
                    // EVERY eligible discount on this offer, applied or not, see #16;
                    // marks follow CONSTITUTION I.5, plus paid_later for value that never reaches checkout
    discount_checked: ["<each purchase path selected>", "coupon page", "cart", "code sites"],
                    // REQUIRED: an empty discount_stack without this means NOT CHECKED, never "no stack"
    landed_cost,    // charged at checkout on this path's best tested stack; each path is its own price entry
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

## #8, Disconfirmation mandate (esp. for cheapest-source recommendations)

Run a dedicated reverse-search subagent against the negative space of the cheapest pick: scam /
counterfeit / "X is a fake reseller" / refurb-not-as-advertised / shipping-from-China-charged-as-US /
dead-on-arrival reviews. The report MUST include a "Risks & counter-evidence" section. An empty result
is written as **"actively reverse-searched, none found, not proof of safety"**, never silence. If the
Codex MCP is connected, also run this reverse-search through it as an independent cross-model check,
treat its findings as **L5 corroboration, not proof** (see `reference/codex-crossval.md`).

## #10, Affiliate disclosure tracking (read-only)

Many extensions / sites (Honey, Karma, Slickdeals, smzdm) run on affiliate hijacking. This is fine
for the *user* to know, but it MUST NOT bias the ranking: when an extension claims "save $X via our
exclusive link," cross-check against the same retailer's public price before crediting the saving.

## #9, Failures AND never-tried become explicit gaps (coverage floor)

- **(a) Failures:** any subagent that returns `failed/empty` triggers one query rewrite + retry; if
  still empty, classify the access state using `login-handoff.md` and list the unresolved gap in
  the final "Coverage gaps" section. The private record uses `outcome: coverage_gap` and the matching
  enum `gap_reason` from `refresh-protocol.md`; an empty result alone does not prove a structural limit.
- **(b) Coverage floor (never-tried):** a channel class that is IN SCOPE per `channel-classes.md`
  but was **never attempted** is also a gap. Record `outcome: coverage_gap` with
  `gap_reason: not-attempted` (Step 7), explain why in `detail`, and preserve that reason in the report.
  The report's "Coverage gaps" section MUST list every in-scope
  class not taken to `E1` depth. Completeness-by-omission (silence about a channel you never queried
, e.g. a category-specialist or local-pickup class) is a bug. A report may not look complete while
  a buyer channel was never checked.

## #16, Discount stack: the answer is the price the buyer can actually get

A worker that reports only the sticker has reported half an offer. For every offer and purchase path, list in `discount_stack` every discount available to this buyer now without joining or signing up for anything, whether or not the run could apply it: a subscription or auto-replenish price cancellable without fee, clip coupons (some render only after a subscription is selected, so look again after selecting it), first-order offers, codes from the cart and from coupon and deal sites, member pricing, loyalty rewards and cashback portals. Discounts that need a sign-up are conditional rows, not part of the stack. List in `discount_checked` every place you looked; an empty stack without it reads as "not checked", and that offer may not be reported as having no stack.

Mark each line with its CONSTITUTION I.5 status. Only `cart_tested` lines, in a combination that was tested together, reduce `landed_cost`, which is the amount charged at checkout. Product-page-only lines are a labelled "if applied" figure. `paid_later` value (cash back, portal cashback, rewards earned by this order) is shown beside the total with its form and expiry and is never subtracted; at most one portal or extension tracks an order. Store credit, gift-card balances and rewards already earned are the buyer's money and never a discount.

The headline answer is the path whose tested stack charges least, with its conditions written next to it; each other path of the same offer, including plain one-time, is its own row. A multi-pack is a different `variant_key` with its own total and per-unit price, ranked only when the buyer's quantity covers it. A sticker headline is acceptable only when the stack was tried and failed, could not be tested (labelled under #3), or was declined by the buyer.

> **War-story:** a run headlined the one-time price of the winning offer and listed the cheaper path, a fee-free cancellable subscription plus a first-order coupon on the same listing, as an aside. When the buyer said "buy it", the one-time option was what got bought. The buyer had to point out the subscription and the coupon, the order was cancelled before shipment and placed again, and the same item came out about a tenth cheaper. The aside was correct and useless: whatever the headline says is what gets executed.
