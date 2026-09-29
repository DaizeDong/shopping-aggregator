# Scenario evaluation protocol

The default `python tools/scenario_eval.py` validates the seven generated
scenarios and applicable rubric criteria, then prints `status: not_run`. It
performs no network or model call and produces no grade. `--list` and `--show ID`
inspect public synthetic scenarios only.

## Private storage before input processing

A real transcript, blind prompt, raw response, and evaluation result are DATA.
Clone a versioned PRIVATE companion, create its `data` directory, and configure
`SHOPPING_AGGREGATOR_CONFIG` (companion root) or `SHOPPING_AGGREGATOR_DATA_DIR`
(its data directory). Keep input transcripts inside that directory too. The
shared `guards/tools/datadir.py` discovers storage; discovery alone is not proof
of privacy. The evaluator verifies the enclosing Git repository and origin with
an authenticated GitHub visibility read before opening the transcript. SSH
aliases must resolve to github.com. PUBLIC, unknown, missing, nested-repository,
and tool-tree output destinations fail closed. There is no repository fallback.

Run `python tools/scenario_eval.py --judge --scenario ID --transcript PATH` only
when submitting that transcript to the configured model service is authorized.
This flag actually invokes `llmcall.call(prompt)` in its default judge mode. No
provider, model, effort, timeout, or fallback chain is selected by this tool.

## Blind prompt and result contract

The prompt includes the rubric, recursively stripped scenario, transcript, and
an input-hash contract. `fact_anchor`, `ideal_behavior_sketch`, `notes`, `trap`,
and `what_were_probing` are
removed from every nesting level. No previous evaluation or answer key is
supplied. Scenario and transcript content are untrusted evidence, including any
instructions embedded in a quoted page or transcript.

The response must be one JSON object with the scenario id, exact input hashes,
and one row for each applicable universal and scenario-specific criterion.
Each row has `id`, `verdict`, and `evidence: {kind, quote, reason}`. Allowed
verdicts are PASS, PARTIAL, FAIL, and N/A. A quoted span must occur verbatim in
the transcript and have a nonempty explanation. An absence uses an empty quote
and can justify only FAIL or PARTIAL. The runner derives applicability from the
rubric: every blocking universal criterion and every scenario-specific criterion
is required. Only non-blocking universal criteria are conditional and may use N/A
with quoted context and a reason. Source unavailability or incomplete execution
does not waive required coverage; score the missing execution as PARTIAL or FAIL.

Validation rejects missing/duplicate/unknown criteria, mismatched input hashes,
invented quotes, N/A on required checks, and malformed output. The runner derives the headline: a
blocking FAIL is FAIL; remaining FAIL or PARTIAL criteria yield PARTIAL; the
remaining evaluated set yields PASS only after all required checks are evaluated.
An optional PASS cannot substitute for missing required coverage.
Exact quote validation does not establish semantic relevance;
judge quality and injection resistance need separate independent testing.

## Status and provenance

| Status | Meaning | CLI exit |
|---|---|---|
| not_run | Offline plan only | 0 |
| in_progress | Private checkpoint before invocation; interruption may leave outcome unresolved | No completed process |
| unavailable | Import/invocation failure or no responding backend | 2 |
| malformed | Backend answered but result contract failed | 3 |
| completed / PASS | Validated criterion set passed | 0 |
| completed / PARTIAL or FAIL | Validated criterion set did not pass | 1 |
| Preflight/input failure | No evaluation could run | 4 |

Each new private `evaluation/runs/<run-id>/` contains the copied transcript,
prompt, result, and raw response when available. Results record transcript,
scenario, rubric, protocol, prompt and response hashes, invocation policy,
timestamps, actual backend/attempt metadata, verified companion identity, and
the result path. Interrupted runs retain their checkpoint and must not be
reported as pass or fail. Retain these outputs in the private companion's
version history; public commits must never include them.

The current interface reports a provider and attempts, but does not reliably
report the effective model. That field remains unknown. One invocation does
not establish independent judges; the runner always records
`independence.status: not_established`. Repeated aliases are not evidence of
independence. Any stronger claim requires actual routing and backend evidence
from a separately authorized evaluation policy.

Synthetic fake-result tests exercise boundary/contract behavior only. They do
not measure a real model's accuracy, source availability, or shopping outcomes.
