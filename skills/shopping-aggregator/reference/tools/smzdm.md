# Tool: 什么值得买 (SMZDM)

- **Domain(s):** mobile-apps-aggregators, browser-extensions, taobao-tmall, jd-pdd
- **Barrier route:** ① 平台官方运营 · **Source tier:** L2 · **Ready MCP:** no
- **Cost:** 免费
- **Repo / Provider:** smzdm.com — 中国最大的导购/种草社区
- **Top pick for its domain:** yes for **CN deal-discovery + product review**（比价是副业；社区是主业）

## What it does / when to pick it
中国的 Slickdeals + Wirecutter 混合体。三个分层用法：
1. **首页好价 / 海淘 / 免税** 三个栏目：编辑+社区共同发布的折扣帖，比官方促销页更早+更全。
2. **商品评测 / 测评** 板块：买东西前看真实长测，比短视频网红测评严谨。
3. **Chrome 插件 / App 提醒**：跟踪具体 SKU，与购物党/慢慢买重合；优势是和社区帖子联动。

## Install
- **App**: 各 Android 应用市场 / App Store 搜「什么值得买」。
- **网页**: smzdm.com。
- **Chrome 插件**: 官网下载或扩展商店搜「什么值得买」。

## Auth / keys
免费匿名浏览。账号用于点赞/评论/收藏/订阅提醒。

## Usage — call examples
**agent**: WebFetch `https://www.smzdm.com/?s=<keyword>` 拿搜索结果，或 `https://www.smzdm.com/p/<post_id>/` 拿单帖正文 + 评论。**反爬比慢慢买轻**，但对登录态有要求的功能（订阅、点赞）拿不到。

## General experience & gotchas (踩坑)
- **偏种草社区，不是纯比价**——比价是它的工具栏，社区帖才是核心内容。当用户问「值不值得买/有没有更好替代」时，SMZDM 评测板块价值很大；当用户问「现在哪里最便宜」时，慢慢买/购物党更直接。
- **AI 跟踪**：用户可提交 SKU，AI 监控价格 + 召唤相关社区帖。
- **优惠券分类区**码鲜度较好，比某些扩展商店里失效的码更新及时。
- **海淘 / 免税板块**——对跨境用户有专门内容（美亚 → 国内）。
- **广告 / 软推广**——KOL 帖子越来越多，看到「神价好物」要核实是不是软广。
- **「值不值」评级**——社区投票出来的，过去几年质量稳定；但低浏览量帖子的样本噪声大。

## Failure signals & fallback
搜索返回空、单帖 404、被风控页拦截。**Fallback:** 慢慢买（纯比价/历史价方向）、小红书（更偏 lifestyle/护肤/穿搭的种草补充）、知乎（更长篇评测）。

## Last verified: 2026-06
