# Tool: 购物党 (gwdang)

- **Domain(s):** taobao-tmall, jd-pdd, browser-extensions
- **Barrier route:** ④ · **Source tier:** L2 · **Ready MCP:** no
- **Cost:** 免费（返利变现）
- **Repo / Provider:** gwdang.com · Chrome 扩展 chromewebstore.google.com/detail/jgphnjokjhjlcnnajmfjlacjnjkhleah
- **Top pick for its domain:** yes alongside 慢慢买 — **扩展端的事实标准**

## What it does / when to pick it
**国内浏览器扩展端的事实标准**。覆盖 100+ 平台（淘/天/京/亚马逊/苏宁/当当 等），实时找券 + 180 天历史价 + 跨店比价 + 自动返利。Manifest V3 化已完成（2025-04 更新到 v5.16+），适配淘/京新版页面。Pick alongside 慢慢买：扩展看实时找券、App 看历史价。

## Install
Chrome 网上应用店 / Edge 扩展中心 / Firefox 附加组件 搜「购物党」→ 添加。免费使用，账号可选（返利提现需账号）。

## Auth / keys
免费、可匿名使用。返利提现需账号绑定支付宝/微信。

## Usage — call examples
- **用户**：装好后访问淘宝/京东商品页 → 扩展自动弹「全网比价 / 历史价 / 优惠券」浮窗。
- **agent**：扩展本身没有 API；agent 路径是 **playwright + 模拟扩展数据接口**（不推荐——直接用 manmanbuy.com 后端更稳）。

## General experience & gotchas (踩坑)
- **历史价 180 天**——比慢慢买的全程数据短。**深历史**用慢慢买、**实时找券+界面集成**用购物党。
- **广告多**——返利变现是它的商业模式，扩展会注入推广位/弹窗。隐私敏感用户慎用。
- **拼多多支持有限**——和慢慢买一样的 PDD 限制。
- **自动返利**——通过它的链接下单可以拿一小笔返利（1-5%），但 cookie 必须不被其它扩展覆盖；同时装 Honey / Capital One Shopping 等会抢 affiliate 链接。**对国内用户主要是 Karma 等海外扩展同时装时的问题。**
- **跨店满减 / 凑单**有专门面板——比官方的更易看。
- **优惠券是混合来源**（官方+第三方分发），偶尔失效。下单前应在购物车确认实际抵扣。

## Failure signals & fallback
扩展弹窗显示「无历史价」、找券面板空——平台改版/反爬升级。**Fallback:** 慢慢买（数据更全）、什么值得买（社区分享的码）。

## Last verified: 2026-06
