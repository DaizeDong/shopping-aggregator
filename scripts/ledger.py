#!/usr/bin/env python3
"""Append to, or check, a config root's run ledgers: the only writer for both.

    python scripts/ledger.py append live-runs --row-file - --config-dir <root>   (the row on stdin)
    python scripts/ledger.py append purchases --row-file <file outside this repository>
    python scripts/ledger.py append live-runs --row '{"domain": ...}'   (POSIX shells only)
    python scripts/ledger.py check [live-runs|purchases|all] [--config-dir <root>]

Ledgers live in <config root>/data/: metrics/live-runs.jsonl (what a run observed about sources)
and purchases.jsonl (every order action taken on the buyer's instruction). The root is selected
exactly as the doctor selects it (--config-dir, SHOPPING_AGGREGATOR_CONFIG, _CONFIG_DIR, then the
pinned resolver), and the write is refused when the environment would send the tools/ commands to
a different root (tools/config_selection.py). Environment variables do not survive between an
agent's tool calls, so a run that is not about the default root passes the same --config-dir to
every command.

Reading degrades; writing fails closed. A row is validated against tools/config_schema.py before
anything is opened, and the writer refuses even what the checker only warns about. A purchase row
must name the selected root's profile_id itself: the writer never fills it in, because a default
would file one person's order under whichever root happened to be selected. Writes go through
tools/evaluation_store.py, which proves the destination is a versioned PRIVATE repository and
replaces the file atomically, under a lock kept in that repository's git directory, so concurrent
appends cannot drop each other's rows. Rows are read and written as UTF-8 whatever the console's
code page, and the three characters that str.splitlines() treats as line breaks are escaped, so
every row stays one line for every reader. There is no fallback location: a refused row is
reported in the reply instead (CONSTITUTION II.5).
"""
import argparse
import ctypes
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from config_runtime import ConfigRuntime

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
from config_schema import (live_run_problems, load_strict_json, loads_strict,  # noqa: E402
                           profile_id_of, profile_problems, purchase_problems)
from config_selection import environment_problem, selection_checks  # noqa: E402
from evaluation_store import StorageError, prepare_store  # noqa: E402

LEDGERS = {
    "live-runs": (Path("metrics") / "live-runs.jsonl", live_run_problems),
    "purchases": (Path("purchases.jsonl"), purchase_problems),
}
LINE_BREAKS = {" ": "\\u2028", " ": "\\u2029", "\u0085": "\\u0085"}


class Refused(ValueError):
    """The row or its destination is not acceptable; nothing was written."""


def _alive(pid):
    """Whether a process exists, without signalling it (os.kill would terminate it on Windows)."""
    if pid <= 0:
        return False
    if os.name == "nt":
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.OpenProcess.restype = ctypes.c_void_p
        kernel32.OpenProcess.argtypes = (ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong)
        kernel32.GetExitCodeProcess.argtypes = (ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong))
        kernel32.CloseHandle.argtypes = (ctypes.c_void_p,)
        handle = kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if not handle:
            return ctypes.get_last_error() == 5  # ERROR_ACCESS_DENIED: it exists, we may not look
        try:
            code = ctypes.c_ulong()
            if not kernel32.GetExitCodeProcess(handle, ctypes.byref(code)):
                return True
            return code.value == 259  # STILL_ACTIVE
        finally:
            kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


class LedgerLock:
    """One writer at a time per ledger, for every process on this machine.

    The store replaces the ledger atomically, so a lock on the ledger itself would guard an inode
    that the write swaps out. The lock is an O_EXCL file in the repository's own git directory, the
    one place every writer of that ledger shares whatever its temp directory is. It records the
    holder's PID: a lock whose holder has exited is taken over at once, and any lock older than
    `stale` seconds is taken over too, well before a waiting writer gives up at `timeout`.
    """

    def __init__(self, target, git_dir, timeout=180.0, stale=90.0):
        digest = hashlib.sha256(os.path.normcase(str(target)).encode("utf-8")).hexdigest()[:24]
        self.path = Path(git_dir) / ("shopping-aggregator-ledger-%s.lock" % digest)
        self.timeout, self.stale = timeout, stale

    def _abandoned(self):
        try:
            age = time.time() - self.path.stat().st_mtime
            holder = int(self.path.read_text(encoding="ascii").strip() or "0")
        except (OSError, ValueError):
            return False
        return age > self.stale or (age > 2.0 and not _alive(holder))

    def __enter__(self):
        deadline = time.monotonic() + self.timeout
        while True:
            try:
                handle = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(handle, str(os.getpid()).encode("ascii"))
                os.close(handle)
                return self
            except FileExistsError:
                if self._abandoned():
                    try:
                        self.path.unlink()
                    except FileNotFoundError:
                        pass
                    continue
                if time.monotonic() > deadline:
                    raise StorageError("another writer still holds the ledger lock: %s" % self.path)
                time.sleep(0.05)

    def __exit__(self, *exc_info):
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass


def git_dir_of(root):
    env = {key: value for key, value in os.environ.items() if not key.upper().startswith("GIT_")}
    result = subprocess.run(["git", "-C", str(root), "rev-parse", "--absolute-git-dir"],
                            capture_output=True, text=True, timeout=60, env=env)
    if result.returncode != 0 or not result.stdout.strip():
        raise StorageError("The selected root is not inside a git repository")
    return Path(result.stdout.strip())


def selected_root(config_dir, require=True):
    problem = environment_problem()
    if problem:
        raise StorageError(problem)
    runtime = ConfigRuntime(None)
    root, how = runtime.discover(config_dir)
    if not root:
        if require:
            raise StorageError("No config root: run scripts/init_config.py or pass --config-dir")
        return None, None, runtime
    return Path(root), how, runtime


def checked_data_dir(root, how, runtime):
    data_dir = root / "data"
    if not data_dir.is_dir():
        raise StorageError("The selected root has no data/ directory; it is not a config root (CONFIG.md)")
    for name, ok, detail in selection_checks(root, how, runtime.resolver.resolve_data_dir):
        if not ok:
            raise StorageError("%s: %s" % (name, detail))
    return data_dir


def root_profile_id(root):
    try:
        data = load_strict_json(root / "profile.json")
    except (OSError, ValueError, RecursionError) as exc:
        raise StorageError("profile.json is missing or unreadable in the selected root") from exc
    if profile_problems(data):
        raise StorageError("profile.json does not conform; run scripts/verify_config.py")
    return profile_id_of(data)


def read_row(row_text, row_file):
    if row_text is not None:
        text = row_text
    elif row_file == "-":
        text = sys.stdin.buffer.read().decode("utf-8-sig")
    else:
        path = Path(row_file).resolve()
        if path.is_relative_to(REPO.resolve()):
            raise Refused("the row file is inside the public tool repository; write rows to stdin or to a "
                          "file outside it, and delete this copy")
        text = path.read_text(encoding="utf-8-sig")
    try:
        row = loads_strict(text)
    except (ValueError, RecursionError) as exc:
        raise Refused("the row is not valid strict JSON") from exc
    if not isinstance(row, dict):
        raise Refused("a ledger row must be a JSON object")
    return row


def encode_row(row):
    line = json.dumps(row, ensure_ascii=False, allow_nan=False)
    for char, escaped in LINE_BREAKS.items():
        line = line.replace(char, escaped)
    return (line + "\n").encode("utf-8")


def append(kind, row, config_dir):
    relative, validate = LEDGERS[kind]
    row = dict(row)
    if row.get("ts") is None or row.get("ts") == "":
        row["ts"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    problems = validate(row)
    if problems:
        raise Refused("row does not conform: " + "; ".join("%s %s" % (p[-2], p[-1]) for p in problems))
    root, how, runtime = selected_root(config_dir)
    if kind == "purchases" and row["profile_id"] != root_profile_id(root):
        raise Refused("the row's profile_id is not the selected root's; select that person's root "
                      "with --config-dir")
    store = prepare_store(base=checked_data_dir(root, how, runtime))
    target = store.output_path(relative)
    with LedgerLock(target, git_dir_of(root)):
        existing = target.read_bytes() if target.is_file() else b""
        if existing and not existing.endswith(b"\n"):
            existing += b"\n"
        store.write_bytes(relative, existing + encode_row(row))
    print("appended 1 %s row -> %s (root resolved via %s)" % (kind, target, how))


def check(kind, config_dir):
    root, how, _ = selected_root(config_dir, require=False)
    if root is None:
        print("  no config root resolved: nothing to check (uninitialized)")
        return 0
    print("  resolved via %s -> %s" % (how, root))
    try:
        profile_id = profile_id_of(load_strict_json(root / "profile.json"))
    except (OSError, ValueError, RecursionError):
        profile_id = None
    failed = 0
    for name in (LEDGERS if kind == "all" else [kind]):
        relative, validate = LEDGERS[name]
        path = root / "data" / relative
        if not path.is_file():
            print("  [SKIP] %s: no ledger yet" % name)
            continue
        rows = bad = 0
        try:
            text = path.read_bytes().decode("utf-8")
        except (OSError, UnicodeDecodeError):
            print("  [FAIL] %s: unreadable or not UTF-8" % name)
            failed += 1
            continue
        for number, line in enumerate(text.split("\n"), 1):
            if not line.strip():
                continue
            rows += 1
            try:
                row = loads_strict(line)
                problems = [p for p in validate(row) if len(p) == 2 or p[0] == "block"]
            except (ValueError, RecursionError):
                row, problems = None, [("row", "invalid JSON")]
            if name == "purchases" and isinstance(row, dict) and (profile_id is None
                                                                   or row.get("profile_id") != profile_id):
                problems.append(("profile_id", "belongs to another config root" if profile_id else
                                 "ownership cannot be checked without a valid profile_id in profile.json"))
            for problem in problems:
                print("  [FAIL] %s line %d %s: %s" % (name, number, problem[-2], problem[-1]))
            bad += bool(problems)
        print("  [%s] %s: %d rows, %d invalid" % ("PASS" if not bad else "FAIL", name, rows, bad))
        failed += bad
    return 1 if failed else 0


def main():
    ap = argparse.ArgumentParser(description="Append to or check the run ledgers (CONFIG.md).")
    sub = ap.add_subparsers(dest="command", required=True)
    add = sub.add_parser("append")
    add.add_argument("ledger", choices=sorted(LEDGERS))
    source = add.add_mutually_exclusive_group(required=True)
    source.add_argument("--row", help="the row as JSON text (POSIX shells; PowerShell 5 strips its quotes)")
    source.add_argument("--row-file", help="a JSON file outside this repository, or - for stdin")
    add.add_argument("--config-dir", default=None)
    chk = sub.add_parser("check")
    chk.add_argument("ledger", nargs="?", default="all", choices=sorted(LEDGERS) + ["all"])
    chk.add_argument("--config-dir", default=None)
    a = ap.parse_args()
    if a.command == "check":
        try:
            return check(a.ledger, a.config_dir)
        except (StorageError, ValueError, OSError, RuntimeError) as exc:
            print("ERROR: %s" % exc)
            return 1
    try:
        append(a.ledger, read_row(a.row, a.row_file), a.config_dir)
        return 0
    except (StorageError, ValueError, OSError, RuntimeError) as exc:
        print("REFUSED: %s" % exc)
        print("Nothing was written. Fix an invalid row and append again; otherwise report the row in "
              "the reply (CONSTITUTION II.5).")
        return 1


if __name__ == "__main__":
    sys.exit(main())
