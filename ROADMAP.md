# Roadmap

`shopping-aggregator` is at v0.4.0 — the v0.2.0 structural/framework batch landed the CONSTITUTION,
the demand-side channel-class primitive, the evidence-unit schema (`variant_key` /
`seller_tier` / `evidence_grade`), the seller-identity gate, and the codex-crossval back-end
on top of the v0.1.0 base (9 domain shards, 22 tool docs, the SKILL.md orchestration core, the
philosophy inherited from market-intel). This file tracks what's next.

## v0.2 — Match market-intel's enforcement layer

- [x] **Anti-regression gate (`tools/verify_matrix.py`)** — **shipped in 0.3.0** (CI-enforced via
      `.github/workflows/gate.yml`): 6 deterministic checks (THREEWAY shard↔tool-doc↔index drift,
      FRESH, TEMPLATE, VERSION, RENAME, LIVERUNS). market-intel's RICHER judgement checks
      (REPO/STAR/GHACTIVE/COVER/CHURN/DELETE) are not yet ported — those remain the gap.
- [x] **CONSTITUTION.md** — shipped in 0.2.0. Explicit hard constraints injected at refresh-time
      so the editing subagents physically can't propose changes that violate the philosophy.
      (Market-intel did this in its v0.4-0.5 era.)
- [ ] **More tool docs** — currently 22; target 30-40 to match market-intel's depth. Specific
      gaps: Bright Data Web Unlocker (referenced but no per-tool doc yet), DealNews,
      InvisibleHand, RetailMeNot Genie, Cently, 京东价保 deep-dive, Slickdeals API discovery,
      r/buildapcsales as a structured source.
- [ ] **Tax / shipping / duty tables** — per US state sales tax + cross-border duty estimates
      so the landed-cost compute doesn't always say "(NJ rate assumed)."
- [ ] **Currency normalization spec** — explicit FX-rate-source-of-record (currently relies on
      delegated harness defaults).

## v0.3 — Real-run feedback wired tight

- [ ] **`metrics/live-runs.jsonl` → refresh prioritization** automation — refresh-protocol reads
      the JSONL, ranks sources by `dead`/`price_mismatch`/`user_correction` frequency, schedules
      re-verification automatically. (Market-intel's open-loop liveness gap = same pattern.)
- [ ] **Heartbeat issue auto-close** — when a refresh PR lands for the month, close the
      heartbeat-triggered "missed refresh" issue automatically.
- [ ] **Discovery state log** — equivalent to market-intel's `discovery-state.md` — track
      candidates surfaced by Discovery sweeps that didn't make it into shards yet (with FOLD /
      NEW-DOMAIN / NEW-SKILL verdicts + reasons).

## v0.4 — Domain expansion

Three new domain shards that didn't make v0.1 (all landed — matrix now 12 domains):
- [x] **`cross-border`** — explicit shard for US↔CN, US↔EU, etc. Currently scattered across
      regional shards; a dedicated shard would handle duties, shipping aggregators, daigou
      pricing, grey-market warranty rules. (duty figures source-of-record:
      `reference/data/cross-border-duty.json`, CBP-primary.)
- [x] **`grocery-cpg`** — Flipp is in here as a tool, but grocery has its own data sources
      (Instacart pricing, Walmart+ grocery, Kroger fuel points, NJ ShopRite digital coupons)
      that warrant a dedicated shard.
- [x] **`auction-resale`** — eBay sold listings (already noted as a gap), Mercari, Poshmark,
      Whatnot, ThredUp. Different trust model from new-retail.

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
