# Cross-validation back-end: Codex MCP (GPT, independent model + web search)

> **Not a price source, a cross-model verification + discovery delegate.** Same category as
> `deep-research` / `market-intel`: a back-end this skill DELEGATES to (PHILOSOPHY P5), NOT a
> retailer or price API. That is why it lives here under `reference/` and is **not** in
> `reference/tools/`, the source matrix, or `registry.json`.

> **General rule for any external agentic delegate (codex today; future MCPs):** invoke it with its
> own browser / sub-MCP tools stripped (sandboxed to its built-in search) and treat it as
> **best-effort**, skip on hang/timeout per guardrail #9. The codex-specific flags below are this
> rule's first concrete instance.

## Why use it

A second, genuinely independent opinion: a different model (OpenAI GPT) with its **own** web-search
backend. Strong for the **soft** layer of a buy decision, weak for authoritative live prices:

- ✅ discover authorized channels / cheaper authentic sources your fixed retailer list missed
- ✅ cross-check the provisional cheapest pick (does an independent search agree?)
- ✅ authenticity / counterfeit reputation, retailer-trust sanity, "is this brand exclusive to one store?"
- ❌ NOT an authoritative live price. GPT web-browse returns stale / cached / approximate prices for
  anti-bot retail pages (Sephora / Ulta / Target / Amazon). Treat every price it gives as an
  **L5 lead** that must re-pass the live-fetch + citation gate (SKILL.md Step 6 / guardrail #1)
  before it can enter the landed-cost ranking.

## ⚠️ CRITICAL: disable Codex's own browser/MCP tools, or it hangs for HOURS

The user's `~/.codex/config.toml` registers Codex's OWN MCP servers (e.g. `[mcp_servers.playwright]`).
If you call the Codex MCP without disabling them, Codex will try to **drive its own headless browser**
to fetch a live retail page, and on an anti-bot page (Newegg / Best Buy / Amazon Cloudflare) that
`browser_navigate` call **hangs with no timeout**. **Real incident 2026-06-17:** a single Codex
`mcp__playwright browser_navigate` to Newegg ran **38,037 s (~10.5 hours)** before the user aborted.
It also collides with Claude's own playwright instance (two `npx @playwright/mcp` fighting over the
browser profile).

**The fix, ALWAYS pass these when calling `mcp__codex__codex`:**
- `config: { "mcp_servers": {}, "tools": { "web_search": true }, "model_reasoning_effort": "..." }`
, `mcp_servers: {}` strips Codex's browser/MCP tools so it can ONLY use the built-in web_search.
- `sandbox: "read-only"` + `approval-policy: "never"` (headless, nobody can answer an approval prompt).
- In the **prompt** also say: *"Use ONLY web_search. Do NOT use any browser / playwright / navigate /
  page / shell tool."* (belt-and-suspenders.)
- This reinforces the doctrine: Codex does **web_search soft cross-val**, NOT live-browser price fetch ,
  live fetch is THIS skill's Bright Data / playwright job.

Verified 2026-06-17: with `mcp_servers:{}` + web_search-only, the same query returned in **<1 min**
(vs the 10.5 h hang). Canonical call:

```
mcp__codex__codex({
  prompt: "Use ONLY web_search; no browser/playwright/shell. <buy-intent + ask for price+URL+date>",
  model: "gpt-5.5",
  config: { "mcp_servers": {}, "tools": { "web_search": true }, "model_reasoning_effort": "xhigh" },
  sandbox: "read-only",
  "approval-policy": "never"
})
```

## Call it via the MCP server, NOT `codex exec`

Use the connected **Codex MCP** (`mcp__codex__*`). Do **not** shell out to `codex exec` from the
agent: in the Claude Code Bash sandbox, `codex exec` fails at startup with
`Error: timed out waiting for cloud config bundle after 15s` (reproduced 2026-06-16, persists even
with the Bash sandbox disabled, that cloud-config endpoint is unreachable from the agent shell).
The **MCP-server route works** because Claude's harness spawns it on the working network path:

```
claude mcp add codex -s user -- codex mcp-server      # one-time; ChatGPT-login auth, NO key in cmd
# verify:  claude mcp list   ->  "codex … ✔ Connected"
```

A newly added MCP only exposes its tools after a **full session restart**, a `/mcp` reconnect
connects the server but does not always register its tools for ToolSearch. Once live, a subagent
loads it with `ToolSearch select:mcp__codex__codex` and calls it.

### Gotchas
- `codex exec` does **not** accept `--search` (that flag exists only on the interactive top-level
  `codex`). For exec, web search is `-c tools.web_search=true`. The MCP server has web search via
  the native Responses tool.
- Model: use the newest / best (2026-06 = `gpt-5.5`, reasoning effort `xhigh`). Auth is the user's
  ChatGPT subscription, so cost is plan-rate, not per-token, no reason to downgrade. See user memory
  `feedback_codex_best_model`.

## How to fold results
1. Give Codex the parsed buy intent (product + specs + region/ZIP + authentic-channel rules).
2. Ask for: cheapest authorized retailer + price + **source URL + date seen**, runner-ups,
   ships-to-ZIP / nearby pickup, authenticity caveats, and which prices it confirmed live vs approximate.
3. Merge: any NEW channel Codex surfaced -> re-fetch live via Bright Data / playwright (Step 5) and
   verify before ranking. Any price DISAGREEMENT vs your run -> re-fetch, don't average (guardrail #7)
   and surface as a divergence note. Authenticity flags -> fold into the Risks section (L5 corroboration).
4. If the Codex MCP is not connected, skip and note "codex cross-check unavailable" (guardrail #9).
   It is **best-effort**, never block the buy decision on it.

## Empirical note (2026-06-16 → 06-17)
- 2026-06-16: `codex mcp-server` -> `✔ Connected`; `codex exec` via Bash -> cloud-config timeout
  (blocked). MCP route is the supported one. Tools exposed only after a full session restart.
- 2026-06-17: first real `mcp__codex__codex` run (a high-end GPU price check, xhigh, MCP tools NOT
  disabled) **hung ~10.5 h**, Codex drove its own playwright `browser_navigate` to an anti-bot
  retailer (Cloudflare) with no timeout. Re-run with `config.mcp_servers={}` + web_search-only
  returned in <1 min. **Lesson is now the CRITICAL section above.** Cross-val data point: Codex
  web_search quoted the part roughly **15 to 30% BELOW** the live authorized listings (which were also
  out of stock), exactly why its prices are L5 leads, not authoritative. Direction matters: a
  model-summarized price errs *low*, which is precisely the direction that wins a naive ranking.
