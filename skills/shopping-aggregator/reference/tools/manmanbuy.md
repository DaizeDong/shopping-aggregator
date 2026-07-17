# Tool: 慢慢买 (manmanbuy)

- **Domain(s):** taobao-tmall, jd-pdd, mobile-apps-aggregators, browser-extensions
- **Barrier route:** ④ + ① 自营平台 · **Source tier:** L2 · **Ready MCP:** no
- **Cost:** 免费
- **Repo / Provider:** manmanbuy.com, 国内长青老牌
- **Top pick for its domain:** **yes (中国电商历史价数据最长最完整的源)**

## What it does / when to pick it
**国内电商历史价的事实标准**。覆盖淘宝、天猫、京东、拼多多、唯品会、苏宁、网易严选、考拉等 40+ 平台。**数据可追溯至 SKU 上架开始**,比 180-day-only 的 购物党 / 什么值得买 插件深得多。提供：历史价格曲线、降价提醒（按 SKU）、价保查询、淘口令快速比价（PC 端）、跨平台同款。

四端齐全：**App（iOS/Android）+ 微信小程序 + Chrome 扩展 + 网页 manmanbuy.com**,App 端最稳定。

## Install
- **App**: App Store / 各 Android 应用市场搜「慢慢买」。
- **小程序**: 微信内搜「慢慢买」。
- **Chrome 扩展**: chromewebstore.google.com 搜「慢慢买历史价格比价」。
- **网页**: manmanbuy.com 直接使用。

## Auth / keys
免费、可匿名查询。设价格提醒需账号（微信登录最便）。

## Usage, call examples
- **用户**: 复制淘宝/京东商品链接或淘口令 → 粘贴到 App / 小程序 → 看历史曲线 → 设提醒。
- **agent**: 因为没有官方 API，路径是 **playwright fetch `tool.manmanbuy.com/history.aspx?url=<URL编码后的商品页>`**（PC 端历史价查询页）→ 解析返回的曲线 SVG / 数据点。**注意：触发人机验证概率高，必要时让用户在自己的浏览器里查**。

## General experience & gotchas (踩坑)
- **PC 端要粘贴淘口令**（淘宝/天猫的分享码 `¥xxxx¥`）不能直接用 URL,这是反爬措施。agent 路径上要先把 URL 转淘口令（一般是淘宝App生成）。
- **查询频繁触发人机验证 / 微信登录**,大批量 fan-out 不要走这里，用户自己手动查最稳。
- **冷门 SKU 数据稀疏**,如果某 SKU 关注度低，慢慢买可能只追踪了几个月。
- **拼多多覆盖弱**,慢慢买能拿到部分公开页面价但 PDD 反深链接，体验差。
- **App 内"猜你喜欢"算法定价拿不到**,慢慢买只看公开页面价，与 App 内实际到手价可能差不少；最终下单要让用户在 App 内确认。
- **跨店满减、店铺优惠券**不计入,单 SKU 比价时容易高估"显示价"。

## Failure signals & fallback
查询超时、被风控页拦截、"请刷新验证"。**Fallback:** 购物党扩展（180-day 历史价，覆盖与慢慢买高度重合）、什么值得买（社区导向，比价是副业）、用户 App 内手动查。**国内电商的历史价没有真正的替代源**,慢慢买死了就是空白。

## Last verified: 2026-06
