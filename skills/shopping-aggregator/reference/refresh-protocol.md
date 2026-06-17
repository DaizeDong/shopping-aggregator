# Refresh protocol — keep the shopping source matrix current

This skill's value is a curated shopping-source matrix. Tools, prices, browser-extension
affiliate-network status, and OSS repo activity in the consumer shopping space move fast (Honey
went from default-good to avoid in under 12 months; Rakuten terminated Honey from its merchant
network on 2026-01-12; OSS repos can go silent in 6 months). Re-run this protocol periodically
to keep `domains/`, `volatile/pricing-install.md`, and `sources-index.md` accurate.

> This protocol is a **slim adaptation of market-intel's refresh-protocol**. Where the protocols
> overlap (the Discovery phase mechanics, the gate doctrine, the quality guardrails), this file
> defers to market-intel and only documents the shopping-specific differences.

## Cadence

- **Default: monthly** (consumer shopping moves on monthly promo cycle; browser-extension network
  status can flip overnight as seen with Honey/Rakuten Jan 2026).
- **Faster (weekly) for volatile domains**: `browser-extensions` (affiliate-network drama),
  `ai-shopping-assistants` (rapid feature changes 2025-2026).
- **Slower (quarterly) for stable domains**: `claude-mcps` (small project ecosystem, low churn
  by volume), `oss-self-host` (repos either active or stale, easy to spot).
- **Opportunistic**: whenever you hit a dead tool / changed price in a real run, fix that shard
  immediately + append to `metrics/live-runs.jsonl`.

## Procedure (full monthly sweep)

The protocol has two phases — **Discovery** (find new) + **Verify & Diff** (confirm/retire old).
The Discovery phase mechanics are inherited from market-intel's protocol (see
`market-intel/skills/market-intel/reference/refresh-protocol.md` Discovery phase section, D1-D5).
Don't duplicate those mechanics here — read them there if you're running a deep sweep.

### Shopping-specific Discovery sources

Beyond the generic MCP-registry + GitHub + community surfaces in market-intel, also sweep:

1. **Chrome Web Store / Edge Add-ons / Firefox AMO** — search "price compare", "coupon",
   "cashback", "比价"; sort by **Recently Updated**. New extensions that surface in trending
   coupon-space within 30 days of launch are usually low-quality astroturf — manual review
   required. Established players (>1M users + >1yr history) only.
2. **App Store / Google Play** — search "price compare", "deal finder", "barcode scan",
   "比价", "购物党". Note iOS app updates around major US shopping events (Black Friday, Prime
   Day) — feature releases often cluster there.
3. **PayPal / Rakuten / Capital One press releases** — monitor for affiliate-network changes.
   The Honey / Rakuten termination Jan 2026 was announced via PPC.land coverage of Rakuten's
   merchant communication, not a press release. So *also* monitor ad-tech industry press
   (PPC.land, Search Engine Journal, AdExchanger, Marketing Brew).
4. **Reddit r/personalfinance / r/buildapcsales / r/frugalmalefashion** — community sentiment
   shifts (e.g. "uninstalling Honey megathread") often precede mainstream coverage by weeks.
5. **GitHub `awesome-claude-skills` and shopping-relevant lists** — same as market-intel; also
   search `topic:claude-skill shopping`, `topic:mcp-server shopping`, `topic:mcp-server ecommerce`.
6. **慢慢买 / 什么值得买 / 购物党 status pages and microblog accounts** — CN tools often go
   silent without formal announcement; watch their 微博/微信 official accounts.
7. **Channel-completeness audit (coverage-driven, NOT just tool-driven).** Surfaces 1–6 hunt for new
   TOOLS — they structurally cannot surface a retailer that has no tool (Micro Center was invisible
   for exactly this reason). So ALSO audit `reference/channel-classes.md` against reality: for each
   major product category + region, list the authorized retailers a knowledgeable buyer would check,
   and flag any channel CLASS or canonical retailer missing from the shards. A missing channel is a
   coverage gap even when no tool exists for it. `coverage_gap` events in `metrics/live-runs.jsonl`
   (emitted by real runs per SKILL.md guardrail #9 / Step 7) feed this audit directly.

### Apply the same quality guardrails

- Verify each claimed tool exists (gh-api last-commit, official-site reachability).
- Verify each price against the official site — do not trust a subagent's recalled pricing.
- Verify each browser extension's **current affiliate network membership**. (Honey lost Rakuten,
  Impact, Awin in early 2026 — a 2025 doc would still call Honey "covers everything." It doesn't.)
- Verify each mobile app's last update date and major-version. Stale > 12 months + low review
  velocity = candidate for `⚠ aging` flag.
- For OSS repos, check both last commit AND issue tracker (lots of unresolved breakage issues =
  effectively abandoned even if last commit recent).

### Shopping-specific shard updates

For each domain, update changed rows in `domains/<domain>.md`; move/refresh price+install lines
in `volatile/pricing-install.md`; bump that section's `last_verified: YYYY-MM`. Update
`sources-index.md` only if a domain's top pick changed.

Special attention to:
- **Honey-equivalents**: if any extension undergoes a Honey-like trust event, add a `⚠ AVOID`
  row in `browser-extensions.md` and `tools/<slug>.md` immediately. Don't silently delete (that
  loses the institutional memory).
- **Affiliate network shifts**: if Rakuten/Impact/Awin/CJ make a major termination of an
  extension, update the extension's tool doc to reflect coverage shrinkage.
- **PA-API-style API deprecations**: Amazon PA-API 5.0 dies 2026-05-15. When an API dies, mark
  the tool doc `✗ DEAD <date>` (never silent-delete), update its row in the domain shard with
  the replacement (Creators API), and CHANGELOG the change.

### Sync L2 per-tool docs + tool registry

For every tool ADDed or REPLACEd:
- Create/update `reference/tools/<slug>.md` (per-tool install + auth + usage + 踩坑, each fact
  verified against official site or gh-api).
- Add its row to `reference/tools/index.md`.
- Update `reference/tools/registry.json` with the {slug, name, kind, repo, domain, top_pick}
  entry. **The registry is regenerated**, not hand-edited, when the index drifts (see
  market-intel's verify_matrix.py for the regen script if importing the gate later).

For every tool deleted/tombstoned:
- Mark its doc `⚠ Avoid (dead/superseded)` (never silent-delete).
- Drop its index row.
- Update registry.

### Record the diff

In `CHANGELOG.md` at the repo root: date + per-domain added/removed/changed. Bump
`.claude-plugin/plugin.json` `version`.

### Commit + push

To whichever Git remote this skill repo lives at. The heartbeat workflow checks for monthly
activity — see `.github/workflows/heartbeat.yml`.

## What's NOT in this protocol (defer to market-intel)

- Anti-regression gate (`verify_matrix.py`) — market-intel's gate runs in CI and bans matrix
  regressions. This skill **does not yet** have its own gate (planned in ROADMAP). Until then,
  refresh discipline is voluntary — gate-shaped enforcement is on the ROADMAP for v0.2.
- CONSTITUTION-injection-as-hard-constraints — the skill now ships its own `CONSTITUTION.md` at the
  repo root (I.1–VII). A refresh sweep updates the matrix and may NOT relax the constitution (see
  CONSTITUTION VII).
- Horizon-scan for new domains — read market-intel's protocol section "Horizon scan."

## Feedback loop

The skill writes one line per source touched to `metrics/live-runs.jsonl` during real runs (see
SKILL.md Step 7). The refresh-protocol **must** read this file as a prioritization input:

```bash
jq -r '.domain + "\t" + .source + "\t" + .outcome' metrics/live-runs.jsonl | sort | uniq -c | sort -rn
```

Sources/channels with the most `dead` / `price_mismatch` / `coverage_gap` events get top priority in
the next sweep. A `coverage_gap` line means a real run hit an in-scope channel it could not take to E1
depth — this is the path by which a **missing CHANNEL** (not just a dead tool) reaches the refresh
loop; route it to the channel-completeness audit above. The highest-weight signal is the
`user_correction` **field** (a JSON key present on any line — NOT an `outcome` value) — the user
manually fixed something we were wrong about.
