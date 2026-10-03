"""Generated delivery and fare fixtures, with no network calls."""
from datetime import datetime, timezone
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from delivery_check import delivery_errors, baggage_errors
from flight_cost import assess_total
from make_fixtures import baggage_requirements, delivery_fixture, flight_quote


def test_complete_manifest_passes(tmp_path):
    tracked = delivery_fixture(tmp_path)
    assert delivery_errors(tmp_path, tracked) == []


@pytest.mark.parametrize("path", ["skills/shopping-aggregator/reference/domains/air-travel.md",
                                 "skills/shopping-aggregator/reference/data/airline-baggage.json"])
def test_existing_but_untracked_is_not_delivery(tmp_path, path):
    tracked = delivery_fixture(tmp_path)
    tracked.remove(path)
    assert (tmp_path / path).is_file()
    assert any(path in e and "delivery" in e for e in delivery_errors(tmp_path, tracked))


def test_tracked_but_missing_is_rejected(tmp_path):
    tracked = delivery_fixture(tmp_path)
    (tmp_path / "skills/shopping-aggregator/reference/domains/air-travel.md").unlink()
    assert any("air-travel.md" in e for e in delivery_errors(tmp_path, tracked))


def test_readme_domain_coverage_must_agree(tmp_path):
    tracked = delivery_fixture(tmp_path)
    (tmp_path / "README_CN.md").write_text("# Example\n", encoding="utf-8")
    assert any("README_CN.md" in e for e in delivery_errors(tmp_path, tracked))


def test_required_shard_cannot_disappear_from_index(tmp_path):
    tracked = delivery_fixture(tmp_path)
    (tmp_path / "skills/shopping-aggregator/reference/sources-index.md").write_text("# Example\n", encoding="utf-8")
    assert any("air-travel" in e for e in delivery_errors(tmp_path, tracked))


@pytest.mark.parametrize("change", [
    lambda d: d.update(rows=[{"fee": 0}]),
    lambda d: d.update(last_verified="2030-01-02"),
    lambda d: d.update(status="verified"),
    lambda d: d.update(fee=0),
    lambda d: d.update(required_terms=None),
])
def test_unverified_baggage_resource_cannot_become_fee_evidence(change):
    obj = baggage_requirements()
    assert not baggage_errors(obj)
    change(obj)
    assert baggage_errors(obj)


@pytest.mark.parametrize("tool", ["refresh_priority.py", "verify_matrix.py"])
def test_missing_guards_reports_installation_repair(tmp_path, tool):
    import subprocess
    destination = tmp_path / "tools" / tool
    destination.parent.mkdir()
    destination.write_bytes((Path(__file__).resolve().parent / tool).read_bytes())
    run = subprocess.run([sys.executable, "-B", str(destination)], capture_output=True, text=True)
    assert run.returncode == 1
    assert "git submodule update --init --recursive" in run.stderr
    assert "Traceback" not in run.stderr


def test_uninitialized_reader_is_an_empty_state(tmp_path):
    import os
    import shutil
    import subprocess
    root = Path(__file__).resolve().parents[1]
    (tmp_path / "tools").mkdir()
    (tmp_path / "guards/tools").mkdir(parents=True)
    (tmp_path / ".git").mkdir()
    for relative in ("tools/refresh_priority.py", "guards/tools/datadir.py"):
        shutil.copyfile(root / relative, tmp_path / relative)
    env = {key: value for key, value in os.environ.items() if not key.startswith("SHOPPING_AGGREGATOR_")}
    env.update(HOME=str(tmp_path), USERPROFILE=str(tmp_path), PYTHONUTF8="1")
    run = subprocess.run([sys.executable, "-B", str(tmp_path / "tools/refresh_priority.py")],
                         capture_output=True, text=True, encoding="utf-8", env=env)
    assert run.returncode == 0
    assert "no live-run" in run.stderr
    assert "PRIVATE shopping-aggregator-config companion" in run.stderr
    assert "Traceback" not in run.stderr


def assess(quote):
    return assess_total(quote, datetime(2030, 1, 2, 12, tzinfo=timezone.utc))


def test_complete_selected_source_quote_has_comparable_total():
    result = assess(flight_quote())
    assert result["status"] == "comparable_total"
    assert result["total"] == "140.00"
    assert result["claim_scope"] == "selected verified offers only"


@pytest.mark.parametrize("term", ["tax", "checked_bags", "cabin_bags", "seat_selection", "payment_fx", "fare", "refund_terms", "fare_brand"])
def test_unknown_terms_cannot_support_total_ranking(term):
    quote = flight_quote()
    quote["terms"][term] = {"status": "unknown", "value": None}
    result = assess(quote)
    assert result["status"] == "not_comparable"
    assert "total" not in result


def test_cabin_bag_cost_is_required_and_added():
    quote = flight_quote()
    quote["terms"].pop("cabin_bags", None)
    assert assess(quote)["status"] == "not_comparable"
    quote["terms"]["cabin_bags"] = {"status": "verified", "value": "15"}
    assert assess(quote)["total"] == "155.00"


@pytest.mark.parametrize("change", [
    lambda q: q["sources"].pop(),
    lambda q: q["sources"][1].update(transport_id="synthetic-browser"),
    lambda q: q["sources"][1].update(evidence_grade="E2"),
    lambda q: q["sources"][1].update(fetched_at="2030-01-01T12:00:00+00:00"),
    lambda q: q["sources"][1].update(variant_key="other"),
    lambda q: q["sources"][1].update(selected=False),
    lambda q: q["terms"]["fare"].update(value=float("nan")),
    lambda q: q["terms"]["fare"].update(value=True),
])
def test_unverified_or_nonindependent_sources_cannot_rank(change):
    quote = flight_quote()
    change(quote)
    assert assess(quote)["status"] == "not_comparable"


@pytest.mark.parametrize("amount", ["1e40", "1e1000000", "9.99e999999"])
def test_unrepresentable_finite_amount_returns_a_gap(amount):
    quote = flight_quote()
    quote["terms"]["fare"]["value"] = amount
    result = assess(quote)
    assert result["status"] == "not_comparable"
    assert result["gaps"]
    assert "total" not in result
