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

## `DATA` gate check (enforced by `tools/verify_matrix.py`)

Scans only `reference/data/*.json`. **No-op (PASS) when the dir has no `.json`.**

- **BLOCK**: invalid JSON / not an object · missing or non-integer `schema_version` ·
  `rows` missing or empty · a row missing any of `key`/`value`/`source_url`/`verified_date` ·
  `source_url` not `http(s)` · `verified_date` not `YYYY-MM-DD` or in the future ·
  `last_verified` in the future · duplicate `key` within a file.
- **WARN** (rot signal, mirrors FRESH): missing/malformed `last_verified` · a numeric-looking
  `value` (rate/amount/quota) with no `unit` · `evidence_grade` outside `{E1,E2,E3}`.

## Volatility note

Cross-border **de-minimis** (e.g. US Section 321 $800 and its China-origin carve-outs) is the
single highest-volatility, most decision-changing fact in this repo, re-verify against the
**primary government source** (CBP / USTR / Federal Register) on **every refresh**, never from
memory. Mark such rows `evidence_grade: "E1"` and keep `verified_date` tight.

## Relationship to other files

- `volatile/pricing-install.md`, human-readable prose; this dir is machine-readable durable facts.
- `tools/registry.json`, tool inventory; this dir is non-tool facts.
- `evidence-schema.md`, per-run live evidence units; this dir is month-level durable facts.
