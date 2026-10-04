"""Native CLI boundary controls using generator-owned synthetic inputs."""
from io import BytesIO
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_fixtures import flight_search_fixture, live_run_examples, matrix_package_fixture


@pytest.mark.parametrize("card_count", [0, 1])
@pytest.mark.parametrize("filtered", [False, True])
def test_search_does_not_publish_an_unhealthy_document_as_success(monkeypatch, capsys, card_count, filtered):
    import flight_probe
    fixture = flight_search_fixture(card_count)
    assert len(fixture["html"]) > 300000
    monkeypatch.setattr(flight_probe.urllib.request, "urlopen",
                        lambda *args, **kwargs: BytesIO(fixture["html"].encode()))
    argv = fixture["argv"] + (["--max-hours", "1"] if filtered else [])
    assert flight_probe.main(argv) == 2
    output = capsys.readouterr()
    assert output.out == ""
    assert "not_fetched" in output.err.lower()


@pytest.mark.parametrize("filtered", [False, True])
def test_search_preserves_healthy_observation_and_filtering(monkeypatch, capsys, filtered):
    import flight_probe
    fixture = flight_search_fixture(12)
    monkeypatch.setattr(flight_probe.urllib.request, "urlopen",
                        lambda *args, **kwargs: BytesIO(fixture["html"].encode()))
    argv = fixture["argv"] + (["--max-hours", "1"] if filtered else [])
    assert flight_probe.main(argv) == 0
    output = capsys.readouterr()
    rows = json.loads(output.out)
    assert len(rows) == (0 if filtered else 12)
    assert "not_fetched" not in output.err.lower()


def _matrix_cli(tmp_path, records):
    root = Path(__file__).resolve().parents[1]
    package = tmp_path / "package"
    matrix_package_fixture(package)
    for relative in ("tools/verify_matrix.py", "tools/config_schema.py", "tools/config_selection.py",
                     "tools/delivery_check.py",
                     "guards/tools/datadir.py"):
        destination = package / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / relative, destination)
    path = package / "skills/shopping-aggregator/metrics/live-runs.jsonl.example"
    path.write_text("".join(json.dumps(row) + "\n" for row in records), encoding="utf-8")
    environment = {key: value for key, value in os.environ.items()
                   if not key.upper().startswith(("GIT_", "SHOPPING_AGGREGATOR_"))}
    environment.update(HOME=str(tmp_path), USERPROFILE=str(tmp_path), PYTHONUTF8="1")
    subprocess.run(["git", "init", "-q", str(package)], env=environment, check=True)
    subprocess.run(["git", "-C", str(package), "add", "."], env=environment, check=True)
    result = subprocess.run([sys.executable, "-B", str(package / "tools/verify_matrix.py"), "--no-net"],
                            env=environment, capture_output=True, text=True, encoding="utf-8")
    (tmp_path / "matrix.log").write_text(result.stdout + result.stderr, encoding="utf-8")
    return result


@pytest.mark.parametrize("reason", ["session-gated-declined", "session-gated-unattended",
                                  "structurally-unreachable", "tool-outage", "not-attempted"])
def test_matrix_accepts_each_typed_coverage_reason(tmp_path, reason):
    rows = live_run_examples()
    rows[-1]["gap_reason"] = reason
    result = _matrix_cli(tmp_path, rows)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("reason", [None, "", "unknown", True, [], {}])
def test_matrix_rejects_invalid_coverage_reasons(tmp_path, reason):
    rows = live_run_examples()
    rows[-1]["gap_reason"] = reason
    result = _matrix_cli(tmp_path, rows)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "BLOCK [LIVERUNS]" in result.stdout and "gap_reason" in result.stdout


def test_matrix_requires_reason_only_for_coverage_gaps(tmp_path):
    rows = live_run_examples()
    del rows[-1]["gap_reason"]
    result = _matrix_cli(tmp_path, rows)
    assert result.returncode == 1 and "gap_reason" in result.stdout


def test_shipped_live_example_is_generator_owned():
    root = Path(__file__).resolve().parents[1]
    rows = [json.loads(line) for line in
            (root / "skills/shopping-aggregator/metrics/live-runs.jsonl.example").read_text().splitlines()]
    assert rows == live_run_examples()


def test_verified_example_does_not_create_a_human_correction_priority():
    from refresh_priority import event_weight
    row = next(row for row in live_run_examples() if row["outcome"] == "verified")
    assert event_weight(row) == (0, [])
