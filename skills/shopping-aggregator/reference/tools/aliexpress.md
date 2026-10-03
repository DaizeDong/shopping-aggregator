# Tool: AliExpress (Open Platform / Affiliate API + Choice)

- **Domain(s):** ebay-walmart-target (cross-border catalog), oss-self-host (as a data source)
- **Barrier route:** ① official API · **Source tier:** L1 (official API) / L2 (Choice listing data) · **Ready MCP:** no (REST, signed requests; no first-party MCP)
- **Cost:** Verify current API eligibility and fees with the provider. Product landed cost requires current shipping, tax, duty and carrier-fee evidence for the selected order; see the tariff workflow below.
- **Repo / Provider:** openservice.aliexpress.com (Open Platform) · portals.aliexpress.com (Affiliate), Alibaba Group
- **Top pick for its domain:** the canonical **official** route for AliExpress price/catalog data; pick over scraping when affiliate/partner access is acceptable

## What it does / when to pick it
AliExpress exposes an **official Open Platform** with a real **Affiliate API**, pick it when the user wants legitimate, signed, rate-limited access to AliExpress product/price/promo data instead of scraping. Two surfaces: the **Open Platform** (`openservice.aliexpress.com`, full e-commerce APIs, product, category, freight, etc.) and the **Affiliate Portal** (`portals.aliexpress.com`, generate tracking links + pull promotional/product data, earn commission). Good for cross-border price comparison and deal sourcing; **always normalize landed cost** because the sticker price may omit shipping, duties, taxes or carrier charges.

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

## Tariff and landed-cost verification

Start with `../data/cross-border-duty.json` and the source-of-record procedure in
`../data/README.md`. For the selected product, verify which instruments are currently
in force, the goods' origin, classification, destination and shipment terms against
current authoritative sources. Confirm the carrier's handling charges and whether
any charges are already included in the seller's total. Record sources and verification
times. Unknown charges remain an explicit gap and cannot support a lowest-total claim.

A shipping-location filter or a Choice label does not establish origin, customs status,
or duty exemption. Verify those facts for the selected offer before comparing totals.

## General experience & gotchas (踩坑)
- **AliExpress Choice** is a logistics label; verify the selected offer's origin, shipping terms and included charges. A free-shipping claim alone does not establish landed cost.
- **真伪 / authenticity**, AliExpress is a marketplace of third-party sellers; **counterfeit and misrepresented goods are common**, especially for branded electronics/apparel. Treat brand claims with suspicion; weight seller rating, order count, and reviews. **Do not present AliExpress brand-name listings as trust-tier-equal to authorized US retailers.**
- **No official OpenAPI spec / no first-party Node SDK**, signing is manual; lean on community SDKs but audit them (they handle your secret).
- **Affiliate API ≠ full Open Platform**, affiliate scope is promotional/product data + links; dropshipping/order APIs need the other developer types.
- **Quota is per-day and can change**, don't hardcode 5,000; read the console.

## Failure signals & fallback
Signature errors (clock skew / wrong signing), `permission denied` (app scope not approved), daily quota hit (429-equivalent). **Fallback:** BigGo MCP (AliExpress as ④ secondary source), or community SDK with manual signing; for landed cost, follow the current origin/classification/instrument checks above and reconcile them with the selected listing and carrier terms.

## Last verified: 2026-06
