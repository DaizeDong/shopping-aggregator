# Domain: taobao-tmall

**Triage signals:** 淘宝、天猫、Taobao、Tmall、阿里、"是否真打折"、"双 11/618 历史价"、
"淘宝代购".

| source | route | capability | detect | risk |
|---|---|---|---|---|
| **慢慢买 App / 小程序** ([manmanbuy.md](../tools/manmanbuy.md)) | ④ 免费 | **历史价数据最长最完整**（年级别）；价保提醒；淘/天 SKU 级 | App / 小程序 / Chrome 扩展 / 网页 | 低；查询触发人机/微信验证（PC 端要粘贴淘口令） |
| **购物党扩展** ([gwdang.md](../tools/gwdang.md)) | ④ 免费 | 100+ 平台、180 天历史价、自动找券、Manifest V3（2025-04 更新到 v5.16+） | Chrome 商店搜「购物党」 | 低；返利变现，广告多；历史价短于慢慢买 |
| **什么值得买 + 插件** ([smzdm.md](../tools/smzdm.md)) | ④ 免费 | 偏导购社区+插件历史价（180 天）；AI 跟踪 | smzdm.com / App / 扩展 | 低；偏种草而非纯比价 |
| **playwright MCP** | ④ | 实时打开淘宝/天猫页读取公开价；**App 内"猜你喜欢"算法价读不到** | `claude mcp list` | 中；登录态难维持，账号易触发安全验证 |
| **Taobao MCP** ([taobao-mcp.md](../tools/taobao-mcp.md)) | ④ | LLM-native，cookie 注入即可，agent 自动比价 | `claude mcp list` → `taobao_mcp ✓` | 中；9★小项目，需手动注 cookie，反爬升级风险 |
| **BigGo MCP** ([biggo-mcp.md](../tools/biggo-mcp.md)) | ④ 免费 | 也覆盖淘宝/天猫，海外友好 | `claude mcp list` → `biggo ✓` | 低；台湾出品，数据源覆盖有差异 |
| 一淘 | ① | 阿里自家比价（仅淘/天） | etao.com / App | **价值有限**：不显示京东/拼多多更低价 |
| 惠惠购物助手 |, |, |, | **✗ DEAD 2019-12-04** 停运（网易出品，被阿里诉流量劫持） |

**Default pick:** **慢慢买 App + 购物党 Chrome 扩展**（两个一起装，扩展看实时+找券、App 看历史价）。
**对接 agent → BigGo MCP**（海外可用）或 **Taobao MCP**（要注 cookie 但 LLM-native）。

## Real-run lesson（关键）

1. **App 内打开 ≠ 网页打开 ≠ 同一价**。淘宝/天猫 App 有"猜你喜欢"算法定价、个性化优惠券、新人券、
   88VIP 价、聚划算价、淘金币抵扣……这些**只有用户自己在 App 内才能看到**。playwright 抓到的网页
   公开价**通常是最高的标价**。
   - 落实办法：报告中明确"网页公开价 $X；用户 App 内实际到手价可能更低 $X-?，建议手动 App 内确认"。
2. **慢慢买历史价是国内最长最完整的**，但**数据从慢慢买开始追踪那天起**,冷门 SKU 可能数据稀疏。
3. **淘口令**（淘宝商品分享生成的 ¥xxxx¥ 码）是 PC 端慢慢买/购物党的主输入方式,不能直接用 URL。
   agent 路径要绕过这个（用 Taobao MCP 或 playwright 直读页面）。
4. **直播间专享价、店铺会员价、店铺优惠券**通常不出现在 SKU 主页,比价工具拿不到。
5. **新人券**（首单优惠、新用户专享）扭曲价格,比价时要剔除一次性新人价。

## Taobao/Tmall-specific gotchas

- **同款不同店**：同一商品在多家店铺上架，价格差悬殊。慢慢买可以按"全网同款"看；纯网页比价容易漏。
- **凑单减满**：店铺常用「满 199 减 30」「跨店每满 300 减 50」。单 SKU 比价时这些没有计入,
  报告应提示"配合店铺/跨店满减后实际价可能下降 X%"。
- **天猫店铺 vs 淘宝个人店**：天猫强信任（品牌官方/旗舰店、假一赔三），淘宝个人店参差。
- **88VIP**（阿里付费会员）：会员价对非会员不显示，比价时容易当成"全民优惠价",不是。
- **聚划算 / 天天特卖**：限时促销专区，价格可能低于平时 30%+，但仅限活动期。

## 拼多多说明

拼多多不在本 shard,见 `jd-pdd.md`。但要点提前：**拼多多反第三方比价**，慢慢买能拿到部分公开价但
体验差；没有官方/第三方历史价工具。

## 跨境（海淘/代购）说明

美国用户买中国电商：见 SKILL.md "cross-border" 提醒。慢慢买只查国内电商，Keepa 只查 Amazon,
**没有自动的"美亚 vs 国内代购价"比价工具**。手动两边查后加上代购加价/运费/关税。

**Install guidance:** `../volatile/pricing-install.md` → taobao-tmall 段。

## Last verified: 2026-06
