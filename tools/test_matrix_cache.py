"""Exercise cold and warm cache decisions through fresh native matrix CLI processes."""
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_fixtures import (matrix_observation_fixture, matrix_package_fixture,
                           storage_repository_fixture, storage_visibility_fixture)


def matrix_child(package, verdict):
    original = subprocess.run
    def generated_github(args, *positional, **kwargs):
        if args[0] == "gh":
            assert args[:3] == ["gh", "api", "repos/example-owner/example-repo"]
            return subprocess.CompletedProcess(args, 0, json.dumps(matrix_observation_fixture(verdict)), "")
        return original(args, *positional, **kwargs)
    subprocess.run = generated_github
    sys.path.insert(0, str(package / "tools"))
    runpy.run_path(str(package / "tools/verify_matrix.py"), run_name="__main__")


@pytest.mark.parametrize("verdict,exit_code", [("BLOCK", 1), ("WARN", 0), ("PASS", 0)])
def test_cold_and_warm_cache_have_same_severity(tmp_path, verdict, exit_code):
    root = Path(__file__).resolve().parents[1]
    package = tmp_path / "package"
    matrix_package_fixture(package)
    for relative in ("tools/verify_matrix.py", "tools/evaluation_store.py", "tools/delivery_check.py",
                     "guards/tools/datadir.py", "guards/tools/data_boundary.py", "guards/tools/pii_guard.py"):
        destination = package / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / relative, destination)
    environment = {key: value for key, value in os.environ.items()
                   if not key.upper().startswith(("GIT_", "SHOPPING_AGGREGATOR_"))}
    environment.update(HOME=str(tmp_path), USERPROFILE=str(tmp_path), PYTHONUTF8="1")
    subprocess.run(["git", "init", "-q", str(package)], env=environment, check=True)
    subprocess.run(["git", "-C", str(package), "add", "."], env=environment, check=True)
    data, _ = storage_repository_fixture(tmp_path / "companion")
    storage_visibility_fixture(tmp_path / ".pii-guard/visibility.json")
    environment["SHOPPING_AGGREGATOR_DATA_DIR"] = str(data)
    results = []
    for temperature in ("cold", "warm"):
        result = subprocess.run([sys.executable, "-B", "-X", "utf8", str(Path(__file__).resolve()),
                                 "--matrix-child", str(package), verdict],
                                env=environment, capture_output=True, text=True, encoding="utf-8")
        (tmp_path / (temperature + ".log")).write_text(result.stdout + result.stderr, encoding="utf-8")
        results.append(result)
    cache = json.loads((data / "cache/gh-api-cache.json").read_text(encoding="utf-8"))
    assert cache["example-owner/example-repo"]["verdict"] == verdict
    for result in results:
        assert result.returncode == exit_code, result.stdout + result.stderr
        assert f"1 {verdict}" in result.stdout
        if verdict in {"BLOCK", "WARN"}:
            assert any(line.startswith(verdict) and "[GHACTIVE]" in line
                       for line in result.stdout.splitlines())
    assert all("[DATA]" not in result.stdout for result in results)


if __name__ == "__main__" and sys.argv[1:2] == ["--matrix-child"]:
    matrix_child(Path(sys.argv[2]), sys.argv[3])
