#!/usr/bin/env python3
"""Tests for where verify_matrix keeps its GitHub activity cache.

The reason this file exists: `_cache_path` found the companion by loading tools/datadir.py by file
path and fell back to skills/shopping-aggregator/metrics/ when that file was absent. datadir.py then
moved into the guards submodule. The file check went false on every run, the fallback became the
only path ever taken, and each authenticated run wrote its cache into the public worktree, where
data_boundary blocked the next push. Nothing reported it, because "resolver missing" and "no
companion" produced the same output.

So the property under test is stated both ways:

  1. With a verified private companion, the cache lives under <companion>/data/cache/.
  2. With no companion, resolving a cache path fails before any directory is created.

Run: python test_cache_path.py     (also collectable by pytest)
"""
import os
from pathlib import Path
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_fixtures import storage_repository_fixture, storage_visibility_fixture  # noqa: E402
import verify_matrix  # noqa: E402
import evaluation_store  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _inside_repo(path):
    return os.path.commonpath([os.path.abspath(path), REPO]) == REPO


@pytest.fixture
def private_cache(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    storage_visibility_fixture(tmp_path / ".pii-guard/visibility.json")
    data, _ = storage_repository_fixture(tmp_path / "companion")
    monkeypatch.setenv("SHOPPING_AGGREGATOR_DATA_DIR", str(data))
    return data


def test_companion_cache_lives_outside_the_repo(private_cache):
    path = verify_matrix._cache_path("gh-api-cache.json")
    assert path == private_cache / "cache/gh-api-cache.json", path
    assert not _inside_repo(path), path


def test_no_companion_means_no_cache_path(tmp_path, monkeypatch):
    missing = tmp_path / "missing/data"
    monkeypatch.setenv("SHOPPING_AGGREGATOR_DATA_DIR", str(missing))
    with pytest.raises(evaluation_store.StorageError):
        verify_matrix._cache_path("gh-api-cache.json")
    assert not missing.parent.exists()


def test_the_real_resolver_is_the_one_consulted(private_cache, monkeypatch):
    # The original bug: the resolver was looked up by a file path that no longer existed, so the
    # companion branch never ran. Prove the function consults the imported resolver by making that
    # resolver unmistakable.
    calls = []
    original = evaluation_store.prepare_store

    def spy():
        store = original()
        calls.append(store.base)
        return store

    monkeypatch.setattr(evaluation_store, "prepare_store", spy)
    path = verify_matrix._cache_path("gh-api-cache.json")
    assert calls == [private_cache], calls
    assert path == private_cache / "cache/gh-api-cache.json"


if __name__ == "__main__":
    raise SystemExit(pytest.main([str(Path(__file__).resolve()), "-q"]))
