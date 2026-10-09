# Roadmap

Current: **v0.10.0**

The current release supports per-person configuration, verified shopping comparisons
and retail purchases on explicit per-action instruction. Current workflow details
are in [SKILL.md](skills/shopping-aggregator/SKILL.md); dated release facts remain
in [CHANGELOG.md](CHANGELOG.md).

## Current configuration and storage contracts

Per-person cache and selected evaluation retention follow the same per-kind rules
as the companion root. [CONFIG.md](CONFIG.md#storage-lifecycle) owns these rules.
Synthetic checks establish declared local behavior; live capability and protected-data
retirement require separate evidence.

## Shipped

### v0.10.0, per-person configuration

- [x] **`CONFIG.md` defines a config root per person** (profile, registry, private reference tables, both ledgers, `people/<id>/`); real roots live only in the PRIVATE companion, and the schema refuses identity, contact and payment data.
- [x] **`scripts/init_config.py`, `scripts/verify_config.py`, `scripts/ledger.py`**, with `tools/config_schema.py` as the one implementation every caller shares; switching people is one selection (`SHOPPING_AGGREGATOR_CONFIG`, or `--config-dir` per command) that moves profile and ledgers together.
- [x] **Purchases are recorded** (`data/purchases.jsonl`) under the selected root's profile id, and the observation ledger has a validated writer.

### v0.6.0, the login handoff and the reading-a-result-page guardrails

- [x] **Access state is a first-class property of a channel** (S1 anonymous / S2 session-gated /
      S3 structural), with `reference/login-handoff.md` plus SKILL.md steps 3b and 5b. An S2
      channel is never a coverage gap until the operator has been asked, in one batched ask.
- [x] **The agent never authenticates** (CONSTITUTION V.4), and post-login access is read-only and
      scoped to product content, never account or order or payment views.
- [x] **Control query (guardrail 11) and typed gap reasons (guardrail 9c)**, so a gated search that
      renders its shell and reports zero results can no longer be recorded as "nobody sells this".
- [x] **Search depth is declared (guardrail 12)**, pages judged by new ids rather than by returned
      count, after a URL page param was observed being silently ignored.
- [x] Cross-border oversized-goods rules (volumetric weight, box dimensions, sea freight) and the
      rule that tariff list membership is verified against the primary schedule.

### v0.5.0, private runtime data boundary

- [x] **Every path declared TOOL / FIXTURE / DATA** (`.dataclass.json`); real-run output resolves
      from a private companion dir via the resolver (now `guards/tools/datadir.py`), with no in-repo fallback.
- [x] **`guards/tools/data_boundary.py` wired into both hooks and CI** as the primary control, with
      `pii_guard` demoted to backstop; fixtures are generated, so a real record cannot pass.
- [x] `reference/source-reliability.md`, the generalizable half of the removed observations,
      distilled with product, price and region stripped.

### v0.4.0, self-evolve: enforcement + landed-cost data + domain expansion

- [x] **Tax / shipping / duty / FX data tables** (`reference/data/`), `us-sales-tax.json`,
      `cross-border-duty.json`, `shipping-baselines.json`, `fx-source-of-record.md`, each on the
      `{schema_version,last_verified,rows[{source_url,verified_date,...}]}` envelope, every figure
      source-cited (CBP / Federal Register / EU Council / USITC HTS / GACC primary). Landed-cost
      compute no longer has to say "(state rate assumed)." **Closes the v0.2 tax/duty + currency-spec
      bullets.**
- [x] **3 new domain shards (9 → 12)**, `cross-border` (US↔CN/EU duties + forwarders; duty figures
      source-of-record `reference/data/cross-border-duty.json`, CBP-primary), `grocery-cpg`
      (Flipp circular + banner-app loyalty + Instacart cart), `auction-resale` (eBay Sold SERP +
      StockX + GOAT/Whatnot/Poshmark/Mercari/Depop/ThredUp). All wired into sources-index + both
      README matrices.
- [x] **~32 tool docs (was 22)**, added Bright Data, DealNews, InvisibleHand, RetailMeNot,
      Cently, 京东价保 (jd-price-protection), Slickdeals, reddit-deals, ScraperAPI, AliExpress,
      Xiaohongshu, and more. **Closes the v0.2 "more tool docs (30-40)" bullet.**
- [x] **market-intel RICHER judgement checks ported** into `tools/verify_matrix.py`, REPO / STAR /
      GHACTIVE / DOCCOVER / STALE / COVER / CHURN / DELETE / CONST / METH, plus a new **DATA**
      envelope check and a **NOHARDCODE** provenance lint. `--no-net` skips the network gates for
      offline CI. **Closes the only remaining v0.2 gate gap** (the original 6 deterministic checks
      shipped in 0.3.0).
- [x] **Refresh automation**, `tools/refresh_priority.py` ranks the private `live-runs.jsonl`
      sources by weighted problem events (`user_correction` 100 / `dead` 10 / `price_mismatch` 5 /
      `coverage_gap` 3) for the next sweep; one shared definition used by protocol + gate.
      **Closes the v0.3 "live-runs → refresh prioritization" bullet.**
- [x] **Scenario-eval harness**, `tools/scenario_eval.py` for fixture-driven evaluation of the
      orchestration output.
- [x] **Data-table staleness hook** in `refresh-protocol.md`, every sweep MUST re-confirm the four
      data tables against their cited primary source; de-minimis / cross-border duty = mandatory
      CBP re-check on EVERY sweep (highest-volatility, highest-blast-radius figure).

### Earlier

- [x] **Anti-regression gate (`tools/verify_matrix.py`)**, base 6 deterministic checks shipped in
      0.3.0, CI-enforced via `.github/workflows/gate.yml` (THREEWAY · FRESH · TEMPLATE · VERSION ·
      RENAME · LIVERUNS).
- [x] **CONSTITUTION.md**, shipped in 0.2.0. Hard constraints injected at refresh-time so the
      editing subagents receive the invariants; deterministic checks enforce the clauses they cover.
- [x] **Domain expansion (cross-border / grocery-cpg / auction-resale)**, shard bodies authored
      in the v0.4 era, wired into all discovery surfaces in 0.4.0.

## Next: remaining feedback work

- [ ] **Heartbeat issue auto-close**, when a refresh PR lands for the month, close the
      heartbeat-triggered "missed refresh" issue automatically.
- [ ] **Discovery state log**, equivalent to market-intel's `discovery-state.md`, track
      candidates surfaced by Discovery sweeps that didn't make it into shards yet (with FOLD /
      NEW-DOMAIN / NEW-SKILL verdicts + reasons).

## Planned: public packaging

- [ ] **Demo conversations** in `docs/`, annotated end-to-end transcripts (US buy / CN buy /
      cross-border buy / "wait for sale" projection) that show what good output looks like.
- [ ] **Comparison vs alternatives** doc, when a user is choosing between this and BigGo MCP
      directly, or this vs Perplexity Shopping, or this vs market-intel's ecommerce-arbitrage,
      explicit positioning.
- [ ] **Skill-installation troubleshooting**, common gotchas with `/plugin install` on
      Windows, MCP transport flakes, etc.

## Future proposals

- [ ] **Live API integration with retailer Open Banking** for actual purchase confirmation
      (only if Claude Code's tool-use story supports a "purchase intent → execute" loop with
      consent flow, currently it doesn't).
- [ ] **Cross-skill orchestration**, automatic invocation of `market-intel` when the buy intent
      crosses into "should I switch product categories" or "should I buy a different brand."
- [ ] **Snapshot dataset** for the open-source community, a quarterly anonymized snapshot of
      "what tools we recommended for what queries" so others can audit the matrix performance.

---

## Not on the roadmap (rejected, with reasons)

- ❌ **Build a full shopping orchestrator like Perplexity Shopping**, out of scope per P5 (thin
  layer doctrine). If the user wants that, recommend Perplexity Pro.
- ❌ **Unattended or speculative auto-purchase**, out of scope per autonomy / consent. Buying on the buyer's explicit per-action instruction is supported since v0.9.0, retail only, through `reference/purchase-execution.md`.
- ❌ **In-skill cashback redemption**, not the skill's role; user manages their own Capital
  One Shopping / Karma / Rakuten accounts.
- ❌ **Build a custom MCP server**, defer to BigGo MCP / Apify / Keepa. P5 again.
- ❌ **Auto-monitor + alert mode inside the skill**, out of scope per P5; this is one-shot,
  use `/schedule` or `/loop` wrapper, see SKILL.md "Recurring / monitoring use" section.
