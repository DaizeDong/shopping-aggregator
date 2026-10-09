# Design Philosophy, Root-cause design, not incremental patching

> **设计理念, 从根本进行设计，而非小修小补**

The principles below adapt market-intel's approach to consumer shopping. They govern
landed-cost ranking, evidence, source maintenance and delegation. When a failure
recurs, review the assumption that produces it and encode the correction in the
workflow or its checks.

> 以下七条原则将 market-intel 的设计方法用于消费购物，指导到手价排序、证据、来源维护和委托。
> 问题反复出现时，应检查导致它的前提，并把修正落实到流程或检查中。

---

## P1, Fix the framing, not the symptom · 改框架，不改症状

Use landed cost as the ranking unit throughout the workflow, report template and
tool documentation: sticker price + shipping + tax + duty − verified checkout coupons.
A shipping note beside a sticker-price ranking would leave the ranking inconsistent
with what the buyer pays. Delayed cashback is separate because eligibility,
attribution, exclusions and payout can fail after checkout.

> 在流程、报告模板和工具文档中统一按到手价排序：标价 + 运费 + 税费 + 关税 − 已核验结账优惠。
> 仅在标价旁注明运费仍会使排名偏离实际支付额。延迟返利可能因资格、归因、排除项或到账条件
> 而在结账后失效，因此单独列出。

## P2, Mechanisms, not intentions · 机制，而非意图

Make `snapshot_ts`, `stock_state` and `landed_cost` required fields in the
structured evidence unit. The synthesis layer must reject a unit missing the
required information. A reminder to add timestamps does not provide this check.

> 结构化证据单元必须包含 `snapshot_ts`、`stock_state` 和 `landed_cost`。
> 合成层须拒绝缺少必要信息的单元，将要求落实为检查。

## P3, Monotonic evolution against default decay · 对抗默认腐化的单调进化

Source matrices become stale when extensions lose affiliate networks
(Honey 2026-01), APIs close (PA-API 2026-05-15), or repositories stop receiving
commits for six months. Refreshes preserve existing guardrails and methodology,
enforce coverage thresholds, and retain dead sources as `⚠ Avoid` tombstones.
Automation must make these changes visible rather than silently remove coverage.

> 扩展失去联盟网、API 关闭或仓库长期停更，都会使来源矩阵过时。刷新必须保留已有护栏和方法要求，
> 遵守覆盖阈值，并将失效来源保留为 `⚠ Avoid` 条目，使读者能看到来源变化。

## P4, The editor is never its own verifier · 编辑者不能自审

A fresh verifier that has not seen the original fetch independently reopens the
cited URL and checks price, stock and timestamp. The synthesis layer then reconciles
the observations. This separates collection from verification and reduces reliance
on the original worker's judgment. Fresh context alone does not establish a different
backend; the workflow must disclose the independence actually achieved.

> 由未看过原始采集结果的核验者独立打开引用 URL，检查价格、库存和时间，再由合成层对照结果。
> 这样可分开采集与核验，减少对原工作者判断的依赖。新上下文本身不能证明使用了不同后端，
> 流程必须说明实际达到的独立性。

## P5, Thin layer, delegate the heavy work · 薄层，重活外包

Delegate source collection to playwright MCP, BigGo MCP, Keepa MCP, `deep-research`
and `market-intel`. This skill owns triage, source detection, shopping-specific
requirements and the structured output schema. Reusing those capabilities limits
maintenance as host workflows, MCPs and scrapers change.

The five-subagent adversarial review behind market-intel rejected a duplicate
research engine with conflicting triggers. The same scope decision applies here.

> 采集委托给 playwright MCP、BigGo MCP、Keepa MCP、`deep-research` 和 `market-intel`。
> 本 skill 负责分诊、来源检测、购物证据要求和结构化输出，减少对底层能力的重复维护。
> market-intel 的五子任务对抗评审否决了会产生触发冲突的重复引擎；本项目采用同样的范围划分。

## P6, Visible degradation > silent decay · 可见的退化优于隐形的腐烂

Reflect a source's changed status wherever it is recommended: the domain shard,
tool document and report. Rakuten's termination of Honey on 2026-01-12 is an example
of a trust change that these surfaces must carry. A reader needs the status to
decide whether to use that source.

Configuration and retention apply the same evidence distinction. PRIVATE storage
establishes a boundary, while each artifact's role determines retention. Local
readiness checks do not establish live integration. [CONFIG.md](CONFIG.md) and the
source contracts define exact ownership and lifecycle.

> 来源状态变化须同步到方向分片、工具文档和报告，使读者能够判断是否继续使用。
> 2026-01-12 Rakuten 终止 Honey 合作属于需要同步的信任变化。配置与保留也须区分证据：
> PRIVATE 说明存储边界，产物用途决定保留规则，本地配置检查不能证明线上集成可用。

---

## P7, Load budget is a design constraint · 加载预算是设计约束

`SKILL.md` is loaded on every invocation; references are loaded only when needed.
Keep required rules and checks in SKILL, and put detailed procedures, rationale and
failure examples in the relevant reference. Avoid duplicate prose that can drift.

A prior change grew SKILL from 291 to 422 lines (+45%) by adding narrative already
present in references. The placement test is whether SKILL remains correct and
actionable without the reference, and whether removing a paragraph leaves its rule
enforceable. Move explanation, while retaining any necessary rule and stable cited IDs.

Keep an invariant in the main file when omitting it would reintroduce the failure
the skill prevents. Keep troubleshooting branches beside the steps where they are
needed. A small skill may appropriately remain one file when every run needs every line.

Measure loading per run before restructuring. A reviewed 33-file tool directory
had distinct routing, registry and per-tool duties; merging it would add runtime
loading without reducing duplication. File count alone is not a loading measure.

## How these apply to shopping-aggregator specifically

| Principle | Concrete consequence in this repo |
|---|---|
| P1 | Landed-cost ranking primitive (not sticker); structured evidence unit schema mandates it |
| P2 | Snapshot timestamp + stock state + landed cost are SCHEMA fields, not documentation reminders |
| P3 | `⚠ Avoid` tombstones for dead tools (Honey, PA-API, The Tracktor), never silent delete |
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

Review each answer against the corresponding principle before accepting the change.
