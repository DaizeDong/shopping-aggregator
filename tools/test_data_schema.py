"""Native offline matrix admission for generated verified-fact tables."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_fixtures import baggage_requirements, fact_table_fixture, matrix_package_fixture


@pytest.mark.parametrize("variant", ["empty", "malformed", "boolean-version", "unsupported-version",
    "duplicate-key", "empty-key", "missing-value", "non-http-source", "missing-host", "invalid-date",
    "month-only", "future-date", "untyped-row"])
def test_invalid_fact_tables_block(variant):
    import datetime
    from verify_matrix import check_data_schema
    findings = check_data_schema("synthetic.json", fact_table_fixture(variant), datetime.date.today())
    assert any(level == "block" for level, _, _ in findings)


@pytest.mark.parametrize("variant", ["missing-unit", "unknown-grade"])
def test_fact_quality_gaps_remain_visible_warnings(variant):
    import datetime
    from verify_matrix import check_data_schema
    findings = check_data_schema("synthetic.json", fact_table_fixture(variant), datetime.date.today())
    assert len(findings) == 1 and findings[0][0] == "warn"


def test_baggage_checklist_remains_a_separate_unverified_schema():
    from delivery_check import baggage_errors
    assert baggage_errors(baggage_requirements()) == []


@pytest.mark.parametrize("variant,rejected", [("valid", False), ("empty", True), ("malformed", True)])
def test_original_offline_cli_enforces_fact_schema(tmp_path, variant, rejected):
    root = Path(__file__).resolve().parents[1]
    package = tmp_path / "package"
    matrix_package_fixture(package)
    for relative in ("tools/verify_matrix.py", "tools/delivery_check.py", "guards/tools/datadir.py"):
        destination = package / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / relative, destination)
    table = package / "skills/shopping-aggregator/reference/data/example-facts.json"
    table.write_text(json.dumps(fact_table_fixture(variant)), encoding="utf-8")
    environment = {key: value for key, value in os.environ.items()
                   if not key.upper().startswith(("GIT_", "SHOPPING_AGGREGATOR_"))}
    environment.update(HOME=str(tmp_path), USERPROFILE=str(tmp_path), PYTHONUTF8="1")
    subprocess.run(["git", "init", "-q", str(package)], env=environment, check=True)
    subprocess.run(["git", "-C", str(package), "add", "."], env=environment, check=True)
    result = subprocess.run([sys.executable, "-B", str(package / "tools/verify_matrix.py"), "--no-net"],
                            env=environment, capture_output=True, text=True, encoding="utf-8")
    (tmp_path / "matrix.log").write_text(result.stdout + result.stderr, encoding="utf-8")
    assert result.returncode == int(rejected), result.stdout + result.stderr
    assert ("BLOCK [DATA]" in result.stdout) == rejected
