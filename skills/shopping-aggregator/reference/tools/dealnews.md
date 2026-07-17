# Tool: DealNews (+ DealNews API)

- **Domain(s):** mobile-apps-aggregators
- **Barrier route:** ① editorial-curated · **Source tier:** L2 (web/app healthy) → API is **key-gated, undocumented acquisition** · **Ready MCP:** no
- **Cost:** web + app free (ad/affiliate funded) · **API: key-gated** (no public self-serve signup found, contact DealNews)
- **Repo / Provider:** dealnews.com (editorial, founded 1997, DealNews.com Inc.) · PHP client github.com/dealnews/api-php-client
- **Top pick for its domain:** no, Slickdeals is the default US discovery pick; DealNews is the **editorial-vetted** complement (lower throughput, higher per-deal quality)

## What it does / when to pick it
The longest-running US **editor-verified** deal aggregator (since 1997). In-house editors hand-pick **300 to 400+ deals/weekday** across **6,000+ retailers**, blending automated price scanning with human vetting, every listed deal is confirmed before publication. Pick when the user wants **"top deals today, editor-vetted"** rather than Slickdeals' community-vote signal: fewer false positives, fewer expired/fake-sale entries, but lower volume and less crowd "is this code working" verification. Like Slickdeals it is **DISCOVERY, not SKU comparison**, for landed-cost tables use the retailer-direct routes.

## Install
- **Web**: dealnews.com, Frontpage + category pages (e.g. `dealnews.com/t1/Deals/`).
- **iOS**: App Store id405566099 (DealNews.com, Inc.) · **Android**: Google Play `com.dealnews.android.ui`, both actively updated 2026.
- **Email digests**: daily/weekly newsletters are the primary touchpoint per the publisher; keyword-followable interests (electronics, gift cards, etc.).
- **API (optional, gated)**: PHP client at github.com/dealnews/api-php-client.

## Auth / keys
- Web/app: browsing anonymous; follows/alerts need a free account.
- **API: requires an API key.** The PHP client instantiates `new \DealNews\API\Client\HTTP("YOUR_API_KEY")`, but **key acquisition is NOT publicly documented**; no self-serve developer portal was found. Treat the API as **contact-DealNews / partner-gated**; do not assume you can get a key for a personal-use skill.

## Usage, call examples
**agent (default, no key needed)**: WebFetch `https://www.dealnews.com/` Frontpage, `https://www.dealnews.com/t1/Deals/` for current top deals, or a category page. Outbound retailer links carry **affiliate redirects**, extract the underlying URL for clean tracking.

**API (if a key exists)**, PHP client pattern:
```php
$client = new \DealNews\API\Client\HTTP("YOUR_API_KEY");
$response = $client->get("/features");  // $response['status'], ['headers'], ['body']
```

## General experience & gotchas (踩坑)
- **⚠ API PHP client is stale / unmaintained**, last release **v1.0.1, Apr 2017**, 0 stars/0 forks, only the `/features` endpoint shown in the README; full API spec is not public. The **consumer web/app is healthy in 2026**, but the *developer API path* is effectively dormant, **default to WebFetch of the site, not the API.** Do NOT present the API as a live, easy integration.
- **Editorial = lower throughput than Slickdeals**, ~400/weekday vs Slickdeals' forum 10 to 50×. Use DealNews when the user values vetting over breadth.
- **Editor-vetted = fewer fake-sales**, they claim to only list when a price-comparison confirms the lowest price; still verify big-ticket against history (Camelcamelcamel/Keepa).
- **Affiliate redirects** on outbound links (no paid placements claimed, but revenue is affiliate). Strip the redirect for a clean direct link.
- **App redesign drew criticism** (2025 to 26) for harder navigation; the web site + email remain the cleanest surfaces.
- **No price-history / per-SKU alert** like Camelcamelcamel, it's a *deal feed*, not a tracker.

## Failure signals & fallback
Empty/expired deal links; affiliate redirect dropping to homepage; **API: 401/no-key, or 4xx on undocumented endpoints, fall back to WebFetch of the site.** **Tool fallback:** Slickdeals (community signal), r/deals + r/buildapcsales (unmoderated tier), SMZDM (CN equivalent).

## Last verified: 2026-06
