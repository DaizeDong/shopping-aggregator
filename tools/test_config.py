"""Config contract tests (CONFIG.md): init, doctor, switching between people, ledgers.

Every root here is generated from tools/make_fixtures.py; nothing reads the operator's real
companion. Each test runs under a temporary HOME with a generated visibility receipt, so the
PRIVATE proof is real but only ever sees invented repositories. Every command names its root
explicitly, because the resolver's sibling step would otherwise find whatever companion sits next
to this checkout.
"""
import copy
import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

TOOLS = Path(__file__).resolve().parent
REPO = TOOLS.parent
sys.path.insert(0, str(TOOLS))
from config_schema import (forwarder_table_problems, live_run_problems, loads_strict,  # noqa: E402
                           profile_problems, purchase_problems)
from make_fixtures import (forwarder_table_example, profile_example, purchase_examples,  # noqa: E402
                           registry_example, storage_repository_fixture, storage_visibility_fixture)

PROXY_VARS = ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY",
              "http_proxy", "https_proxy", "all_proxy", "no_proxy")
GIT_USER = ["-c", "user.name=Example User", "-c", "user.email=user1@example.com"]


def run(script, *args, stdin=None, env=None):
    result = subprocess.run([sys.executable, "-B", str(REPO / "scripts" / script), *args],
                            capture_output=True, text=True, encoding="utf-8", errors="replace",
                            input=stdin, env=env)
    return result.returncode, result.stdout + result.stderr


def paths(problems):
    return {problem[-2] for problem in problems}


@pytest.fixture
def home(tmp_path, monkeypatch):
    for name in PROXY_VARS:
        monkeypatch.delenv(name, raising=False)
    for name in ("SHOPPING_AGGREGATOR_CONFIG", "SHOPPING_AGGREGATOR_CONFIG_DIR",
                 "SHOPPING_AGGREGATOR_DATA_DIR"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    storage_visibility_fixture(tmp_path / ".pii-guard/visibility.json", {
        "example-owner/example-private": "PRIVATE",
        "example-owner/example-private-b": "PRIVATE",
        "example-owner/example-public": "PUBLIC",
    })
    return tmp_path


def write_forwarder_table(root, table=None):
    forwarder = root / "reference" / "forwarder-example-forwarder.json"
    forwarder.parent.mkdir(parents=True, exist_ok=True)
    forwarder.write_text(json.dumps(table or forwarder_table_example(), indent=2) + "\n", encoding="utf-8")


def commit(root, message="Synthetic root"):
    subprocess.run(["git", "-C", str(root), *GIT_USER, "add", "-A"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(root), *GIT_USER, "commit", "-q", "-m", message],
                   check=True, capture_output=True)


def make_root(path, identity, profile, purchases=None):
    """A filled root: init the skeleton, then fill it from the generators, then version it."""
    data, _ = storage_repository_fixture(path, identity)
    (data / "input.txt").unlink()
    code, output = run("init_config.py", "--out", str(path))
    assert code == 0, output
    (path / "profile.json").write_text(json.dumps(profile, indent=2) + "\n", encoding="utf-8")
    (path / "registry.json").write_text(json.dumps(registry_example(), indent=2) + "\n", encoding="utf-8")
    if purchases:
        (data / "purchases.jsonl").write_text("".join(json.dumps(r) + "\n" for r in purchases),
                                              encoding="utf-8")
    write_forwarder_table(path)
    commit(path)
    return path


def tree_digest(root):
    digest = hashlib.sha256()
    for path in sorted(p for p in Path(root).rglob("*") if p.is_file()):
        digest.update(path.relative_to(root).as_posix().encode() + b"\0" + path.read_bytes())
    return digest.hexdigest()


def gap_row(**extra):
    row = {"domain": "example-domain", "source": "example-source", "outcome": "coverage_gap",
           "detail": "Synthetic gap.", "user_correction": None, "gap_reason": "not-attempted"}
    row.update(extra)
    return row


# --- init and the doctor -------------------------------------------------------------------------

def test_init_is_deterministic_and_value_free(home):
    first, second = home / "a", home / "b"
    assert run("init_config.py", "--out", str(first))[0] == 0
    assert run("init_config.py", "--out", str(second))[0] == 0
    assert tree_digest(first) == tree_digest(second)
    skeleton = json.loads((first / "profile.json").read_text(encoding="utf-8"))
    assert skeleton["profile_id"] == "" and skeleton["ship_to"]["zip"] == ""
    assert skeleton["purchase_defaults"]["subscriptions"] == ""


def test_blank_profile_is_never_ready(home):
    root = home / "blank"
    storage_repository_fixture(root)
    assert run("init_config.py", "--out", str(root))[0] == 0
    code, output = run("verify_config.py", "--config-dir", str(root))
    assert code == 1 and "NOT READY" in output
    assert "profile.json.profile_id" in output and "profile.json.purchase_defaults.subscriptions" in output


def test_two_people_switch_by_selection(home, monkeypatch):
    a = make_root(home / "people-a", "example-owner/example-private", profile_example("buyer-a"),
                  purchase_examples("buyer-a"))
    b = make_root(home / "people-b", "example-owner/example-private-b",
                  profile_example("buyer-b", zip_code="10002"))
    code, output = run("verify_config.py", "--config-dir", str(a))
    assert code == 0, output
    assert output.count("resolved via") == 1 and str(a.resolve()) in output
    monkeypatch.setenv("SHOPPING_AGGREGATOR_CONFIG", str(b))
    code, output = run("verify_config.py")
    assert code == 0, output
    assert "env:SHOPPING_AGGREGATOR_CONFIG" in output and str(b.resolve()) in output


def test_a_second_person_lives_under_people_in_the_same_companion(home, monkeypatch):
    parent = make_root(home / "companion", "example-owner/example-private", profile_example("buyer-a"))
    child = parent / "people" / "buyer-b"
    code, output = run("init_config.py", "--out", str(child))
    assert code == 0, output
    (child / "profile.json").write_text(json.dumps(profile_example("buyer-b", zip_code="10002"), indent=2)
                                        + "\n", encoding="utf-8")
    (child / "registry.json").write_text(json.dumps(registry_example(), indent=2) + "\n", encoding="utf-8")
    write_forwarder_table(child)
    commit(parent, "Second person")
    code, output = run("verify_config.py", "--config-dir", str(parent), "--all")
    assert code == 0, output
    assert "people/buyer-b" in output and output.count("resolved via") == 1
    monkeypatch.setenv("SHOPPING_AGGREGATOR_CONFIG", str(child))
    code, output = run("ledger.py", "append", "purchases", "--row-file", "-",
                       stdin=json.dumps(purchase_examples("buyer-b")[1]))
    assert code == 0, output
    assert (child / "data" / "purchases.jsonl").is_file()
    assert not (parent / "data" / "purchases.jsonl").exists()


def test_all_refuses_two_roots_with_one_profile_id(home):
    parent = make_root(home / "companion", "example-owner/example-private", profile_example("buyer-a"))
    child = parent / "people" / "copy"
    assert run("init_config.py", "--out", str(child))[0] == 0
    (child / "profile.json").write_text(json.dumps(profile_example("buyer-a"), indent=2) + "\n", encoding="utf-8")
    (child / "registry.json").write_text(json.dumps(registry_example(), indent=2) + "\n", encoding="utf-8")
    write_forwarder_table(child)
    commit(parent, "Copied person")
    code, output = run("verify_config.py", "--config-dir", str(parent), "--all")
    assert code == 1 and "share one profile_id" in output


def test_public_root_cannot_hold_a_profile(home):
    root = make_root(home / "public", "example-owner/example-public", profile_example())
    code, output = run("verify_config.py", "--config-dir", str(root))
    assert code == 1 and "versioned PRIVATE repository" in output


def test_doctor_reports_paths_never_values(home):
    profile = profile_example()
    # Innocent keys with private values, and private values used as keys: only shape checks see them.
    profile["preferences"] = {"note": "write to user1@example.com", "drop-off": "12 Example Street",
                              "billing": "4111 1111 1111 1111", "user2@example.com": "size M"}
    profile["ship_to"] = dict(profile["ship_to"], street="1 Example Street")
    profile["label"] = "Call (555) 867-5309"
    root = make_root(home / "poisoned", "example-owner/example-private", profile)
    code, output = run("verify_config.py", "--config-dir", str(root))
    assert code == 1
    for field in ("preferences.note", "preferences.drop-off", "preferences.billing", "preferences.<key>",
                  "ship_to.street", "label"):
        assert "profile.json." + field in output, field
    for value in ("user1@example.com", "user2@example.com", "Example Street", "4111", "867-5309"):
        assert value not in output, value


def test_doctor_refuses_another_persons_purchases(home):
    root = make_root(home / "mixed", "example-owner/example-private", profile_example("buyer-b"),
                     purchase_examples("buyer-a"))
    code, output = run("verify_config.py", "--config-dir", str(root))
    assert code == 1 and "belongs to another config root" in output
    # Another problem in the profile must not switch the cross-root check off.
    unfinished = dict(profile_example("buyer-b"), label="")
    root = make_root(home / "mixed-unfinished", "example-owner/example-private", unfinished,
                     purchase_examples("buyer-a"))
    code, output = run("verify_config.py", "--config-dir", str(root))
    assert code == 1 and "belongs to another config root" in output


def test_forwarder_table_must_match_its_profile(home):
    table = forwarder_table_example("another-forwarder")
    del table["classes"]["general"]["2"][0]["rate_per_kg"]
    root = make_root(home / "forwarder", "example-owner/example-private", profile_example())
    write_forwarder_table(root, table)
    code, output = run("verify_config.py", "--config-dir", str(root))
    assert code == 1
    assert "profile.json.forwarders[0].rate_table: name" in output
    assert "profile.json.forwarders[0].rate_table: classes.general.2[0].rate_per_kg" in output
    assert "forwarder-example-forwarder" not in output


def test_rate_table_outside_the_root_is_never_followed(home):
    (home / "outside.json").write_text(json.dumps({"user1@example.com": 1}), encoding="utf-8")
    profile = profile_example()
    profile["forwarders"][0]["rate_table"] = "../outside.json"
    root = make_root(home / "escape", "example-owner/example-private", profile)
    code, output = run("verify_config.py", "--config-dir", str(root))
    assert code == 1 and "profile.json.forwarders[0].rate_table" in output
    assert "rate_table exists" not in output and "user1@example.com" not in output


@pytest.mark.parametrize("rule", ["data/cache/", "*.jsonl", "data/metrics/", "purchases.jsonl",
                                  "data/evaluation/"])
def test_nothing_under_data_may_be_ignored(home, rule):
    root = make_root(home / "ignored", "example-owner/example-private", profile_example())
    with (root / ".gitignore").open("a", encoding="utf-8") as stream:
        stream.write(rule + "\n")
    commit(root, "Ignore part of data/")
    code, output = run("verify_config.py", "--config-dir", str(root))
    assert code == 1 and "nothing under data/ is ignored" in output, rule


# --- selection: one root per run, nothing falls through ------------------------------------------

def test_empty_selection_never_falls_through(home):
    root = make_root(home / "a", "example-owner/example-private", profile_example())
    code, output = run("verify_config.py", "--config-dir", "")
    assert code == 1 and "empty" in output and str(root) not in output
    env = dict(os.environ, SHOPPING_AGGREGATOR_CONFIG="")
    code, output = run("ledger.py", "append", "live-runs", "--row-file", "-", stdin=json.dumps(gap_row()), env=env)
    assert code == 1 and "empty" in output
    assert not (root / "data" / "metrics" / "live-runs.jsonl").exists()


def test_the_runtime_itself_refuses_an_empty_variable(home, monkeypatch):
    # The ledger checks the environment before discovery; the runtime must refuse on its own too,
    # because the doctor and init reach it first.
    sys.path.insert(0, str(REPO / "scripts"))
    config_runtime = importlib.import_module("config_runtime")
    for variable in ("SHOPPING_AGGREGATOR_CONFIG", "SHOPPING_AGGREGATOR_CONFIG_DIR"):
        monkeypatch.setenv(variable, " ")
        with pytest.raises(config_runtime.ConfigError):
            config_runtime.ConfigRuntime(None).discover(None)
        monkeypatch.delenv(variable)


def test_stale_data_dir_override_fails_after_a_switch(home, monkeypatch):
    a = make_root(home / "a", "example-owner/example-private", profile_example("buyer-a"))
    b = make_root(home / "b", "example-owner/example-private-b", profile_example("buyer-b"))
    monkeypatch.setenv("SHOPPING_AGGREGATOR_DATA_DIR", str(a / "data"))
    code, output = run("verify_config.py", "--config-dir", str(b))
    assert code == 1 and "_DATA_DIR is the selected root's data/" in output
    monkeypatch.setenv("SHOPPING_AGGREGATOR_DATA_DIR", str(b))
    assert run("verify_config.py", "--config-dir", str(b))[0] == 1
    monkeypatch.setenv("SHOPPING_AGGREGATOR_DATA_DIR", str(b / "data"))
    code, output = run("verify_config.py", "--config-dir", str(b))
    assert code == 0, output


def test_environment_must_agree_with_an_explicit_root(home, monkeypatch):
    a = make_root(home / "a", "example-owner/example-private", profile_example("buyer-a"))
    b = make_root(home / "b", "example-owner/example-private-b", profile_example("buyer-b"))
    monkeypatch.setenv("SHOPPING_AGGREGATOR_CONFIG", str(a))
    code, output = run("verify_config.py", "--config-dir", str(b))
    assert code == 1 and "SHOPPING_AGGREGATOR_CONFIG agrees with --config-dir" in output


# --- ledgers -------------------------------------------------------------------------------------

def test_ledger_appends_to_the_selected_root_only(home):
    a = make_root(home / "a", "example-owner/example-private", profile_example("buyer-a"))
    b = make_root(home / "b", "example-owner/example-private-b", profile_example("buyer-b"))
    row = json.dumps(purchase_examples("buyer-b")[1])
    code, output = run("ledger.py", "append", "purchases", "--row-file", "-", "--config-dir", str(b), stdin=row)
    assert code == 0, output
    assert (b / "data" / "purchases.jsonl").read_text(encoding="utf-8").count("\n") == 1
    assert not (a / "data" / "purchases.jsonl").exists()
    code, output = run("ledger.py", "append", "purchases", "--row-file", "-", "--config-dir", str(a), stdin=row)
    assert code == 1 and "REFUSED" in output and "buyer-b" not in output
    assert not (a / "data" / "purchases.jsonl").exists()


def test_purchase_rows_must_name_their_profile(home):
    root = make_root(home / "a", "example-owner/example-private", profile_example("buyer-a"))
    row = dict(purchase_examples("buyer-a")[0])
    del row["profile_id"]
    code, output = run("ledger.py", "append", "purchases", "--row-file", "-", "--config-dir", str(root),
                       stdin=json.dumps(row))
    assert code == 1 and "profile_id" in output
    assert not (root / "data" / "purchases.jsonl").exists()


def test_ledger_refuses_invalid_rows_and_public_roots(home):
    private = make_root(home / "private", "example-owner/example-private", profile_example())
    public = make_root(home / "public", "example-owner/example-public", profile_example())
    gap = gap_row()
    del gap["gap_reason"]
    code, output = run("ledger.py", "append", "live-runs", "--row", json.dumps(gap), "--config-dir", str(private))
    assert code == 1 and "gap_reason" in output
    code, output = run("ledger.py", "append", "live-runs", "--row", json.dumps(gap_row(outcome="verfied")),
                       "--config-dir", str(private))
    assert code == 1 and "outcome" in output
    assert not (private / "data" / "metrics" / "live-runs.jsonl").exists()
    code, output = run("ledger.py", "append", "live-runs", "--row", json.dumps(gap_row()), "--config-dir", str(public))
    assert code == 1 and "REFUSED" in output
    assert not (public / "data" / "metrics" / "live-runs.jsonl").exists()
    code, output = run("ledger.py", "append", "live-runs", "--row", json.dumps(gap_row(ts=None)),
                       "--config-dir", str(private))
    assert code == 0, output
    written = json.loads((private / "data" / "metrics" / "live-runs.jsonl").read_text(encoding="utf-8"))
    assert written["ts"]
    assert run("ledger.py", "check", "--config-dir", str(private))[0] == 0


def test_row_files_never_live_in_the_public_repository(home):
    root = make_root(home / "a", "example-owner/example-private", profile_example())
    code, output = run("ledger.py", "append", "live-runs", "--row-file", str(REPO / "row.json"),
                       "--config-dir", str(root))
    assert code == 1 and "inside the public tool repository" in output
    assert not (REPO / "row.json").exists()


def test_concurrent_appends_all_land(home):
    root = make_root(home / "a", "example-owner/example-private", profile_example())
    workers = [subprocess.Popen([sys.executable, "-B", str(REPO / "scripts" / "ledger.py"), "append", "live-runs",
                                 "--row-file", "-", "--config-dir", str(root)],
                                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
               for _ in range(6)]
    outputs = [worker.communicate(json.dumps(gap_row(detail="Synthetic gap %d." % index)), timeout=300)[0]
               for index, worker in enumerate(workers)]
    assert all(worker.returncode == 0 for worker in workers), outputs
    lines = (root / "data" / "metrics" / "live-runs.jsonl").read_text(encoding="utf-8").splitlines()
    assert sorted(json.loads(line)["detail"] for line in lines) == sorted(
        "Synthetic gap %d." % index for index in range(6))


def test_the_lock_serialises_read_and_replace(home, monkeypatch):
    """Two writers whose read-then-replace overlap: without the lock one row is silently lost."""
    import threading
    import time
    root = make_root(home / "a", "example-owner/example-private", profile_example())
    sys.path.insert(0, str(REPO / "scripts"))
    ledger = importlib.import_module("ledger")
    real_prepare = ledger.prepare_store

    class SlowStore:
        def __init__(self, store):
            self.store = store

        def output_path(self, relative):
            return self.store.output_path(relative)

        def write_bytes(self, relative, data):
            time.sleep(1.5)
            return self.store.write_bytes(relative, data)

    monkeypatch.setattr(ledger, "prepare_store", lambda base=None: SlowStore(real_prepare(base=base)))
    errors = []

    def write(index):
        try:
            ledger.append("live-runs", gap_row(detail="Overlap %d." % index), str(root))
        except Exception as exc:  # surfaced below
            errors.append(exc)

    threads = [threading.Thread(target=write, args=(index,)) for index in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=300)
    assert not errors, errors
    lines = (root / "data" / "metrics" / "live-runs.jsonl").read_text(encoding="utf-8").splitlines()
    assert sorted(json.loads(line)["detail"] for line in lines) == ["Overlap 0.", "Overlap 1."]


def test_check_degrades_when_nothing_is_initialized(monkeypatch, capsys):
    sys.path.insert(0, str(REPO / "scripts"))
    ledger = importlib.import_module("ledger")

    class Uninitialized:
        def __init__(self, *_args):
            pass

        def discover(self, *_args):
            return None, None

    monkeypatch.setattr(ledger, "ConfigRuntime", Uninitialized)
    assert ledger.check("all", None) == 0
    assert "uninitialized" in capsys.readouterr().out


# --- schema, without subprocesses ----------------------------------------------------------------

def test_privacy_scan_catches_shapes_and_spares_categories():
    profile = profile_example()
    profile["label"] = "Call (555) 867-5309"
    assert "label" in paths(profile_problems(profile))
    # One poisoned entry per profile, each a different check, so no check hides behind another.
    for key, value, expected in (("bank", "routing 021000021 acct 000123456789", "preferences.bank"),
                                 ("user1@example.com", "size M", "preferences.<key>"),
                                 ("4111 1111 1111 1111", "visa", "preferences.<key>"),
                                 ("session", "AbC123x" * 6, "preferences.session"),
                                 ("pwd", "x", "preferences.pwd"),
                                 ("card-number", "x", "preferences.card-number"),
                                 ("birthday", "1990-01-01", "preferences.birthday")):
        profile = profile_example()
        profile["preferences"] = {key: value}
        found = paths(profile_problems(profile))
        assert expected in found, key
        assert not any("example.com" in path or "4111" in path for path in found)
    for city in ("12B Example Street", "Apt 5, 12 Example Street"):
        profile = profile_example()
        profile["ship_to"]["city"] = city
        assert "ship_to.city" in paths(profile_problems(profile)), city
    profile = profile_example()
    profile["accounts"][0]["identity"] = "5558675309"
    assert "accounts[0].identity" in paths(profile_problems(profile))
    profile = profile_example()
    profile["preferences"] = {"graphics-card": "white, 2-slot", "headphones": "over-ear",
                              "cookies": "no nuts", "streetwear": "size M", "birthday-gifts": "early",
                              "software-license": "annual", "phone-case": "clear",
                              "detergent": "2 bags, 12 ct pods", "pack": "2 pack any way works",
                              "rolling-pin": "maple", "enamel-pin": "small", "pin-badges": "round",
                              "victorias-secret": "unscented", "secret-deodorant": "clear gel",
                              "passport-holder": "leather", "passport-cover": "black",
                              "no-store-card": "true", "no-account-checkout": "guest",
                              "credit-card": "use the one with grocery cash back", "gift-card": "use first",
                              "promo-code": "none"}
    assert profile_problems(profile) == []


@pytest.mark.parametrize("key", ["wifi-password", "atm-pin", "pin", "passport-number", "api-key",
                                 "date-of-birth", "drivers-license-number", "card-number", "ssn",
                                 "social-security-number", "routing", "secret"])
def test_credential_names_are_refused(key):
    profile = profile_example()
    profile["preferences"] = {key: "x"}
    assert "preferences." + key in paths(profile_problems(profile)), key


@pytest.mark.parametrize("value", ["1 Example Way", "12 Example Circle", "Example Street 12",
                                   "12, Example Road", "PO Box 1234", "One Example Street",
                                   "Apt 5, 12 Example Street", "12B Example Street"])
def test_street_shapes_are_refused(value):
    profile = profile_example()
    profile["ship_to"]["city"] = value
    assert "ship_to.city" in paths(profile_problems(profile)), value


def test_zip_and_retailer_fields_have_real_shapes():
    for zip_code in ("5558675309", "1000", "ABCDE"):
        profile = profile_example()
        profile["ship_to"]["zip"] = zip_code
        assert "ship_to.zip" in paths(profile_problems(profile)), zip_code
    for zip_code in ("10001", "10001-1234"):
        profile = profile_example()
        profile["ship_to"]["zip"] = zip_code
        assert profile_problems(profile) == [], zip_code
    for retailer in ("*", "all retailers", "https://www.example.com/", "Example.com"):
        profile = profile_example()
        profile["accounts"][0]["retailer"] = retailer
        assert "accounts[0].retailer" in paths(profile_problems(profile)), retailer


def test_closed_objects_refuse_unknown_fields():
    for mutate, field in ((lambda p: p["market"].update(stack_discounts="never"), "market.stack_discounts"),
                          (lambda p: p["home_stores"][0].update(skip="yes"), "home_stores[0].skip"),
                          (lambda p: p["purchase_defaults"].update(clip_coupons=False),
                           "purchase_defaults.clip_coupons")):
        profile = profile_example()
        mutate(profile)
        assert field in paths(profile_problems(profile)), field


def test_validators_never_raise_on_wrong_types():
    profile = profile_example()
    profile["accounts"][0]["checkout"] = ["agent"]
    profile["purchase_defaults"]["subscriptions"] = ["ask"]
    profile["travel"]["cabin"] = {"a": 1}
    profile["forwarders"][0]["zone"] = ["1"]
    profile["home_stores"] = [7]
    assert {"accounts[0].checkout", "purchase_defaults.subscriptions", "travel.cabin", "forwarders[0].zone",
            "home_stores[0]"} <= paths(profile_problems(profile))
    deep = profile_example()
    nest = "leaf"
    for _ in range(40):
        nest = [nest]
    deep["preferences"] = {"deep": nest}
    assert profile_problems(deep)
    row = copy.deepcopy(purchase_examples()[1])
    row.update(status=["placed"], path={"x": 1}, paid_with=[1])
    row["discounts"][0]["mark"] = ["cart_tested"]
    assert {"status", "path", "paid_with", "discounts[0].mark"} <= paths(purchase_problems(row))
    assert "outcome" in paths(live_run_problems(gap_row(outcome=["x"])))
    assert "gap_reason" in paths(live_run_problems(gap_row(gap_reason=["y"])))
    table = forwarder_table_example()
    table["zone_by"] = ["zip-first-digit"]
    assert "zone_by" in paths(forwarder_table_problems(table, zone=["1"]))


def test_ledger_rows_need_real_values():
    assert "domain" in paths(live_run_problems(gap_row(domain=None)))
    assert "ts" in paths(live_run_problems(gap_row(ts="2026-13-45")))
    assert live_run_problems(gap_row(ts="2026-01-02")) == []
    row = dict(purchase_examples()[0], retailer=None)
    assert "retailer" in paths(purchase_problems(row))
    cancelled = copy.deepcopy(purchase_examples()[1])
    cancelled["status"] = "cancelled"
    del cancelled["subscription"]["next_delivery"]
    assert purchase_problems(cancelled) == []
    placed = copy.deepcopy(purchase_examples()[1])
    del placed["subscription"]["next_delivery"]
    assert "subscription.next_delivery" in paths(purchase_problems(placed))
    replaced = dict(purchase_examples()[0], status="replaced")
    assert "replaced_by" in paths(purchase_problems(replaced))
    assert "replaced_by" in paths(purchase_problems(dict(replaced, replaced_by=replaced["order_ref"])))
    assert "replaced_by" in paths(purchase_problems(dict(purchase_examples()[0], replaced_by="EX-9")))
    with pytest.raises(ValueError):
        loads_strict('{"charged_total": NaN}')
    with pytest.raises(ValueError):
        loads_strict('{"a": 1, "a": 2}')


def test_forwarder_facts_must_agree_with_the_profile():
    table = forwarder_table_example()
    assert forwarder_table_problems(table, "example-forwarder", "1", True) == []
    assert "duty_inclusive" in paths(forwarder_table_problems(table, "example-forwarder", "1", False))
    assert "zones" in paths(forwarder_table_problems(table, "example-forwarder", "9", True))


# --- round 2: encoding, selection for tools/, ownership, shapes ---------------------------------

def test_stdin_rows_are_utf8_and_stay_one_line(home):
    root = make_root(home / "a", "example-owner/example-private", profile_example())
    row = gap_row(detail="Synthetic Caf\u00e9 \u517d\u5934 note \u2028 split \u0085 here")
    code, output = run("ledger.py", "append", "live-runs", "--row-file", "-", "--config-dir", str(root),
                       stdin=json.dumps(row, ensure_ascii=False))
    assert code == 0, output
    raw = (root / "data" / "metrics" / "live-runs.jsonl").read_bytes().decode("utf-8")
    assert raw.count("\n") == 1 and "\u2028" not in raw and "\u0085" not in raw
    assert json.loads(raw)["detail"] == row["detail"]
    assert run("ledger.py", "check", "--config-dir", str(root))[0] == 0
    assert run("verify_config.py", "--config-dir", str(root))[0] == 0


def test_a_selection_variable_that_is_set_must_be_usable(home, monkeypatch):
    root = make_root(home / "a", "example-owner/example-private", profile_example())
    missing = str(home / "no-such-root")
    env = dict(os.environ, SHOPPING_AGGREGATOR_CONFIG=missing)
    code, output = run("ledger.py", "append", "live-runs", "--row-file", "-", "--config-dir", str(root),
                       stdin=json.dumps(gap_row()), env=env)
    assert code == 1 and "not an existing directory" in output
    assert not (root / "data" / "metrics" / "live-runs.jsonl").exists()
    result = subprocess.run([sys.executable, "-B", str(TOOLS / "refresh_priority.py")], env=env,
                            capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert result.returncode != 0 and "not an existing directory" in result.stdout + result.stderr
    import evaluation_store
    monkeypatch.setenv("SHOPPING_AGGREGATOR_CONFIG", "")
    with pytest.raises(evaluation_store.StorageError):
        evaluation_store.resolve_base()


def test_the_writer_refuses_a_conflicting_environment(home):
    a = make_root(home / "a", "example-owner/example-private", profile_example("buyer-a"))
    b = make_root(home / "b", "example-owner/example-private-b", profile_example("buyer-b"))
    env = dict(os.environ, SHOPPING_AGGREGATOR_DATA_DIR=str(b / "data"))
    code, output = run("ledger.py", "append", "live-runs", "--row-file", "-", "--config-dir", str(a),
                       stdin=json.dumps(gap_row()), env=env)
    assert code == 1 and "_DATA_DIR is the selected root's data/" in output
    env = dict(os.environ, SHOPPING_AGGREGATOR_CONFIG=str(b))
    code, output = run("ledger.py", "append", "live-runs", "--row-file", "-", "--config-dir", str(a),
                       stdin=json.dumps(gap_row()), env=env)
    assert code == 1 and "agrees with --config-dir" in output
    assert not (a / "data" / "metrics" / "live-runs.jsonl").exists()


def test_a_data_only_location_is_not_a_root(home):
    store = home / "store"
    (store / "data").mkdir(parents=True)
    env = dict(os.environ, SHOPPING_AGGREGATOR_DATA_DIR=str(store))
    code, output = run("verify_config.py", env=env)
    assert code == 1 and "resolver data dir is the root's data/" in output
    code, output = run("ledger.py", "append", "live-runs", "--row-file", "-", stdin=json.dumps(gap_row()), env=env)
    assert code == 1 and "REFUSED" in output
    assert not (store / "data" / "metrics").exists()


def test_ownership_is_checked_even_when_the_profile_id_is_unusable(home):
    unusable = dict(profile_example("buyer-b"), profile_id="Buyer B")
    root = make_root(home / "unusable", "example-owner/example-private", unusable, purchase_examples("buyer-a"))
    code, output = run("verify_config.py", "--config-dir", str(root))
    assert code == 1 and "ownership cannot be checked" in output
    code, output = run("ledger.py", "check", "--config-dir", str(root))
    assert code == 1 and "ownership cannot be checked" in output


def test_forwarder_zone_must_match_the_ship_to_zip():
    table = forwarder_table_example()
    assert forwarder_table_problems(table, "example-forwarder", "1", True, "10001") == []
    assert "zones" in paths(forwarder_table_problems(table, "example-forwarder", "2", True, "10001"))


def test_timestamps_and_subscription_terms_are_exact():
    assert "ts" in paths(live_run_problems(gap_row(ts="2026-01-02T25:61:61Z")))
    assert "ts" in paths(live_run_problems(gap_row(ts=123)))
    assert live_run_problems(gap_row(ts="2026-01-02T03:04:05Z")) == []
    cancelled = copy.deepcopy(purchase_examples()[1])
    cancelled["status"] = "cancelled"
    cancelled["subscription"]["next_delivery"] = None
    assert purchase_problems(cancelled) == []
    every_ten_days = copy.deepcopy(purchase_examples()[1])
    every_ten_days["subscription"]["interval"] = "10-days"
    assert purchase_problems(every_ten_days) == []


def test_the_writer_refuses_a_non_string_timestamp(home):
    root = make_root(home / "a", "example-owner/example-private", profile_example())
    code, output = run("ledger.py", "append", "live-runs", "--row-file", "-", "--config-dir", str(root),
                       stdin=json.dumps(gap_row(ts=123)))
    assert code == 1 and "ts" in output


def test_the_matrix_refuses_a_tracked_config_root(tmp_path):
    import shutil
    from make_fixtures import matrix_package_fixture
    package = tmp_path / "package"
    matrix_package_fixture(package)
    for relative in ("tools/verify_matrix.py", "tools/config_schema.py", "tools/config_selection.py",
                     "tools/delivery_check.py", "guards/tools/datadir.py"):
        destination = package / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO / relative, destination)
    copied = package / "notes" / "my-root" / "profile.json"
    copied.parent.mkdir(parents=True)
    copied.write_text(json.dumps(profile_example()), encoding="utf-8")
    environment = {key: value for key, value in os.environ.items()
                   if not key.upper().startswith(("GIT_", "SHOPPING_AGGREGATOR_"))}
    environment.update(HOME=str(tmp_path), USERPROFILE=str(tmp_path), PYTHONUTF8="1")
    subprocess.run(["git", "init", "-q", str(package)], env=environment, check=True)
    subprocess.run(["git", "-C", str(package), "add", "-f", "."], env=environment, check=True)
    result = subprocess.run([sys.executable, "-B", str(package / "tools/verify_matrix.py"), "--no-net"],
                            env=environment, capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert result.returncode == 1 and "CONFIGROOT" in result.stdout + result.stderr
