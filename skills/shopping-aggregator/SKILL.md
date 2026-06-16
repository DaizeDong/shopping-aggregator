---
name: shopping-aggregator
description: Use when the user wants to compare prices for a SPECIFIC product they're about to buy across multiple retailers — Amazon / eBay / Walmart / Target / Best Buy / Taobao / Tmall / JD / Pinduoduo — plus price-history sources (Keepa / Camelcamelcamel / 慢慢买) and coupon/cashback layers (Capital One Shopping / Karma / Coupert / 购物党). Triages buy intent (product + region + budget + urgency), detects available shopping MCP/extension/tool, delegates live-price fan-out to playwright/BigGo-MCP/Keepa, enforces price-specific quality guardrails (timestamp + stock + landed cost + coupon-cart verification + retailer trust tiers). Sister skill to market-intel — that one handles broad commercial / seller-side research; THIS one handles consumer-purchase price comparison. Trigger phrases: "compare prices for X", "what's the cheapest place to buy", "is this a good deal", "should I wait for a sale", "比价", "查历史价", "全网最低价", "X 在哪里买便宜", "凑单"。
Base directory for this skill: ${CLAUDE_PLUGIN_ROOT}/skills/shopping-aggregator
---

Base directory for this skill: ${CLAUDE_PLUGIN_ROOT}/skills/shopping-aggregator

# shopping-aggregator

A thin orchestration layer for consumer shopping price comparison. It does **only three things that
nothing else does**: (1) parse a buy intent (product, region, budget, urgency, sensitivity) into
a triage of the right shopping domains; (2) detect which specialized shopping MCP / extension / OSS
tool is actually connected and guide installing missing ones; (3) enforce **price-specific**
quality guardrails (snapshot timestamp, stock state, landed cost normalization, coupon-cart
verification, retailer trust tiers). The heavy lifting — live page fetch, history backfill,
adversarial verification, citation synthesis — is **delegated** to playwright MCP / BigGo MCP /
Keepa MCP / `deep-research` / `market-intel`'s research harness. Do not re-implement those.

> **Design philosophy (governs all changes): root-cause design, not incremental patching** — change
> the assumption underneath a problem, not the symptom on top. This thin-delegation shape, the
> landed-cost (not sticker-price) ranking primitive, and the timestamp-mandatory volatile-data rule
> all follow from it. Full statement in the repo's `PHILOSOPHY.md`; every change must pass "does it
> fix the framing, or just patch a symptom?"

## Sister skill — when to use which

| You want | Use |
|---|---|
| "Help me compare prices and find the cheapest place to buy product X" | **this skill (shopping-aggregator)** |
| "Is this a good deal, should I wait for a sale, what's the historical low?" | **this skill** |
| "Research the competitive landscape / market sizing / category trends for X" | **market-intel** |
| "Find arbitrage / FBA / wholesale opportunities (seller side)" | **market-intel** (ecommerce-arbitrage shard) |
| "X/Twitter sentiment / competitor analysis / SEO intel" | **market-intel** |

If both apply (e.g. "I'm buying X — also tell me what reviewers think and whether the category is
declining"), invoke this skill for the buy decision and **delegate the side-research to market-intel
as a sub-task** rather than re-doing it here.

## When to stop and delegate immediately

Before doing anything, decide if this skill even applies:

- **Single retailer + you already picked it** ("just check Amazon for Bose QC45") → open the page, no
  workflow needed.
- **Bulk arbitrage / FBA sourcing / supplier discovery** → delegate to `market-intel`'s
  `ecommerce-arbitrage` shard. Different sources (Keepa for history, Helium 10 sales estimates,
  alibaba.com sourcing) and different verifier mindset.
- **Pure category research, no specific product** ("how big is the smart-lock market") →
  `market-intel`.
- **Single-fact lookup** ("what's Costco's return policy") → plain web search, no workflow.

## Workflow

### Step 1 — Parse the buy intent (BLOCKING)

Capture all five before fanning out. **Default-good for ambiguous asks: ask the user for the missing
fields before proceeding.** Skipping this step is the most common failure mode — it produces a
generic landscape report when the user wanted a buy decision.

| field | examples | why it changes routing |
|---|---|---|
| **Product** | "Bose QuietComfort 45 (QC45), refurb OK" | brand + model + spec + condition (new/refurb/used) controls SKU-level matching |
| **Region** | US (NJ), CN (mainland), cross-border | switches domain set: US-only → Amazon/eBay/Walmart/Best Buy; CN-only → Taobao/JD/PDD; cross-border → both + customs |
| **Budget / urgency** | "<$200", "willing to wait for sale", "need it for Wed" | "wait for sale" enables Keepa/Camelcamelcamel historical-low; "need Wed" hard-filters shipping speed |
| **Sensitivity** | warranty, refurb-OK, seller rating cutoff, shipping speed, returns | drives trust tiers (AliExpress seller rating, Amazon WHD vs marketplace) |
| **Existing accounts / extensions** | "I have Amazon Prime + Capital One Shopping" | use what's already installed; don't recommend new tooling unless clearly worth it |

If the user said only "find me the cheapest", confirm region + condition acceptability before
fanning out. Cheapest "new from authorized seller in US" ≠ cheapest "any condition + any seller
on AliExpress."

### Step 2 — Triage to domains

Read `reference/sources-index.md` (thin one-line-per-domain index). Match the buy intent to 1–N
domains. **Do not read full domain shards yet.** If region = US, expect to hit `amazon-us`,
`ebay-walmart-target`, `browser-extensions`, `mobile-apps-aggregators`, `claude-mcps`. If region =
CN, expect `taobao-tmall`, `jd-pdd`, plus `claude-mcps` and possibly `oss-self-host`. For
historical-low queries always include `amazon-us` (Camelcamelcamel/Keepa) or `taobao-tmall`
(慢慢买).

Pick a depth budget and hold to its hard caps:

| depth | max subagents | max rounds | max verifiers | use when |
|---|---|---|---|---|
| quick | 3 | 1 | 1 | one product + one region, no history needed |
| standard (default) | 6 | 2 | 3 | typical "what's the best price right now" |
| deep | 12 | 3 | 5 | explicit "comprehensive / 全面 / check everywhere" or high-ticket purchase ($500+) where execution cost > research cost |

Maintain a running count; when a cap is hit, stop fanning out and move to synthesis.

### Step 3 — Detect available sources (do NOT guess by tool name)

Run `claude mcp list` and parse the three-state health output — a source is only usable if it
shows `✓ Connected`. Treat `✗ Failed` and `! Needs authentication` as **not available**.
Tool-name prefix matching (`mcp__*shopping*`) is unreliable: deferred tools, plugin prefixes,
and dead connections all distort it.

For shopping specifically, also detect:
- **playwright MCP** — almost always connected; the default ④ route for live page fetch.
- **firecrawl** skill — adequate fallback for static pages; **NOT enough for Amazon/Taobao**
  (anti-bot, 500 / login-wall — see `reference/domains/amazon-us.md` "real-run lesson"). Skip to
  playwright for those.
- **BigGo MCP** — primary purpose-built consumer price-compare MCP (see `reference/tools/biggo-mcp.md`).
- **Keepa MCP** — historical-price authority for Amazon.
- **Apify price-intelligence MCP** — paid, broadest US-retailer coverage.

Also check user-side tooling (you can ask, you can't auto-detect): Camelcamelcamel bookmark, Keepa
account, browser extensions (Capital One Shopping / Karma / 购物党 / 慢慢买 App).

### Step 4 — Select sources + guide install (non-blocking)

For each triaged domain, read **only** its shard: `reference/domains/<domain>.md`. Pick the best
**available** source. **Prefer the free browser-automation / act-like-human route (④) over paid
APIs when it fits** — playwright MCP can read the real Amazon / Taobao rendered page in one shot;
paid APIs (Keepa, Rainforest, PriceAPI) earn their cost only when they unlock something playwright
can't (deep history, scale, compliance).

If the topic clearly depends on a source that is missing:

> "This buy decision depends on <source> (e.g. price history → Keepa). Recommend installing it:
> `claude mcp add -s user <...>` (exact command + cost in `reference/volatile/pricing-install.md`).
> **Note: a newly added MCP only takes effect after you restart the session or `/mcp` reconnect —
> it will NOT work this turn.** For now I'll proceed with a fallback source and flag the gap."

Never block on install. Prefer HTTP-transport sources on Windows (no local Node/uv needed; stdio
`npx`/`uvx` MCPs are flaky there). See `reference/install-guide.md` for L0 mechanics +
secret-handling hygiene (keys must NEVER enter the transcript).

### Step 5 — Delegate execution

Hand the selected sources + sub-questions to the heavy harness:

- **Per-retailer live price** → playwright MCP (one subagent per retailer; each told to load the
  MCP via ToolSearch first — subagents inherit MCPs only in deferred form).
- **Multi-retailer one-shot** → BigGo MCP if connected, else Apify price-intelligence MCP, else
  fan out playwright.
- **History query** → Keepa MCP (Amazon) / Camelcamelcamel web fetch (Amazon free) / 慢慢买
  (CN platforms).
- **Adjacent research** (reviews, "is this brand reliable", "should I wait for Prime Day") →
  delegate to `market-intel` or `deep-research`.
- **Independent cross-validation + channel discovery (cross-model)** → delegate to the **Codex MCP**
  (`mcp__codex__*` — GPT with its own web search), a genuinely independent second model + search
  backend. Use it to (a) discover authorized channels / cheaper authentic sources your fixed retailer
  list missed, (b) cross-check the provisional cheapest pick, (c) sanity-check authenticity /
  counterfeit reputation. **Codex prices are L5 *leads*, never authoritative** — any price it surfaces
  must re-pass the live-fetch + citation gate (Step 6 / guardrail #1) before entering the landed-cost
  ranking. **Best-effort**: if the Codex MCP is not connected, skip it and note the gap (guardrail #9).
  Call it via the **MCP server** (`codex mcp-server`), NOT Bash `codex exec` (the latter hits a
  cloud-config egress block inside the agent sandbox). Full how-to: `reference/codex-crossval.md`.

Require every subagent to return a **structured evidence unit**, not free prose:
```
{
  status: ok|partial|empty|failed,
  retailer: "amazon.com" | "ebay" | ...,
  product_match: { title, asin/itemId/skuId, confidence: high/med/low },
  prices: [{
    sticker, currency,
    shipping, tax_estimate, coupon_applied, cashback_estimate,
    landed_cost,
    stock_state: in_stock|low_stock|out_of_stock|preorder,
    seller_name, seller_rating, condition: new|refurb|used,
    snapshot_ts: "YYYY-MM-DD HH:MM TZ",
    source_url, source_tier: L1|L2|L3|L4|L5
  }],
  history: { 90d_low, 90d_high, 365d_low, "now_vs_low": "$X above", source_url } | null,
  coupon_attempts: [{ code, applied: yes|no, savings }],
  notes: "..."
}
```
with a length cap per field. The main agent reduces these units — it does **not** read raw page
dumps. If fan-out exceeds ~5 retailers, insert a combiner layer (each combiner merges 3–4 workers)
so the main context never holds N long page dumps.

### Step 6 — Normalize and rank by LANDED COST

This is the most-skipped step and the most decision-relevant.

- **All prices to user's preferred currency** (default = user's region currency). When converting,
  cite the FX rate + timestamp; do not silently round.
- **Add: shipping + tax + coupon savings - cashback estimate → landed cost.** Sticker price alone
  is a ranking trap — Amazon Prime free-ship vs eBay $15 ship can flip a "winner."
- **Tax estimate**: use user's state (e.g. NJ sales tax 6.625%) for US; for cross-border include
  customs duty estimate or flag "unknown duties — confirm at checkout."
- **Coupon application**: verify by **playwright cart test** when possible (don't trust the
  retailer's "coupons available" badge — most don't actually apply). Mark each `code, applied?, $`.
- **Trust-adjust**: drop seller-marketplace listings with rating < 95% or < 500 ratings unless user
  said it's fine. AliExpress especially needs this filter.
- **Output the table sorted by landed cost**, with a "but actually" footnote on top-2 picks
  (warranty, return policy, shipping speed differentiators).
- **History note**: "current price is $X above 90-day low / at 365-day low / NEW LOW" — explicitly.
  If recommending "wait for sale," cite the historical seasonality (Camelcamelcamel chart link or
  Keepa screenshot).

## Quality guardrails (HARD rules — apply during synthesis)

These are **price-data-specific** extensions of the market-intel guardrails. Read both together.

1. **Snapshot timestamp is MANDATORY.** Every price entry must carry
   `[fetched YYYY-MM-DD HH:MM TZ]`. Prices change hourly (esp. Amazon Buy Box). A price without a
   timestamp is "unverified." When recommending, also state the snapshot date at report top.
2. **Stock state is part of the price.** "$120 cheapest" with `out_of_stock` is not the answer.
   Rank in-stock first; OOS or preorder = footnote, not top pick.
3. **Landed cost, not sticker price.** See Step 6. If a source returns sticker only and you can't
   compute landed cost, label it `⚠ sticker only — actual landed cost may be higher.`
4. **Coupon verification gate.** Don't trust "100 coupons available!" badges. Either verify via
   playwright cart test or label `coupon claims unverified`. Honey-style false-positive coupons
   are real (see Honey 2026 status — `reference/domains/browser-extensions.md`).
5. **Retailer trust tiers.** L1 first-party retailer (amazon.com, walmart.com sold-by-retailer) ·
   L2 marketplace seller w/ high rating · L3 marketplace seller w/ low rating or thin history ·
   L4 unknown / dropshipper · L5 unverifiable. Don't rank L4/L5 as winners without explicit user
   override. Mark every retailer's tier in the output.
6. **No silent degradation.** When Keepa is unavailable and you fall back to spot-only playwright,
   the report must say `⚠ historical data unavailable, only live price shown — cannot confirm
   if this is a good deal vs. recent floor.` Never swap silently.
7. **Cross-snapshot disagreement = re-fetch, don't average.** If two playwright pulls of the same
   page disagree by >5%, re-fetch a 3rd time and either resolve or surface both with timestamps —
   prices can genuinely change mid-fan-out (Buy Box rotation).
8. **Disconfirmation mandate (esp. for cheapest-source recommendations).** Run a dedicated
   reverse-search subagent: scam / counterfeit / "X is a fake reseller" / refurb-not-as-advertised
   / shipping-from-China-charged-as-US / dead-on-arrival reviews. Report must include a "Risks &
   counter-evidence" section. Empty → "actively reverse-searched, none found — not proof of
   safety." If the **Codex MCP** is connected, also run this reverse-search through it as an
   independent cross-model check (treat its findings as L5 corroboration, not proof; see
   `reference/codex-crossval.md`).
9. **Failures become explicit gaps.** Any subagent that returns `failed/empty` triggers one query
   rewrite + retry; if still empty, list it in an explicit "Not covered" section. A report must
   never look complete while hiding a missing retailer.
10. **Affiliate disclosure tracking (read-only).** Many extensions / sites (Honey, Karma,
    Slickdeals, smzdm) operate on affiliate hijacking. This is fine for the *user* to know but
    don't let it bias the ranking — when an extension claims "save $X via our exclusive link,"
    cross-check against the same retailer's public price.

## Output

Synthesize per `reference/report-template.md`: snapshot timestamp, parsed buy intent (so the user
can confirm we understood), landed-cost ranked table, history note, coupon-applied list, risks &
counter-evidence, explicit coverage gaps + "configure source X for deeper data" lines, full
source list.

## Close the feedback loop (Step 7 — write what you observed)

At the end of a real shopping run, append one line per source you actually touched to
`metrics/live-runs.jsonl` (this reuses verdicts the guardrails already produced — near-zero extra
cost). This is the highest-value error signal: it tells the next refresh which matrix entries the
real world just proved right or wrong.

```jsonc
{ "ts":"<UTC>", "domain":"amazon-us", "source":"keepa",
  "outcome":"verified|unverifiable|dead|fallback_used|price_mismatch|coupon_fake",
  "detail":"<what diverged, e.g. Keepa said 90d-low $89 but Camelcamelcamel said $79>",
  "user_correction": null }   // set when the user manually corrected an entry — highest-weight truth
```

If you can't write the file (e.g. the repo isn't checked out), note the observations in your reply.

## Recurring / monitoring use

This skill is **one-shot** — it answers "should I buy this now and where." If the user wants
"watch this product and tell me when it drops below $X", that's a wrap: instruct them to use
`/schedule` (cron job that re-runs the skill on cadence) or set a Keepa / Camelcamelcamel /
慢慢买 native price alert. Monitoring + distribution is out of scope for this thin layer
(market-intel P5 — same doctrine).

## Progressive loading rules

- SKILL.md (this file) is always loaded — keep it the only frequently-loaded content.
- Read `reference/sources-index.md` at triage (thin).
- Read `reference/domains/<domain>.md` only for triaged domains. **Never read the whole domains/
  directory.**
- Read `reference/tools/index.md` (thin) to find a picked tool's doc slug; then read
  `reference/tools/<slug>.md` **only for the specific tool you're about to use**. **Never read the
  whole `tools/` directory** — that breaks progressive loading.
- Read `reference/install-guide.md` when setting up any source. It points down to per-domain (L1)
  and per-tool (L2) detail.
- Read `reference/volatile/pricing-install.md` only when actually guiding an install — prices and
  commands there are time-stamped and may be stale; verify against the official site before use.

## Maintenance

The source matrix decays. When asked to "refresh the shopping-aggregator source matrix /
刷新比价工具库", or on a scheduled sweep, follow `reference/refresh-protocol.md`: fan out one
subagent per domain to find new/changed/dead tools since each shard's `last_verified`, apply the
same quality guardrails, edit shards incrementally, record the diff in `CHANGELOG.md`, and bump
the plugin version. Refresh cadence is faster than market-intel's: **monthly** (consumer shopping
moves on Q/quarterly promo cycle; browser-extension policies change fast).
