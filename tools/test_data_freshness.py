#!/usr/bin/env python3
"""Tests for the reference/data staleness gate (verify_matrix.check_data_freshness).

The reason this file exists: reference/data/README.md had said for months that cross-border
de-minimis "must be re-verified against the primary government source on every refresh, never from
memory". That was an intention with no mechanism. cross-border-duty.json then sat two months past
its last refresh still describing IEEPA as live US tariff authority, months after the Supreme Court
had struck that authority down, and every gate in this repo stayed green the entire time. The gates
asked whether `last_verified` EXISTED and whether it was in the FUTURE. Nothing ever asked whether
it was OLD.

So the property under test is stated the strong way, in both directions:

  1. A table past its own declared cadence MUST be reported, and past 2x MUST block.
  2. A table that cannot be aged MUST fail rather than pass quietly. This is the regression that
     matters most: the old code read `if mlv and <future check>`, so a malformed `last_verified`
     silently skipped every freshness assertion and the file printed clean. "Clean" and "never
     checked" must not produce the same output.
  3. A table that never declares `review_cadence_days` MUST block, because a table with no declared
     rot rate can never be reported stale, which is how this file class went wrong in the first
     place.

Run: python test_data_freshness.py     (also collectable by pytest)
"""
import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from verify_matrix import check_data_freshness  # noqa: E402

TODAY = datetime.date(2026, 8, 19)


def env(last_verified="2026-08", cadence=45, **extra):
    e = {"schema_version": 1, "rows": []}
    if last_verified is not None:
        e["last_verified"] = last_verified
    if cadence is not None:
        e["review_cadence_days"] = cadence
    e.update(extra)
    return e


def levels(obj, fn="t.json", today=TODAY):
    return [lvl for lvl, _code, _msg in check_data_freshness(fn, obj, today)]


def only(obj, **kw):
    """Assert exactly one finding and return (level, msg)."""
    out = check_data_freshness(kw.pop("fn", "t.json"), obj, kw.pop("today", TODAY))
    assert len(out) == 1, f"expected exactly 1 finding, got {out}"
    return out[0][0], out[0][2]


# --------------------------------------------------------------------------- happy path

def test_fresh_file_is_silent():
    # stamped this month, 18d old against a 45d cadence
    assert levels(env("2026-08", 45)) == []


def test_generous_cadence_tolerates_an_old_stamp():
    # sales-tax-shaped: statutory rates move about once a year
    assert levels(env("2026-06", 365)) == []


# --------------------------------------------------------------------------- staleness ladder

def test_past_cadence_warns():
    # 2026-06-01 -> 2026-08-19 is 79d, past a 45d cadence but under 2x
    lvl, msg = only(env("2026-06", 45))
    assert lvl == "warn", msg
    assert "79d" in msg and "45d" in msg, msg


def test_past_double_cadence_blocks():
    lvl, msg = only(env("2026-06", 30))  # 79d > 60d
    assert lvl == "block", msg
    assert "over 2x" in msg, msg


def test_block_message_names_the_abolished_instrument_trap():
    # Row-level re-verification cannot catch an instrument being abolished, because the original
    # notice stays online and still says what it said. The operator must be told to re-ask the
    # framework question, not just re-confirm each rate.
    _lvl, msg = only(env("2026-01", 30))
    assert "still exist" in msg, msg


def test_boundaries_are_exact():
    # age(2026-07) = 49d. cadence 49 -> silent; 48 -> warn. cadence 24 -> 48 < 49 -> block.
    assert levels(env("2026-07", 49)) == []
    assert levels(env("2026-07", 48)) == ["warn"]
    assert levels(env("2026-07", 24)) == ["block"]


# ------------------------------------------------- NEGATIVE CONTROLS: it must be able to fail
# Each of these asserts the gate FIRES. A gate whose tests only ever assert silence cannot
# distinguish "nothing wrong" from "not looking".

def test_missing_cadence_blocks():
    lvl, msg = only(env("2026-08", None))
    assert lvl == "block", msg
    assert "review_cadence_days" in msg, msg


def test_bool_cadence_blocks():
    # bool is a subclass of int in Python, so `isinstance(True, int)` is True. Without the explicit
    # bool guard, `"review_cadence_days": true` would be accepted as a 1-day cadence.
    lvl, _msg = only(env("2026-08", True))
    assert lvl == "block"


def test_string_cadence_blocks():
    assert levels(env("2026-08", "45")) == ["block"]


def test_nonpositive_cadence_blocks():
    assert levels(env("2026-08", 0)) == ["block"]
    assert levels(env("2026-08", -1)) == ["block"]


def test_malformed_stamp_blocks_and_does_not_skip_silently():
    # THE REGRESSION. Old code: `mlv = re.match(...); if mlv and <future>`. A malformed stamp made
    # mlv None, so the future check was skipped and the file passed clean. Every one of these must
    # produce a block, never an empty result.
    for bad in ["2026-6", "June 2026", "2026", "", "   ", "2026-08-19", "not-a-date", "26-08"]:
        out = check_data_freshness("t.json", env(bad, 45), TODAY)
        assert out, f"malformed last_verified {bad!r} produced NO finding (silent skip)"
        assert out[0][0] == "block", f"{bad!r} -> {out}"


def test_month_out_of_range_blocks():
    assert levels(env("2026-13", 45)) == ["block"]
    assert levels(env("2026-00", 45)) == ["block"]


def test_missing_stamp_blocks():
    lvl, msg = only(env(None, 45))
    assert lvl == "block", msg
    assert "last_verified" in msg, msg


def test_future_stamp_blocks():
    assert levels(env("2026-09", 45)) == ["block"]
    assert levels(env("2027-01", 45)) == ["block"]


def test_future_check_still_fires_when_cadence_is_absent():
    # Ordering guard: a future stamp must be caught even though the cadence key is also missing,
    # so one defect cannot mask the other.
    lvl, msg = only(env("2026-09", None))
    assert lvl == "block" and "future" in msg, msg


# --------------------------------------------------------------------------- live files

def test_shipped_data_files_declare_a_cadence():
    """Every reference/data/*.json this repo actually ships must declare its rot rate.

    Guarded rather than skipped: if the data dir cannot be located, that is a failure, not a pass.
    A test that silently finds nothing to check is the same defect this whole file is about.
    """
    import glob
    import json

    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)
    hits = glob.glob(os.path.join(root, "skills", "*", "reference", "data", "*.json"))
    assert hits, "found no reference/data/*.json to check; resolution is broken, not clean"
    for path in hits:
        with open(path, encoding="utf-8") as fh:
            obj = json.load(fh)
        cad = obj.get("review_cadence_days")
        assert isinstance(cad, int) and not isinstance(cad, bool) and cad > 0, (
            f"{os.path.basename(path)} does not declare a positive integer 'review_cadence_days'"
        )


def main():
    fns = [(n, f) for n, f in sorted(globals().items())
           if n.startswith("test_") and callable(f)]
    failed = 0
    for name, fn in fns:
        try:
            fn()
            print(f"  ok    {name}")
        except AssertionError as e:
            failed += 1
            print(f"  FAIL  {name}: {e}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"  ERROR {name}: {type(e).__name__}: {e}")
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
