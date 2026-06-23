#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""refresh_priority.py — turn metrics/live-runs.jsonl into a refresh priority list.

The refresh-protocol must read live-runs.jsonl as a prioritization input: sources/channels
that the world just proved wrong get worked first in the next sweep. This replaces the old
hand-run jq one-liner with a single deterministic, weighted ranking so the protocol and the
gate share one definition of "what hurts most."

Schema consumed (LIVERUNS, per skills/shopping-aggregator/SKILL.md Step 7 + verify_matrix.py):
  {"ts","domain","source","route?","outcome","detail","user_correction"}

Weighting (highest signal first), per reference/refresh-protocol.md "Feedback loop":
  - user_correction : the user manually fixed something we were wrong about. This is a JSON
                      KEY present on the line (non-null value) — NOT an `outcome` value.
                      Highest weight.
  - dead            : a tool/source stopped working.
  - price_mismatch  : the source's price diverged from the live authorized listing.
  - coverage_gap    : an in-scope channel could not be taken to E1 depth (missing channel/tool).

Score per (domain, source) = sum over its events of each event's weight. A single event can
contribute multiple weights (e.g. an outcome=="dead" line that also carries a non-null
user_correction counts for both). Sources are ranked by descending score; ties broken by
event count, then alphabetically, so output is stable.

Usage:
  python tools/refresh_priority.py                 # ranked table (default)
  python tools/refresh_priority.py --json          # machine-readable ranking
  python tools/refresh_priority.py --by domain     # aggregate by domain instead of source
  python tools/refresh_priority.py --file PATH      # read a specific jsonl (default: the skill's)

Exit codes: 0 normal (even with zero priority events); non-zero on unreadable / invalid input.
"""

import argparse
import json
import os
import sys

# Mirror verify_matrix.py path resolution: tools/ sits next to skills/.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_LIVERUNS = os.path.join(
    ROOT, "skills", "shopping-aggregator", "metrics", "live-runs.jsonl"
)

# user_correction is intentionally the heaviest: a human told us we were wrong.
WEIGHTS = {
    "user_correction": 100,  # JSON key present + non-null (NOT an outcome value)
    "dead": 10,
    "price_mismatch": 5,
    "coverage_gap": 3,
}

# Outcome values that contribute to a priority score (the rest, e.g. "verified",
# "created", are not problems and carry no weight).
SCORING_OUTCOMES = ("dead", "price_mismatch", "coverage_gap")


def load_records(path):
    """Yield (lineno, record) for every non-blank line. Raises on bad JSON."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            raw = fh.read()
    except OSError as e:
        raise SystemExit(f"refresh_priority: cannot read {path}: {e}")
    out = []
    for i, ln in enumerate(raw.splitlines(), 1):
        ln = ln.strip()
        if not ln:
            continue
        try:
            out.append((i, json.loads(ln)))
        except json.JSONDecodeError as e:
            raise SystemExit(
                f"refresh_priority: {path} line {i} is not valid JSON: {e}"
            )
    return out


def event_weight(rec):
    """Total weight a single event contributes, plus which signals fired."""
    signals = []
    # user_correction = the KEY is present AND non-null (not an outcome).
    if rec.get("user_correction") is not None:
        signals.append("user_correction")
    outcome = rec.get("outcome")
    if outcome in SCORING_OUTCOMES:
        signals.append(outcome)
    return sum(WEIGHTS[s] for s in signals), signals


def rank(records, by="source"):
    """Aggregate weighted scores keyed by (domain, source) or by `by` alone."""
    agg = {}
    for _, rec in records:
        w, signals = event_weight(rec)
        if w == 0:
            continue
        domain = rec.get("domain", "?")
        source = rec.get("source", "?")
        key = source if by == "source" else domain
        slot = agg.setdefault(
            key,
            {
                "key": key,
                "by": by,
                "score": 0,
                "events": 0,
                "domains": set(),
                "sources": set(),
                "user_correction": 0,
                "dead": 0,
                "price_mismatch": 0,
                "coverage_gap": 0,
            },
        )
        slot["score"] += w
        slot["events"] += 1
        slot["domains"].add(domain)
        slot["sources"].add(source)
        for s in signals:
            slot[s] += 1
    ranked = sorted(
        agg.values(),
        key=lambda r: (-r["score"], -r["events"], r["key"]),
    )
    return ranked


def to_jsonable(rows):
    out = []
    for r in rows:
        r = dict(r)
        r["domains"] = sorted(r["domains"])
        r["sources"] = sorted(r["sources"])
        out.append(r)
    return out


def print_table(rows, by):
    if not rows:
        print("(no priority events — nothing dead/price_mismatch/coverage_gap/user_correction "
              "in live-runs.jsonl)")
        return
    label = "SOURCE" if by == "source" else "DOMAIN"
    ctx = "domains" if by == "source" else "sources"
    print(f"{'PRIORITY':<9}{'SCORE':>6}  {'UC':>3} {'DEAD':>4} {'MISM':>4} {'GAP':>3}  "
          f"{label:<22} {ctx}")
    print("-" * 78)
    for n, r in enumerate(rows, 1):
        ctx_vals = ",".join(r["domains"] if by == "source" else r["sources"])
        print(f"#{n:<8}{r['score']:>6}  {r['user_correction']:>3} {r['dead']:>4} "
              f"{r['price_mismatch']:>4} {r['coverage_gap']:>3}  {r['key']:<22} {ctx_vals}")
    print()
    print("Work top-down in the next sweep. Weights: user_correction=100 (human override) > "
          "dead=10 > price_mismatch=5 > coverage_gap=3.")


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Rank shopping sources by refresh priority from live-runs.jsonl."
    )
    ap.add_argument("--file", default=DEFAULT_LIVERUNS,
                    help="Path to live-runs.jsonl (default: the skill's metrics file).")
    ap.add_argument("--by", choices=("source", "domain"), default="source",
                    help="Aggregate by source (default) or by domain.")
    ap.add_argument("--json", action="store_true",
                    help="Emit ranking as JSON instead of a table.")
    args = ap.parse_args(argv)

    records = load_records(args.file)
    rows = rank(records, by=args.by)

    if args.json:
        print(json.dumps(
            {"file": args.file, "by": args.by, "weights": WEIGHTS,
             "ranking": to_jsonable(rows)},
            indent=2, ensure_ascii=False))
    else:
        print_table(rows, args.by)
    return 0


if __name__ == "__main__":
    sys.exit(main())
