"""Native Git controls for the PRIVATE storage boundary, using generated repositories."""
from pathlib import Path
import json
import os
import subprocess
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import evaluation_store as storage
from make_fixtures import (evaluation_fixture, storage_repository_fixture,
                           storage_visibility_fixture)


@pytest.fixture
def storage_environment(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    receipt = storage_visibility_fixture(tmp_path / ".pii-guard/visibility.json", {
        "example-owner/example-private": "PRIVATE",
        "example-owner/example-public": "PUBLIC",
    })
    return receipt


@pytest.mark.parametrize("destination,selectors,rejected", [
    ("private", False, False), ("public", False, True), ("public", True, True),
])
def test_physical_repository_controls_storage(tmp_path, monkeypatch, storage_environment,
                                              destination, selectors, rejected):
    private, _ = storage_repository_fixture(tmp_path / "private")
    public, _ = storage_repository_fixture(tmp_path / "public", "example-owner/example-public")
    target = public if destination == "public" else private
    monkeypatch.setenv("SHOPPING_AGGREGATOR_DATA_DIR", str(target))
    if selectors:
        monkeypatch.setenv("GIT_DIR", str(private.parent / ".git"))
        monkeypatch.setenv("GIT_WORK_TREE", str(public.parent))
    if rejected:
        with pytest.raises(storage.StorageError):
            storage.prepare_store()
    else:
        assert storage.prepare_store().repository == private.parent
    assert not (target / "evaluation").exists()


@pytest.fixture
def prepared(tmp_path, monkeypatch, storage_environment):
    data, transcript = storage_repository_fixture(tmp_path / "companion")
    monkeypatch.setenv("SHOPPING_AGGREGATOR_DATA_DIR", str(data))
    return storage.prepare_store(), transcript


def test_arbitrary_remote_name_is_supported(tmp_path, monkeypatch, storage_environment):
    data, _ = storage_repository_fixture(tmp_path / "companion", remote_name="backup")
    monkeypatch.setenv("SHOPPING_AGGREGATOR_DATA_DIR", str(data))
    assert storage.prepare_store().repository == data.parent


def test_unborn_repository_is_not_versioned(tmp_path, monkeypatch, storage_environment):
    data, _ = storage_repository_fixture(tmp_path / "companion", head=False)
    monkeypatch.setenv("SHOPPING_AGGREGATOR_DATA_DIR", str(data))
    with pytest.raises(storage.StorageError, match="versioned"):
        storage.prepare_store()


@pytest.mark.parametrize("route", ["public", "unknown"])
def test_push_destination_must_also_be_private(prepared, route):
    store, _ = prepared
    subprocess.run(["git", "-C", str(store.repository), "remote", "set-url", "--push", "origin",
                    f"https://github.com/example-owner/example-{route}.git"], check=True)
    with pytest.raises(storage.StorageError):
        store.output_path("cache/result.json")
    assert not (store.base / "cache").exists()


def test_effective_rewrite_cannot_hide_public_physical_remote(tmp_path, monkeypatch, storage_environment):
    data, _ = storage_repository_fixture(tmp_path / "public", "example-owner/example-public")
    monkeypatch.setenv("SHOPPING_AGGREGATOR_DATA_DIR", str(data))
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "url.https://github.com/example-owner/example-private.git.insteadOf")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", "https://github.com/example-owner/example-public.git")
    with pytest.raises(storage.StorageError):
        storage.prepare_store()


@pytest.mark.parametrize("operation", ["transcript", "output"])
def test_existing_store_rechecks_receipt(prepared, storage_environment, operation):
    store, transcript = prepared
    storage_visibility_fixture(storage_environment, {"example-owner/example-private": "PUBLIC"})
    with pytest.raises(storage.StorageError):
        if operation == "transcript":
            store.transcript(transcript)
        else:
            store.write_bytes("cache/result.json", evaluation_fixture()["transcript"].encode())
    assert not (store.base / "cache").exists()


@pytest.mark.parametrize("receipt_kind", ["missing", "damaged", "stale", "future"])
def test_unverifiable_receipt_fails_closed(prepared, storage_environment, receipt_kind):
    from datetime import datetime, timedelta, timezone
    store, _ = prepared
    if receipt_kind == "missing":
        storage_environment.unlink()
    elif receipt_kind == "damaged":
        storage_environment.write_text("{", encoding="utf-8")
    else:
        days = -365 if receipt_kind == "stale" else 2
        refreshed = (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()
        storage_visibility_fixture(storage_environment, refreshed=refreshed)
    with pytest.raises(storage.StorageError):
        store.output_path("cache/result.json")


@pytest.mark.parametrize("target", ["data/", "data/cache/", "data/input.txt"])
def test_ignored_runtime_paths_are_rejected(prepared, target):
    store, transcript = prepared
    (store.repository / ".gitignore").write_text(target + "\n", encoding="utf-8")
    with pytest.raises(storage.StorageError, match="version control"):
        if target.endswith("input.txt"):
            store.transcript(transcript)
        else:
            store.output_path("cache/result.json")


def test_nested_private_repository_cannot_replace_store_authority(prepared):
    store, _ = prepared
    nested, _ = storage_repository_fixture(store.base / "cache")
    with pytest.raises(storage.StorageError, match="changed"):
        store.output_path("cache/result.json")
    assert not (nested.parent / "result.json").exists()


def test_hardlink_input_is_rejected(prepared, tmp_path):
    store, transcript = prepared
    alias = tmp_path / "alias.txt"
    os.link(transcript, alias)
    with pytest.raises(storage.StorageError, match="alias"):
        store.transcript(transcript)


def test_atomic_write_rechecks_before_replace(prepared, storage_environment):
    store, _ = prepared
    path = store.base / "result.json"
    before = evaluation_fixture()["transcript"].encode()
    path.write_bytes(before)
    with pytest.raises(storage.StorageError):
        with store.atomic_writer("result.json") as stream:
            json.dump(evaluation_fixture(), stream)
            storage_visibility_fixture(storage_environment, {"example-owner/example-private": "PUBLIC"})
    assert path.read_bytes() == before
    assert sorted(p.name for p in store.base.iterdir()) == ["input.txt", "result.json"]


def test_private_proof_does_not_launch_a_transport(prepared, monkeypatch):
    store, _ = prepared
    original = subprocess.run
    def git_only(args, *positional, **kwargs):
        assert Path(args[0]).name.lower() in {"git", "git.exe"}
        return original(args, *positional, **kwargs)
    monkeypatch.setattr(subprocess, "run", git_only)
    assert store.output_path("cache/result.json") == store.base / "cache/result.json"


def test_repository_root_storage_cannot_write_git_metadata(prepared, monkeypatch):
    store, _ = prepared
    monkeypatch.setenv("SHOPPING_AGGREGATOR_DATA_DIR", str(store.repository))
    rooted = storage.prepare_store()
    configuration = store.repository / ".git/config"
    before = configuration.read_bytes()
    with pytest.raises(storage.StorageError):
        rooted.write_bytes(".git/config", evaluation_fixture()["transcript"].encode())
    assert configuration.read_bytes() == before


def test_directory_alias_cannot_redirect_output(prepared, tmp_path):
    store, _ = prepared
    target, _ = storage_repository_fixture(tmp_path / "public", "example-owner/example-public")
    alias = store.base / "cache"
    if os.name == "nt":
        subprocess.run(["cmd", "/d", "/c", "mklink", "/J", str(alias), str(target)],
                       capture_output=True, check=True)
    else:
        alias.symlink_to(target, target_is_directory=True)
    try:
        with pytest.raises(storage.StorageError, match="alias"):
            store.write_bytes("cache/result.json", evaluation_fixture()["transcript"].encode())
        assert not (target / "result.json").exists()
    finally:
        if os.name == "nt":
            alias.rmdir()
        else:
            alias.unlink()
