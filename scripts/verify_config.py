#!/usr/bin/env python3
"""Doctor for a shopping-aggregator config root: layout, registry, profile, tables and ledgers.

Uses the emitted consumer identity and its pinned guards resolver, regardless of caller cwd.
Explicit --config-dir, SHOPPING_AGGREGATOR_CONFIG and _CONFIG_DIR selections take precedence and
never fall through. Prints exactly one "resolved via <how> -> <path>" line for the selected root.

Exit 0: the root conforms to CONFIG.md (layout, registry, a filled profile, valid tables and
ledgers, overrides that agree with the selection). Exit 1: a check failed, including a profile
nobody has filled yet. Exit 2: usage error. Conformance is not proof that any retailer, session
or MCP works; those need their own exercise.

Usage: python scripts/verify_config.py [--config-dir <dir>] [--all]
Stdlib only. Reports field paths, never the values in them.
"""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from config_runtime import ConfigRuntime, env_var, secrets_ignore_problems

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from config_schema import (forwarder_table_problems, live_run_problems, load_strict_json,  # noqa: E402
                           loads_strict, profile_id_of, profile_problems, purchase_problems,
                           rate_table_ok)
from config_selection import selection_checks  # noqa: E402
from evaluation_store import StorageError, prove_private  # noqa: E402

PASS, FAIL = "PASS", "FAIL"
LOAD_ERRORS = (OSError, ValueError, RecursionError)
# Every path the writers create under data/. The private store refuses an ignored path, so one
# ignore rule that matches any of these turns that writer off while everything else looks fine.
DATA_PROBES = ("data/metrics/live-runs.jsonl", "data/metrics/live-runs.legacy.jsonl", "data/purchases.jsonl",
               "data/evaluation/runs/probe/result.json", "data/cache/gh-api-cache.json")


def load_problem(exc):
    """Describe a load failure without echoing input."""
    if isinstance(exc, json.JSONDecodeError):
        return "invalid JSON at line %d, column %d" % (exc.lineno, exc.colno)
    if isinstance(exc, UnicodeDecodeError):
        return "not valid UTF-8"
    if isinstance(exc, RecursionError):
        return "nested too deeply"
    return str(exc) if exc.__class__.__name__ == "JSONFormatError" else exc.__class__.__name__


def check_registry(data, skill, check):
    check("registry.json is an object", isinstance(data, dict))
    if not isinstance(data, dict):
        return
    version = data.get("schema_version")
    check("registry.json.schema_version", type(version) is int and version == 1,
          "required integer equal to 1")
    check("registry.json.skill", data.get("skill") == skill,
          "required string matching the consuming plugin identity")
    tools = data.get("tools")
    check("registry.json.tools", isinstance(tools, list), "required array")
    for index, tool in enumerate(tools if isinstance(tools, list) else []):
        prefix = "registry.json.tools[%d]" % index
        check(prefix, isinstance(tool, dict), "required object")
        if not isinstance(tool, dict):
            continue
        slug = tool.get("slug")
        check(prefix + ".slug", isinstance(slug, str) and
              re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug) is not None, "required kebab-case string")
        check(prefix + ".installed", isinstance(tool.get("installed"), bool), "required Boolean")
        if "transport" in tool:
            check(prefix + ".transport", isinstance(tool["transport"], str) and
                  tool["transport"] in ("stdio", "http", "sse", "rest", "python-lib"),
                  "expected stdio, http, sse, rest or python-lib")
        if "notes" in tool:
            check(prefix + ".notes", isinstance(tool["notes"], str), "expected string")


def check_ledger(path, label, validate, check, profile_id=None, owned=False):
    if not os.path.isfile(path):
        return
    try:
        with open(path, "rb") as stream:
            text = stream.read().decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        check(label + " readable", False, load_problem(exc))
        return
    bad, rows = 0, 0
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        rows += 1
        try:
            row = loads_strict(line)
        except LOAD_ERRORS as exc:
            check("%s line %d" % (label, number), False, load_problem(exc))
            bad += 1
            continue
        problems = list(validate(row))
        if owned and isinstance(row, dict) and (profile_id is None or row.get("profile_id") != profile_id):
            problems.append(("profile_id", "belongs to another config root" if profile_id else
                             "ownership cannot be checked without a valid profile_id in profile.json"))
        blocking = [p for p in problems if len(p) == 2 or p[0] == "block"]
        for problem in blocking:
            check("%s line %d %s" % (label, number, problem[-2]), False, problem[-1])
        bad += bool(blocking)
    check("%s rows valid (%d rows)" % (label, rows), bad == 0)


def check_forwarder_table(cfg, item, index, check, zip_code=None):
    label = "profile.json.forwarders[%d].rate_table" % index
    table = item.get("rate_table")
    if not rate_table_ok(table):
        return  # the profile check already refused it; never follow such a path
    root = Path(cfg).resolve()
    path = (root / table).resolve()
    if not path.is_relative_to(root):
        check(label + " stays inside the config root", False, "resolves outside the root")
        return
    check(label + " exists", path.is_file(), "file missing under the config root")
    if not path.is_file():
        return
    try:
        data = load_strict_json(path)
    except LOAD_ERRORS as exc:
        check(label + " valid JSON", False, load_problem(exc))
        return
    problems = forwarder_table_problems(data, item.get("name"), item.get("zone"), item.get("duty_inclusive"),
                                        zip_code)
    for field, message in problems:
        check("%s: %s" % (label, field), False, message)
    check(label + " conforms", not problems)


def ignored_under_data(cfg):
    """Paths under data/ that git would ignore: the writers' own paths and any existing file.

    Returns a list (empty means none), or None when git could not answer. GIT_* variables are
    cleared so a hook's environment cannot point the question at another repository.
    """
    env = {key: value for key, value in os.environ.items() if not key.upper().startswith("GIT_")}
    try:
        probe = subprocess.run(["git", "-C", str(cfg), "check-ignore", "--no-index", *DATA_PROBES],
                               capture_output=True, text=True, timeout=60, env=env)
        existing = subprocess.run(["git", "-C", str(cfg), "ls-files", "--others", "--ignored",
                                   "--exclude-standard", "--", "data"],
                                  capture_output=True, text=True, timeout=60, env=env)
    except (OSError, subprocess.SubprocessError):
        return None
    if probe.returncode not in (0, 1) or existing.returncode != 0:
        return None
    return sorted(set(probe.stdout.split()) | set(existing.stdout.split()))


def doctor(cfg, skill, check):
    """Check one root; returns its profile_id when that field is valid."""
    check("config dir exists", os.path.isdir(cfg))
    if not os.path.isdir(cfg):
        return None
    for name in ("README.md", ".gitignore"):
        check(name + " present", os.path.isfile(os.path.join(cfg, name)))
    for name in ("data", "tools", "secrets"):
        check(name + "/ dir present", os.path.isdir(os.path.join(cfg, name)))
    # A profile names where a person lives and what they pay for. The root has to be in a versioned
    # repository whose every remote is PRIVATE before it may hold one (CONFIG.md, Storage).
    try:
        prove_private(cfg)
        check("root is in a versioned PRIVATE repository", True)
    except StorageError as exc:
        check("root is in a versioned PRIVATE repository", False, str(exc))

    registry = os.path.join(cfg, "registry.json")
    check("registry.json present", os.path.isfile(registry))
    if os.path.isfile(registry):
        try:
            check_registry(load_strict_json(registry), skill, check)
        except LOAD_ERRORS as exc:
            check("registry.json valid JSON", False, load_problem(exc))

    profile_id = None
    profile = os.path.join(cfg, "profile.json")
    check("profile.json present", os.path.isfile(profile))
    if os.path.isfile(profile):
        try:
            data = load_strict_json(profile)
        except LOAD_ERRORS as exc:
            check("profile.json valid JSON", False, load_problem(exc))
        else:
            problems = profile_problems(data)
            for field, message in problems:
                check("profile.json." + field, False, message)
            check("profile.json conforms (filled, no identity or payment data)", not problems)
            profile_id = profile_id_of(data)
            forwarders = data.get("forwarders") if isinstance(data, dict) else None
            ship = data.get("ship_to") if isinstance(data, dict) else None
            zip_code = ship.get("zip") if isinstance(ship, dict) else None
            for index, item in enumerate(forwarders if isinstance(forwarders, list) else []):
                if isinstance(item, dict) and "rate_table" in item:
                    check_forwarder_table(cfg, item, index, check, zip_code)

    gitignore = os.path.join(cfg, ".gitignore")
    if os.path.isfile(gitignore):
        try:
            with open(gitignore, "r", encoding="utf-8") as stream:
                problems = secrets_ignore_problems(stream.read())
        except (OSError, UnicodeError):
            problems = ["root .gitignore is unreadable"]
        check("root .gitignore excludes representative secret paths", not problems, "; ".join(problems))
    ignored = ignored_under_data(cfg)
    check("nothing under data/ is ignored (the private writer refuses ignored paths)", ignored == [],
          "git could not answer" if ignored is None else
          "%d path(s) ignored; remove the rule, data/ is versioned" % len(ignored))

    data_dir = os.path.join(cfg, "data")
    check_ledger(os.path.join(data_dir, "metrics", "live-runs.jsonl"), "data/metrics/live-runs.jsonl",
                 live_run_problems, check)
    check_ledger(os.path.join(data_dir, "purchases.jsonl"), "data/purchases.jsonl",
                 purchase_problems, check, profile_id=profile_id, owned=True)
    return profile_id


def check_selection(runtime, cfg, how, check):
    """Every tool must land in the selected root, including those that follow only the environment."""
    for name, ok, detail in selection_checks(cfg, how, runtime.resolver.resolve_data_dir):
        check(name, ok, detail)


def report(results):
    failed = sum(1 for _, ok, _ in results if not ok)
    for name, ok, detail in results:
        line = "  [%s] %s" % (PASS if ok else FAIL, name)
        if detail and not ok:
            line += "  -> %s" % detail
        print(line)
    return failed


def main():
    ap = argparse.ArgumentParser(description="Validate a shopping-aggregator config root (CONFIG.md).")
    ap.add_argument("--skill", default=None)
    ap.add_argument("--config-dir", default=None)
    ap.add_argument("--all", action="store_true", help="also validate every people/<id>/ root")
    a = ap.parse_args()

    try:
        runtime = ConfigRuntime(a.skill)
        cfg, how = runtime.discover(a.config_dir)
    except (OSError, ValueError, RuntimeError) as exc:
        print("ERROR: %s" % exc)
        return 1
    skill = runtime.skill
    print("Config doctor for skill '%s'" % skill)
    print("Discovery env var: %s (and %s_DIR)" % (env_var(skill), env_var(skill)))
    if not cfg:
        print("  [%s] config located -> none found." % FAIL)
        print("       Set %s=<dir> or run: python scripts/init_config.py" % env_var(skill))
        return 1
    print("  resolved via %s -> %s" % (how, cfg))
    print("-" * 60)

    results = []

    def record(name, ok, detail=""):
        results.append((name, ok, detail))

    ids = [("root", doctor(cfg, skill, record))]
    check_selection(runtime, cfg, how, record)
    failed = report(results)
    people = os.path.join(cfg, "people")
    others = sorted(name for name in (os.listdir(people) if os.path.isdir(people) else [])
                    if os.path.isdir(os.path.join(people, name)))
    if others:
        print("  people/: %d other root(s): %s" % (len(others), ", ".join(others)))
    if a.all:
        for name in others:
            print("-" * 60)
            print("  people/%s" % name)
            sub_results = []
            ids.append(("people/" + name, doctor(os.path.join(people, name), skill,
                                                 lambda n, ok, d="": sub_results.append((n, ok, d)))))
            failed += report(sub_results)
        seen = {}
        for where, profile_id in ids:
            if profile_id is not None:
                seen.setdefault(profile_id, []).append(where)
        shared = [", ".join(where) for where in seen.values() if len(where) > 1]
        print("-" * 60)
        failed += report([("profile_id unique across roots", not shared,
                           "; ".join(shared) + " share one profile_id")])
    print("-" * 60)
    if failed:
        print("NOT READY: %d check(s) failed. Fix the above; CONFIG.md defines every field." % failed)
        return 1
    print("CONFIG CONFORMS: %s matches CONFIG.md." % cfg)
    print("Sessions, MCP servers and retailers still need their own functional checks.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
