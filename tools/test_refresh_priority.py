"""Native CLI coverage for generated live-run gap reasons and refresh rankings."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_fixtures import live_run_examples


def example(outcome):
    row = copy.deepcopy(next(row for row in live_run_examples() if row["outcome"] == outcome))
    row["user_correction"] = None
    return row


@pytest.fixture
def run_priority(tmp_path):
    def run(records, *args):
        source = tmp_path / "observations.jsonl"
        source.write_text("".join(json.dumps(row) + "\n" for row in records), encoding="utf-8")
        environment = {key: value for key, value in os.environ.items()
                       if not key.upper().startswith("SHOPPING_AGGREGATOR_")}
        environment["PYTHONUTF8"] = "1"
        tool = Path(__file__).with_name("refresh_priority.py")
        return subprocess.run([sys.executable, "-B", str(tool), "--file", str(source), *args],
                              cwd=tmp_path, env=environment, capture_output=True,
                              text=True, encoding="utf-8")
    return run


@pytest.mark.parametrize("reason", ["session-gated-declined", "session-gated-unattended",
    "structurally-unreachable", "tool-outage", "not-attempted"])
def test_cli_preserves_each_valid_gap_reason(run_priority, reason):
    row = example("coverage_gap")
    row["gap_reason"] = reason
    result = run_priority([row], "--json")
    assert result.returncode == 0, result.stderr
    ranking = json.loads(result.stdout)["ranking"]
    assert len(ranking) == 1
    assert ranking[0]["score"] == 3
    assert ranking[0]["coverage_gap"] == 1
    assert ranking[0]["gap_reasons"] == {reason: 1}


@pytest.mark.parametrize("case,value", [("missing", None), ("null", None), ("blank", ""),
    ("number", 1), ("boolean", True), ("list", []), ("object", {}),
    ("unknown", "not-a-gap-reason")])
def test_cli_rejects_invalid_gap_reason_without_echoing_record(run_priority, case, value):
    row = example("coverage_gap")
    if case == "missing":
        row.pop("gap_reason")
    else:
        row["gap_reason"] = value
    result = run_priority([example("verified"), row], "--json")
    assert result.returncode != 0
    assert result.stdout == ""
    assert "line 2" in result.stderr
    assert "gap_reason" in result.stderr
    assert row["detail"] not in result.stderr
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize("outcome", ["verified", "dead"])
def test_cli_accepts_nongap_without_reason(run_priority, outcome):
    row = example(outcome)
    row.pop("gap_reason", None)
    result = run_priority([row], "--json")
    assert result.returncode == 0, result.stderr
    ranking = json.loads(result.stdout)["ranking"]
    if outcome == "verified":
        assert ranking == []
    else:
        assert ranking[0]["score"] == 10
        assert ranking[0]["gap_reasons"] == {}


@pytest.mark.parametrize("by", ["source", "domain"])
@pytest.mark.parametrize("output", ["json", "table"])
def test_cli_keeps_distinct_reasons_within_one_aggregate(run_priority, by, output):
    first = example("coverage_gap")
    first["gap_reason"] = "session-gated-declined"
    second = copy.deepcopy(first)
    second["gap_reason"] = "structurally-unreachable"
    args = ["--by", by]
    if output == "json":
        args.append("--json")
    result = run_priority([first, second, first], *args)
    assert result.returncode == 0, result.stderr
    if output == "json":
        ranking = json.loads(result.stdout)["ranking"]
        assert len(ranking) == 1
        assert ranking[0]["key"] == first[by]
        assert ranking[0]["score"] == 9
        assert ranking[0]["coverage_gap"] == 3
        assert ranking[0]["gap_reasons"] == {
            "session-gated-declined": 2, "structurally-unreachable": 1}
    else:
        assert first[by] in result.stdout
        assert "session-gated-declined=2" in result.stdout
        assert "structurally-unreachable=1" in result.stdout


def test_gap_reason_counts_preserve_priority_weights_and_tie_order(run_priority):
    correction = example("verified")
    correction.update(source="example-correction", user_correction=correction["detail"])
    gap = example("coverage_gap")
    gap["source"] = "example-gaps"
    mismatch = example("dead")
    mismatch.update(source="example-mismatch", outcome="price_mismatch")
    dead_a = example("dead")
    dead_a["source"] = "example-a"
    dead_b = copy.deepcopy(dead_a)
    dead_b["source"] = "example-b"
    result = run_priority([dead_b, gap, mismatch, gap, correction, dead_a, mismatch, gap, gap],
                          "--json")
    assert result.returncode == 0, result.stderr
    ranking = json.loads(result.stdout)["ranking"]
    assert [row["key"] for row in ranking] == ["example-correction", "example-gaps",
                                               "example-mismatch", "example-a", "example-b"]
    assert [row["score"] for row in ranking] == [100, 12, 10, 10, 10]
    assert [row["events"] for row in ranking] == [1, 4, 2, 1, 1]
