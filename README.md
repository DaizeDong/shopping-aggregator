# shopping-aggregator

Triage any buy intent across 13 shopping domains, rank by landed cost (not sticker), and delegate the live-price fan-out to your existing research harness.

[![Claude Code Skill](https://img.shields.io/badge/Claude%20Code-Skill-orange?style=flat)](https://docs.anthropic.com/en/docs/claude-code)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Source Matrix](https://img.shields.io/badge/Source%20Matrix-13%20domains-green?style=flat)](skills/shopping-aggregator/reference/sources-index.md)
[![Data tables](https://img.shields.io/badge/Data%20tables-tax%20%7C%20duty%20%7C%20FX%20%7C%20shipping-green?style=flat)](skills/shopping-aggregator/reference/data/README.md)
[![Languages](https://img.shields.io/badge/Languages-EN%20%2F%20CN-blue?style=flat)](#languages)
[![Roadmap](https://img.shields.io/badge/Roadmap-v0.4.0-purple?style=flat)](ROADMAP.md)

[English](README.md) | [中文版](README_CN.md)

---

## ⭐ Read this first — the design philosophy

shopping-aggregator inherits market-intel's organizing principle — **root-cause design, not
incremental patching.** When something is wrong, change the assumption underneath it, not the
symptom on top. That principle, applied to *consumer shopping*, produced every shopping-specific
decision in this skill:

- **Landed cost, not sticker price** — sticker rankings are a trap (Amazon Prime free-ship vs
  eBay $15 ship flips winners). We made landed cost the ranking primitive.
- **Snapshot timestamp is mandatory** — prices change hourly (Buy Box). An undated price is
  unverified by default.
- **Coupon-cart verification** — extension "savings" badges are a known fraud surface (the
  Honey lawsuit). We verify via playwright cart test or label as ⚠ claim.
- **Honey ≠ default-good in 2026** — the Rakuten/Impact/Awin terminations of Jan 2026 changed
  the trust landscape. The skill carries this forward proactively.

📜 **[Read the full design philosophy → PHILOSOPHY.md](PHILOSOPHY.md)**.

### Sister skill — when to use which

`shopping-aggregator` is the **consumer-purchase specialization** of the broader market-research
toolkit at [`market-intel`](https://github.com/DaizeDong/market-intel).

| Your question | Skill |
|---|---|
| "Compare prices for X across retailers, where's cheapest" | **shopping-aggregator (here)** |
| "Is this a good deal, should I wait, what's the historical low" | **shopping-aggregator** |
| "Research the X category, who are the players, what's growing" | [**market-intel**](https://github.com/DaizeDong/market-intel) |
| "Find arbitrage / FBA / wholesale opportunities (seller side)" | [**market-intel**](https://github.com/DaizeDong/market-intel) → `ecommerce-arbitrage` shard |
| "X/Twitter sentiment / competitor SEO / lead generation" | [**market-intel**](https://github.com/DaizeDong/market-intel) |

Both skills can coexist — install both, the orchestration logic in each handles its own scope.

---

## What it is (and isn't)

A thin orchestration skill for **consumer shopping price comparison**. Triages your buy intent
(product + region + budget + urgency), finds the right specialized shopping source (and helps you
install it), then hands the heavy lifting to your existing research harness — instead of
reinventing it.

Claude Code already has a `deep-research` harness, a `research-lit` skill, and `market-intel` for
broad commercial research. Those fall short the moment a question is **"I'm about to buy X — find
me the best price"**: that's a specialized consumer workflow with its own data sources (Keepa,
Camelcamelcamel, 慢慢买), its own normalization (landed cost, currency, tax, shipping, coupons),
its own trust model (per-retailer marketplace seller tiers), and its own time-axis (Buy Box
rotates hourly).

`shopping-aggregator` is the **thin layer** that fills exactly that gap. It does **only three
things nothing else does**, and delegates everything else:

1. **Parse the buy intent** — product + region + budget + urgency + sensitivity → triage to 1–N
   of 13 shopping domains **and to the demand-side channel classes** (so a tool-less authorized
   retailer — e.g. Micro Center — stays visible instead of being structurally invisible).
2. **Detect + guide install** — check which specialized shopping MCP/extension/OSS tool is
   connected (via `claude mcp list`, not unreliable tool-name guessing), and if a key source is
   missing, hand you the exact install command — or open its **per-tool how-to doc**
   ([`reference/tools/`](skills/shopping-aggregator/reference/tools/index.md)) for install + auth
   + usage + gotchas.
3. **Quality guardrails** — snapshot timestamp, stock state, landed cost (not sticker),
   coupon-cart verification, retailer trust tiers, no silent degradation, disconfirmation
   mandate, surfaced disagreements, explicit gaps.

The actual live-price fan-out, history lookup, adversarial verification, and citation synthesis
are **delegated** to playwright MCP / BigGo MCP / Keepa MCP / `deep-research` / `market-intel`.
No reinvented engine.

---

## Install

```
/plugin install github:DaizeDong/shopping-aggregator
```

Or clone manually:

```bash
git clone https://github.com/DaizeDong/shopping-aggregator.git ~/.claude/plugins/shopping-aggregator
```

---

## 60-second tour

You say:

```
compare prices for Bose QuietComfort 45 across US retailers, refurb OK,
budget under $200, no rush — should I wait for a sale?
```

What runs:

1. **Parse intent** → product: Bose QC45 (refurb OK); region: US; budget $200; urgency: low.
2. **Triage** → maps to `amazon-us`, `ebay-walmart-target`, `browser-extensions` (coupon stack),
   `mobile-apps-aggregators` (Slickdeals "wait for sale" signal); picks depth budget standard.
3. **Detect** → runs `claude mcp list`; sees playwright connected, BigGo MCP not connected, no
   Keepa subscription; notes the gap.
4. **Guide install** (non-blocking) → "Camelcamelcamel free will give you Amazon history; if you
   shop a lot, Keepa MCP €49/mo gives deeper data. For now I'll use Camelcamelcamel + playwright
   per retailer."
5. **Delegate** → fans out subagents: playwright on amazon.com / amazon WHD / ebay.com / Walmart /
   Best Buy / Target; one subagent on Camelcamelcamel for history; one on Slickdeals for "is
   there a deal megathread"; one reverse-search subagent on counterfeit / refurb-fraud reports.
6. **Guardrails** → independent verifier re-fetches prices; landed cost computed with NJ sales
   tax + Prime ship vs flat ship; coupon-cart-test verifies "$10 off" code claim; surfaces
   disagreement between snapshot times if Buy Box rotated; reverse-search yields "BoseRefurb on
   eBay had several DOA reports last 90 days — recommend skipping."
7. **Report** → landed-cost ranked table, history note ("$X above 90-day low, drops historically
   around Black Friday by ~25%"), coupon-applied list (✓/⚠/✗), risks section, coverage gaps
   (Costco needs login → skipped), full source list.

### The source matrix (13 domains)

The knowledge asset. Each domain shard names the best tool, its **barrier route**, how to detect
it, and what to install.

| Domain | Top pick (barrier route) |
|---|---|
| [amazon-us](skills/shopping-aggregator/reference/domains/amazon-us.md) | playwright ④ + Camelcamelcamel ① free (+ Keepa ① paid for history) |
| [ebay-walmart-target](skills/shopping-aggregator/reference/domains/ebay-walmart-target.md) | eBay Browse API ① free + playwright ④ |
| [auction-resale](skills/shopping-aggregator/reference/domains/auction-resale.md) | eBay Sold SERP ④ free (`LH_Sold=1`) + StockX API ① (approved) / playwright ④ for GOAT/Whatnot/Poshmark/Mercari/Depop/ThredUp |
| [taobao-tmall](skills/shopping-aggregator/reference/domains/taobao-tmall.md) | 慢慢买 ④ + 购物党 ④ |
| [jd-pdd](skills/shopping-aggregator/reference/domains/jd-pdd.md) | 慢慢买 ④ + 京东价保 ① + 购物党 ④ |
| [browser-extensions](skills/shopping-aggregator/reference/domains/browser-extensions.md) | Capital One Shopping ① + Karma ① (⚠ AVOID Honey 2026) |
| [mobile-apps-aggregators](skills/shopping-aggregator/reference/domains/mobile-apps-aggregators.md) | Slickdeals + Flipp + 什么值得买 |
| [ai-shopping-assistants](skills/shopping-aggregator/reference/domains/ai-shopping-assistants.md) | Perplexity Shopping Pro |
| [claude-mcps](skills/shopping-aggregator/reference/domains/claude-mcps.md) | BigGo MCP ④ free + Apify price-intelligence ② paid |
| [oss-self-host](skills/shopping-aggregator/reference/domains/oss-self-host.md) | pricebuddy (US/EU) + PriceDive (CN, only fresh multi-platform) |
| [grocery-cpg](skills/shopping-aggregator/reference/domains/grocery-cpg.md) | Flipp ① circular + banner app ① loyalty (playwright ④ Instacart cart) — hyper-regional, pin ZIP+banner |
| [cross-border](skills/shopping-aggregator/reference/domains/cross-border.md) | Superbuy ④ + Stackry/MyUS ④ + YesStyle ④ (duty per `data/cross-border-duty.json`, CBP-primary) |
| [hotel-travel](skills/shopping-aggregator/reference/domains/hotel-travel.md) | Booking.com ④ (Genius often lowest public) → drive to Your-Details, then hand off payment; Google Hotels ④ discovery-only (date-lock); flights/cars/trains OUT of scope |

**Barrier routes:** ① official · ② resale · ③ self-host scrape · ④ **browser automation /
act-like-human** (first-class for live consumer prices).

Three install levels:
[`install-guide.md`](skills/shopping-aggregator/reference/install-guide.md) (L0 mechanics) →
[`pricing-install.md`](skills/shopping-aggregator/reference/volatile/pricing-install.md) (L1
per-domain) →
[`tools/<slug>.md`](skills/shopping-aggregator/reference/tools/index.md) (L2 per-tool).

---

## How to invoke

It auto-activates on phrases like `compare prices for X`, `cheapest place to buy`,
`is this a good deal`, `should I wait for a sale`, `比价`, `查历史价`, `全网最低价`,
`X 在哪里买便宜`, `凑单`. For broad market research it deliberately steps aside (use
[`market-intel`](https://github.com/DaizeDong/market-intel)); for single-fact lookups it steps
aside (just open the page).

To re-sweep the matrix manually (extensions lose affiliate networks, APIs die, OSS repos go
silent), trigger `刷新比价工具库` / `refresh the shopping-aggregator source matrix`. The
[refresh protocol](skills/shopping-aggregator/reference/refresh-protocol.md) re-sweeps each domain
(one subagent per domain → structured diff → incremental shard edits → `CHANGELOG.md` + version
bump). Default cadence **monthly**; weekly for browser-extensions and AI-shopping-assistants.

---

## Example output

A run ends in a landed-cost-ranked report. Quality guardrails (price-data-specific) that shape it —
hard rules applied during synthesis, full list in
[`SKILL.md`](skills/shopping-aggregator/SKILL.md):

- **Snapshot timestamp is MANDATORY** — every price entry carries `[fetched YYYY-MM-DD HH:MM TZ]`.
- **Stock state is part of the price** — OOS at $X ≠ in-stock at $X+5.
- **Landed cost, not sticker price** — ship + tax + coupon - cashback.
- **Coupon verification gate** — playwright cart test, not extension badge.
- **Retailer trust tiers** `seller_tier` L1 first-party → L5 unverifiable; don't rank L4/L5 as winners.
- **Evidence grade gates ranking first** — `evidence_grade` E1 (live PDP/API) · E2 (aggregator) · E3
  (snippet/cross-model lead); only an E1 read can be the ranked winner, a domain never upgrades a snippet.
- **Seller identity, not domain** — a retailer domain hosts 3P marketplace sellers; read `Sold by` /
  `Shipped by` before stamping first-party (L1).
- **Variant pinning** — `variant_key` (brand|model|color|bundle|condition); different variant = different
  SKU, never compared as one.
- **Coverage floor** — an in-scope channel class never checked is an explicit `coverage_gap`, not silent
  omission; deterministic invariants are CI-enforced by `tools/verify_matrix.py`.
- **No silent degradation** — when Keepa is unavailable, fall-back-to-playwright is flagged.
- **Cross-snapshot disagreement = re-fetch, don't average** — Buy Box rotates.
- **Disconfirmation mandate** — counterfeit / DOA / fraud reverse-search.
- **Failures become explicit gaps** — no hiding a missing retailer.
- **Affiliate disclosure tracking** — extension "savings" don't bias the ranking.

---

## Limitations

`shopping-aggregator` is a thin orchestration layer, not a price engine — it has structural limits
by design:

- **No reinvented fetch engine** — the live-price fan-out, history lookup, and adversarial
  verification are delegated to playwright / BigGo / Keepa / `deep-research` / `market-intel`. If
  none is connected, the skill guides install rather than fetching itself.
- **The matrix decays** — extensions lose affiliate networks (Honey/Rakuten Jan 2026), APIs die
  (PA-API 2026-05-15), OSS repos go silent. Freshness is maintained by the refresh protocol, not
  guaranteed at every moment.
- **Login-walled retailers** (e.g. Costco) are reported as explicit coverage gaps, not silently
  omitted, but are not auto-fetched.
- **Not a seller-side / arbitrage tool** — for FBA / wholesale / market research, use
  [`market-intel`](https://github.com/DaizeDong/market-intel).
- **No auto-purchase** — the skill produces a recommendation; you click buy.

Remaining roadmap gaps: demo conversations + comparison-vs-alternatives docs (v0.5 packaging),
heartbeat issue auto-close + discovery-state log (v0.3 loop-closing). See [ROADMAP.md](ROADMAP.md).

---

## Languages

English (`README.md`) · 中文 ([`README_CN.md`](README_CN.md))

---

## Roadmap · Contributing · License

See [ROADMAP.md](ROADMAP.md) · [CHANGELOG.md](CHANGELOG.md) · [LICENSE](LICENSE) (MIT).

Sister skill: [market-intel](https://github.com/DaizeDong/market-intel) — broad commercial
research / seller-side intel.
