# Changelog

## [0.4.0] — 2026-06-22

**Self-evolve round** — the single largest batch since v0.2.0. Run as parallel specialist subagents (data-tables / shards / tool-docs / gate-port / refresh-automation / scenario-eval) with a serial integrator finalizing version + docs + CI. Closes the entire v0.2 enforcement gap, the v0.4 domain expansion, and the landed-cost data gap at once. Matrix **9 → 12 domains**, tool docs **22 → ~32**, gate **6 → ~18 checks**, and the skill gains its first source-cited landed-cost data layer.

**Landed-cost data tables (NEW `reference/data/`).** Four source-of-record tables on a shared envelope `{schema_version, last_verified, rows:[{source_url, verified_date, evidence_grade, ...}]}`:
- **`us-sales-tax.json`** — per-US-state sales-tax rows (each cited to the state DoR). Landed-cost compute no longer hard-codes "(NJ rate assumed)."
- **`cross-border-duty.json`** — de-minimis thresholds + typical-category HTS duty rates, US↔CN/EU. **Highest-volatility facts in the repo.** Captures the post-2025 reality: **US §321 de-minimis SUSPENDED for all countries** (EO 14324, eff 2025-08-29; statutory repeal 2027-07-01), EU EUR-150 relief → **EUR 3 flat duty** from 2026-07-01, CN postal allowances. Web-verified this round against Federal Register 2025-16802 + CBP CSMS #66065494 + EU Council 2026-02-11 (all E1).
- **`shipping-baselines.json`** — carrier/forwarder baseline shipping bands.
- **`fx-source-of-record.md`** — names the dated, free FX rate source the harness reads (values fetched live, not cached).

**3 new domain shards (matrix 9 → 12), wired into every discovery surface.**
- **`reference/domains/auction-resale.md`** — resale/used value: eBay Sold SERP ④ free (`LH_Sold=1`), StockX Public API v2 ① (approval-gated), playwright ④ for GOAT/Whatnot/Poshmark/Mercari/Depop/ThredUp. Different trust model from new-retail.
- **`reference/domains/grocery-cpg.md`** — groceries/CPG: Flipp ① circular discovery + banner-app ① loyalty truth (Kroger fuel points, Target Circle, ShopRite Price Plus, Wegmans, Costco Executive), playwright ④ for live Instacart cart. Hyper-regional — pin ZIP→banner first.
- **`reference/domains/cross-border.md`** — 海淘/代购/forwarders: Superbuy/Stackry/MyUS/YesStyle ④. **Duty by default** — de-minimis suspended; all figures live in `reference/data/cross-border-duty.json` (CBP / Federal Register / EU Council primary, E1).
- **Wiring:** 3 rows added to `reference/sources-index.md` + both README source matrices; Domains badge **9 → 12**; a **Flipp grocery hand-off** note spliced into `mobile-apps-aggregators.md` (Flipp stays discoverable there, grocery mechanics route to `grocery-cpg.md`); the `12 domains` count bumped across README/README_CN/SKILL.md.

**Tool docs 22 → ~32.** Added per-tool how-to docs (install + auth + usage + 踩坑) for the documented-but-undocumented gaps: Bright Data, DealNews, InvisibleHand, RetailMeNot, Cently, 京东价保 (jd-price-protection), Slickdeals, reddit-deals, ScraperAPI, AliExpress, Xiaohongshu, and more — each with a registry + index row (THREEWAY stays consistent).

**Gate: market-intel's RICHER judgement checks ported (`tools/verify_matrix.py`, 6 → ~18 checks).** On top of the original deterministic 6 (THREEWAY/FRESH/TEMPLATE/VERSION/RENAME/LIVERUNS): **REPO** (repo existence, 404→BLOCK), **STAR** (★-claim tolerance), **GHACTIVE** (archived/stale push, cached 7d), **DOCCOVER** (live shard repo with no per-tool doc), **STALE** (tool doc >9mo unverified), **COVER/CHURN/DELETE** (git-baseline anti-mass-deletion + rewrite + death-code discipline), **CONST** (CONSTITUTION scope guard), **METH** (SKILL.md keeps the tier/grade legend + ≥10 guardrails). NEW checks added beyond the port: **DATA** (data-table envelope + per-row `source_url`/`verified_date`, future-date BLOCK) and **NOHARDCODE** (a tax/duty number in SKILL.md prose with no `reference/data/` citation and no `(assumed)` stamp → WARN, per CONSTITUTION I.7) and **SHARDSYNC** (a net-new shard must be registered → BLOCK). Network gates honour `--no-net` for offline CI; fail-closed on any uncaught error.

**Refresh + eval automation.** NEW `tools/refresh_priority.py` — deterministic weighted ranking of `metrics/live-runs.jsonl` problem events (`user_correction` 100 / `dead` 10 / `price_mismatch` 5 / `coverage_gap` 3); one definition shared by the refresh-protocol and the gate, replacing the old hand-run `jq | sort | uniq -c`. NEW `tools/scenario_eval.py` — fixture-driven scenario evaluation harness.

**`reference/refresh-protocol.md` — data-table staleness hook.** Every refresh sweep MUST re-confirm the four `reference/data/` tables against their cited primary source and bump `last_verified` — a green DATA shape-check is NOT permission to skip the fact-check. **De-minimis / cross-border duty = mandatory CBP-primary re-check on EVERY sweep** (most volatile + highest blast radius; a wrong de-minimis status silently mis-prices every cross-border landed cost). Adds per-table re-verification guidance for sales-tax / FX / shipping.

**Docs + version.** `ROADMAP.md` restructured — completed work moved to a **Shipped** section (v0.4.0 self-evolve + earlier), stale "RICHER checks not ported" / "more tool docs (currently 22)" / "tax tables" claims removed as now-done; remaining roadmap is v0.3 loop-closing + v0.5 packaging. README/README_CN badges: **Tool docs → ~32 per-tool**, NEW **Data tables** badge (tax | duty | FX | shipping); Status sections de-staled. `.claude-plugin/plugin.json` bump **0.3.3 → 0.4.0**. Gate: **PASS** (`python tools/verify_matrix.py --no-net`, exit 0).

## [0.3.3] — 2026-06-17

Documentation-consistency sweep (no skill-logic change). Grep-audited the whole repo for stale version strings, wrong counts, broken links, and pre-0.2.0 feature descriptions; only the two READMEs were stale.
- **`README.md` + `README_CN.md`** — version badge 0.1.0 → 0.3.3; fixed a broken **doubled `SKILL.md` link** (`skills/shopping-aggregator/skills/shopping-aggregator/SKILL.md` → `skills/shopping-aggregator/SKILL.md`); rewrote Status/roadmap to reflect what shipped since v0.1.0 (channel-class primitive, seller_tier+evidence_grade split, variant_key, coverage floor, CONSTITUTION, codex-crossval, the executable gate), corrected tool-doc count **17 → 22**, re-scoped remaining gaps to market-intel's richer judgement checks; added the new headline guardrails (evidence-grade-gates-ranking, seller-identity-not-domain, variant pinning, coverage floor) to the guardrails list and the channel-class mapping to the intent-parse step.
- Verified the rest is NOT stale: ROADMAP / refresh-protocol / CONSTITUTION / PHILOSOPHY / shards already current as of 0.3.2; remaining `source_tier` mentions are the gate's own definition (exempt) + the live-runs genesis line (historical record); the two `guardrail #5` shard refs correctly point to seller-tier (genuinely #5).
- bump 0.3.2 → 0.3.3. Gate: PASS.

## [0.3.2] — 2026-06-17

Structure-audit cleanup. A 6-lens structural audit returned **MINOR-ONLY (leaning CONVERGED)** — the architecture is sound (thin layer, layered-DRY canonical-home+pointer, scoped gate, no orphans/double-homing; DRY lens converged outright). Landed only the 3 genuine items + doc-honesty; explicitly did NOT re-open structure (no new shards, no SKILL.md re-split, no brittle gate checks — those were named churn/net-negative).

- **`reference/refresh-protocol.md`** — flipped an operationally-live falsehood: it told a refresh-sweep agent the skill "does not yet have its own gate (planned)", but the gate shipped in 0.3.0. Now states it ships `tools/verify_matrix.py` + `gate.yml` (6 checks); market-intel's richer judgement checks remain the gap.
- **`tools/verify_matrix.py`** — added a 6th deterministic check **LIVERUNS**: `metrics/live-runs.jsonl` (consumed by the refresh loop) — every non-blank line must parse as JSON + carry the 6 required keys (BLOCK); `outcome` in the declared set (WARN). A corrupt metrics file no longer silently breaks the refresh loop.
- **`SKILL.md`** — Step 4: made the shardless-channel-class path explicit (brand-direct / cross-border / non-PC category-specialists have no domain shard → run them directly via the channel-classes route; do NOT create shards). Progressive-loading block: added `channel-classes.md` (a triage-tier load that was omitted).
- **`ROADMAP.md`** — version → 0.3.2; checked off the now-shipped gate bullet.
- bump 0.3.1 → 0.3.2. Gate: PASS (6 checks). README version/count refresh deferred (human-only cosmetic). **Structure declared converged — stop.**

## [0.3.1] — 2026-06-17

Iteration-loop round-1 cleanup. A 4-lens review of 0.3.0 CONVERGED (4/4 lenses converged, zero critical/major regression — the restructure dropped no rule, all evidence-schema.md pointers resolve, the gate is genuine enforcement). These are the residual minors it surfaced:
- **`reference/report-template.md`** — the ranking-table note pointed the "only an E1 row may be #1" rule at guardrail #5, but the 0.3.0 split moved that rule to **#5b** (#5 is now seller-tier). Fixed.
- **`SKILL.md` Step 3** — two in-prose pointers (`domains/amazon-us.md`, `tools/biggo-mcp.md`) were missing the `reference/` prefix every other pointer in the file uses → would mis-resolve for an agent following them verbatim. Fixed.
- **`tools/verify_matrix.py`** — THREEWAY docstring clarified as EXISTENCE-only (per-domain placement is advisory, not gated) — removes a slight overclaim.
- bump 0.3.0 → 0.3.1. Gate: PASS.

## [0.3.0] — 2026-06-17

APPRAISAL-driven batch from an honest 6-lens self-evaluation of v0.2.0. Overall finding: the skill was 思路-correct but had written many advisory "MUST" rules with **NO executable gate** behind them — violating its own PHILOSOPHY P2 (mechanism, not intention) — and `SKILL.md` (332 lines) had outgrown its thin always-loaded budget against the parent market-intel (299). This batch closes the P2 gap with the skill's first real gate, repairs a dead feedback loop, and slims the entry-point doc.

- **NEW `tools/verify_matrix.py` + `.github/workflows/gate.yml`** — the skill's **FIRST executable deterministic lint gate** (Python 3, run from repo root, exit 0 = PASS / non-zero = BLOCK, fail-closed). Five non-judgemental artifact/contract checks adapted from market-intel's gate, trimmed to only the deterministic ones: (1) **THREEWAY** — `registry.json` slugs ⟷ `reference/tools/<slug>.md` files ⟷ `index.md` rows (registry slugs de-duped first, since biggo-mcp/manmanbuy/smzdm appear once per domain), BLOCK on mismatch; (2) **FRESH** — every `domains/*.md` + `tools/*.md` must carry a `last_verified` / `Last verified:` line (WARN, by design — a rot signal, not a broken contract, and durable while prose is restructured); (3) **TEMPLATE** — `report-template.md` must have a `Coverage gaps` heading (CONSTITUTION I.6) AND an `Ev` column in the ranking table (I.3), BLOCK; (4) **VERSION** — CHANGELOG top version == `plugin.json` version, BLOCK on mismatch; (5) **RENAME** — the snake_case token `source_tier` (renamed to `seller_tier` + `evidence_grade` in 0.2.0) must not leak in any `.md` under `skills/`, BLOCK. CI runs `python tools/verify_matrix.py` on push + pull_request. This turns the advisory structure into a **checked mechanism** — the central appraisal finding. Gates only durable contracts/artifacts (no prose line numbers, no guardrail numbering) so it survives prose restructuring.
- **Feedback loop backfilled (`metrics/live-runs.jsonl`)** — the file was **empty**, so refresh-protocol's feedback jq depended on a dead file. Backfilled 7 honest one-line-per-source entries for the two documented real runs (REDACTED-CATEGORY → 10001; REDACTED-PRODUCT → 10001), each tagged `(backfilled 2026-06-17 from documented run)`: brightdata=verified, BigGo niche-GPU=`coverage_gap`, Micro Center missing-then-found=`coverage_gap`, Best Buy fake-first-party=`price_mismatch`, codex undershoot=`price_mismatch`. Genesis line preserved; all lines valid JSON.
- **`ROADMAP.md` de-staled** — rewrote the stale v0.1.0 heading to current 0.2.0 state (shipped CONSTITUTION / channel-classes / evidence-schema with `variant_key`+`seller_tier`+`evidence_grade` / seller-identity gate / codex-crossval); checked off the CONSTITUTION bullet; annotated the `verify_matrix.py` bullet as LANDING in this 0.3.0 batch; corrected the tool-doc count 17 → 22.
- **`reference/codex-crossval.md`** — canonical-call example `model_reasoning_effort` fixed `high` → `xhigh` to match the surrounding doctrine.
- **`SKILL.md` slimmed 332 → 249 lines** by moving the annotated evidence-unit schema + the long guardrail-#5/#5b/#7/#8/#9/#10 bodies + the two "Run B" war-stories into **NEW `reference/evidence-schema.md`** (read at Step 5); SKILL.md keeps a bare field-name schema + pointer. Step 2 split into **2a triage / 2b channel-class map / 2c depth budget** with a mandatory `[matched domains | in-scope channel classes | depth cap]` output line, channel-classes promoted to a first-class sub-step, `quick` (3/1/1) made the **default** with an honest 80/20 line, and ai-shopping-assistants added to the US enumeration. Guardrail #5 split into **#5** (seller tiers L1–L5, read Sold-by) + **#5b** (evidence grade E1/E2/E3 gates ranking first, only E1 wins); #7 and #9 use (a)/(b) sub-bullets so the second obligation can't be missed. Added a 6-item **"before you emit the report" self-check** at the end of Step 6, and an explicit **zero-context verifier spawn** at the end of Step 5 (CONSTITUTION II.4). Removed the duplicate body "Base directory" line.
- **`CONSTITUTION.md` II.5** — softened to an honest-downgrade: live-run observations MUST be appended when the repo is checked out + writable; otherwise MUST be noted in the reply; dropping them entirely is a bug.

**Still advisory** (judgement-dense, not mechanizable): seller-identity reasoning, evidence-grade assignment, cross-source reconciliation cause-sets, channel-class matching — these remain MUST-prose because they require model judgement, not a regex. **Now enforced** (by `verify_matrix.py`): registry/index/tool-doc three-way consistency, freshness stamps (warn), report-template Coverage-gaps + Ev contract, CHANGELOG ⟷ plugin version sync, no `source_tier` leak.

## [0.2.0] — 2026-06-17

STRUCTURAL / framework batch from a multi-round, 6-lens consensus reflection on WHY the skill kept missing tool-less channels (Micro Center) and produced internally inconsistent retrieval — root causes, not source expansion. Root causes found: (1) the only machine-readable artifact (`registry.json`) + the CONSTITUTION's consistency rules are TOOL-shaped, so a channel with no tool is structurally un-representable and invisible to triage/refresh; (2) discovery enumerates TOOLS, never MISSING CHANNELS; (3) a "price" was a scalar with no SKU-variant key, no evidence-provenance grade, no cross-source reconciliation, and coverage had ceilings but no floor. This batch upgrades those from prose intent to schema/guardrail MECHANISM (PHILOSOPHY P2). Owner decision deferred to ROADMAP: whether closing the coverage/reconciliation loop ultimately needs the skill's first executable lint gate (the fixes here are advisory / by-construction on already-enforced artifacts, since the skill has no gate yet).

- **NEW `reference/channel-classes.md`** — a DEMAND-SIDE channel-class primitive (mass-market · category-specialist · brand-direct · warehouse · local-pickup-only · cross-border · refurb), the counterweight to the supply-side tool matrix. Tool-less authorized retailers (Micro Center, B&H, Adorama…) are now first-class via the browser/scrape route. `SKILL.md` Step 2 maps the product to its channel classes; `sources-index.md` points to it. Root fix for "tool-less channel = invisible."
- **`SKILL.md` evidence-unit schema** — added `variant_key` (REQUIRED) and split `source_tier` into `seller_tier` (who sold it) + `evidence_grade` (E1 PDP/API · E2 aggregator · E3 snippet/lead). Guardrail #5: evidence_grade gates ranking FIRST and overrides seller_tier — only E1 may win, E3 is a lead never ranked (fixes the $1,450-snippet-as-price error). Guardrail #7 extended to cross-SOURCE reconciliation (same-variant_key, closed cause-set, resolve by E1>E2>E3, never average). Guardrail #9 added a coverage FLOOR — an in-scope channel class never attempted is a `not-attempted` gap that emits a `coverage_gap` line.
- **`CONSTITUTION.md`** — I.3 now requires seller_tier + evidence_grade; new I.3a requires variant_key (different variant = different SKU, never merged); I.4 tightened (the #1 rec must rest on ≥2 independent E1 reads of the same variant_key, no single-source escape for the winner); II.4 verifier must also confirm seller + evidence_grade for any E1/L1 winner.
- **`reference/report-template.md`** — ranking table gains `Variant (key)` + `Ev` columns (one row per variant_key); Sources lines carry an evidence-grade token; Disagreement matrix notes same-variant_key + closed cause-set + E1-wins.
- **`reference/refresh-protocol.md`** — Discovery gains a coverage-driven **channel-completeness audit** (not just tool hunting); feedback jq now prioritizes the new `coverage_gap` outcome (how a MISSING CHANNEL reaches the refresh loop) and corrects the `user_correction` orphan (it is a JSON key, not an outcome value); fixed a stale line that claimed no CONSTITUTION.md ships (it now does).
- bump 0.1.6 → 0.2.0. DROPPED as scope creep (per multi-lens consensus): per-retailer scraper/price engine; channels-in-registry.json; auto channel-discovery crawler; numeric confidence/reconciliation scoring; shard rename; a `channel_gap` synonym (reuse parent skill's `coverage_gap`); a new BLOCKING workflow step (the skill has no executable gate, so a BLOCKING step would be empty intent — the very P2 anti-pattern).

## [0.1.6] — 2026-06-17

Skill-improvement batch (Tier 1) from a 9-agent skeptical evaluation of two real end-to-end runs (REDACTED-CATEGORY → 10001; REDACTED-PRODUCT → 10001). Closes the three decision-grade misses those runs exposed. (Tier 2 — a store-pickup `fulfillment` schema field + a single-page-overflow note — deferred to 0.1.7; `codex-stale-price-note` dropped as already-documented; `bounded-external-delegate` folded into codex-crossval.md as one generalizing line.)

- **`reference/domains/ebay-walmart-target.md`** — added **Micro Center** as a source (triage list + per-retailer gotcha): US authorized PC-parts retailer, **pickup-only + per-store stock**, must scrape the specific store page (storeid) for the buyer's ZIP; codex/BigGo miss per-store stock. Run B's only in-stock authorized unit (a specific store branch, 2 units) was findable only this way. Also extended the **Best Buy** bullet with the **Marketplace 3P** trap (the "REDACTED-PRICE" REDACTED-PRODUCT was a 3.74★ marketplace seller, not Best Buy first-party).
- **`SKILL.md` guardrail #5** — upgraded to a **seller-identity gate**: a retailer domain is not proof of first-party (Best Buy/Walmart Marketplace, Newegg/Amazon 3P all render under the retailer domain); **stamp L1 only after reading the `Sold by`/`Shipped by` field**; a missing seller_name **degrades to L3, never rejects** the unit (preserves codex/BigGo L5 leads). `seller_name` marked required-for-L1–L4 in the evidence-unit schema. Mirrors the P2 mechanism-not-intention move already made for `snapshot_ts`.
- **`reference/domains/amazon-us.md`** — noted the **main Buy Box can be a 3P seller** (read "Ships from/Sold by"; only "Sold by Amazon.com"/brand store is L1).
- **`reference/tools/biggo-mcp.md` + `reference/domains/claude-mcps.md`** — corrected the falsified "OK for US" coverage claim to "OK for US mainstream; **weak for niche/US-specific SKUs**" (Run B: BigGo returned ZERO for a niche US GPU SKU); **an empty BigGo result ≠ unavailable** — fall back to Bright Data SERP + retailer scrape (P6 visible-degradation). Noted BigGo's `spec_search` suggestion is a spec lookup, not a price source.
- **`reference/codex-crossval.md`** — added one generalizing line: any external agentic delegate (codex today; future MCPs) is invoked with its browser/sub-MCP tools stripped + best-effort skip per guardrail #9.
- bump 0.1.5 → 0.1.6. No matrix/registry/tool-doc additions (Micro Center documented in-shard, not as a new tool primitive).

## [0.1.5] — 2026-06-17

Harden the Codex cross-val back-end after a real **10.5-hour hang**. First live `mcp__codex__codex` run (REDACTED-PRODUCT price check, MCP tools not disabled) drove Codex's OWN playwright `browser_navigate` to Newegg (Cloudflare anti-bot), which hung with no timeout for **38,037 s** until the user aborted — NOT a network/auth problem (model calls succeeded, Pro plan, tokens counted). Root cause: the user's `~/.codex/config.toml` registers `[mcp_servers.playwright]`, so Codex tries to drive a headless browser to live retail pages (and collides with Claude's own playwright). 

- **`reference/codex-crossval.md`** — new **⚠️ CRITICAL** section: ALWAYS call `mcp__codex__codex` with `config.mcp_servers={}` (strips Codex's browser/MCP tools → web_search only) + `sandbox:read-only` + `approval-policy:never` + a prompt instruction to use only web_search. Verified 2026-06-17: same query then returned in <1 min. Reinforces the doctrine — Codex does web_search soft cross-val, NOT live-browser price fetch (that's this skill's Bright Data/playwright job). Empirical note updated with the incident + a cross-val data point (Codex's ~$1.0–1.3k undershot the live authorized $1.20–1.45k listings → why its prices are L5 leads).
- No SKILL.md / matrix / registry changes.

## [0.1.4] — 2026-06-16

Add **Codex MCP as an optional cross-model cross-validation + channel-discovery back-end** (NOT a price source). Prompted by a user question + an empirical test: a different model (GPT) with its own web search is a genuinely independent second opinion for the *soft* layer (authorized channels, missed cheaper authentic sources, counterfeit reputation, cross-checking the cheapest pick) — but unreliable for authoritative live prices on anti-bot retail pages, so its prices are **L5 leads** that must re-pass the live-fetch + citation gate before ranking. Doctrine: Codex is a delegation back-end like `deep-research` / `market-intel` (PHILOSOPHY P5), so it is documented under `reference/`, **not** added to `reference/tools/` or the source matrix / registry — no matrix/registry churn.

- **`reference/codex-crossval.md`** (new) — how-to: why the MCP route not `codex exec` (the latter hits a `cloud config bundle` egress timeout in the agent sandbox; the `codex mcp-server` MCP route works — verified `✔ Connected` 2026-06-16), the `--search` vs `-c tools.web_search=true` gotcha, best model = newest (gpt-5.5 / xhigh, ChatGPT-subscription auth), the L5-lead rule, and how to fold results (re-verify new channels, surface divergences per guardrail #7, best-effort skip per #9).
- **`SKILL.md` Step 5** — added the Codex-MCP cross-validation / discovery delegate bullet (L5 leads, best-effort, MCP-not-exec).
- **`SKILL.md` guardrail #8** — the disconfirmation reverse-search may also run through the Codex MCP as an independent cross-model check (L5 corroboration).
- No tool / matrix / registry changes.

## [0.1.3] — 2026-06-16

Sync to market-intel v0.12.0 spec change: `companion-config-spec` v1 now formally
recognizes two storage modes for a companion repo's secrets — Mode A (committed to private
repo, single source of truth) and Mode B (gitignored, out-of-band backup). The
shopping-aggregator install-guide's L3 row already delegates to market-intel's spec for the
formal contract; no shopping-aggregator-side doc changes required (the cross-reference
picks up the new section automatically). Bump for traceability only.

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
