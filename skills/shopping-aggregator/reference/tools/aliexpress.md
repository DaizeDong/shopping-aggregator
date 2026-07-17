# Tool: AliExpress (Open Platform / Affiliate API + Choice)

- **Domain(s):** ebay-walmart-target (cross-border catalog), oss-self-host (as a data source)
- **Barrier route:** ① official API · **Source tier:** L1 (official API) / L2 (Choice listing data) · **Ready MCP:** no (REST, signed requests; no first-party MCP)
- **Cost:** API **free** (partner program, 2-day approval); product cost = listing price **+ ~35% US import duty** (de minimis ended, see ⚠ tariff note)
- **Repo / Provider:** openservice.aliexpress.com (Open Platform) · portals.aliexpress.com (Affiliate), Alibaba Group
- **Top pick for its domain:** the canonical **official** route for AliExpress price/catalog data; pick over scraping when affiliate/partner access is acceptable

## What it does / when to pick it
AliExpress exposes an **official Open Platform** with a real **Affiliate API**, pick it when the user wants legitimate, signed, rate-limited access to AliExpress product/price/promo data instead of scraping. Two surfaces: the **Open Platform** (`openservice.aliexpress.com`, full e-commerce APIs, product, category, freight, etc.) and the **Affiliate Portal** (`portals.aliexpress.com`, generate tracking links + pull promotional/product data, earn commission). Good for cross-border price comparison and deal sourcing; **always normalize landed cost** because the sticker price hides large US duties now.

## Install
1. Register a **UAC (Unified Account Center)** account at `openservice.aliexpress.com` and sign up as a developer.
2. Register an **application**; choose developer type, for affiliates pick **"Affiliate API"** (vs "Self-Developer" / "Commercial Developer").
3. Request **API permission** for the app. Affiliate review is usually **~2 business days** (open a support ticket if no email in 3 to 4 days).
4. Use the app key/secret to make **signed** requests (HMAC signature; no official OpenAPI spec, no first-party Node SDK, community SDKs like `moh3a/ae_sdk`, `allanchangcl/aliexapi` fill the gap).

## Auth / keys
App key + app secret from the Open Platform console; requests are **signed** (signature param per AliExpress signing scheme). **Treat secret as secret**, env var only. Migration note: legacy Taobao Open Platform integrations were **fully migrated to the new Open Platform**, old TOP credentials/endpoints are deprecated.

## Usage, call examples
- **Affiliate product query / link generation** via the Affiliate API endpoints (e.g. product query, hot products, link generation) under `openservice.aliexpress.com/doc`.
- **Rate limit:** ~**5,000 requests/day** (verify current quota in console, it has changed historically).
- For agents without partner access, BigGo MCP covers AliExpress as a secondary source (④ route), but the official API is the L1 path.

## ⚠ Tariff / landed-cost note (verify per order, 2026)
**The US $800 de minimis exemption ended for Chinese-origin goods (Feb 2025); 2026 is the first full year where every package from China is dutiable regardless of value.** Practical impact for any AliExpress price the skill surfaces:
- Typical consumer goods now carry **~35% duty** (≈10% + 25% Section 301) on (item + shipping + insurance); carrier **handling fees** add more on small orders.
- Listed/Choice prices have effectively **risen 20 to 40%** and customs clearance adds delivery delay.
- **Mitigation to surface to the user:** filter **"Ships from United States"** (already customs-cleared, no import duty, faster); consolidate orders to amortize handling fees.
- **Landed cost = listing + shipping + ~35% duty + handling**, never quote the sticker price as the real cost. This separation from IEEPA tariffs means it survived the Feb 2026 Supreme Court IEEPA ruling and is firmly in effect.

## General experience & gotchas (踩坑)
- **AliExpress Choice** = consolidated-logistics program (curated, often faster/“free”-ish shipping), but Choice items still ship from China and are **fully dutiable** now; "free shipping" ≠ free landed cost.
- **真伪 / authenticity**, AliExpress is a marketplace of third-party sellers; **counterfeit and misrepresented goods are common**, especially for branded electronics/apparel. Treat brand claims with suspicion; weight seller rating, order count, and reviews. **Do not present AliExpress brand-name listings as trust-tier-equal to authorized US retailers.**
- **No official OpenAPI spec / no first-party Node SDK**, signing is manual; lean on community SDKs but audit them (they handle your secret).
- **Affiliate API ≠ full Open Platform**, affiliate scope is promotional/product data + links; dropshipping/order APIs need the other developer types.
- **Quota is per-day and can change**, don't hardcode 5,000; read the console.

## Failure signals & fallback
Signature errors (clock skew / wrong signing), `permission denied` (app scope not approved), daily quota hit (429-equivalent). **Fallback:** BigGo MCP (AliExpress as ④ secondary source), or community SDK with manual signing; for landed-cost truth, compute duty manually rather than trusting any listing's "total".

## Last verified: 2026-06
