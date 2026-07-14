# Judge protocol — heterogeneous, blind, ground-truth-free

> Grades orchestration quality (Signal C) on a real run over `scenarios.jsonl` against `rubric.md`.
> **Non-deterministic by design, never in CI, never blocking.** A FAIL here is a signal to a human, not
> a gate that stops a commit. (The committable gate is `tools/verify_matrix.py`.)
>
> **`scenarios.jsonl` is GENERATED — never hand-edit it.** To add or change a scenario, add a case to
> `tools/make_fixtures.py` and re-run it. The reason is not tidiness: a scenario is a realistic
> `buy_intent`, and the most convenient realistic buy intent available to an agent is always *what the
> operator actually bought*. Building every intent from the generator's reference-SKU table makes that
> paste impossible to commit — a real purchase cannot be regenerated, so `tools/data_boundary.py`
> BLOCKS on any row the case table could not have produced.

## Core principles

1. **Heterogeneous judges.** Each transcript is judged by **at least two genuinely different models**:
   - **Claude** (this skill's own model family), and
   - **Codex / GPT** via `mcp__codex__codex`, invoked with its own browser/MCP tools stripped
     (`config.mcp_servers = {}`, `tools.web_search = true`, `sandbox: "read-only"`,
     `approval-policy: "never"`) exactly as `../codex-crossval.md` mandates — judging is a soft,
     web_search-only task, never a live-browser task. A single-model self-grade is the same failure mode
     the constitution forbids for verification (II.4): the grader shares the writer's blind spots.

2. **Blind to the author.** The judge sees the scenario `buy_intent`, the run transcript, and the final
   report — it does **NOT** see which agent/model produced the run, nor any prior judge's verdict. Judges
   grade independently and in parallel; disagreement is the point.

3. **No ground truth in the prompt.** The judge is **never** told the "right" price, the "right"
   retailer, or a scenario's `fact_anchor`. `fact_anchor` in `scenarios.jsonl` is *author provenance
   only* (how the eval author justified the trap) and MUST be stripped before the judge prompt is built —
   see "Prompt construction" below. The judge grades **constitutional conformance and reasoning quality**
   (is the price E1-sourced, timestamped, caveated; is the #1 backed by >=2 E1 reads; was the tariff/Honey
   fact verified live and cited), NOT "did the number match a value I know". Grading against a remembered
   number would reward stale/memorized data — the exact anti-pattern the live-fetch doctrine exists to
   kill.

4. **Per-criterion evidence required.** For every rubric criterion the judge must emit
   PASS/PARTIAL/FAIL/N/A **plus a quoted snippet of transcript/report evidence** for that verdict. A
   verdict with no cited evidence is itself discarded as low-quality (judges can hallucinate too).

5. **Best-effort, fail-soft.** If a judge model is unavailable or times out, record the verdicts from the
   judge(s) that did run and note the missing one — never block on a judge. (Same posture as guardrail #9
   for delegates.)

## Prompt construction (what the judge receives)

The runner builds **one judge prompt per (scenario, judge-model)** containing exactly:

1. The **rubric** (`rubric.md`) — universal criteria + that scenario's per-scenario criteria.
2. The scenario's `buy_intent`, `region`, and `trap` from `scenarios.jsonl`
   — **with `fact_anchor`, `ideal_behavior_sketch`, and `notes` removed** (they encode author intent /
   provenance and would leak ground truth or the expected answer).
3. The full **run transcript** + **final report** to be judged.
4. The output contract (below).

The runner MUST assert the stripped keys are absent before sending. Leaking `fact_anchor` or
`ideal_behavior_sketch` into the judge prompt is a bug in the harness — it converts a blind reasoning
grade into an answer-key match.

### Judge instruction (verbatim core)

> You are grading whether a shopping buy-decision run obeyed a fixed set of rules (the rubric). You are
> NOT given the correct price or the correct store, and you must not assume one — do not penalize a price
> for differing from any value you happen to believe; only judge whether the price is properly sourced
> (live PDP/API = E1), timestamped, stock-stated, seller/evidence-tiered, and caveated as the rubric
> requires. For each criterion output PASS / PARTIAL / FAIL / N/A and quote the exact transcript/report
> text that justifies it. If the evidence is absent, that is FAIL (for a blocking criterion) or PARTIAL,
> not a guess. Do not reward confident prose that lacks the required marks.

## Output contract (per judge, per scenario)

JSON, e.g.:

```json
{
  "scenario_id": "cross-border-tariff-04",
  "judge_model": "gpt-5.5",
  "criteria": [
    {"id": "U1", "verdict": "PASS", "evidence": "row shows [fetched 2026-06-22 14:03 EDT]"},
    {"id": "S10", "verdict": "FAIL", "evidence": "AliExpress row landed cost = sticker+ship only; no duty line"},
    {"id": "S11", "verdict": "PARTIAL", "evidence": "mentions tariffs but cites no dated source"}
  ],
  "scenario_verdict": "FAIL",
  "weakest_blocking": "S10",
  "judge_notes": "Ranked the China parcel #1 without landed-cost duty — the canonical trap."
}
```

`scenario_verdict` = FAIL if any **[BLOCKING]** criterion is FAIL; otherwise the lowest non-N/A grade.

## Reconciling heterogeneous judges

- **Agreement** (both FAIL or both PASS on the headline) → that is the verdict; high confidence.
- **Split** (Claude says PASS, Codex says FAIL, or vice-versa) → **do NOT average and do NOT pick a
  winner.** Surface the split with both judges' cited evidence for a human to adjudicate. A split is the
  most valuable output of this harness: it is exactly where the constitution's wording is ambiguous or the
  run is borderline. (Mirrors II.2: on disagreement you re-examine, you don't average.)
- Persisting splits on the same criterion across runs are a signal that either the rubric wording or the
  underlying CONSTITUTION clause needs sharpening (handle via the PR path in CONSTITUTION VII — not a
  refresh sweep).

## Cadence & non-CI posture

- Run **manually / occasionally** (e.g. before a notable release, or when orchestration logic changed) —
  NOT on every commit. Prices are volatile, judges are non-deterministic, and live fetches cost real
  calls; wiring this into CI would make CI flaky and slow for no contract benefit. The deterministic
  contract gate (`verify_matrix.py`) is the one that belongs in CI.
- Results are advisory input to the refresh loop and may be summarized by a human, but this harness
  does **not** itself write to `live-runs.jsonl` (that file is for live user runs; keep eval noise out
  of it). Note that file is DATA and lives in the private data dir, never in this repo — see SKILL.md
  Step 7. Eval output, being synthetic, is not bound by that: it just has no business in there.
