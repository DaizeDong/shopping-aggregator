# Tool: 小红书 (Xiaohongshu / RED / RedNote)

- **Domain(s):** taobao-tmall, jd-pdd, mobile-apps-aggregators
- **Barrier route:** ④ login-walled UGC · **Source tier:** L4（种草/评测信号源，**非价格源**） · **Ready MCP:** no
- **Cost:** 免费浏览（需账号）
- **Repo / Provider:** xiaohongshu.com / RedNote App · 官方商业合作走蒲公英 pgy.xiaohongshu.com
- **Top pick for its domain:** **no — 这是"值不值得买"的评测/口碑源，不是"哪里最便宜"的比价源**

## What it does / when to pick it
**生活方式 + 产品种草/测评社区**（2013 起家时就是海淘产品评测平台，现为 Instagram+Pinterest+Amazon 混合体，月活 3 亿+，用户偏年轻女性、美妆/穿搭/护肤/旅行/数码）。它在本 skill 的角色是**评测/口碑信号**——回答「这个产品好不好用 / 有没有更值的替代 / 真实使用体验」，**不回答「现在哪里最便宜」**。

**何时调它**：用户问「X 值不值得买」「Y 和 Z 哪个好」「有没有人长测过」时，小红书 + 什么值得买评测板 + 知乎 一起作为口碑佐证。**何时不调**：任何需要价格/历史价/到手价的环节——小红书**没有消费级价格 API、不给历史价、笔记里的「价格」是博主下单时的旧价或软广报价，不可作为定价证据**（evidence_grade 顶多 E3 lead，永不进价格 ranking，见 CONSTITUTION I.3）。

## Install
- **App**: App Store / Google Play 搜「小红书」或「RedNote / rednote」。境外可用，邮箱或国际手机号 / Apple / Google 登录，海外账号一般免实名。
- **网页**: xiaohongshu.com（功能大幅阉割，核心能力在 App）。
- **无官方浏览器扩展**（Chrome Web Store 无第一方小红书比价/价格扩展可核验——它不是浏览器扩展类工具，故无 tombstone 适用项）。

## Auth / keys
**login-walled**：匿名访问受限，搜索/看完整笔记/评论基本要登录态。**无开放的消费/价格 API**——小红书开放平台/企业号 API 权限集中在**广告投放与数据报表**（卖家侧），不向第三方开放笔记内容或价格查询。**蒲公英**(pgy.xiaohongshu.com) 是官方 KOL 合作/报备平台（品牌投放用），同样不是数据查询接口。

## Usage — call examples
- **用户**：App 内搜产品名 → 看测评/避雷笔记 + 评论区真实反馈 → 形成「值不值」判断。
- **agent**：**首选让用户在 App 内自查**。WebFetch `https://www.xiaohongshu.com/search_result?keyword=<kw>` 反爬极强（风控系统对 IP 频率/设备指纹/行为轨迹多维检测，简单 HTTP 请求易触发验证码甚至封号），通常拿不到稳定结果。第三方逆向/爬虫工具非官方授权、违反用户协议且封号风险高——**不在 skill 内集成**。只把小红书当**人工口碑佐证源**，不做自动化抓取。

## General experience & gotchas (踩坑)
- **⚠ 非价格源**——这是本 doc 的头号铁律。笔记里的价格、链接、「神价」都不可信作定价；定价永远回到比价工具 + 平台实时页。
- **⚠ 软广/恰饭极多**——海量笔记是**报备(蒲公英)或非报备合作**的软广。报备合作**带广告标识**（可据此识别）；非报备软广**故意不标、伪装成素人测评**最难辨。看到「无限回购」「闭眼入」「平价替代」高赞笔记，默认先怀疑是软广，交叉核验。
- **种草 ≠ 客观**——好评样本偏正向（恰饭 + 幸存者偏差）；**专门搜「<产品> 避雷 / 翻车 / 缺点 / 智商税」**才能拿到负面信号，单看默认流会高估产品。
- **login-walled + 反爬**——别做大批量 fan-out 抓取，会触发风控/封号；交给用户手动。
- **内容审核/地域**：受中国法规与社区公约约束，敏感话题受限；2025 年起对境内外用户做了分流。
- **界面以中文为主**，海外用户可借翻译；但测评语境（成分/型号/口碑黑话）机翻易失真。

## Failure signals & fallback
搜索空结果、被风控/验证码拦、笔记 404、满屏疑似软广无可信测评。**Fallback:** 什么值得买（评测板更严谨、报备更透明）、知乎（更长篇深度评测）、B站测评、海外用 Wirecutter/Reddit。**价格永远不找小红书要**——价格 fallback 见 `reference/domains/` 各价格源（慢慢买/购物党/playwright）。

## Last verified: 2026-06
