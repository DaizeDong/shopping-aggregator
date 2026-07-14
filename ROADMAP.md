# Roadmap

Current: **v0.4.0**

`shopping-aggregator` is at v0.4.0. The v0.4.0 self-evolve round closed the entire v0.2 enforcement
gap and the v0.4 domain expansion in one batch (see **Shipped** below), on top of the v0.2.0
structural/framework batch (CONSTITUTION, demand-side channel-class primitive, the evidence-unit
schema `variant_key` / `seller_tier` / `evidence_grade`, seller-identity gate, codex-crossval) and
the v0.1.0 base (orchestration core, philosophy inherited from market-intel). This file tracks what's
next; completed work is in **Shipped**.

## Shipped

### v0.4.0 — self-evolve: enforcement + landed-cost data + domain expansion

- [x] **Tax / shipping / duty / FX data tables** (`reference/data/`) — `us-sales-tax.json`,
      `cross-border-duty.json`, `shipping-baselines.json`, `fx-source-of-record.md`, each on the
      `{schema_version,last_verified,rows[{source_url,verified_date,...}]}` envelope, every figure
      source-cited (CBP / Federal Register / EU Council / USITC HTS / GACC primary). Landed-cost
      compute no longer has to say "(NJ rate assumed)." **Closes the v0.2 tax/duty + currency-spec
      bullets.**
- [x] **3 new domain shards (9 → 12)** — `cross-border` (US↔CN/EU duties + forwarders; duty figures
      source-of-record `reference/data/cross-border-duty.json`, CBP-primary), `grocery-cpg`
      (Flipp circular + banner-app loyalty + Instacart cart), `auction-resale` (eBay Sold SERP +
      StockX + GOAT/Whatnot/Poshmark/Mercari/Depop/ThredUp). All wired into sources-index + both
      README matrices.
- [x] **~32 tool docs (was 22)** — added Bright Data, DealNews, InvisibleHand, RetailMeNot,
      Cently, 京东价保 (jd-price-protection), Slickdeals, reddit-deals, ScraperAPI, AliExpress,
      Xiaohongshu, and more. **Closes the v0.2 "more tool docs (30-40)" bullet.**
- [x] **market-intel RICHER judgement checks ported** into `tools/verify_matrix.py` — REPO / STAR /
      GHACTIVE / DOCCOVER / STALE / COVER / CHURN / DELETE / CONST / METH, plus a new **DATA**
      envelope check and a **NOHARDCODE** provenance lint. `--no-net` skips the network gates for
      offline CI. **Closes the only remaining v0.2 gate gap** (the original 6 deterministic checks
      shipped in 0.3.0).
- [x] **Refresh automation** — `tools/refresh_priority.py` ranks the private `live-runs.jsonl`
      sources by weighted problem events (`user_correction` 100 / `dead` 10 / `price_mismatch` 5 /
      `coverage_gap` 3) for the next sweep; one shared definition used by protocol + gate.
      **Closes the v0.3 "live-runs → refresh prioritization" bullet.**
- [x] **Scenario-eval harness** — `tools/scenario_eval.py` for fixture-driven evaluation of the
      orchestration output.
- [x] **Data-table staleness hook** in `refresh-protocol.md` — every sweep MUST re-confirm the four
      data tables against their cited primary source; de-minimis / cross-border duty = mandatory
      CBP re-check on EVERY sweep (highest-volatility, highest-blast-radius figure).

### Earlier

- [x] **Anti-regression gate (`tools/verify_matrix.py`)** — base 6 deterministic checks shipped in
      0.3.0, CI-enforced via `.github/workflows/gate.yml` (THREEWAY · FRESH · TEMPLATE · VERSION ·
      RENAME · LIVERUNS).
- [x] **CONSTITUTION.md** — shipped in 0.2.0. Hard constraints injected at refresh-time so the
      editing subagents physically can't propose changes that violate the philosophy.
- [x] **Domain expansion (cross-border / grocery-cpg / auction-resale)** — shard bodies authored
      in the v0.4 era, wired into all discovery surfaces in 0.4.0.

## v0.3 — Real-run feedback (remaining)

- [ ] **Heartbeat issue auto-close** — when a refresh PR lands for the month, close the
      heartbeat-triggered "missed refresh" issue automatically.
- [ ] **Discovery state log** — equivalent to market-intel's `discovery-state.md` — track
      candidates surfaced by Discovery sweeps that didn't make it into shards yet (with FOLD /
      NEW-DOMAIN / NEW-SKILL verdicts + reasons).

## v0.5 — Public packaging quality

- [ ] **Demo conversations** in `docs/` — annotated end-to-end transcripts (US buy / CN buy /
      cross-border buy / "wait for sale" projection) that show what good output looks like.
- [ ] **Comparison vs alternatives** doc — when a user is choosing between this and BigGo MCP
      directly, or this vs Perplexity Shopping, or this vs market-intel's ecommerce-arbitrage,
      explicit positioning.
- [ ] **Skill-installation troubleshooting** — common gotchas with `/plugin install` on
      Windows, MCP transport flakes, etc.

## Beyond v0.5 — speculative

- [ ] **Live API integration with retailer Open Banking** for actual purchase confirmation
      (only if Claude Code's tool-use story supports a "purchase intent → execute" loop with
      consent flow — currently it doesn't).
- [ ] **Cross-skill orchestration** — automatic invocation of `market-intel` when the buy intent
      crosses into "should I switch product categories" or "should I buy a different brand."
- [ ] **Snapshot dataset** for the open-source community — a quarterly anonymized snapshot of
      "what tools we recommended for what queries" so others can audit the matrix performance.

---

## Not on the roadmap (rejected, with reasons)

- ❌ **Build a full shopping orchestrator like Perplexity Shopping** — out of scope per P5 (thin
  layer doctrine). If the user wants that, recommend Perplexity Pro.
- ❌ **Auto-execute purchases / "buy this now" flow** — out of scope per autonomy / consent
  considerations. The skill produces a recommendation; the user clicks buy.
- ❌ **In-skill cashback redemption** — not the skill's role; user manages their own Capital
  One Shopping / Karma / Rakuten accounts.
- ❌ **Build a custom MCP server** — defer to BigGo MCP / Apify / Keepa. P5 again.
- ❌ **Auto-monitor + alert mode inside the skill** — out of scope per P5; this is one-shot,
  use `/schedule` or `/loop` wrapper, see SKILL.md "Recurring / monitoring use" section.
