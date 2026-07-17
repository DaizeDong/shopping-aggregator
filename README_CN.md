# shopping-aggregator

把任意购买意图分流到 13 个购物 domain，按到手价（而非标价）排序，再把多源同时抓价的重活交给你已有的 research harness。

[![Claude Code Skill](https://img.shields.io/badge/Claude%20Code-Skill-orange?style=flat)](https://docs.anthropic.com/en/docs/claude-code)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![数据源矩阵](https://img.shields.io/badge/%E6%95%B0%E6%8D%AE%E6%BA%90%E7%9F%A9%E9%98%B5-13%20domains-green?style=flat)](skills/shopping-aggregator/reference/sources-index.md)
[![数据表](https://img.shields.io/badge/%E6%95%B0%E6%8D%AE%E8%A1%A8-%E7%A8%8E%20%7C%20%E5%85%B3%E7%A8%8E%20%7C%20FX%20%7C%20%E8%BF%90%E8%B4%B9-green?style=flat)](skills/shopping-aggregator/reference/data/README.md)
[![语言](https://img.shields.io/badge/%E8%AF%AD%E8%A8%80-EN%20%2F%20CN-blue?style=flat)](#语言)
[![Roadmap](https://img.shields.io/badge/Roadmap-v0.4.0-purple?style=flat)](ROADMAP.md)

[English](README.md) | [中文版](README_CN.md)

---

## ⭐ 先读这里, 设计理念

shopping-aggregator 继承 market-intel 的统领原则,**从根本进行设计，而非小修小补**：出问题
就改它底下的假设，而不是补它表面的症状。把这个原则套到「消费购物」场景上，催生了下面这些
shopping-specific 决定：

- **Landed cost（到手价）而非标价**,标价排序是陷阱（Amazon Prime 包邮 vs eBay $15 运费会
  翻盘冠军）。我们把"到手价"作为排序原语。
- **快照时间戳必填**,价格按小时变（Amazon Buy Box）。没时间戳的价 = unverified。
- **优惠码必须走购物车实测**,扩展的"已节省 $X"是有名的造假面（Honey 案）。我们用 playwright
  实测购物车，或标 ⚠ 未核实。
- **2026 Honey ≠ 默认推荐**,2026 年 1 月 Rakuten/Impact/Awin 接连切断 Honey 联盟网，
  信任格局已变。skill 主动 surface 这点。

📜 **[完整设计理念 → PHILOSOPHY.md](PHILOSOPHY.md)**。

### 姊妹 skill, 何时用谁

`shopping-aggregator` 是更广义 market-research 工具集
[`market-intel`](https://github.com/DaizeDong/market-intel) 的**消费购物特化分支**。

| 你的问题 | 用哪个 |
|---|---|
| "X 在哪里买最便宜，对比各零售商" | **shopping-aggregator（本仓库）** |
| "这价划算吗，要不要等促销，历史最低多少" | **shopping-aggregator** |
| "X 这个品类调研一下，玩家有哪些，趋势如何" | [**market-intel**](https://github.com/DaizeDong/market-intel) |
| "找搬砖/FBA/批发机会（卖家侧）" | [**market-intel**](https://github.com/DaizeDong/market-intel) → `ecommerce-arbitrage` shard |
| "X/Twitter 舆情、SEO 调研、获客" | [**market-intel**](https://github.com/DaizeDong/market-intel) |

两个 skill 可以共存，各自的编排逻辑会管自己的边界。

---

## 它是什么（和不是什么）

为**消费级购物比价**设计的轻量编排 skill。把你的购买意图（商品 + 地区 + 预算 + 紧迫度）分流到正确的
比价数据源（并指导你安装），然后把比价的"重活",多源同时抓价、历史核查、对抗式校验,交给你
已有的 research harness 去做，而**不重复造轮子**。

Claude Code 有 `deep-research` 通用研究框架、`research-lit` 学术文献，以及 `market-intel`
通用商业调研。但当问题变成「我要买 X, 帮我找最优价」时,这是消费工作流，有自己的数据源
（Keepa、Camelcamelcamel、慢慢买）、自己的标准化（到手价、汇率、税费、运费、优惠码）、自己
的信任模型（每家零售商内部的店铺/卖家分层）、自己的时间轴（Buy Box 按小时轮换）,前面那些
都不够用。

`shopping-aggregator` 就是填这个空白的薄层。它**只做三件别人不做的事**，其它全部委托：

1. **解析购买意图**, 商品 + 地区 + 预算 + 紧迫度 + 敏感项 → triage 到 13 个购物 domain 的 1-N 个，
   **并映射到需求侧 channel class**（让无工具的授权零售商,如 Micro Center,不再结构性隐形）。
2. **检测 + 引导安装**, `claude mcp list` 查哪些专业购物 MCP/扩展/OSS 已连上；缺关键源时给
   出确切安装命令，并指向**每工具一文档**
   ([`reference/tools/`](skills/shopping-aggregator/reference/tools/index.md))。
3. **质量护栏**, 时间戳、库存状态、到手价（非标价）、优惠码购物车实测、零售商信任分层、
   不准默默降级、强制反向搜索、surface 分歧、明确空白。

实际的多源 fan-out、历史查询、对抗校验、引用合成都**委托给** playwright MCP / BigGo MCP /
Keepa MCP / `deep-research` / `market-intel`。无重复造轮。

---

## 安装

```
/plugin install github:DaizeDong/shopping-aggregator
```

或手动克隆：

```bash
git clone https://github.com/DaizeDong/shopping-aggregator.git ~/.claude/plugins/shopping-aggregator
```

---

## 60 秒上手

你说：

```
对比 Bose QC45 在美国各零售商的价格，二手翻新可接受，预算 $200 以内，不急，
该不该等促销？
```

会发生：

1. **解析意图** → 商品: Bose QC45（refurb OK）; 地区: US; 预算 $200; 紧迫度: 低。
2. **Triage** → 命中 `amazon-us`, `ebay-walmart-target`, `browser-extensions`（优惠码叠加）,
   `mobile-apps-aggregators`（Slickdeals 等不等促销信号）；选 standard depth。
3. **检测** → 跑 `claude mcp list`；playwright 已连，BigGo MCP 未连，无 Keepa 订阅；记空白。
4. **引导安装**（不阻塞）→ "Camelcamelcamel 免费可看 Amazon 历史；高频购物推荐 Keepa MCP
   €49/月；本次先用 Camelcamelcamel + playwright 跑各零售商"。
5. **委托** → fan-out subagents：playwright on amazon.com / amazon WHD / ebay / Walmart /
   Best Buy / Target；一个 Camelcamelcamel 查历史；一个 Slickdeals 看有无社区帖；一个反向
   搜索 subagent 查"翻新假冒/DOA"投诉。
6. **护栏** → 独立 verifier 重抓价；用 NJ 销售税 6.625% + Prime ship vs flat ship 算到手价；
   playwright 购物车实测"$10 off"码；如果 Buy Box 在两次快照间轮换，surface 价格区间；反向
   搜索若发现"BoseRefurb on eBay 近 90 天多次 DOA 报告"，标"不推荐"。
7. **报告** → 按到手价排名表 + 历史备注（"距 90 天低 $X，黑五历史平均跌 25%"）+ 优惠码列表
   （✓/⚠/✗）+ 风险与反向证据 + 覆盖空白（Costco 需登录跳过）+ 完整出处。

### 数据源矩阵（13 个 domain）

知识资产。每个 domain shard 写明最佳工具、它的**信息壁垒路线**、如何检测、如何安装。

| Domain | 推荐源（壁垒路线） |
|---|---|
| [amazon-us](skills/shopping-aggregator/reference/domains/amazon-us.md) | playwright ④ + Camelcamelcamel ① 免费（+ Keepa ① 付费 看历史） |
| [ebay-walmart-target](skills/shopping-aggregator/reference/domains/ebay-walmart-target.md) | eBay Browse API ① 免费 + playwright ④ |
| [auction-resale](skills/shopping-aggregator/reference/domains/auction-resale.md) | eBay Sold SERP ④ 免费（`LH_Sold=1`）+ StockX API ①（需审批）/ playwright ④ 跑 GOAT/Whatnot/Poshmark/Mercari/Depop/ThredUp |
| [taobao-tmall](skills/shopping-aggregator/reference/domains/taobao-tmall.md) | 慢慢买 ④ + 购物党 ④ |
| [jd-pdd](skills/shopping-aggregator/reference/domains/jd-pdd.md) | 慢慢买 ④ + 京东价保 ① + 购物党 ④ |
| [browser-extensions](skills/shopping-aggregator/reference/domains/browser-extensions.md) | Capital One Shopping ① + Karma ①（⚠ 2026 卸载 Honey） |
| [mobile-apps-aggregators](skills/shopping-aggregator/reference/domains/mobile-apps-aggregators.md) | Slickdeals + Flipp + 什么值得买 |
| [ai-shopping-assistants](skills/shopping-aggregator/reference/domains/ai-shopping-assistants.md) | Perplexity Shopping Pro |
| [claude-mcps](skills/shopping-aggregator/reference/domains/claude-mcps.md) | BigGo MCP ④ 免费 + Apify price-intelligence ② 付费 |
| [oss-self-host](skills/shopping-aggregator/reference/domains/oss-self-host.md) | pricebuddy（西方）+ PriceDive（中国唯一新鲜多平台） |
| [grocery-cpg](skills/shopping-aggregator/reference/domains/grocery-cpg.md) | Flipp ① 周报 circular + 商超会员 App ① 忠诚度（playwright ④ 跑 Instacart 实时购物车）,超本地化，先钉 ZIP+banner |
| [cross-border](skills/shopping-aggregator/reference/domains/cross-border.md) | Superbuy ④ + Stackry/MyUS ④ + YesStyle ④（关税数字见 `data/cross-border-duty.json`，CBP 为准） |
| [hotel-travel](skills/shopping-aggregator/reference/domains/hotel-travel.md) | Booking.com ④（Genius 常为最低公开价）→ 开到 Your-Details 页后把付款交给用户；Google Hotels ④ 仅做发现（锁日期）；机票/租车/火车不在范围 |

**壁垒路线：** ① 官方 · ② 转售 · ③ 自托管爬虫 · ④ **浏览器自动化 / 模拟人**（消费实时价首选）。

三级 install 文档：
[`install-guide.md`](skills/shopping-aggregator/reference/install-guide.md) (L0 机制) →
[`pricing-install.md`](skills/shopping-aggregator/reference/volatile/pricing-install.md) (L1
每域命令) →
[`tools/<slug>.md`](skills/shopping-aggregator/reference/tools/index.md) (L2 每工具)。

---

## 如何触发

它在如下短语下自动激活：`比价`、`查历史价`、`全网最低价`、`X 在哪里买便宜`、`凑单`、
`compare prices for X`、`cheapest place to buy`、`is this a good deal`、`should I wait for a sale`。
广义商业调研让位给 [`market-intel`](https://github.com/DaizeDong/market-intel)，单事实查询直接
打开页面就好。

手动重扫矩阵（扩展失联盟网、API 死亡、OSS 仓库停更）：触发 `刷新比价工具库` /
`refresh the shopping-aggregator source matrix`。[refresh 协议](skills/shopping-aggregator/reference/refresh-protocol.md)
每月扫一遍（每域一个 subagent → 结构化 diff → 增量编辑 shard → `CHANGELOG.md` + 版本号）。默认**每月**；
浏览器扩展和 AI 助手 domain 周级。

---

## 示例输出

一次运行最终产出一张按到手价排名的报告。塑造它的质量护栏（购物特有，合成时强制执行，详见
[`SKILL.md`](skills/shopping-aggregator/SKILL.md)）：

- **快照时间戳必填**, 每条价格挂 `[fetched YYYY-MM-DD HH:MM TZ]`。
- **库存状态是价格的一部分**, 缺货 $X ≠ 现货 $X+5。
- **到手价，不是标价**, 运费 + 税 + 券 - 返利。
- **优惠码购物车实测**, 实测，不信扩展的"已节省"徽章。
- **零售商信任分层** `seller_tier` L1 first-party → L5 不可验证；L4/L5 不能排冠军。
- **证据等级先于卖家层级闸门排名**, `evidence_grade` E1（实读 PDP/API）· E2（聚合器）· E3（片段/跨模型线索）；
  只有 E1 实读能当排名冠军，干净域名也不能把片段升级。
- **卖家身份而非域名**, 零售商域名下挂着第三方市场卖家；盖 first-party(L1) 前必须读 `Sold by` / `Shipped by`。
- **变体钉死**, `variant_key`（品牌|型号|配色|捆绑|成色）；不同变体 = 不同 SKU，绝不当一个比。
- **覆盖地板**, 在场却从未查的渠道类 = 显式 `coverage_gap`，不许静默遗漏；确定性不变量由 `tools/verify_matrix.py` CI 强制。
- **不准默默降级**, Keepa 没用时回退 playwright 要明确告知"历史数据缺失"。
- **跨快照分歧不平均，重抓**, Buy Box 会换。
- **反向搜索强制**, 假冒/DOA/欺诈关键词。
- **失败必须列空白**, 不许藏漏掉的零售商。
- **联盟链接披露追踪**, 扩展的"savings"不入排名权重。

---

## 限制

`shopping-aggregator` 是薄编排层，不是价格引擎,它在设计上就有结构性边界：

- **不重复造抓取引擎**, 多源实时抓价、历史查询、对抗校验都委托给 playwright / BigGo / Keepa /
  `deep-research` / `market-intel`。若都没连上，skill 引导安装而不自己抓。
- **矩阵会腐烂**, 扩展失联盟网（Honey/Rakuten 2026-01）、API 死亡（PA-API 2026-05-15）、OSS
  仓库停更。新鲜度由 refresh 协议维护，并非时时保证。
- **登录墙零售商**（如 Costco）报为显式覆盖空白，不静默遗漏，但不自动抓取。
- **非卖家侧/搬砖工具**, FBA / 批发 / 市场调研请用
  [`market-intel`](https://github.com/DaizeDong/market-intel)。
- **不自动下单**, skill 产出推荐，下单由你点。

剩余路线缺口：demo 对话 + 与替代品对比文档（v0.5 打包质量），heartbeat issue 自动关闭 +
discovery-state 日志（v0.3 闭环）。详见 [ROADMAP.md](ROADMAP.md)。

---

## 语言

English ([`README.md`](README.md)) · 中文 (`README_CN.md`)

---

## Roadmap · 贡献 · 许可

见 [ROADMAP.md](ROADMAP.md) · [CHANGELOG.md](CHANGELOG.md) · [LICENSE](LICENSE)（MIT）。

姊妹 skill：[market-intel](https://github.com/DaizeDong/market-intel), 广义商业研究 / 卖家侧情报。
