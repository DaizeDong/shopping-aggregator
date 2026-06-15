# Tool: eBay Browse API

- **Domain(s):** ebay-walmart-target
- **Barrier route:** ① official · **Source tier:** L1 · **Ready MCP:** no (REST API direct or custom MCP wrapper)
- **Cost:** **5000 calls/day free** (default); production needs eBay Partner Network (EPN) + Growth Check
- **Repo / Provider:** developer.ebay.com/api-docs/buy/browse/overview.html — official eBay developer platform
- **Top pick for its domain:** yes for eBay (only free cross-seller catalog API in the matrix)

## What it does / when to pick it
**The only free cross-seller catalog API of any major US retailer.** Search active eBay listings by keyword, filter by condition (new/used/refurb), pull Buy-It-Now and Best Offer indicators, fetch item details. Pick whenever the user is comparing eBay prices — this beats playwright on speed and reliability for eBay specifically.

## Install
1. Sign up at developer.ebay.com → create an application → get an OAuth client ID + secret.
2. Use sandbox credentials for testing (free, no production gate).
3. For production access (Browse API live data, 5000 calls/day), join **eBay Partner Network (EPN)** and complete the Growth Check. EPN is the affiliate program; joining is free but requires a website / app.
4. Implement OAuth2 client_credentials flow to get a Bearer token (token expires in 2 hours; refresh as needed).
5. Call `https://api.ebay.com/buy/browse/v1/item_summary/search?q=...` with `Authorization: Bearer <token>`.

## Auth / keys
Client ID + client secret + Bearer token. **Secret-handling hygiene**: never echo the secret to transcript; user fills via env var, agent reads `process.env.EBAY_CLIENT_SECRET` only.

## Usage — call examples
```
curl -X GET "https://api.ebay.com/buy/browse/v1/item_summary/search?q=Bose+QuietComfort+45&filter=conditionIds:{1000|2000}&limit=20" \
  -H "Authorization: Bearer <TOKEN>" \
  -H "X-EBAY-C-MARKETPLACE-ID: EBAY_US"
```
Returns array of items: title, price, condition, seller, sold-quantity, image, item URL.

## General experience & gotchas (踩坑)
- **EPN gate for production** — sandbox is free-for-all; live data needs the partner program. For a personal-use skill, expect to wait ~1-2 weeks for approval.
- **5000 calls/day is generous for consumer use** but tight if you do broad surveys (each search = 1 call; pagination = more).
- **Token expiry every 2 hours** — implement refresh; otherwise calls 401 unexpectedly.
- **Sold listings need a different scope** — `Browse API` shows active listings only. For "what did this sell for in the last 90 days" use the **completed/sold filter** on eBay's advanced search (web scrape) — there is no Browse API endpoint for sold-history (Finding API used to expose this; it's been decommissioned since 2025-02-05).
- **Best Offer accepted prices are HIDDEN** in the API — a listing might show Buy-It-Now $200 but accepted Best Offers at $140; only sold-completed-listings (scraped) reveal that.
- **Marketplace ID matters** — `EBAY_US` vs `EBAY_GB` vs `EBAY_DE` return different listings + currencies. Default to user's region.

## Failure signals & fallback
HTTP 401 (token expired or invalid), 429 (rate-limited; back off), empty results (search terms too narrow). **Fallback:** playwright MCP fetch of eBay search page (rate-limit risk) → BigGo MCP (covers eBay).

## Last verified: 2026-06
