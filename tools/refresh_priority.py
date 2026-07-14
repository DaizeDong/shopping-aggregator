#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""refresh_priority.py — turn live-runs.jsonl into a refresh priority list.

The refresh-protocol must read live-runs.jsonl as a prioritization input: sources/channels
that the world just proved wrong get worked first in the next sweep. This replaces the old
hand-run jq one-liner with a single deterministic, weighted ranking so the protocol and the
gate share one definition of "what hurts most."

WHERE THE FILE LIVES (this used to be wrong, and the wrongness was the leak)
---------------------------------------------------------------------------
live-runs.jsonl is DATA, not TOOL: every line is an observation from a REAL run, so the file
accumulated which products got priced, which retailers got bought from, and which region they
ship to. It was git-tracked in a public repo, and every content scan passed it — there is no
email or phone in a domain slug. It now resolves from the PRIVATE data dir (tools/datadir.py),
and there is deliberately NO in-repo fallback: a fallback into the repo is not a convenience,
it IS the leak. Uninitialized, this tool raises DataDirNotInitialized with instructions.

The generalizable half of those observations — which source works for which channel, which
retailers can't be taken to E1 — was distilled by hand into reference/source-reliability.md and
stays public. The observations themselves do not.

Schema consumed (LIVERUNS, per skills/shopping-aggregator/SKILL.md Step 7 + verify_matrix.py);
the published shape is skills/shopping-aggregator/metrics/live-runs.jsonl.example:
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
  python tools/refresh_priority.py --file PATH     # read a specific jsonl (default: the private one)

Exit codes: 0 normal (even with zero priority events); non-zero on unreadable / invalid input;
2 when the private data dir does not exist (the tool is uninitialized — not a crash, a state).
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from datadir import DataDirNotInitialized, resolve_data_dir  # noqa: E402

SKILL_SLUG = "shopping-aggregator"


def _liveruns_file():
    """The private live-runs.jsonl. Never a path inside the repo — see the module docstring."""
    d = resolve_data_dir(SKILL_SLUG)
    if d is None:
        raise DataDirNotInitialized(
            "shopping-aggregator has no private data directory, so there are no live-run\n"
            "observations to rank. A freshly cloned public skill is SUPPOSED to look like this:\n"
            "it ships as an uninitialized tool, carrying the schema and none of the contents.\n"
            "Point it at your own store:\n"
            "    mkdir -p ~/.shopping-aggregator-config/data/metrics\n"
            "    (or set SHOPPING_AGGREGATOR_DATA_DIR)\n"
            "The shape you are expected to produce is published in the repo as\n"
            "skills/shopping-aggregator/metrics/live-runs.jsonl.example."
        )
    return os.path.join(str(d), "metrics", "live-runs.jsonl")


class _LazyPath:
    """A path that resolves at USE time, not import time.

    `DEFAULT_LIVERUNS` is an argparse default, so it is evaluated whenever this module is merely
    imported — and on a fresh clone there is no path at all to evaluate. Resolving eagerly would
    make `import refresh_priority` explode on a machine that has simply never initialized the
    skill. Defer it: importing stays free, and DataDirNotInitialized (with instructions) fires
    only when something actually reaches for the file.
    """

    def __init__(self, fn):
        self._fn = fn

    def __fspath__(self):
        return os.fspath(self._fn())

    def __str__(self):
        return str(self._fn())

    def __repr__(self):
        return "_LazyPath(%s)" % self._fn()


DEFAULT_LIVERUNS = _LazyPath(_liveruns_file)

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
                    help="Path to live-runs.jsonl (default: the PRIVATE data dir's copy — "
                         "real-run output never lives in the repo).")
    ap.add_argument("--by", choices=("source", "domain"), default="source",
                    help="Aggregate by source (default) or by domain.")
    ap.add_argument("--json", action="store_true",
                    help="Emit ranking as JSON instead of a table.")
    args = ap.parse_args(argv)

    # Resolving the default reaches for the private data dir, which may not exist. That is a STATE
    # (an uninitialized tool), not a crash — report it with instructions, don't dump a traceback.
    try:
        path = os.fspath(args.file)
    except DataDirNotInitialized as e:
        print(str(e), file=sys.stderr)
        return 2

    records = load_records(path)
    rows = rank(records, by=args.by)

    if args.json:
        print(json.dumps(
            {"file": path, "by": args.by, "weights": WEIGHTS,
             "ranking": to_jsonable(rows)},
            indent=2, ensure_ascii=False))
    else:
        print_table(rows, args.by)
    return 0


if __name__ == "__main__":
    sys.exit(main())
