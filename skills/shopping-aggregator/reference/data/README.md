# `reference/data/`, verifiable data tables (single source-of-record)

Durable, month-level **facts** that the landed-cost / triage logic reads instead of
hard-coding (sales tax, cross-border duty / de-minimis, FX source-of-record, shipping
baselines). Each `*.json` here is the **single source of truth** for its facts; SKILL.md
and shards must read these, not restate numbers inline.

> Iron law (CONSTITUTION III.2): every `$` / rate / threshold / quota MUST carry a
> `source_url` (authoritative http(s) page, a statute / gov / official policy page, **not**
> a SERP or memory) + a `verified_date`. Never from memory.

## Envelope schema (every `*.json` in this dir)

```json
{
  "schema_version": 1,
  "last_verified": "YYYY-MM",
  "review_cadence_days": 45,
  "domain": "<optional: e.g. tax | duty | fx | shipping>",
  "title": "<optional human label>",
  "rows": [
    {
      "key": "<stable identifier, unique within file>",
      "value": "<the fact: number | string>",
      "unit": "<optional but strongly advised: % | USD | bool | ...>",
      "source_url": "https://<authoritative page>",
      "verified_date": "YYYY-MM-DD",
      "evidence_grade": "<optional: E1 primary | E2 secondary | E3 community>",
      "note": "<optional>"
    }
  ]
}
```

- `schema_version` integer `1`, mirrors `reference/tools/registry.json`'s `schema_version`.
  If this README and a data file disagree, **this README is authoritative** (same role
  registry.json holds in the THREEWAY check).
- `last_verified: "YYYY-MM"`, file-level freshness, same convention as
  `reference/volatile/pricing-install.md` and the FRESH check.
- `review_cadence_days`, positive integer, **required**. How fast THIS table's facts rot, declared
  per file because one global TTL is wrong in both directions: statutory sales-tax rates move about
  once a year, while the 2026 US tariff regime moved three times in eight months. Current values:
  `cross-border-duty` 45, `shipping-baselines` 180, `us-sales-tax` 365. Declaring it is mandatory
  precisely because a table that never says how fast it rots can never be reported stale.

## `DATA` gate check (enforced by `tools/verify_matrix.py`)

Scans only `reference/data/*.json`. **No-op (PASS) when the dir has no `.json`.**

- **BLOCK**: invalid JSON / not an object · missing or non-integer `schema_version` ·
  `rows` missing or empty · a row missing any of `key`/`value`/`source_url`/`verified_date` ·
  `source_url` not `http(s)` · `verified_date` not `YYYY-MM-DD` or in the future ·
  `last_verified` in the future · duplicate `key` within a file.
- **BLOCK** (freshness, added 2026-08): `review_cadence_days` missing or not a positive integer ·
  `last_verified` not parseable as `YYYY-MM` (an unageable stamp fails rather than skipping the
  check) · age past **2x** the declared cadence.
- **WARN**: age past **1x** the declared cadence · a numeric-looking `value`
  (rate/amount/quota) with no `unit` · `evidence_grade` outside `{E1,E2,E3}`.

Freshness logic lives in `verify_matrix.check_data_freshness()`, kept a pure function so
`tools/test_data_freshness.py` can exercise it without burning GitHub API quota on what is purely
local arithmetic.

## Volatility note

Cross-border **de-minimis** (e.g. US Section 321 $800 and its China-origin carve-outs) is the
single highest-volatility, most decision-changing fact in this repo, re-verify against the
**primary government source** (CBP / USTR / Federal Register) on **every refresh**, never from
memory. Mark such rows `evidence_grade: "E1"` and keep `verified_date` tight.

> **Row-level re-verification does not catch an abolished instrument.** This is the failure that
> motivated the freshness gate, and the gate alone does not fix it. In 2026-06 this file was
> refreshed row by row and still came out describing IEEPA as live US tariff authority, months
> after the Supreme Court had struck that authority down. Every row re-verified cleanly, because
> each row's Federal Register notice is still online and still says exactly what it said the day it
> was published. Checking each rate against its own source can only ever confirm that the source
> has not changed its mind.
>
> So a refresh of this file MUST begin with the framework question, not the rows: **which tariff
> instruments are in force today**, and is each row's instrument still one of them. Only then check
> the rates. An instrument that was repealed, expired, enjoined, or struck down leaves a row that
> is individually verifiable and jointly wrong.

## Relationship to other files

- `volatile/pricing-install.md`, human-readable prose; this dir is machine-readable durable facts.
- `tools/registry.json`, tool inventory; this dir is non-tool facts.
- `evidence-schema.md`, per-run live evidence units; this dir is month-level durable facts.
