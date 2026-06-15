# Volatile pricing & install commands (per domain)

> ⚠️ This file is **time-stamped**. Prices and install commands rot fast in this space (PA-API
> died 2026-05-15; Honey lost networks Jan 2026; Apify per-call prices fluctuate). Each section
> below carries `last_verified: YYYY-MM`. **Verify against the official site before quoting**.
> Stale sections get re-checked in the monthly refresh.

## amazon-us

### Keepa (paid, primary history source)
- Cost: €49/mo for 20 tokens/min (base tier), scales upward; €459+/mo for power use.
- Sign up: keepa.com → Dashboard → API tab.
- Install MCP (BWB03 one-click): download `.mcpb` from `BWB03/keepa-adapter` releases → Claude
  imports automatically.
- Install MCP (cosjef stdio): `git clone github.com/cosjef/Keepa_MCP` → edit `~/.claude.json` to
  add stdio server pointing at `python main.py`.
- Restart Claude session.
- `last_verified: 2026-06`

### Camelcamelcamel (free history)
- Web: just visit `camelcamelcamel.com/product/<ASIN>`.
- Camelizer extension: Chrome Web Store search "Camelizer", click Add.
- `last_verified: 2026-06`

### BigGo MCP (free MCP)
- `claude mcp add -s user biggo -- uvx BigGo-MCP-Server@latest`
- Restart session.
- `last_verified: 2026-06`

### Apify price-intelligence MCP (paid)
- Sign up apify.com, free $5/mo credit.
- Get API token from console.apify.com/account/integrations.
- **Do NOT use `claude mcp add`** (echoes token). Edit `~/.claude.json` directly:
  ```json
  "mcpServers": {
    "apify-price-intel": {
      "url": "https://mcp.apify.com/?actor=onetapstudio/price-intelligence-mcp",
      "headers": { "Authorization": "Bearer <YOUR_TOKEN>" }
    }
  }
  ```
- Restart session.
- Cost: $0.008–$0.15 per product per retailer; budget 3-10x for heavy fan-out.
- `last_verified: 2026-06`

### Amazon PA-API 5.0
- ✗ **DEAD as of 2026-05-15**. Replaced by Amazon Creators API (10 affiliate sales / 30d gate).
  Skip for new builds.
- `last_verified: 2026-06`

## ebay-walmart-target

### eBay Browse API (free)
- developer.ebay.com → Register a free account → create application → get Client ID + Secret.
- For production, join eBay Partner Network (EPN) and complete Growth Check (free, ~1-2 weeks).
- OAuth2 client_credentials → Bearer token (2h expiry).
- 5000 calls/day free quota.
- `last_verified: 2026-06`

### Apify price-intelligence MCP (paid)
- See amazon-us section above; same install.
- `last_verified: 2026-06`

### BigGo MCP (free)
- See amazon-us section.
- `last_verified: 2026-06`

### Oxylabs E-Commerce (paid)
- oxylabs.io → sign up → $49/mo trial / ~24.5K requests.
- REST API: `POST https://realtime.oxylabs.io/v1/queries` with HTTP basic auth.
- `last_verified: 2026-06`

### Walmart / Target / Best Buy / Costco direct APIs
- ✗ No usable consumer API. Use playwright MCP per retailer + Apify/Oxylabs for scale.
- `last_verified: 2026-06`

## taobao-tmall

### 慢慢买
- App: App Store / 各 Android 应用市场 搜「慢慢买」→ 装即用。
- 微信小程序: 微信内搜「慢慢买」→ 用即用。
- Chrome 扩展: chromewebstore.google.com 搜「慢慢买历史价格比价」→ Add。
- 网页: manmanbuy.com 直接打开。
- 免费；账号可选。
- `last_verified: 2026-06`

### 购物党
- Chrome 扩展: chromewebstore.google.com 搜「购物党」→ Add（v5.16+ Manifest V3）。
- 免费；返利提现需账号。
- `last_verified: 2026-06`

### 什么值得买 (SMZDM)
- App / 网页: smzdm.com。
- 免费，账号可选。
- `last_verified: 2026-06`

### Taobao MCP (JeremyDong22/taobao_mcp)
- `git clone github.com/JeremyDong22/taobao_mcp && cd taobao_mcp && pip install -r requirements.txt`.
- 启动 stdio MCP，注入登录态 cookie（每 1-2 周需刷新）。
- 编辑 `~/.claude.json` 加 stdio server。
- 重启 session。
- `last_verified: 2026-06`

## jd-pdd

- 慢慢买 / 购物党 / SMZDM 安装同上。
- 京东价保: 登录 京东 App / 网页 → 我的订单 → 价保（下单后启用）；无独立安装步骤。
- PDD: **无第三方比价工具支持** — 用户在 App 内手动核。
- `last_verified: 2026-06`

## browser-extensions

### Capital One Shopping
- Chrome Web Store search "Capital One Shopping" → Add.
- 免费；email 注册可领 rewards。
- `last_verified: 2026-06`

### Karma
- Chrome Web Store search "Karma Save & Earn" → Add.
- 免费；email 注册同步 wishlist。
- `last_verified: 2026-06`

### Coupert
- Chrome Web Store search "Coupert" → Add.
- 免费；email 注册可领 cashback。
- `last_verified: 2026-06`

### ⚠ Honey
- **AVOID 2026** — see `tools/honey.md`. If installed: Chrome → Extensions → Honey → Remove.
- `last_verified: 2026-06`

## mobile-apps-aggregators

### Slickdeals
- App Store / Google Play search "Slickdeals" → Install.
- 免费；账号可选。
- `last_verified: 2026-06`

### ShopSavvy
- App Store / Google Play search "ShopSavvy" → Install (v18.9.40+).
- 免费。
- `last_verified: 2026-06`

### Flipp
- App Store / Google Play search "Flipp" → Install (v99.1+).
- 免费；zip code on first launch.
- `last_verified: 2026-06`

## ai-shopping-assistants

### Perplexity Shopping
- perplexity.ai → 注册账号。
- Pro 升级 $20/mo（含 in-app PayPal checkout，US-only）。
- 无 MCP — 浏览器中使用。
- `last_verified: 2026-06`

## oss-self-host

### pricebuddy
- `git clone github.com/jez500/pricebuddy && cd pricebuddy && cp .env.example .env`
- 编辑 `.env`: LLM provider 选 OpenAI / Anthropic / Gemini / Ollama；填 key。
- `docker compose up -d` → 访问 http://localhost:8080。
- `last_verified: 2026-06`

### PriceGhost
- `git clone github.com/clucraft/PriceGhost && cd PriceGhost && cp .env.example .env`
- 配置 LLM、retailers、alerts。
- `docker compose up -d`。
- `last_verified: 2026-06`

### PriceDive
- `git clone github.com/DAILtech/PriceDive && cd PriceDive && pip install -r requirements.txt`
- `python init_db.py && python tracker.py --add <product_url>`。
- Taobao/Tmall 部分查询需 cookie 注入。
- `last_verified: 2026-06`

### Discount-Bandit
- `git clone github.com/Cybrarist/Discount-Bandit && cd Discount-Bandit && docker compose up -d`。
- `last_verified: 2026-06`

## claude-mcps

See per-MCP sections above (BigGo, Apify, Keepa, Taobao, Oxylabs). All same install pattern;
all require **session restart after add**.
