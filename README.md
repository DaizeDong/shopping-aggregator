# shopping-aggregator

Compare consumer purchases across 14 shopping domains using verified checkout costs,
with source collection delegated to an existing research workflow.

[![Claude Code Skill](https://img.shields.io/badge/Claude%20Code-Skill-orange?style=flat)](https://docs.anthropic.com/en/docs/claude-code)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Source Matrix](https://img.shields.io/badge/Source%20Matrix-14%20domains-green?style=flat)](skills/shopping-aggregator/reference/sources-index.md)
[![Data tables](https://img.shields.io/badge/Data%20tables-tax%20%7C%20duty%20%7C%20FX%20%7C%20shipping-green?style=flat)](skills/shopping-aggregator/reference/data/README.md)
[![Languages](https://img.shields.io/badge/Languages-EN%20%2F%20CN-blue?style=flat)](README_CN.md)
[![Roadmap](https://img.shields.io/badge/Roadmap-v0.10.0-purple?style=flat)](ROADMAP.md)

[English](README.md) | [中文版](README_CN.md)

---

## Design philosophy

Shopping comparisons need a consistent product variant, current stock, seller identity
and the full checkout cost. Shipping, tax, duty and verified coupons can change the
ranking; delayed cashback remains conditional and is shown separately. Each price
needs a snapshot timestamp because offers such as Amazon's Buy Box change frequently.

Coupon claims require a cart test or an unverified label. The Honey case and the
Rakuten/Impact/Awin terminations in January 2026 are part of the source trust review;
Honey is not a default recommendation. Stronger evidence requirements can leave an
offer unranked or coverage incomplete. The report retains those limits.

See [PHILOSOPHY.md](PHILOSOPHY.md) for the design principles and their shopping applications.

### Sister skill, when to use which

`shopping-aggregator` is the **consumer-purchase specialization** of the broader market-research
toolkit at [`market-intel`](https://github.com/DaizeDong/market-intel).

| Your question | Skill |
|---|---|
| "Compare prices for X across retailers, where's cheapest" | **shopping-aggregator (here)** |
| "Is this a good deal, should I wait, what's the historical low" | **shopping-aggregator** |
| "Research the X category, who are the players, what's growing" | [**market-intel**](https://github.com/DaizeDong/market-intel) |
| "Find arbitrage / FBA / wholesale opportunities (seller side)" | [**market-intel**](https://github.com/DaizeDong/market-intel) → `ecommerce-arbitrage` shard |
| "X/Twitter sentiment / competitor SEO / lead generation" | [**market-intel**](https://github.com/DaizeDong/market-intel) |

Both skills can be installed; each routes requests within its documented scope.

---

## Scope

The skill handles consumer buying decisions with shopping-specific sources such as
Keepa, Camelcamelcamel and 慢慢买, cost normalization and marketplace seller checks:

1. **Parse intent:** product, region, budget, urgency and sensitivity determine the
   relevant shopping domains and demand-side channel classes. A retailer without a
   dedicated tool, such as Micro Center, still belongs in the coverage plan.
2. **Select sources and setup:** discover tools in the active host and perform a
   functional read. Use [per-tool documentation](skills/shopping-aggregator/reference/tools/index.md)
   for missing MCP, extension or open-source setup. `claude mcp list` is a Claude
   installation diagnostic; a connected indicator alone does not prove a usable source.
3. **Apply evidence requirements:** verify price, stock, variant, seller, timestamp and
   discounts, then report conflicts, risks and missing channels.

Live-price collection, history lookup and verification use available playwright MCP,
BigGo MCP, Keepa MCP, `deep-research` or `market-intel` capabilities.

---

## Install

```
/plugin install github:DaizeDong/shopping-aggregator
```

Or clone manually:

```bash
git clone --recurse-submodules https://github.com/DaizeDong/shopping-aggregator.git ~/.claude/plugins/shopping-aggregator
```

The command-line tools require the bundled Guards resolver. If an existing clone or
plugin installation is missing `guards/tools/datadir.py`, run
`git submodule update --init --recursive` from the plugin directory. Then check the
installation with `python tools/refresh_priority.py --help` and
`python tools/scenario_eval.py`; the latter prints an offline evaluation plan.

---

## Config

Each buyer has a **config root** in a PRIVATE versioned companion repository. It holds
market, destination, memberships, store credit, checkout permissions and purchase
defaults alongside that buyer’s observation and purchase ledgers. [CONFIG.md](CONFIG.md)
defines the supported files and fields; buyer state must not be duplicated in agent
memory or script defaults.

```bash
python scripts/init_config.py        # find the companion, or create ~/.shopping-aggregator-config
python scripts/verify_config.py      # doctor: prints the selected root; NOT READY until the profile is filled
```

Discovery order: `--config-dir` (or `--out` for init), then `$SHOPPING_AGGREGATOR_CONFIG` (alias `$SHOPPING_AGGREGATOR_CONFIG_DIR`), then the pinned `guards/tools/datadir.py` order: `$SHOPPING_AGGREGATOR_DATA_DIR`, a sibling `shopping-aggregator-config/` next to this repository, `~/.shopping-aggregator-config`, then `~/.shopping-aggregator-data`. A leftover `SHOPPING_AGGREGATOR_DATA_DIR` must equal the selected root's `data/`, or the doctor fails. The root must sit in a PRIVATE versioned repository before it holds real values.

To switch to another person, point `SHOPPING_AGGREGATOR_CONFIG` at their root, or keep them under `<companion>/people/<id>/` and select that directory; their profile, purchases and observations switch together, and every report names the `profile_id` it used. `--config-dir` selects a root for one `scripts/` command only, while the `tools/` commands follow only the environment variable. Without any config the skill still compares prices, asking for the same facts in Step 1, but it never submits an order itself: the final click goes to you.

Per-person storage follows [CONFIG.md’s lifecycle rules](CONFIG.md#storage-lifecycle):
observations and purchases remain core, cache is rebuildable with a seven-day policy,
and evaluation runs retain selected evidence. Unknown per-person files have no owner;
[config.contract.json](config.contract.json) declares the native lifecycle adapter.

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
3. **Detect** → discovers sources in the active host, then checks the selected read operation,
   authentication and usable response content. A connected listing alone does not establish
   readiness; unavailable BigGo access or a missing Keepa subscription remains a coverage gap.
4. **Guide install** (non-blocking) → "Camelcamelcamel free will give you Amazon history; if you
   shop a lot, Keepa MCP €49/mo gives deeper data. For now I'll use Camelcamelcamel + playwright
   per retailer."
5. **Delegate** → fans out subagents: playwright on amazon.com / amazon WHD / ebay.com / Walmart /
   Best Buy / Target; one subagent on Camelcamelcamel for history; one on Slickdeals for "is
   there a deal megathread"; one reverse-search subagent on counterfeit / refurb-fraud reports.
6. **Guardrails** → independent verifier re-fetches prices; landed cost computed with the sales tax
   of the profile's ship-to state + member free shipping vs flat ship; coupon-cart-test verifies "$10 off" code claim; surfaces
   disagreement between snapshot times if Buy Box rotated; reverse-search yields "BoseRefurb on
   eBay had several DOA reports last 90 days, recommend skipping."
7. **Report** → landed-cost ranked table, history note ("$X above 90-day low, drops historically
   around Black Friday by ~25%"), coupon-applied list (✓/⚠/✗), risks section, coverage gaps
   (Costco: offer an S2 login handoff; record a typed gap if declined or unattended), full source list.

### The source matrix (14 domains)

Each domain shard records recommended sources, barrier routes, detection and setup.

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
| [grocery-cpg](skills/shopping-aggregator/reference/domains/grocery-cpg.md) | Flipp ① circular + banner app ① loyalty (playwright ④ Instacart cart), hyper-regional, pin ZIP+banner |
| [cross-border](skills/shopping-aggregator/reference/domains/cross-border.md) | Superbuy ④ + Stackry/MyUS ④ + YesStyle ④ (duty per `data/cross-border-duty.json`, CBP-primary) |
| [hotel-travel](skills/shopping-aggregator/reference/domains/hotel-travel.md) | Selected lodging totals, taxes and cancellation terms; hand off before personal/payment data |
| [air-travel](skills/shopping-aggregator/reference/domains/air-travel.md) | Flight discovery, card-scoped prices, selected fare/baggage/refund terms and independently verified total comparison; unknown terms cannot support a lowest-total claim |

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

A run ends in a landed-cost-ranked report. Quality guardrails (price-data-specific) that shape it:
hard rules applied during synthesis, full list in
[`SKILL.md`](skills/shopping-aggregator/SKILL.md):

- **Snapshot timestamp is MANDATORY**, every price entry carries `[fetched YYYY-MM-DD HH:MM TZ]`.
- **Stock state is part of the price**, OOS at $X ≠ in-stock at $X+5.
- **Rank by checkout cost:** sticker price + shipping + tax + duty - verified checkout coupon discounts. Delayed cashback stays a separate conditional note and is never deducted from the ranked price.
- **Coupon verification gate**, playwright cart test, not extension badge.
- **Retailer trust tiers** `seller_tier` L1 first-party → L5 unverifiable; don't rank L4/L5 as winners.
- **Evidence grade gates ranking first**, `evidence_grade` E1 (live PDP/API) · E2 (aggregator) · E3
  (snippet/cross-model lead); only an E1 read can be the ranked winner, a domain never upgrades a snippet.
- **Seller identity, not domain**, a retailer domain hosts 3P marketplace sellers; read `Sold by` /
  `Shipped by` before stamping first-party (L1).
- **Variant pinning**, `variant_key` (brand|model|color|bundle|condition); different variant = different
  SKU, never compared as one.
- **Coverage floor**, an in-scope channel class never checked is an explicit `coverage_gap`, not silent
  omission; deterministic invariants are CI-enforced by `tools/verify_matrix.py`.
- **No silent degradation**, when Keepa is unavailable, fall-back-to-playwright is flagged.
- **Cross-snapshot disagreement = re-fetch, don't average**, Buy Box rotates.
- **Disconfirmation mandate**, counterfeit / DOA / fraud reverse-search.
- **Failures become explicit gaps**, no hiding a missing retailer.
- **Affiliate disclosure tracking**, extension "savings" don't bias the ranking.

---

## Limitations

- **Source availability:** collection depends on the capabilities listed under Scope.
  If none is connected, the skill provides setup guidance.
- **Catalog freshness:** extensions lose affiliate networks (Honey/Rakuten Jan 2026), APIs
  close (PA-API 2026-05-15), and repositories stop updating. The refresh protocol requires
  re-verification; catalog presence does not establish current availability.
- **Session-gated access:** finish anonymous S1 work, then batch S2 channels into one
  login handoff. Open the login page, pause and resume only after user confirmation.
  The user handles authentication; the agent never enters credentials. Re-run the control
  query after login before trusting content. Declined or unattended handoffs produce
  typed `session-gated-*` gaps. See [login-handoff.md](skills/shopping-aggregator/reference/login-handoff.md).

- **Seller-side scope:** for FBA, wholesale or market research, use
  [`market-intel`](https://github.com/DaizeDong/market-intel).
- **Purchase authorization:** retail orders only, on an explicit per-action instruction, at the full discount stack (guardrail #16), verified line by line on the final page before a single click, and only at retailers where the selected profile lets the agent check out. Lodging and flights stay hand-off. Without that instruction or that permission it produces a recommendation and you click buy.

Remaining roadmap gaps: demo conversations + comparison-vs-alternatives docs (v0.5 packaging),
heartbeat issue auto-close + discovery-state log (v0.3 loop-closing). See [ROADMAP.md](ROADMAP.md).

---

## Languages

English (`README.md`) · 中文 ([`README_CN.md`](README_CN.md))

---

## Roadmap · Contributing · License

See [ROADMAP.md](ROADMAP.md) · [CHANGELOG.md](CHANGELOG.md) · [LICENSE](LICENSE) (MIT).

Sister skill: [market-intel](https://github.com/DaizeDong/market-intel), broad commercial
research / seller-side intel.
