# shopping-aggregator

在 14 个购物方向中比较购买方案，按已核验的结账总价排序，并把来源采集交给已有调研流程。

[![Claude Code Skill](https://img.shields.io/badge/Claude%20Code-Skill-orange?style=flat)](https://docs.anthropic.com/en/docs/claude-code)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![数据源矩阵](https://img.shields.io/badge/%E6%95%B0%E6%8D%AE%E6%BA%90%E7%9F%A9%E9%98%B5-14%20domains-green?style=flat)](skills/shopping-aggregator/reference/sources-index.md)
[![数据表](https://img.shields.io/badge/%E6%95%B0%E6%8D%AE%E8%A1%A8-%E7%A8%8E%20%7C%20%E5%85%B3%E7%A8%8E%20%7C%20FX%20%7C%20%E8%BF%90%E8%B4%B9-green?style=flat)](skills/shopping-aggregator/reference/data/README.md)
[![语言](https://img.shields.io/badge/%E8%AF%AD%E8%A8%80-EN%20%2F%20CN-blue?style=flat)](#语言)
[![Roadmap](https://img.shields.io/badge/Roadmap-v0.10.0-purple?style=flat)](ROADMAP.md)

[English](README.md) | [中文版](README_CN.md)

---

## 设计理念

购物比价需要固定商品变体，核实当前库存、卖家身份和完整结账价。运费、税费、关税和已核验优惠
都可能改变排名；延迟返利有条件，单独列出。Amazon Buy Box 等报价会频繁变化，因此每条价格
都需要快照时间。

优惠码要经购物车测试，否则标为未核实。Honey 案及 2026 年 1 月 Rakuten、Impact、Awin
终止合作的记录属于来源信任评估的一部分，Honey 不作为默认推荐。证据要求可能使部分报价无法
排名，覆盖也可能不完整；报告应保留这些限制。

设计原则及其在购物中的应用见 [PHILOSOPHY.md](PHILOSOPHY.md)。

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

两个 skill 可以同时安装，分别处理各自范围内的请求。

---

## 适用范围

本 skill 使用 Keepa、Camelcamelcamel、慢慢买等购物来源，结合成本标准化和平台卖家核验，
支持消费者的购买决策：

1. **解析意图：** 根据商品、地区、预算、紧迫度和敏感项，确定相关购物方向与需求侧渠道类别。
   即使零售商没有专用工具，例如 Micro Center，也要纳入覆盖计划。
2. **选源与配置：** 在当前宿主中发现工具并完成一次功能性读取。缺少 MCP、扩展或开源工具时，
   查阅[逐工具文档](skills/shopping-aggregator/reference/tools/index.md)。`claude mcp list`
   是 Claude 的安装诊断，连接指示本身不能证明来源可用。
3. **证据要求：** 核验价格、库存、变体、卖家、时间和优惠，再报告冲突、风险和缺少的渠道。

实时采价、历史查询和验证使用当前可用的 playwright MCP、BigGo MCP、Keepa MCP、
`deep-research` 或 `market-intel` 能力。

---

## 安装

```
/plugin install github:DaizeDong/shopping-aggregator
```

或手动克隆：

```bash
git clone --recurse-submodules https://github.com/DaizeDong/shopping-aggregator.git ~/.claude/plugins/shopping-aggregator
```

命令行工具需要 Guards 子模块提供的解析器。如果已有克隆或插件安装缺少
`guards/tools/datadir.py`，请在插件目录执行 `git submodule update --init --recursive`。
随后运行 `python tools/refresh_priority.py --help` 和 `python tools/scenario_eval.py`
检查安装；后一条命令只输出离线评估计划。

---

## 配置

每位买家长期不变的事实（购买市场、收货邮编和州、会员、礼品卡这类储值、哪些零售商允许代理下单、默认购买方式）存在私有伴生仓里的一个**配置根**里，运行时记的两本账（观测记录和购买记录）也写在那里。每个文件、每个字段都由 [CONFIG.md](CONFIG.md) 定义，schema 以外的地方一律不存：不进代理的记忆，也不写成脚本里的默认值。

```bash
python scripts/init_config.py        # 找到伴生仓；找不到就创建 ~/.shopping-aggregator-config
python scripts/verify_config.py      # 体检：打印选中的配置根；profile 没填完就报 NOT READY
```

查找顺序：先看 `--config-dir`（初始化时是 `--out`），再看 `$SHOPPING_AGGREGATOR_CONFIG`（别名 `$SHOPPING_AGGREGATOR_CONFIG_DIR`），最后按锁定版本的 `guards/tools/datadir.py` 找，依次是 `$SHOPPING_AGGREGATOR_DATA_DIR`、本仓旁边的 `shopping-aggregator-config/`、`~/.shopping-aggregator-config`、`~/.shopping-aggregator-data`。如果还留着 `SHOPPING_AGGREGATOR_DATA_DIR`，它必须正好指向选中配置根的 `data/`，否则体检不通过。配置根必须先放进有版本管理的私有仓，才能写入真实信息。

切换到另一个人：把 `SHOPPING_AGGREGATOR_CONFIG` 指向这个人的配置根，或者把对方放在 `<伴生仓>/people/<id>/` 下再选中这个目录。对方的 profile、购买记录和观测记录会一起切过去，每份报告都会写明用的是哪个 `profile_id`。`--config-dir` 只对它所在的那一条 `scripts/` 命令生效，`tools/` 下的命令只认环境变量。完全没有配置也能比价，Step 1 会照旧在对话里逐项询问，只是不会替你点下单，最后一步交给你自己。

个人目录遵守 [CONFIG.md 的保留规则](CONFIG.md#storage-lifecycle)：购买与观察记录是核心数据，
缓存沿用七天的可重建规则，评估记录保留选定证据。未知个人目录文件没有声明的所有者；
原生生命周期适配器见 [config.contract.json](config.contract.json)。

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
3. **检测** → 在当前宿主发现来源，再核验所选读取操作、认证和可用响应正文。仅显示已连接不能证明可用；BigGo 无法访问或缺少 Keepa 订阅时仍记覆盖空白。
4. **引导安装**（不阻塞）→ "Camelcamelcamel 免费可看 Amazon 历史；高频购物推荐 Keepa MCP
   €49/月；本次先用 Camelcamelcamel + playwright 跑各零售商"。
5. **委托** → fan-out subagents：playwright on amazon.com / amazon WHD / ebay / Walmart /
   Best Buy / Target；一个 Camelcamelcamel 查历史；一个 Slickdeals 看有无社区帖；一个反向
   搜索 subagent 查"翻新假冒/DOA"投诉。
6. **护栏** → 独立 verifier 重抓价；按 profile 收货州的销售税 + 会员包邮 vs 固定运费算到手价；
   playwright 购物车实测"$10 off"码；如果 Buy Box 在两次快照间轮换，surface 价格区间；反向
   搜索若发现"BoseRefurb on eBay 近 90 天多次 DOA 报告"，标"不推荐"。
7. **报告** → 按到手价排名表 + 历史备注（"距 90 天低 $X，黑五历史平均跌 25%"）+ 优惠码列表
   （✓/⚠/✗）+ 风险与反向证据 + 覆盖空白（Costco 需登录时先交接给用户；用户拒绝或不在时注明原因）+ 完整出处。

### 数据源矩阵（14 个 domain）

每个方向分片记录推荐来源、访问路线、检测与配置方法。

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
| [hotel-travel](skills/shopping-aggregator/reference/domains/hotel-travel.md) | 核实所选房型的总价、税费和取消条款；填写个人及付款信息前交给用户 |
| [air-travel](skills/shopping-aggregator/reference/domains/air-travel.md) | 查找航班，逐个报价卡片读取价格，核实票价档位、行李和退改条款，再独立核验总价；条款不明时不能声称总价最低 |

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
- **按结账价排序：** 标价 + 运费 + 税费 + 关税 - 已核验的结账优惠。延迟返利单独列为有条件的收益，不从排名价格中扣除。
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

- **来源可用性：** 采集依赖适用范围中列出的工具能力。没有可连接来源时，提供配置指引。
- **目录时效：** 扩展可能失去联盟网（Honey/Rakuten 2026-01），API 可能关闭（PA-API 2026-05-15），
  仓库可能停更。刷新协议要求重新核验；目录中存在条目不代表来源当前可用。
- **会话门控访问：** 先完成匿名 S1 工作，再把 S2 渠道合并为一次登录交接。打开登录页后暂停，
  等用户确认再继续。用户负责认证，代理不输入凭据；登录后重跑控制查询，确认内容可用。
  用户拒绝或无人值守时记录带类型的 `session-gated-*` 缺口。
  详见[登录交接](skills/shopping-aggregator/reference/login-handoff.md)。

- **卖家侧范围：** FBA、批发或市场调研使用
  [`market-intel`](https://github.com/DaizeDong/market-intel)。
- **下单授权：** 仅在买家明确逐项指示、且选定 profile 允许代理在该零售商结账时下单。
  仅限零售商品，按完整优惠组合（guardrail #16）购买，在最终页逐条核验后只提交一次。
  酒店和机票仍交给用户；缺少指示或权限时只给推荐，由用户完成购买。

剩余路线缺口：demo 对话 + 与替代品对比文档（v0.5 打包质量），heartbeat issue 自动关闭 +
discovery-state 日志（v0.3 闭环）。详见 [ROADMAP.md](ROADMAP.md)。

---

## 语言

English ([`README.md`](README.md)) · 中文 (`README_CN.md`)

---

## Roadmap · 贡献 · 许可

见 [ROADMAP.md](ROADMAP.md) · [CHANGELOG.md](CHANGELOG.md) · [LICENSE](LICENSE)（MIT）。

姊妹 skill：[market-intel](https://github.com/DaizeDong/market-intel), 广义商业研究 / 卖家侧情报。
