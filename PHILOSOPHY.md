# Design Philosophy — Root-cause design, not incremental patching

> **设计理念 —— 从根本进行设计，而非小修小补**

This is the organizing principle of shopping-aggregator — **inherited unchanged from market-intel**
(by design; the philosophy is skill-agnostic and was earned through hard lessons there). Every
shopping-specific feature in this repo exists because of the six principles below, applied to the
**consumer shopping** context. The principles are not after-the-fact rationalizations — they are
the lens that produced each decision, and the test every future change must pass.

> 这是 shopping-aggregator 的统领原则，**完整继承自 market-intel**——这套理念是 skill-agnostic
> 的，在那边经过血泪验证；本仓库每个 shopping-specific 决定都源于把下面六条套到「消费购物」场景。

**The one-sentence version:** when something is wrong, change the assumption underneath it, not
the symptom on top of it. A patch leaves the bad default in place; fixing the framing changes
every decision that follows.

> **一句话：** 出了问题，改它底下的假设，而不是它表面的症状。补丁让错误的默认值继续存在；
> 改框架则会改变其后的每一个决定。

---

## P1 — Fix the framing, not the symptom · 改框架，不改症状

- **The patch:** sticker price ranking misled users → add a "shipping included?" note in the
  output.
- **The root:** the **ranking primitive itself was wrong**. Sticker price is not the consumer's
  question; **landed cost** is. So we reclassified the ranking unit from "$X sticker" to "$Y
  landed (sticker + ship + tax + coupon − cashback)" everywhere in the workflow + report
  template + tool docs.
- **Why it matters:** the patch (a note in the output) would leave the bad default in place; the
  next session would re-rank by sticker and someone would re-discover the same trap. Fixing the
  framing reroutes every comparison the skill ever makes.

> - **补丁：** 标价排序误导用户 → 输出里加一行"包邮吗？"备注。
> - **根本：** **排序原语本身错了**。标价不是消费者的问题，**到手价**才是。于是把整个 workflow +
>   report 模板 + 工具文档里的排序单位从「$X 标价」改成「$Y 到手价 = 标价+运费+税-券-返利」。
> - **为何重要：** 补丁让错误默认值留着；改框架重塑了 skill 以后做的每一次比较。

## P2 — Mechanisms, not intentions · 机制，而非意图

- **The patch:** write "remember to add the timestamp" in the docs, and hope it happens.
- **The root:** **make the timestamp mandatory in the structured evidence unit schema** — a
  subagent's return missing `snapshot_ts` is rejected at the synthesis layer, not flagged with a
  warning. Same for `stock_state` and `landed_cost`. The schema becomes the enforcement.
- **Why it matters:** intentions decay between runs; an LLM forgets to add timestamps. A schema
  refuses to accept a unit without one. Correct behavior becomes structural.

> - **补丁：** 文档里写"记得加时间戳"，然后指望它发生。
> - **根本：** **把时间戳作为结构化证据单元 schema 的必填字段** —— subagent 返回没带
>   `snapshot_ts` 的会在合成层被拒，而不是给个 warning。`stock_state` 和 `landed_cost`
>   同理。schema 即执行。
> - **为何重要：** 意图会衰减、LLM 会忘加时间戳。schema 不会接受没时间戳的条目。正确行为变结构性。

## P3 — Monotonic evolution against default decay · 对抗默认腐化的单调进化

- **The patch:** schedule a "refresh" reminder and trust the matrix stays good.
- **The root:** recognize that **the default trajectory of any source matrix is decay** —
  extensions lose affiliate networks (Honey 2026-01), APIs die (PA-API 2026-05-15), OSS goes
  silent (any repo without a 6mo commit). Design the refresh so the system can *only move
  forward*: guardrails only accumulate, dead tools become `⚠ Avoid` tombstones (not silent
  deletions), coverage can't drop past a threshold, methodology is preserved.
- **Why it matters:** "evolves automatically" is the easy promise; "cannot silently degrade" is
  the hard guarantee — and the only one worth making.

> - **补丁：** 设个"刷新"提醒，相信矩阵会保持优秀。
> - **根本：** 承认**任何源矩阵的默认轨迹都是腐烂**——扩展会失联盟网、API 会死、OSS 会停更。
>   设计 refresh 让系统**只能往前走**：护栏只增不减，死工具变 `⚠ Avoid` 墓碑而非默删，覆盖率
>   不能跌破阈值，方法论保留。
> - **为何重要：** "自动进化"是好说的；"不会默默退化"是难给的保证——也是唯一值得给的。

## P4 — The editor is never its own verifier · 编辑者不能自审

- **The patch:** "let the same subagent that fetched the price also verify it's accurate."
- **The root:** **dispatch a fresh verifier subagent that does NOT see the original fetch** —
  it independently re-fetches the cited URL, confirms the price + stock state + timestamp match
  the unit. Then the synthesis layer reconciles. Confirmation bias is structurally prevented
  by zero-context verification.
- **Why it matters:** an LLM that wrote a wrong number is the LLM least likely to spot it. A
  fresh-context verifier is cheap and ruthless.

> - **补丁：** "让抓价的 subagent 自己再校验一遍"。
> - **根本：** **派一个零上下文的 verifier subagent**——它独立重抓引用 URL，确认价格 + 库存 + 时间戳
>   和单元一致。然后合成层调和分歧。confirmation bias 在结构上被阻断。
> - **为何重要：** 写错数字的 LLM 是最不可能发现错的 LLM。fresh-context verifier 廉价又狠。

## P5 — Thin layer, delegate the heavy work · 薄层，重活外包

- **The patch:** "build another deep-research harness specialized for shopping."
- **The root:** **a thin orchestration layer that delegates** to playwright MCP, BigGo MCP, Keepa
  MCP, deep-research, market-intel. No reinvented engine. The skill's value is the **triage +
  source detection + price-specific guardrails + structured output schema** — three things
  nothing else does. Delegation is not laziness; it's the *only* way to stay current as the
  underlying engines (Claude Code's harness, MCP ecosystem, OSS scrapers) evolve.
- **Why it matters:** a clone-with-trigger-conflict would compete with deep-research instead of
  amplifying it. Same trap market-intel originally fell into and rejected in its 5-subagent
  adversarial design review.

> - **补丁：** "再写一个专为购物特化的 deep-research"。
> - **根本：** **薄编排层，把重活委托** 给 playwright MCP / BigGo MCP / Keepa MCP /
>   deep-research / market-intel。不重造引擎。skill 的价值是 **triage + 源检测 + 购物特有护栏 +
>   结构化输出 schema**——别人不做的三件事。委托不是懒，而是**唯一**让 skill 跟上底层引擎演化的方式。
> - **为何重要：** clone-with-trigger-conflict 会和 deep-research 抢，而不是放大它。

## P6 — Visible degradation > silent decay · 可见的退化优于隐形的腐烂

- **The patch:** "if Honey breaks, the user will figure it out eventually."
- **The root:** **flag it the moment it changes, in every recommendation surface**. When Rakuten
  terminated Honey's affiliate network on 2026-01-12, the skill should already carry that —
  in the browser-extensions shard, in the Honey tool doc, in the recommendations.
- **Why it matters:** silent degradation looks like a working skill until a user follows bad
  advice. Visible degradation gives them the option to choose.

> - **补丁：** "Honey 坏了，用户最终自己会发现"。
> - **根本：** **变化瞬间标出来，每个推荐界面都要更新**。2026-01-12 Rakuten 切断 Honey 联盟网，
>   skill 就该带着这个信息——在 browser-extensions shard、Honey 工具文档、所有推荐里。
> - **为何重要：** 隐形退化看着像 skill 还能用，直到用户跟着坏建议踩坑。可见退化把选择权交还用户。

---

## How these apply to shopping-aggregator specifically

| Principle | Concrete consequence in this repo |
|---|---|
| P1 | Landed-cost ranking primitive (not sticker); structured evidence unit schema mandates it |
| P2 | Snapshot timestamp + stock state + landed cost are SCHEMA fields, not documentation reminders |
| P3 | `⚠ Avoid` tombstones for dead tools (Honey, PA-API, The Tracktor) — never silent delete |
| P4 | Independent verifier subagent re-fetches every cited price URL |
| P5 | playwright/BigGo/Keepa MCPs do the fetching; this skill orchestrates + normalizes + guards |
| P6 | Honey status surfaced proactively in browser-extensions shard + Honey tool doc + recommendations |

---

## The test for every future change

Before merging any PR / matrix update / new shard / new guardrail, answer:

1. Does this **fix the framing** or just **patch a symptom**?
2. Is the correct behavior **enforced by a mechanism** (schema, gate, structural constraint), or
   merely **documented as intention**?
3. Does this **only allow the matrix to move forward** (gain coverage, gain accuracy), or could
   it silently regress?
4. Did **a fresh verifier with no context** check the change, or did the editor self-audit?
5. Did we **delegate** to existing engines, or did we **reinvent** them?
6. Will any **degradation be visible** in the output, or could it **silently mislead the user**?

If you can answer all six yes, the change passes the philosophy bar.
