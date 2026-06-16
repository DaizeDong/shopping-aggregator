# Changelog

## [0.1.2] — 2026-06-16

`install-guide.md` slimmed from 133 → 93 lines (30% smaller) by delegating L0 install
mechanics (prerequisites, MCP transport types, `claude mcp add` procedure, secret-handling
hygiene, Windows notes) to market-intel's authoritative install-guide via cross-references.

This eliminates the duplicated-content drift risk that surfaced in v0.1.1 (where the same
OS-clipboard command updates had to be made in two places). What remains in this file is
only what's specific to shopping-aggregator's tool mix: the four shopping-tool kinds
(MCPs, browser extensions, mobile apps, OSS self-host), user-side tool detection (extensions
the skill can't probe automatically), and the deviation list versus market-intel.

The companion-config-repo pattern reference now also points to market-intel as the canonical
spec; the same pattern works for a `shopping-aggregator-config/` companion if a user wants
to maintain Keepa subscription + browser-extension install state outside this matrix.

No tool/matrix changes.

## [0.1.1] — 2026-06-16

- **`reference/install-guide.md`** — secret-handling hygiene now lists clipboard commands for
  all three OSes (PowerShell `Get-Clipboard`, macOS `pbpaste`, Linux `xclip -o`/`wl-paste`)
  rather than implying PowerShell. The "Windows notes" section retains PowerShell appropriately
  since it's the Windows-specific section.
- **`reference/refresh-protocol.md`** — "push to DaizeDong/shopping-aggregator" replaced with
  "push to whichever Git remote this skill repo lives at."

No tool/matrix changes. Forkability cleanup only.

## [0.1.0] — 2026-06-15

Initial public release. Hand-curated matrix derived from a 5-subagent shopping landscape survey
done 2026-06-15 (US + CN consumer-shopping coverage), paired with patterns inherited unchanged
from `DaizeDong/market-intel` (philosophy, install-guide L0 mechanics, progressive-loading
discipline, refresh-protocol bones, plugin layout).

### Why this skill exists

The 2026-06-15 survey surfaced that **no native SKILL.md exists for consumer shopping price
comparison** — every "skill bundle" in the wider ecosystem (coreyhaines31/marketingskills 32.6k★,
alirezarezvani/claude-skills 338-skill bundle, ComposioHQ/awesome-claude-skills 63.8k★) targets
marketing / SEO / seller-side intel. Consumer price compare was a gap. This skill fills it as a
sister to market-intel — market-intel handles broad commercial research, shopping-aggregator
handles the consumer buy decision.

### Initial content

**9 domain shards:**
- amazon-us
- ebay-walmart-target
- taobao-tmall
- jd-pdd
- browser-extensions (incl. ⚠ Honey 2026 status: avoid)
- mobile-apps-aggregators
- ai-shopping-assistants
- claude-mcps
- oss-self-host

**17 tool docs** (per-tool how-to: install + auth + usage + gotchas):
- Amazon history: keepa, camelcamelcamel
- Multi-platform MCPs: biggo-mcp, apify-price-intelligence, taobao-mcp, oxylabs
- US retailer API: ebay-api
- CN tools: manmanbuy, gwdang, smzdm
- US browser extensions: capital-one-shopping, karma-extension, coupert, ⚠ honey
- US deal/aggregator apps: slickdeals, shopsavvy, flipp
- AI shopping: perplexity-shopping
- OSS self-host: pricebuddy, priceghost, pricedive, discount-bandit

**Support docs:**
- `SKILL.md` — orchestration core with 7-step workflow (parse intent → triage → detect → install
  guide → delegate → normalize landed cost → record live-run)
- `sources-index.md` — thin domain index
- `install-guide.md` — L0 install mechanics + secret hygiene + Windows notes
- `report-template.md` — landed-cost ranking + history note + risks + gaps template
- `refresh-protocol.md` — monthly cadence; weekly for browser-extensions + AI assistants
- `volatile/pricing-install.md` — per-domain install commands + prices, time-stamped
- `tools/index.md` + `tools/registry.json` — three-way consistency-checkable tool catalog

### Shopping-specific guardrails (in addition to market-intel's general ones)

1. Snapshot timestamp is mandatory on every price entry.
2. Stock state is part of the price.
3. Landed cost (ship + tax + coupon - cashback), not sticker.
4. Coupon verification via playwright cart test, not extension badge.
5. Retailer trust tiers L1 first-party → L5 unverifiable.
6. No silent degradation when a primary source is missing.
7. Cross-snapshot disagreement → re-fetch, don't average (Buy Box rotation).
8. Disconfirmation mandate (counterfeit / DOA / fraud reverse-search).
9. Failures become explicit gaps.
10. Affiliate disclosure tracking — extension "savings" don't bias the ranking.

### Notable inclusions

- **Honey 2026 status proactively surfaced** — MDL active discovery (Jun 2026), Rakuten/Impact/Awin
  affiliate-network terminations (Jan 2026), recommendation: uninstall.
- **Amazon PA-API 5.0 marked dead** (✗ retired 2026-05-15, replaced by Creators API).
- **PriceDive** (53★, Python) called out as the **only fresh OSS for CN multi-platform**
  (Taobao/JD/PDD) — non-obvious without the survey.
- **pricebuddy** (962★) + **PriceGhost** (641★) called out as the modern OSS picks for Western
  markets, **above** older Discount-Bandit recommendation in market-intel's
  ecommerce-arbitrage shard.

### Cross-skill integration

- `DaizeDong/market-intel` ready-skills shard adds a row pointing here.
- market-intel sources-index adds a `consumer-price-compare` domain row pointing to this repo.
- A new market-intel `domains/consumer-price-compare.md` shard documents the boundary.

### Known limitations of v0.1.0

- No anti-regression CI gate yet (heartbeat only). Planned v0.2 — port market-intel's
  `verify_matrix.py`.
- No CONSTITUTION.md hard-constraint injection yet.
- 17 tool docs (vs market-intel's ~150) — minimum viable, expansion in v0.2.
- No per-state US sales tax tables yet (NJ assumed in default examples).

See [ROADMAP.md](ROADMAP.md) for v0.2 plan.
