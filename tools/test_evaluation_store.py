"""Path-only controls for the companion storage boundary, using generated repositories.

Runtime writes carry no PRIVATE visibility proof: no receipt, no remote lookup and no git
subprocess. These tests pin what is left: resolution with no fallback, a separate versioned
companion outside the tool tree, and destinations that stay inside the data directory, outside
Git metadata and free of filesystem aliases.
"""
from pathlib import Path
import json
import os
import subprocess
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import evaluation_store as storage
from make_fixtures import evaluation_fixture, storage_repository_fixture


@pytest.fixture
def storage_environment(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    for name in ("SHOPPING_AGGREGATOR_CONFIG", "SHOPPING_AGGREGATOR_CONFIG_DIR"):
        monkeypatch.delenv(name, raising=False)
    return tmp_path


@pytest.mark.parametrize("identity", ["example-owner/example-private", "example-owner/example-public"])
def test_remote_visibility_is_not_consulted(tmp_path, monkeypatch, storage_environment, identity):
    data, _ = storage_repository_fixture(tmp_path / "companion", identity)
    monkeypatch.setenv("SHOPPING_AGGREGATOR_DATA_DIR", str(data))
    assert not (tmp_path / ".pii-guard").exists()
    assert storage.prepare_store().repository == data.parent
    assert not (data / "evaluation").exists()


@pytest.fixture
def prepared(tmp_path, monkeypatch, storage_environment):
    data, transcript = storage_repository_fixture(tmp_path / "companion")
    monkeypatch.setenv("SHOPPING_AGGREGATOR_DATA_DIR", str(data))
    return storage.prepare_store(), transcript


def test_arbitrary_remote_name_is_supported(tmp_path, monkeypatch, storage_environment):
    data, _ = storage_repository_fixture(tmp_path / "companion", remote_name="backup")
    monkeypatch.setenv("SHOPPING_AGGREGATOR_DATA_DIR", str(data))
    assert storage.prepare_store().repository == data.parent


def test_unversioned_directory_is_refused(tmp_path, monkeypatch, storage_environment):
    data = tmp_path / "plain" / "data"
    data.mkdir(parents=True)
    monkeypatch.setenv("SHOPPING_AGGREGATOR_DATA_DIR", str(data))
    with pytest.raises(storage.StorageError, match="versioned"):
        storage.prepare_store()


def test_missing_data_directory_raises_with_initialization_guidance(tmp_path, monkeypatch,
                                                                    storage_environment):
    with pytest.raises(storage.StorageError, match="Uninitialized"):
        storage.prepare_store(base=tmp_path / "absent")
    assert not (tmp_path / "absent").exists()


def test_data_inside_the_tool_repository_is_refused(tmp_path, storage_environment):
    with pytest.raises(storage.StorageError):
        storage.prepare_store(base=storage.TOOL_ROOT / "tools")


def test_store_runs_no_subprocess(prepared, monkeypatch):
    store, transcript = prepared
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: pytest.fail("runtime write ran a process"))
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: pytest.fail("runtime write ran a process"))
    assert store.output_path("cache/result.json") == store.base / "cache/result.json"
    assert store.transcript(transcript) == transcript.resolve()
    store.write_bytes("cache/result.json", b"synthetic")
    assert (store.base / "cache/result.json").read_bytes() == b"synthetic"


def test_destination_cannot_escape_the_data_directory(prepared, tmp_path):
    store, _ = prepared
    with pytest.raises(storage.StorageError, match="escapes"):
        store.output_path("../outside.json")
    with pytest.raises(storage.StorageError, match="escapes"):
        store.transcript(tmp_path / "elsewhere.txt")


def test_nested_repository_is_refused(prepared):
    store, _ = prepared
    nested, _ = storage_repository_fixture(store.base / "cache")
    with pytest.raises(storage.StorageError, match="nested"):
        store.output_path("cache/result.json")
    assert not (nested.parent / "result.json").exists()


def test_hardlink_input_is_rejected(prepared, tmp_path):
    store, transcript = prepared
    alias = tmp_path / "alias.txt"
    os.link(transcript, alias)
    with pytest.raises(storage.StorageError, match="alias"):
        store.transcript(transcript)


def test_failed_write_preserves_old_bytes(prepared):
    store, _ = prepared
    path = store.base / "cache/result.json"
    path.parent.mkdir()
    before = evaluation_fixture()["transcript"].encode()
    path.write_bytes(before)
    with pytest.raises(RuntimeError):
        with store.atomic_writer("cache/result.json") as stream:
            json.dump(evaluation_fixture(), stream)
            raise RuntimeError("synthetic failure")
    assert path.read_bytes() == before


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
