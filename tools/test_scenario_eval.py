"""Synthetic boundary and result-contract tests; no real judge or transcript."""
import copy
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import scenario_eval as evaluator
import evaluation_store as storage
from make_fixtures import (evaluation_fixture, judge_response, matrix_cache_fixture,
                           storage_repository_fixture, storage_visibility_fixture)


@pytest.fixture
def private_store(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    storage_visibility_fixture(tmp_path / ".pii-guard/visibility.json")
    data, transcript = storage_repository_fixture(tmp_path / "companion")
    monkeypatch.setattr(storage, "resolve_base", lambda: data)
    return data, transcript


def result_call(verdict="PASS", change=None, provider="synthetic-backend"):
    def call(prompt):
        contract = json.loads(prompt.split("===== CONTRACT =====\n", 1)[1])
        response = judge_response(contract, verdict)
        if change:
            change(response)
        return SimpleNamespace(text=json.dumps(response), provider=provider,
                               attempts=[SimpleNamespace(provider=provider, ok=True, ms=1)],
                               error=None)
    return call


def run_judge(private_store, **kwargs):
    _, transcript = private_store
    return evaluator.evaluate("us-single-sku-01", transcript, **kwargs)


def test_offline_plan_has_no_result_or_model_call(monkeypatch):
    monkeypatch.setattr(evaluator, "call_judge", lambda _: pytest.fail("offline model call"))
    plan = evaluator.plan()
    assert plan["status"] == "not_run"
    assert "scenario_verdict" not in plan
    assert "score" not in plan


@pytest.mark.parametrize("visibility", ["PUBLIC", "", "UNKNOWN"])
def test_nonprivate_preflight_happens_before_transcript_read(private_store, monkeypatch, visibility):
    storage_visibility_fixture(Path.home() / ".pii-guard/visibility.json",
                               {"example-owner/example-private": visibility})
    monkeypatch.setattr(evaluator, "read_transcript", lambda _: pytest.fail("private transcript read"))
    with pytest.raises(storage.StorageError):
        run_judge(private_store, caller=lambda _: pytest.fail("model called"))
    assert not (private_store[0] / "evaluation").exists()


def test_missing_store_fails_without_fallback(monkeypatch, tmp_path):
    monkeypatch.setattr(storage, "resolve_base", lambda: None)
    with pytest.raises(storage.StorageError):
        evaluator.evaluate("us-single-sku-01", tmp_path / "missing", caller=lambda _: None)


def test_public_tool_directory_rejected(monkeypatch):
    monkeypatch.setattr(storage, "resolve_base", lambda: storage.TOOL_ROOT)
    with pytest.raises(storage.StorageError):
        storage.prepare_store()


def test_input_must_stay_in_private_companion(private_store, tmp_path):
    outside = tmp_path / "outside.txt"
    outside.write_text("synthetic", encoding="utf-8")
    with pytest.raises(storage.StorageError):
        evaluator.evaluate("us-single-sku-01", outside, caller=lambda _: None)


def test_nested_repository_is_rejected(private_store):
    base, _ = private_store
    nested = base / "nested"
    nested.mkdir()
    subprocess.run(["git", "init", "-q", str(nested)], check=True)
    transcript = nested / "input.txt"
    transcript.write_text("synthetic", encoding="utf-8")
    with pytest.raises(storage.StorageError):
        evaluator.evaluate("us-single-sku-01", transcript, caller=lambda _: None)


@pytest.mark.parametrize("grade", ["PASS", "FAIL", "PARTIAL"])
def test_completed_result_preserves_grade_and_evidence(private_store, grade):
    result = run_judge(private_store, caller=result_call(grade))
    assert result["status"] == "completed"
    assert result["scenario_verdict"] == grade
    assert result["backend"]["provider"] == "synthetic-backend"
    assert result["independence"]["status"] == "not_established"
    assert result["policy"]["overrides"] == {}
    directory = Path(result["result_path"]).parent
    assert directory.is_relative_to(private_store[0])
    assert {p.name for p in directory.iterdir()} == {"transcript.txt", "prompt.txt", "response.txt", "result.json"}
    assert json.loads((directory / "result.json").read_text(encoding="utf-8")) == result


@pytest.mark.parametrize("mutation", [
    lambda r: r["criteria"].pop(),
    lambda r: r["criteria"].append(copy.deepcopy(r["criteria"][0])),
    lambda r: r.update(scenario_id="wrong-input"),
    lambda r: r["input_hashes"].update(transcript="0" * 64),
    lambda r: r["criteria"][0]["evidence"].update(quote="invented citation"),
    lambda r: r["criteria"][0].update(verdict="UNKNOWN"),
    lambda r: r["criteria"][0]["evidence"].update(kind="absence", quote=""),
    lambda r: r["criteria"][0]["evidence"].update(reason=""),
])
def test_malformed_or_stale_response_never_gets_a_grade(private_store, mutation):
    result = run_judge(private_store, caller=result_call(change=mutation))
    assert result["status"] == "malformed"
    assert "scenario_verdict" not in result


def test_absence_supports_failure_only(private_store):
    def absent(r):
        r["criteria"][0]["evidence"].update(kind="absence", quote="", reason="Required timestamp is absent.")
    result = run_judge(private_store, caller=result_call("FAIL", absent))
    assert result["status"] == "completed"
    assert result["scenario_verdict"] == "FAIL"


@pytest.mark.parametrize("failure", [None, SimpleNamespace(provider=None, error="unavailable", attempts=[])])
def test_unavailable_is_not_a_failed_grade(private_store, failure):
    result = run_judge(private_store, caller=lambda _: failure)
    assert result["status"] == "unavailable"
    assert "scenario_verdict" not in result


def test_unexpected_backend_exception_is_private_and_unavailable(private_store):
    def explode(_):
        raise RuntimeError("synthetic private backend diagnostic")
    result = run_judge(private_store, caller=explode)
    assert result["status"] == "unavailable"
    assert "diagnostic" not in result["error"]
    assert result["backend"]["error"] == "synthetic private backend diagnostic"


def test_judge_cannot_publish_after_storage_becomes_public(private_store):
    def change_visibility(prompt):
        reply = result_call()(prompt)
        storage_visibility_fixture(Path.home() / ".pii-guard/visibility.json",
                                   {"example-owner/example-private": "PUBLIC"})
        return reply
    with pytest.raises(storage.StorageError):
        run_judge(private_store, caller=change_visibility)
    directory, = (private_store[0] / "evaluation/runs").iterdir()
    assert not (directory / "response.txt").exists()
    assert json.loads((directory / "result.json").read_text(encoding="utf-8"))["status"] == "in_progress"


def test_llmcall_invocation_uses_installed_defaults(monkeypatch):
    seen = []
    monkeypatch.setitem(sys.modules, "llmcall", SimpleNamespace(call=lambda *a, **k: seen.append((a, k))))
    evaluator.call_judge("synthetic prompt")
    assert seen == [(("synthetic prompt",), {})]


def test_author_keys_recursively_removed():
    blind = evaluator.strip_author_keys({"notes": "secret", "trap": "author hint",
                                         "what_were_probing": "expected conduct",
                                         "nested": [{"fact_anchor": "secret", "id": "kept"}]})
    assert blind == {"nested": [{"id": "kept"}]}


def test_rubric_selection_is_complete():
    rubric = evaluator.RUBRIC.read_text(encoding="utf-8")
    criteria = evaluator.applicable_criteria(rubric, "us-single-sku-01")
    assert set(criteria) == {f"U{i}" for i in range(1, 11)} | {"S1", "S2"}
    assert criteria["S1"] is True and criteria["S2"] is False
    with pytest.raises(ValueError):
        evaluator.applicable_criteria(rubric, "unknown")


def test_optional_pass_cannot_replace_missing_required_evaluation(private_store):
    def scope_only(response):
        next(row for row in response["criteria"] if row["id"] == "U9")["verdict"] = "PASS"
    result = run_judge(private_store, caller=result_call("N/A", scope_only))
    assert result["status"] == "malformed"
    assert "scenario_verdict" not in result


@pytest.mark.parametrize("criterion", ["U1", "U5", "U10", "S1", "S2"])
def test_required_criterion_cannot_be_waived_by_judge(private_store, criterion):
    def waive(response):
        next(row for row in response["criteria"] if row["id"] == criterion)["verdict"] = "N/A"
    result = run_judge(private_store, caller=result_call(change=waive))
    assert result["status"] == "malformed"
    assert "scenario_verdict" not in result


def test_matrix_cache_without_private_storage_never_falls_back(monkeypatch):
    import verify_matrix
    monkeypatch.setattr(storage, "resolve_base", lambda: None)
    with pytest.raises(storage.StorageError):
        verify_matrix._cache_path("gh-api-cache.json")


def test_matrix_cache_rejects_public_companion(private_store, monkeypatch):
    import verify_matrix
    storage_visibility_fixture(Path.home() / ".pii-guard/visibility.json",
                               {"example-owner/example-private": "PUBLIC"})
    with pytest.raises(storage.StorageError):
        verify_matrix._cache_path("gh-api-cache.json")
    assert not (private_store[0] / "cache").exists()


def test_conditional_na_keeps_required_passes(private_store):
    def conditional(response):
        next(row for row in response["criteria"] if row["id"] == "U7")["verdict"] = "N/A"
    result = run_judge(private_store, caller=result_call(change=conditional))
    assert result["status"] == "completed"
    assert result["scenario_verdict"] == "PASS"
    prompt = (Path(result["result_path"]).parent / "prompt.txt").read_text(encoding="utf-8")
    contract = json.loads(prompt.split("===== CONTRACT =====\n", 1)[1])
    assert contract["applicability"]["U7"] == "conditional"
    assert contract["applicability"]["U1"] == contract["applicability"]["S2"] == "required"


def test_matrix_cache_path_is_verified_without_creating_directories(private_store):
    import verify_matrix
    base, _ = private_store
    assert verify_matrix._cache_path("gh-api-cache.json") == base / "cache/gh-api-cache.json"
    assert not (base / "cache").exists()


def test_matrix_cache_rejects_nested_repository(private_store):
    import verify_matrix
    cache = private_store[0] / "cache"
    cache.mkdir()
    subprocess.run(["git", "init", "-q", str(cache)], check=True)
    with pytest.raises(storage.StorageError):
        verify_matrix._cache_path("gh-api-cache.json")


def test_failed_cache_write_preserves_old_bytes_and_is_visible(private_store, monkeypatch):
    import verify_matrix
    cache = verify_matrix._cache_path("gh-api-cache.json")
    cache.parent.mkdir()
    cache.write_text(json.dumps(matrix_cache_fixture()), encoding="utf-8")
    before = cache.read_bytes()
    def failed_dump(*args, **kwargs):
        raise OSError("synthetic cache write failure")
    monkeypatch.setattr(verify_matrix.json, "dump", failed_dump)
    with pytest.raises(OSError, match="cache write failure"):
        verify_matrix._write_cache("gh-api-cache.json", matrix_cache_fixture())
    assert cache.read_bytes() == before
    assert list(cache.parent.iterdir()) == [cache]


def test_cache_write_rechecks_private_visibility(private_store, monkeypatch):
    import verify_matrix
    verify_matrix._cache_path("gh-api-cache.json")
    storage_visibility_fixture(Path.home() / ".pii-guard/visibility.json", {})
    with pytest.raises(storage.StorageError):
        verify_matrix._write_cache("gh-api-cache.json", matrix_cache_fixture())
    assert not (private_store[0] / "cache").exists()


def test_network_matrix_requires_storage_before_network_access(monkeypatch):
    import verify_matrix
    monkeypatch.setattr(verify_matrix, "NO_NET", False)
    monkeypatch.setattr(storage, "resolve_base", lambda: None)
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: pytest.fail("network or subprocess before private preflight"))
    assert verify_matrix.main() == 1


def test_offline_matrix_never_resolves_or_writes_runtime_cache(monkeypatch):
    import verify_matrix
    monkeypatch.setattr(verify_matrix, "NO_NET", True)
    monkeypatch.setattr(verify_matrix, "resolve_data_dir", lambda *args: None)
    monkeypatch.setattr(verify_matrix, "fails", [])
    monkeypatch.setattr(verify_matrix, "warns", [])
    monkeypatch.setattr(verify_matrix, "_cache_path", lambda *args: pytest.fail("offline cache path requested"))
    monkeypatch.setattr(verify_matrix, "_write_cache", lambda *args: pytest.fail("offline cache write"))
    verify_matrix.run_checks()
