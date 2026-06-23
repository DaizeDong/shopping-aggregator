# Domain: jd-pdd

**Triage signals:** 京东、JD.com、京东自营、拼多多、PDD、Pinduoduo、百亿补贴、"京东价保";
**Temu、SHEIN、希音**（拼多多/SHEIN 的 US-facing 出海前端 — 见下方专段）.

| source | route | capability | detect | risk |
|---|---|---|---|---|
| **慢慢买 App** ([manmanbuy.md](../tools/manmanbuy.md)) | ④ 免费 | 京东/拼多多 历史价（京东数据最完整；拼多多覆盖薄） | App / 小程序 / 扩展 | 低；拼多多 SKU 体验差（深链接被禁） |
| **京东自带价保** | ① 官方 | 7/15/30/180/365 天保价期内自动差价退款；**仅京东自营** | 京东 App / 网页订单详情 | 低；不显示完整历史曲线，只算保价期内差价 |
| **购物党扩展** ([gwdang.md](../tools/gwdang.md)) | ④ 免费 | 京东 SKU 实时找券+180 天历史价 | Chrome 扩展 | 低；拼多多支持有限 |
| **playwright MCP** | ④ | 京东网页公开价直读；**拼多多 SKU 链接打开经常 302 到 App 唤起页**，难抓 | 几乎总连着 | 中；拼多多很难直接抓 |
| 京东开放平台 API | ① | 京东联盟 API 仅给推广位/订单，**无公开价格查询接口** | — | **✗ 非卖家无法用**，京东不开放价格 API |
| 拼多多开放平台 | ① | 仅商家自家数据 | — | **✗ 非卖家无法用** |
| **BigGo MCP** ([biggo-mcp.md](../tools/biggo-mcp.md)) | ④ | 京东覆盖弱，拼多多基本无 | `claude mcp list` | 中；境外项目对国内电商覆盖参差 |

**Default pick:** **京东 → 慢慢买（历史价）+ playwright（实时价）+ 价保（用户在 App 内启用）**；
**拼多多 → 慢慢买（残缺但有总比无好）+ 用户 App 内手动核**。

## Real-run lesson

**拼多多是当下国内电商比价的硬骨头**：
1. 拼多多**主打"百亿补贴"叙事**，刻意反第三方比价工具——SKU 链接在浏览器打开会强制唤起 App，
   抓不到稳定页面。
2. 慢慢买内置的拼多多价格通常滞后或不全。
3. **没有任何 MCP / 第三方 API 能稳定查拼多多**——这是市场空白。
4. 实际操作建议：**让用户自己在拼多多 App 内手动确认价**，比价表里拼多多列标注"用户实时核查"。

## 京东 specific gotchas

- **京东自营 vs 京东 POP 三方**：自营 (`https://item.jd.com/<id>.html`) 物流快、客服稳；POP 三方
  鱼龙混杂。慢慢买/购物党都不直接标识这个——要看页面"由 xx 销售并发货"。
- **价保**是用户买完之后启用的功能：下单后 7/15/30 天内（看品类）系统自动检测降价并退差价。
  **报告应主动提醒**：「京东下单后 X 天内启用价保，如有降价自动退差」。这比比价工具本身价值大。
- **PLUS 会员价**：京东 PLUS 会员专享价，非会员看不到——比价时同样易高估"普惠价"。
- **京东国际**：跨境页面，价格、税费、清关方式都不同；不要和京东自营混。
- **京东优惠券满减叠加**：跨店满减 + 品类券 + 平台券 + PLUS 券，可叠加 4-5 层，**比价工具基本算不准**——
  让用户加购物车看实际结算价是最准的。

## 拼多多 specific gotchas

- **百亿补贴**专区价格通常是平台直补，**非补贴专区同 SKU 价更高**——比价时务必区分是否在百补内。
- **拼单 vs 单买**：拼单价显示在主页，单买价隐藏，差价大。"显示拼单价"≠"用户实际能买到的价"
  （拼不到团就涨回单买价）。
- **新人/老用户砍价/拉新**专属价是引流策略，**不能作为长期参考**——比价时剔除。
- **店铺评分体系不如淘宝/京东成熟**，"售后 7 天无理由"在拼多多落实率参差——trust tier 整体低一档。

## Temu / SHEIN (US-facing) — 拼多多/SHEIN 的出海前端，不是境内 PDD

Temu（PDD 出海）和 SHEIN（希音）是**美国买家**直接遇到的低价前端，与境内拼多多是两套站点/价格/履约。**分工边界（防与 cross-border 重复）**：本段只管 US 本土履约后的可买性/退货/真伪/新人券扭曲；中国直邮的关税/de-minimis/转运 landed-cost 归 [`cross-border.md`](./cross-border.md) + [`../data/cross-border-duty.json`](../data/cross-border-duty.json)，本段不复述税率。核验均 2026-06。

- **已转「美国本土仓 / 本地卖家履约」**：de-minimis 全面暂停后两家备货美仓、境内发货——多数 US 订单**非中国直邮**，按 US 本土零售比价、勿默认套关税；仅当 SKU 标「ships from China / 长时效」才回退 cross-border 叠 landed-cost（[Temu 改本地履约](https://maritimefairtrade.org/temu-halts-shipments-from-china-to-u-s-due-to-trumps-tariffs/)、[de-minimis 仍暂停](https://www.marketplace.org/story/2026/03/03/supreme-court-tariffs-de-minimis-exemption-cheap-imports)）。
- **退货窗口（决策级，常被高估）**：**Temu = 购买日起 90 天**（每单首次退货免运，其后 $7.99；请求后 14 天内须寄出否则作废）；**SHEIN ≈ 30–45 天**（多源记 35），亦每单一次免运。报告须写「从**购买日**算非收货日」——直邮 1–2 周后实际只剩 ~75–80 天（[Temu 政策](https://www.temu.com/return-and-refund-policy.html)、[90 vs 35 天](https://www.purchy.app/blog/temu-return-policy-2026)）。
- **真伪/信任**：均以白牌/工厂直供为主、无品牌授权链——**品牌正品诉求一律不在此采信**（对标 channel-classes 的 brand-direct，trust tier 压到 L4）；SHEIN 版权争议长期、Temu 售后看具体卖家。
- **新人券价格扭曲（最坑）**：「首单价/新人专享/转盘/拉新」是一次性引流价，与境内 PDD 新人/砍价价、百亿补贴 vs 非补贴、拼单 vs 单买同属「显示价≠可持续买到价」——**比价剔新人券、用复购常规结算价**，若引用须标「一次性首单价」。
- **sticker 近期失真**：de-minimis 暂停后两家普涨且把关税并进**显示价**（SHEIN 明示「价含关税」）——勿用旧「地板价」印象锚定。

**Default pick（Temu/SHEIN）：playwright ④ 读 US 站实时结算价（剔新人券）+ 按 US 本土零售比价**；SKU 标中国直邮才转 [`cross-border.md`](./cross-border.md)。退货窗口/真伪写进报告 risks 段。

**Install guidance:** `../volatile/pricing-install.md` → jd-pdd 段。

## Last verified: 2026-06
