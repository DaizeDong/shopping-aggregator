#!/usr/bin/env python3
"""Tests for where verify_matrix keeps its GitHub activity cache.

The reason this file exists: `_cache_path` found the companion by loading tools/datadir.py by file
path and fell back to skills/shopping-aggregator/metrics/ when that file was absent. datadir.py then
moved into the guards submodule. The file check went false on every run, the fallback became the
only path ever taken, and each authenticated run wrote its cache into the public worktree, where
data_boundary blocked the next push. Nothing reported it, because "resolver missing" and "no
companion" produced the same output.

So the property under test is stated both ways:

  1. With a companion, the cache lives under <companion>/data/cache/, never under the repo.
  2. With no companion, there is no cache path at all. None, not an in-repo default.

Run: python test_cache_path.py     (also collectable by pytest)
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verify_matrix  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _inside_repo(path):
    return os.path.commonpath([os.path.abspath(path), REPO]) == REPO


def test_companion_cache_lives_outside_the_repo():
    with tempfile.TemporaryDirectory() as comp:
        original = verify_matrix.resolve_companion_root
        verify_matrix.resolve_companion_root = lambda skill: comp
        try:
            path = verify_matrix._cache_path("gh-api-cache.json")
        finally:
            verify_matrix.resolve_companion_root = original
        assert path == os.path.join(comp, "data", "cache", "gh-api-cache.json"), path
        assert not _inside_repo(path), path


def test_no_companion_means_no_cache_path():
    original = verify_matrix.resolve_companion_root
    verify_matrix.resolve_companion_root = lambda skill: None
    try:
        path = verify_matrix._cache_path("gh-api-cache.json")
    finally:
        verify_matrix.resolve_companion_root = original
    assert path is None, "no companion must mean no cache, got %r" % (path,)


def test_the_real_resolver_is_the_one_consulted():
    # The original bug: the resolver was looked up by a file path that no longer existed, so the
    # companion branch never ran. Prove the function consults the imported resolver by making that
    # resolver unmistakable.
    calls = []
    original = verify_matrix.resolve_companion_root

    def spy(skill):
        calls.append(skill)
        return None

    verify_matrix.resolve_companion_root = spy
    try:
        verify_matrix._cache_path("gh-api-cache.json")
    finally:
        verify_matrix.resolve_companion_root = original
    assert calls == ["shopping-aggregator"], calls


if __name__ == "__main__":
    test_companion_cache_lives_outside_the_repo()
    test_no_companion_means_no_cache_path()
    test_the_real_resolver_is_the_one_consulted()
    print("ok: 3 cache-path tests passed")
