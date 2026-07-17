# FX Source-of-Record Spec

Authoritative FX-rate sources for the shopping-aggregator. This file is the **single
source of record** for which providers we trust, in what order, and what provenance
we must attach to every converted price.

> **Iron rule (learned the hard way on buy-me-a-car MD/EV):** every tax rate, tariff,
> threshold, capability, and price claim must be verified against an authoritative
> primary source via `web_search` and cited inline, **never from memory**. If a claim
> cannot be verified, mark it `evidence: low` / `UNVERIFIED` and prefer omission over
> invention. The same discipline applies to FX: every rate we surface must carry the
> provider + timestamp it came from, so it is auditable rather than asserted.

---

## 1. Provider precedence

| Rank | Provider | Role | Key required | Backing | Verified live (2026-06-22) |
|------|----------|------|--------------|---------|----------------------------|
| 1 (primary) | **Frankfurter** | Authoritative rate source | No | ECB reference rates | Yes |
| 2 (fallback) | **ExchangeRate-API open-access** | Failover when primary is down/rate-limited | No | Aggregated, incl. ECB | Yes |

Resolution order: try **Frankfurter** first; on HTTP error, timeout, or a stale `date`,
fall back to **ExchangeRate-API open-access**. Record which provider actually served the
rate in the provenance block (see §4). Never silently mix, one rate, one provider, per
conversion.

> **Note on the original backup pick (`exchangerate.host`):** as of 2026-06-22,
> `exchangerate.host` **now requires a free access key**, its live endpoint is
> `https://api.exchangerate.host/live?access_key=...`. It is therefore no longer a
> keyless free source and was **rejected** as the backup. ExchangeRate-API's
> open-access tier (`open.er-api.com`, no key) was substituted to keep the "free +
> no key" invariant. Source:
> [exchangerate.host docs](https://exchangerate.host/documentation),
> [exchangerate.host pricing](https://exchangerate.host/pricing).

---

## 2. Primary, Frankfurter

- **Site:** https://frankfurter.dev/
- **Source code:** https://github.com/lineofflight/frankfurter
- **Backing:** Tracks **European Central Bank (ECB)** reference exchange rates.
- **Key:** none. No quotas; abuse rate-limiting only.
- **USD / CNY / EUR:** all confirmed live (see §5).

### Verified endpoint (use this exact path)

```
https://api.frankfurter.dev/v1/latest?base=USD&symbols=EUR,CNY
```

> The `frankfurter.dev/` docs advertise a `v2/...` path; the **live** working path on
> 2026-06-22 is `v1/latest` (the `v2/latest` path returned `404 not found`). The legacy
> `api.frankfurter.app/...` host issues a `301` redirect to `.dev`. **Pin `v1/latest` on
> `api.frankfurter.dev`** and re-verify if it ever 404s.

### Live response schema (observed 2026-06-22)

```json
{
  "amount": 1.0,
  "base": "USD",
  "date": "2026-06-22",
  "rates": { "CNY": 6.7748, "EUR": 0.87291 }
}
```

- `base`, base currency of `amount`.
- `date`, **the ECB rate date**, not the request date. ECB publishes once per business
  day ~16:00 CET; on weekends/EU holidays the most recent rate is returned. **Use this
  `date` field as the provenance timestamp**, not wall-clock now.
- `rates`, map of target code → rate.

### Caveats
- Rates move only on ECB business days. A `date` older than today is expected behaviour,
  not staleness, but if `date` is older than the configured staleness window, fail over.
- ECB rates are reference (mid-market) rates, not transactable retail FX.

---

## 3. Fallback, ExchangeRate-API (open access)

- **Site:** https://www.exchangerate-api.com/
- **Free/keyless docs:** https://www.exchangerate-api.com/docs/free
- **Backing:** Aggregated from multiple data providers (incl. ECB).
- **Key:** none on the open-access tier.
- **USD / CNY / EUR:** all confirmed live (see §5).

### Verified endpoint (use this exact path)

```
https://open.er-api.com/v6/latest/USD
```

### Live response schema (observed 2026-06-22, truncated)

```json
{
  "result": "success",
  "provider": "https://www.exchangerate-api.com",
  "base_code": "USD",
  "time_last_update_unix": 1782172951,
  "time_last_update_utc": "Tue, 23 Jun 2026 00:02:31 +0000",
  "time_next_update_unix": 1782259661,
  "rates": { "USD": 1, "EUR": 0.919, "CNY": 6.786919 }
}
```

- `base_code`, base currency.
- `time_last_update_unix` / `_utc`, **use as provenance timestamp** for this provider.
- `rates`, map of target code → rate.

### Constraints (must respect)
- **Updates once per day.** Polling once/24h (or once/hour) never trips limits;
  over-polling returns **HTTP 429**, which clears after ~20 minutes.
- **Attribution required:** display "Rates By Exchange Rate API" if rates are shown to
  end users. Style may be discreet.
- **No redistribution** of the raw rate dataset. Caching for personal/commercial
  conversion is permitted.

---

## 4. Provenance schema (attach to every converted value)

Every price we convert must carry where its rate came from. Minimum required shape:

```json
{
  "provider": "frankfurter",
  "rate": 6.7748,
  "ts": "2026-06-22T00:00:00Z"
}
```

| Field | Type | Meaning | Source mapping |
|-------|------|---------|----------------|
| `provider` | enum `"frankfurter"` \| `"exchangerate-api"` | Which provider actually served the rate | the one that responded successfully |
| `rate` | number | Units of target per 1 unit of `base` (base = source currency of the price) | `rates[target]` (Frankfurter) / `rates[target]` (ER-API) |
| `ts` | ISO-8601 UTC string | Effective time of the rate, **not** fetch time | Frankfurter `date` → midnight UTC; ER-API `time_last_update_unix` → ISO |

Recommended optional fields for full auditability:

| Field | Type | Meaning |
|-------|------|---------|
| `base` | string | Source currency the `rate` converts **from** |
| `target` | string | Currency the `rate` converts **to** |
| `endpoint` | string | Exact URL queried |
| `fetched_at` | ISO-8601 UTC | Wall-clock time we fetched (distinct from `ts`) |
| `fallback_used` | bool | `true` when the primary failed and we served from fallback |

Rules:
- One provenance block per converted amount. Never average across providers.
- If neither provider returns a usable rate, **do not invent one**, surface the price in
  its original currency and mark the conversion `UNVERIFIED` (consistent with the iron
  rule above). Prefer omission over a fabricated rate.

---

## 5. Verification log

All checks performed 2026-06-22 via `web_search` + live `curl`.

| Claim | Result | Evidence |
|-------|--------|----------|
| Frankfurter is free, no key; ECB is a data **provider** (`providers=ECB`), not an endorser/sponsor | Confirmed | [frankfurter.dev](https://frankfurter.dev/), [frankfurter.dev/providers](https://frankfurter.dev/providers/), [GitHub lineofflight/frankfurter](https://github.com/lineofflight/frankfurter) |
| Frankfurter serves USD/EUR/CNY live | Confirmed | live `GET api.frankfurter.dev/v1/latest?base=USD&symbols=EUR,CNY` → `{"amount":1.0,"base":"USD","date":"2026-06-22","rates":{"CNY":6.7748,"EUR":0.87291}}` |
| Frankfurter `v2/latest` path | **Not live** (404) | live `GET api.frankfurter.dev/v2/latest...` → `{"status":404,"message":"not found"}`, use `v1/latest` |
| `exchangerate.host` keyless | **FALSE as of 2026-06-22**, now needs access key | [exchangerate.host docs](https://exchangerate.host/documentation), [pricing](https://exchangerate.host/pricing) |
| ExchangeRate-API open-access is keyless | Confirmed | [er-api free docs](https://www.exchangerate-api.com/docs/free) |
| ER-API serves USD/EUR/CNY live | Confirmed | live `GET open.er-api.com/v6/latest/USD` → `rates` incl. `"CNY":6.786919`, `"EUR":0.919` |
| ER-API attribution + no-redistribution + daily update + 429 | Confirmed | [er-api free docs](https://www.exchangerate-api.com/docs/free) |

### Evidence ratings
- Primary (Frankfurter): **high**, official docs + open source + live response.
- Fallback (ExchangeRate-API): **high**, official docs + live response. Caveat:
  attribution + no-redistribution terms are binding obligations, not just notes.

### Sources
- https://frankfurter.dev/
- https://github.com/lineofflight/frankfurter
- https://www.exchangerate-api.com/
- https://www.exchangerate-api.com/docs/free
- https://exchangerate.host/documentation
- https://exchangerate.host/pricing
