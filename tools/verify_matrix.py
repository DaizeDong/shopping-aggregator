#!/usr/bin/env python3
"""Deterministic lint + anti-regression gate for the shopping-aggregator skill.

PHILOSOPHY P2 (mechanism-not-intention): the skill is full of advisory "MUST" with no executable
check behind them. This script is the cheap, real mechanism the skill lacked. The ORIGINAL six
checks (THREEWAY/FRESH/TEMPLATE/VERSION/RENAME/LIVERUNS) are deterministic, non-judgemental checks
on DURABLE CONTRACTS / ARTIFACTS — they must keep passing while a parallel agent restructures
SKILL.md prose, so they gate on schema/artifact facts, not wording.

This file then PORTS market-intel's richer-judgement gates (REPO/GHACTIVE, STAR/DOCCOVER/STALE,
COVER/CHURN/DELETE, CONST/METH, FRESH-future) and ADDS a DATA envelope check, conservatively:
the baseline `python tools/verify_matrix.py` MUST stay PASS; anything uncertain is a WARN, never a
BLOCK. Network gates (REPO/GHACTIVE/STAR) are skipped with `--no-net` for offline CI.

Run from the repo root:  python tools/verify_matrix.py [--no-net] [--base main]
Exit 0 = PASS · non-zero = FAIL (BLOCK). FAIL-CLOSED: any uncaught exception => FAIL, never a silent
pass (a gate that can't run is a BLOCK, not a green light).

Checks
------
ORIGINAL (durable-contract lint — unchanged behaviour):
  THREEWAY  registry.json <-> tools/<slug>.md files <-> tools/index.md rows (existence; BLOCK).
  FRESH     every domain shard + tool doc carries a Last-verified line (WARN; future date BLOCK).
  TEMPLATE  report-template.md has a "Coverage gaps" heading + an "Ev" column (BLOCK).
  VERSION   CHANGELOG.md top version == .claude-plugin/plugin.json version (BLOCK).
  RENAME    snake_case `source_tier` does not leak into any live skill file (BLOCK).
  LIVERUNS  the PUBLISHED schema metrics/live-runs.jsonl.example is present and valid JSONL with the
            6 required keys (BLOCK; enum WARN) — plus the operator's real file in the private data
            dir, when this machine has one. The real file is DATA and is absent from the repo (see
            .dataclass.json); a fresh clone therefore checks only the schema, and passes.

PORTED from market-intel (richer judgement; network gates honour --no-net):
  REPO      documented github.com/<owner>/<repo> + registry `repo` slugs exist (gh api, fail-closed).
            A doc'd repo that 404s => BLOCK; a bare/heuristic slug that 404s => WARN.
  GHACTIVE  every documented repo is alive (not archived) and pushed within 12mo (archived/404 BLOCK,
            stale WARN, rate-limited bypass-as-WARN). Cached to metrics/gh-api-cache.json (7d TTL).
  STAR      where a repo and an (NNk★) annotation co-occur, the count is within 25% (BLOCK on lie).
  DOCCOVER  a github repo in a LIVE (non-tombstone) shard row with no per-tool doc => WARN (anti-lost).
  STALE     a tool doc not re-verified in >9 months => WARN (anti-rot nomination).
  COVER     vs git baseline: total source rows didn't drop >10%, no shard lost >30% (BLOCK).
  CHURN     vs baseline: a single shard with >40% of lines changed looks like a rewrite => BLOCK.
  DELETE    vs baseline: a source row removed without a death-code => BLOCK (C4 deletion discipline).
  CONST     CONSTITUTION.md exists and was NOT modified by this run (scope guard; BLOCK).
  METH      SKILL.md keeps L1/L5/E1/E3 tiers + ①②③④ route legend + >=10 numbered guardrails.

ADDED (provenance + registration — new this revision):
  NOHARDCODE SKILL.md prose pairing a tax/duty/de-minimis number (N% / $N) with NO reference/data/
            citation and NO (assumed) stamp => WARN (CONSTITUTION I.7: numbers resolve to a data row).
            Scoped to {sales-tax,de-minimis,tariff,duty,customs} so shipping analogies and trust/depth
            thresholds don't false-fire.
  SHARDSYNC A net-new domain shard (vs git baseline) MUST have a reference/sources-index.md row; a
            net-new reference/data/*.json MUST be named in reference/data/README.md => BLOCK on an
            orphan. Gates only NEW files so the current (already-registered) tree stays PASS; skipped
            without a git baseline.

ADDED (data-integrity — prior revision):
  DATA      reference/data/*.json conform to the envelope {schema_version,last_verified,rows:[...]}
            and every row carries source_url + verified_date (BLOCK on violation; future date BLOCK).
            No data dir / no json files => silent no-op (so the baseline stays green until the
            parallel agent lands reference/data/). Envelope schema is owned by
            reference/data/README.md; this check follows that convention.

Why FRESH/STALE/GHACTIVE-stale are WARN, not BLOCK: a missing/old freshness stamp is doc-rot, not a
broken contract — surfacing it for a human is the right severity, and a hard block would make the
gate brittle to concurrent prose edits. A FUTURE-dated stamp IS a lie (BLOCK). Network unreachability
is transient external state — per market-intel's philosophy we surface it as WARN and let a re-run
pick it up, except a confirmed 404 (a hard fact) which BLOCKs.
"""
import datetime
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from datadir import resolve_data_dir  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS = os.path.join(ROOT, "skills")
SKILL = os.path.join(SKILLS, "shopping-aggregator")
REF = os.path.join(SKILL, "reference")
DOMAINS = os.path.join(REF, "domains")
TOOLS_DIR = os.path.join(REF, "tools")
TOOLS_INDEX = os.path.join(TOOLS_DIR, "index.md")
REGISTRY = os.path.join(TOOLS_DIR, "registry.json")
REPORT_TEMPLATE = os.path.join(REF, "report-template.md")
SKILLMD = os.path.join(SKILL, "SKILL.md")
DATA_DIR = os.path.join(REF, "data")
CHANGELOG = os.path.join(ROOT, "CHANGELOG.md")
CONSTITUTION = os.path.join(ROOT, "CONSTITUTION.md")
PLUGIN_JSON = os.path.join(ROOT, ".claude-plugin", "plugin.json")

# git-relative path prefix for the shards (used by COVER/CHURN/DELETE baseline diffs)
SHARD_GIT_PREFIX = "skills/shopping-aggregator/reference/domains"

STAR_TOL = 0.25            # display star annotations vs real, allow 25%
COVER_GLOBAL_DROP = 0.10   # total source rows may not drop >10%
COVER_SHARD_DROP = 0.30    # no single shard may lose >30% of its rows
CHURN_MAX = 0.40           # a single shard changing >40% of lines looks like a rewrite, not an edit
GHACTIVE_STALE_MONTHS = 12 # a repo not pushed within this is doc-rot (WARN)
STALE_MONTHS = 9           # a tool doc not re-verified within this is nominated for re-check (WARN)
GH_CACHE_MAX_AGE_DAYS = 7

NO_NET = "--no-net" in sys.argv
BASE = "main"
if "--base" in sys.argv:
    BASE = sys.argv[sys.argv.index("--base") + 1]

fails, warns = [], []


def block(code, msg):
    fails.append(f"[{code}] {msg}")


def warn(code, msg):
    warns.append(f"[{code}] {msg}")


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def git_show(ref, relpath):
    """git show <ref>:<relpath>; empty string on any failure (e.g. file absent at baseline)."""
    try:
        r = subprocess.run(["git", "show", f"{ref}:{relpath}"], cwd=ROOT,
                           capture_output=True, text=True, encoding="utf-8")
        return r.stdout if r.returncode == 0 else ""
    except Exception:
        return ""


def git_diff(relpath):
    try:
        return subprocess.run(["git", "diff", BASE, "--", relpath], cwd=ROOT,
                              capture_output=True, text=True, encoding="utf-8").stdout
    except Exception:
        return ""


def git_available():
    try:
        return subprocess.run(["git", "rev-parse", "--git-dir"], cwd=ROOT,
                              capture_output=True, text=True).returncode == 0
    except Exception:
        return False


def base_ref_exists():
    try:
        return subprocess.run(["git", "rev-parse", "--verify", BASE], cwd=ROOT,
                              capture_output=True, text=True).returncode == 0
    except Exception:
        return False


REPO_RE = re.compile(r"github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)")
# repo token immediately before an (NNk★) annotation (only **/spaces between) — STAR pairing.
STAR_LINE_RE = re.compile(r"([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)\*{0,2}\s*\((\d+(?:\.\d+)?)k★\)")


def _strip_git(r):
    return r[:-4] if r.endswith(".git") else r


def count_table_rows(text):
    """Count markdown source-table rows (lines starting with '|' that aren't header/separator)."""
    n = 0
    for ln in text.splitlines():
        s = ln.strip()
        if s.startswith("|") and not re.match(r"^\|[\s:|-]+\|?$", s) and "---" not in s:
            if not re.search(r"\|\s*(source|repo|tool|name)\s*\|", s, re.I):
                n += 1
    return n


def run_checks():
    # ================================================================= ORIGINAL CHECKS (unchanged)
    # ---- THREEWAY: registry.json <-> tools/<slug>.md files <-> tools/index.md rows ----
    if not os.path.isdir(TOOLS_DIR):
        block("THREEWAY", "reference/tools/ directory is missing")
        return
    if not os.path.exists(REGISTRY):
        block("THREEWAY", "reference/tools/registry.json is missing")
        return
    if not os.path.exists(TOOLS_INDEX):
        block("THREEWAY", "reference/tools/index.md is missing")
        return

    try:
        reg = json.loads(read(REGISTRY))
    except Exception as e:
        block("THREEWAY", f"reference/tools/registry.json is not valid JSON: {e}")
        return

    reg_slugs = {t.get("slug") for t in reg.get("tools", []) if t.get("slug")}
    if not reg_slugs:
        block("THREEWAY", "registry.json lists no tool slugs")

    fs_slugs = {
        f[:-3]
        for f in os.listdir(TOOLS_DIR)
        if f.endswith(".md") and f != "index.md"
    }

    idx_text = read(TOOLS_INDEX)
    idx_slugs = set(re.findall(r"\(([a-z0-9][a-z0-9-]*)\.md\)", idx_text))

    reg_no_doc = reg_slugs - fs_slugs
    reg_no_idx = reg_slugs - idx_slugs
    if reg_no_doc:
        block("THREEWAY", f"registry slugs with no reference/tools/<slug>.md: {sorted(reg_no_doc)}")
    if reg_no_idx:
        block("THREEWAY", f"registry slugs missing from index.md: {sorted(reg_no_idx)}")

    doc_no_reg = fs_slugs - reg_slugs
    doc_no_idx = fs_slugs - idx_slugs
    if doc_no_reg:
        block("THREEWAY", f"tool docs not in registry.json (it is authoritative — add them): {sorted(doc_no_reg)}")
    if doc_no_idx:
        block("THREEWAY", f"tool docs not listed in index.md: {sorted(doc_no_idx)}")

    idx_no_reg = idx_slugs - reg_slugs
    idx_no_doc = idx_slugs - fs_slugs
    if idx_no_reg:
        block("THREEWAY", f"index.md rows with no registry slug: {sorted(idx_no_reg)}")
    if idx_no_doc:
        block("THREEWAY", f"index.md rows with no reference/tools/<slug>.md: {sorted(idx_no_doc)}")

    # ---- FRESH: every domain shard + tool doc carries a Last-verified line (WARN) ----
    FRESH_RE = re.compile(r"last[ _]verified", re.IGNORECASE)
    if os.path.isdir(DOMAINS):
        for f in sorted(os.listdir(DOMAINS)):
            if not f.endswith(".md"):
                continue
            if not FRESH_RE.search(read(os.path.join(DOMAINS, f))):
                warn("FRESH", f"domains/{f} has no 'Last verified:' / 'last_verified' line")
    tool_docs_text = {s: read(os.path.join(TOOLS_DIR, s + ".md")) for s in fs_slugs}
    for slug in sorted(fs_slugs):
        if not FRESH_RE.search(tool_docs_text[slug]):
            warn("FRESH", f"tools/{slug}.md has no 'Last verified:' / 'last_verified' line")

    # ---- TEMPLATE: report-template.md has a Coverage gaps heading + an Ev column (BLOCK) ----
    if not os.path.exists(REPORT_TEMPLATE):
        block("TEMPLATE", "reference/report-template.md is missing")
    else:
        tmpl = read(REPORT_TEMPLATE)
        if not re.search(r"^#{1,6}\s+coverage gaps?\b", tmpl, re.IGNORECASE | re.MULTILINE):
            block("TEMPLATE", "report-template.md is missing a 'Coverage gaps' section heading (CONSTITUTION I.6)")
        if not re.search(r"\|\s*[*`]*Ev[*`]*\s*\|", tmpl):
            block("TEMPLATE", "report-template.md ranking table is missing an 'Ev' (evidence_grade) column (CONSTITUTION I.3)")

    # ---- VERSION: CHANGELOG top version == plugin.json version (BLOCK) ----
    if not os.path.exists(CHANGELOG):
        block("VERSION", "CHANGELOG.md is missing")
        changelog_ver = None
    else:
        m = re.search(r"^##\s*\[?v?(\d+\.\d+\.\d+)\]?", read(CHANGELOG), re.MULTILINE)
        changelog_ver = m.group(1) if m else None
        if changelog_ver is None:
            block("VERSION", "could not parse a top version heading (## [X.Y.Z]) from CHANGELOG.md")

    if not os.path.exists(PLUGIN_JSON):
        block("VERSION", ".claude-plugin/plugin.json is missing")
        plugin_ver = None
    else:
        try:
            plugin_ver = json.loads(read(PLUGIN_JSON)).get("version")
        except Exception as e:
            block("VERSION", f".claude-plugin/plugin.json is not valid JSON: {e}")
            plugin_ver = None
        if plugin_ver is None:
            block("VERSION", "plugin.json has no 'version' field")

    if changelog_ver and plugin_ver and changelog_ver != plugin_ver:
        block("VERSION", f"CHANGELOG top version {changelog_ver} != plugin.json version {plugin_ver}")

    # ---- RENAME: snake_case token `source_tier` must not appear in any live skill file ----
    RENAME_RE = re.compile(r"\bsource_tier\b")
    for dirpath, _dirnames, filenames in os.walk(SKILLS):
        for fn in filenames:
            if not fn.endswith(".md"):
                continue
            fp = os.path.join(dirpath, fn)
            if RENAME_RE.search(read(fp)):
                rel = os.path.relpath(fp, ROOT).replace("\\", "/")
                block("RENAME", f"token `source_tier` leaked into {rel} — it was renamed to seller_tier + evidence_grade")

    # ---- LIVERUNS: the live-runs JSONL the refresh loop consumes is valid ----
    # The real file is DATA: every line is an observation from a REAL run (what got priced, which
    # retailer, shipping where), so it lives in the PRIVATE data dir and is absent from this repo
    # (.dataclass.json). What the repo publishes is the SHAPE — live-runs.jsonl.example — and that is
    # the whole of what a fresh clone knows about the lines it is expected to produce. So the schema
    # is now the BLOCKING half of this check: an uninitialized tool still has to be a usable one.
    REQUIRED_KEYS = {"ts", "domain", "source", "outcome", "detail", "user_correction"}
    OUTCOME_OK = {"created", "verified", "unverifiable", "dead", "fallback_used",
                  "price_mismatch", "coupon_fake", "coverage_gap"}

    def _check_liveruns(path, label, required):
        if not os.path.exists(path):
            if required:
                block("LIVERUNS", f"{label} is missing — the repo must publish the schema so the "
                                  f"skill is usable uninitialized (.dataclass.json)")
            return
        for i, ln in enumerate(read(path).splitlines(), 1):
            ln = ln.strip()
            if not ln:
                continue
            try:
                rec = json.loads(ln)
            except Exception as e:
                block("LIVERUNS", f"{label} line {i} is not valid JSON: {e}")
                continue
            missing = REQUIRED_KEYS - set(rec)
            if missing:
                block("LIVERUNS", f"{label} line {i} missing keys: {sorted(missing)}")
            if rec.get("outcome") not in OUTCOME_OK:
                warn("LIVERUNS", f"{label} line {i} outcome '{rec.get('outcome')}' not in the declared set")

    _check_liveruns(os.path.join(SKILL, "metrics", "live-runs.jsonl.example"),
                    "metrics/live-runs.jsonl.example", required=True)

    # And the operator's REAL file, on a machine that has one. A corrupt private file breaks the
    # refresh loop exactly as badly as a corrupt tracked one did — and it is now the only file that
    # actually feeds it. No data dir (fresh clone, CI) = uninitialized = correct: nothing to check.
    _data_dir = resolve_data_dir("shopping-aggregator")
    if _data_dir is not None:
        _check_liveruns(os.path.join(str(_data_dir), "metrics", "live-runs.jsonl"),
                        "<private data dir>/metrics/live-runs.jsonl", required=False)

    # ================================================================= PORTED CHECKS (market-intel)
    # ---- gather domain shard text + the full corpus repos can hide in ----
    fs_domains = set()
    shard_text = {}
    if os.path.isdir(DOMAINS):
        fs_domains = {f[:-3] for f in os.listdir(DOMAINS) if f.endswith(".md")}
        shard_text = {d: read(os.path.join(DOMAINS, d + ".md")) for d in fs_domains}

    extra_paths = [REPORT_TEMPLATE, os.path.join(REF, "sources-index.md"),
                   os.path.join(REF, "install-guide.md"),
                   os.path.join(REF, "volatile", "pricing-install.md"),
                   os.path.join(REF, "channel-classes.md")]
    extra_text = "\n".join(read(p) for p in extra_paths if os.path.exists(p))
    all_text = ("\n".join(shard_text.values()) + "\n" + "\n".join(tool_docs_text.values())
                + "\n" + extra_text)

    # HIGH-CONFIDENCE repos (404 -> BLOCK): explicit github.com URLs + star-annotated slugs + the
    # registry.json `repo` field (authoritative). Strip a trailing .git (same repo as o/r).
    repo_set = {_strip_git(r) for r in REPO_RE.findall(all_text)}
    repo_set |= {_strip_git(m.group(1)) for m in STAR_LINE_RE.finditer(all_text)}
    for t in reg.get("tools", []):
        rp = t.get("repo")
        if rp:
            repo_set.add(_strip_git(rp))
    repos = sorted(r for r in repo_set
                   if not r.endswith(".md") and r.count("/") == 1 and "github.com" not in r)

    # HEURISTIC bare slugs (404 -> WARN only): unstarred slug-like tokens in shard table rows.
    SLUG_RE = re.compile(r"(?<![A-Za-z0-9_./@-])([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)(?![A-Za-z0-9_./-])")
    warn_slugs = set()
    for txt in shard_text.values():
        for ln in txt.splitlines():
            if not ln.lstrip().startswith("|"):
                continue
            for tok in SLUG_RE.findall(ln):
                o, _, r2 = tok.partition("/")
                if (("-" in tok or "_" in tok) and o.isascii() and r2.isascii()
                        and not tok.endswith(".md") and "github.com" not in tok
                        and tok not in repo_set and not o[:1].isdigit()):
                    warn_slugs.add(tok)

    _now_ts = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    _now_iso = _now_ts.isoformat()

    # ---- REPO + STAR (fail-closed) ----
    repo_stars = {}
    if NO_NET:
        warn("REPO", "skipped GitHub verification (--no-net)")
    else:
        import time
        for r in repos:
            res = None
            for attempt in range(3):
                res = subprocess.run(
                    ["gh", "api", f"repos/{r}", "--jq", "{s:.stargazers_count,a:.archived}"],
                    capture_output=True, text=True, encoding="utf-8")
                if res.returncode == 0:
                    break
                if "Not Found" in (res.stderr or "") or "404" in (res.stderr or ""):
                    break
                time.sleep(2 * (attempt + 1))
            if res is None or res.returncode != 0:
                stderr = (res.stderr or "") if res else "no result"
                if "Not Found" in stderr or "404" in stderr:
                    block("REPO", f"{r} does not exist (404) — hallucinated or dead repo")
                else:
                    block("REPO", f"{r} could not be verified after retries (fail-closed): {stderr.strip()[:80]}")
                continue
            try:
                d = json.loads(res.stdout)
                repo_stars[r] = d["s"]
            except Exception:
                block("REPO", f"{r} returned unparseable API response")
        # heuristic bare slugs: verify but only WARN (avoid false-blocking prose / npm scopes)
        for r in sorted(warn_slugs):
            res = subprocess.run(["gh", "api", f"repos/{r}", "--jq", ".full_name"],
                                 capture_output=True, text=True, encoding="utf-8")
            if res.returncode != 0 and ("Not Found" in (res.stderr or "") or "404" in (res.stderr or "")):
                warn("REPO?", f"{r} not found on GitHub — if it's a repo it may be hallucinated/mistyped; "
                              f"if prose/npm-scope, ignore")
        # STAR tolerance on lines pairing a repo with an (NNk★)
        for ln in all_text.splitlines():
            m = STAR_LINE_RE.search(ln)
            if not m:
                continue
            repo, claimed_k = _strip_git(m.group(1)), float(m.group(2))
            real = repo_stars.get(repo)
            if real is None:
                continue
            claimed = claimed_k * 1000
            if real == 0 or abs(claimed - real) / real > STAR_TOL:
                block("STAR", f"{repo}: claims {claimed_k}k★ but API says {real} (>{int(STAR_TOL*100)}% off)")

    # ---- GHACTIVE (deterministic activity gate; archived/404 BLOCK, stale WARN, RL bypass) ----
    GH_CACHE = os.path.join(SKILL, "metrics", "gh-api-cache.json")
    gh_cache = {}
    if os.path.exists(GH_CACHE):
        try:
            gh_cache = json.loads(read(GH_CACHE))
        except Exception:
            gh_cache = {}
    ghactive_results = []
    if NO_NET:
        warn("GHACTIVE", "skipped GitHub activity verification (--no-net)")
    else:
        for r in repos:
            c = gh_cache.get(r)
            if c and "checked_at" in c:
                try:
                    age = (_now_ts - datetime.datetime.fromisoformat(c["checked_at"])).days
                except Exception:
                    age = 999
                if age <= GH_CACHE_MAX_AGE_DAYS and c.get("verdict") != "RATE_LIMITED":
                    ghactive_results.append(c)
                    continue
            res = subprocess.run(
                ["gh", "api", f"repos/{r}", "--jq", "{pushed_at:.pushed_at,archived:.archived}"],
                capture_output=True, text=True, encoding="utf-8")
            if res.returncode != 0:
                stderr = (res.stderr or "")
                if "Not Found" in stderr or "404" in stderr:
                    entry = {"repo": r, "pushed_at": None, "archived": None,
                             "verdict": "BLOCK", "reason": "404 not found", "checked_at": _now_iso}
                    block("GHACTIVE", f"{r}: 404 not found (URL fabricated, deleted, or moved)")
                elif "rate limit" in stderr.lower() or "API rate" in stderr or "403" in stderr:
                    entry = {"repo": r, "pushed_at": None, "archived": None,
                             "verdict": "RATE_LIMITED", "reason": "gh api rate-limited",
                             "checked_at": _now_iso}
                    warn("GHACTIVE", f"{r}: rate-limited — re-run when quota resets (not blocking)")
                else:
                    entry = {"repo": r, "pushed_at": None, "archived": None,
                             "verdict": "RATE_LIMITED",
                             "reason": f"gh error: {stderr.strip()[:60]}", "checked_at": _now_iso}
                    warn("GHACTIVE", f"{r}: could not check activity ({stderr.strip()[:60]})")
                ghactive_results.append(entry)
                gh_cache[r] = entry
                continue
            try:
                d = json.loads(res.stdout)
                pushed_at = d.get("pushed_at")
                archived = bool(d.get("archived"))
            except Exception:
                entry = {"repo": r, "pushed_at": None, "archived": None,
                         "verdict": "RATE_LIMITED", "reason": "unparseable response",
                         "checked_at": _now_iso}
                warn("GHACTIVE", f"{r}: unparseable activity response")
                ghactive_results.append(entry)
                gh_cache[r] = entry
                continue
            if archived:
                entry = {"repo": r, "pushed_at": pushed_at, "archived": True,
                         "verdict": "BLOCK", "reason": "archived upstream", "checked_at": _now_iso}
                block("GHACTIVE", f"{r}: archived=true (formally retired upstream — tombstone the row)")
            else:
                try:
                    pushed_dt = datetime.datetime.strptime(pushed_at[:10], "%Y-%m-%d")
                    months_old = (_now_ts - pushed_dt).days / 30.44
                except Exception:
                    months_old = 0
                if months_old > GHACTIVE_STALE_MONTHS:
                    entry = {"repo": r, "pushed_at": pushed_at, "archived": False, "verdict": "WARN",
                             "reason": f"pushed_at {pushed_at[:10]} is ~{int(months_old)}mo old",
                             "checked_at": _now_iso}
                    warn("GHACTIVE", f"{r}: last push {pushed_at[:10]} (~{int(months_old)}mo ago, "
                                     f">{GHACTIVE_STALE_MONTHS}mo) — re-verify still maintained")
                else:
                    entry = {"repo": r, "pushed_at": pushed_at, "archived": False, "verdict": "PASS",
                             "reason": f"pushed_at {pushed_at[:10]} within {GHACTIVE_STALE_MONTHS}mo",
                             "checked_at": _now_iso}
            ghactive_results.append(entry)
            gh_cache[r] = entry
        try:
            os.makedirs(os.path.dirname(GH_CACHE), exist_ok=True)
            with open(GH_CACHE, "w", encoding="utf-8") as f:
                json.dump(gh_cache, f, ensure_ascii=False, indent=2, sort_keys=True)
        except Exception:
            pass
        if ghactive_results:
            _v = {v: 0 for v in ("PASS", "WARN", "BLOCK", "RATE_LIMITED")}
            for e in ghactive_results:
                _v[e["verdict"]] = _v.get(e["verdict"], 0) + 1
            print(f"GHACTIVE summary: {_v['PASS']} PASS, {_v['WARN']} WARN, {_v['BLOCK']} BLOCK, "
                  f"{_v['RATE_LIMITED']} RATE_LIMITED (of {len(ghactive_results)} repos)")

    # ---- FRESH-future + STALE on tool docs (date semantics ported from market-intel) ----
    today = datetime.date.today()
    this_month = today.strftime("%Y-%m")

    def _ym_to_months(ym):
        return int(ym[:4]) * 12 + int(ym[5:7])

    this_m = _ym_to_months(this_month)
    # any future-dated `last_verified:` anywhere is a lie -> BLOCK
    for m in re.finditer(r"last_verified:\s*(\d{4})-(\d{2})", all_text, re.IGNORECASE):
        ym = f"{m.group(1)}-{m.group(2)}"
        if ym > this_month:
            block("FRESH", f"last_verified {ym} is in the future")
    # per-tool-doc staleness: >STALE_MONTHS -> WARN (anti-rot); future already handled above
    stale_docs = []
    for slug, txt in tool_docs_text.items():
        fm = re.search(r"last[ _]verified:\s*(\d{4})-(\d{2})", txt, re.IGNORECASE)
        if not fm:
            continue
        ym = f"{fm.group(1)}-{fm.group(2)}"
        if ym <= this_month and this_m - _ym_to_months(ym) > STALE_MONTHS:
            stale_docs.append((slug, ym))
    if stale_docs:
        worst = sorted(stale_docs, key=lambda x: x[1])
        shown = ", ".join(f"{s}({y})" for s, y in worst[:10])
        warn("STALE", f"{len(stale_docs)} tool doc(s) not re-verified in >{STALE_MONTHS}mo — re-check "
                      f"repo/price + bump 'Last verified' when next sweeping: {shown}"
                      f"{' …' if len(stale_docs) > 10 else ''}")

    # ---- DOCCOVER (every repo in a LIVE shard row should have a per-tool doc) -> WARN ----
    if tool_docs_text:
        documented = {_strip_git(r).lower() for txt in tool_docs_text.values()
                      for r in REPO_RE.findall(txt)}
        # registry repos are also "documented" (their slug doc exists by THREEWAY)
        for t in reg.get("tools", []):
            if t.get("repo"):
                documented.add(_strip_git(t["repo"]).lower())
        TOMB = ("avoid", "dead", "d-404", "d-stale", "d-supersed", "~~", "deprecated", "(404)",
                "✗", "tombstone")
        undoc = {}
        for d, txt in shard_text.items():
            for ln in txt.splitlines():
                s = ln.strip()
                if not s.startswith("|") or "---" in s or any(t in s.lower() for t in TOMB):
                    continue
                for r in REPO_RE.findall(ln):
                    r = _strip_git(r).lower()
                    if r not in documented:
                        undoc.setdefault(r, d)
        if undoc:
            items = ", ".join(f"{r}({d})" for r, d in list(undoc.items())[:10])
            warn("DOCCOVER", f"{len(undoc)} live shard repo(s) have no per-tool doc — add tools/<slug>.md "
                             f"+ an index/registry row (or tombstone the shard row): {items}")

    # ---- COVER / CHURN / DELETE (vs git baseline) ----
    have_git = git_available()
    have_base = have_git and base_ref_exists()
    if not have_base:
        warn("COVER", f"git baseline '{BASE}' unavailable — skipped COVER/CHURN/DELETE diff gates")
    else:
        base_total = cur_total = 0
        for d in sorted(fs_domains):
            cur = count_table_rows(shard_text[d])
            cur_total += cur
            base_txt = git_show(BASE, f"{SHARD_GIT_PREFIX}/{d}.md")
            base = count_table_rows(base_txt) if base_txt else cur
            base_total += base
            if base and (base - cur) / base > COVER_SHARD_DROP:
                block("COVER", f"{d}: source rows dropped {base}->{cur} "
                               f"(>{int(COVER_SHARD_DROP*100)}%) — possible mass deletion")
        if base_total and (base_total - cur_total) / base_total > COVER_GLOBAL_DROP:
            block("COVER", f"total source rows dropped {base_total}->{cur_total} "
                           f"(>{int(COVER_GLOBAL_DROP*100)}%)")

        DEATH_CODES = ("D-404", "D-STALE", "D-PRICE", "D-TOS", "D-SUPERSEDED")
        changelog_added = "\n".join(
            l[1:] for l in git_diff("CHANGELOG.md").splitlines()
            if l.startswith("+") and not l.startswith("+++"))

        def _row_name(line):
            cells = [c.strip() for c in line.lstrip("+-").strip().strip("|").split("|")]
            return re.sub(r"[*`]", "", cells[0]).strip().lower() if cells else ""

        def _is_src_row(line):
            s = line.lstrip("+-").strip()
            return (s.startswith("|") and "---" not in s
                    and not re.search(r"\|\s*(source|repo|tool|name)\s*\|", s, re.I))

        for d in sorted(fs_domains):
            rel = f"{SHARD_GIT_PREFIX}/{d}.md"
            diff = git_diff(rel)
            if not diff.strip():
                continue
            added = [l for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++")]
            removed = [l for l in diff.splitlines() if l.startswith("-") and not l.startswith("---")]
            base_raw = git_show(BASE, rel)
            # net-new shard (absent at baseline) is an ADDITION, not a rewrite — CHURN only
            # judges edits to EXISTING files; new files are governed by COVER/THREEWAY/FRESH.
            if not base_raw.strip():
                continue
            base_lines = len(base_raw.splitlines()) or 1
            churn = (len(added) + len(removed)) / base_lines
            removed_ratio = len(removed) / base_lines
            # A REWRITE replaces existing content — its signature is a high REMOVED-line ratio, not raw
            # growth. A pure/near-pure ADDITION (many + lines, few/no - lines, e.g. another agent
            # appending 37 lines to a shard) inflates total churn but rewrites nothing, so it must NOT
            # hard-block. BLOCK only when total churn is high AND a substantial share of the baseline
            # was actually removed/replaced; otherwise surface growth-heavy churn as a WARN for review.
            if churn > CHURN_MAX:
                if removed_ratio > CHURN_MAX:
                    block("CHURN", f"{d}: {int(churn*100)}% of lines changed incl {int(removed_ratio*100)}% "
                                   f"removed (>{int(CHURN_MAX*100)}%) — looks like a rewrite, not an "
                                   f"incremental edit; route to human review")
                else:
                    warn("CHURN", f"{d}: {int(churn*100)}% of lines changed but only {int(removed_ratio*100)}% "
                                  f"removed — growth-heavy (additive), not a rewrite; noting for review")
            added_names = {_row_name(l) for l in added if _is_src_row(l)}
            genuinely_removed = [l for l in removed if _is_src_row(l)
                                 and _row_name(l) and _row_name(l) not in added_names]
            if genuinely_removed:
                added_text = "\n".join(added)
                if not any(c in changelog_added or c in added_text for c in DEATH_CODES):
                    block("DELETE", f"{d}: source row(s) removed without a death-code "
                                    f"(D-404/D-STALE/D-PRICE/D-TOS/D-SUPERSEDED) in CHANGELOG or an "
                                    f"Avoid(dead) line")

    # ---- CONST (scope guard on CONSTITUTION.md) ----
    # CONSTITUTION VII: the constitution changes ONLY through a reasoned PR, never via a refresh sweep.
    # A missing/deleted constitution is fail-closed (BLOCK). A modification vs baseline is surfaced as a
    # WARN, not a hard BLOCK: VII expressly permits a PR to amend it (e.g. adding the I.7 landed-cost
    # provenance rule), so blocking every constitution-touching diff would forbid the very mechanism VII
    # mandates. The WARN routes the diff to human review — the correct severity for "did you mean to
    # change the constitution in this change?" — while a refresh-sweep that touches it still gets flagged.
    if not os.path.exists(CONSTITUTION):
        block("CONST", "CONSTITUTION.md missing")
    elif have_base:
        changed = subprocess.run(["git", "diff", "--name-only", BASE, "--", "CONSTITUTION.md"],
                                 cwd=ROOT, capture_output=True, text=True, encoding="utf-8").stdout.strip()
        if changed:
            warn("CONST", "CONSTITUTION.md was modified vs baseline — allowed ONLY via a reasoned PR "
                          "(CONSTITUTION VII), never a refresh sweep. Route to human review.")

    # ---- METH (SKILL.md keeps the tier/grade legend + the numbered guardrails) ----
    # L1/L5/E1/E3 seller-tier + evidence-grade legend lives in SKILL.md. The full ①②③④ channel-route
    # legend is DEFINED in reference/sources-index.md (SKILL.md only references route ④ inline), so —
    # exactly as market-intel checks ①②③④ against its index — we gate the route legend against the
    # index file, not SKILL.md, to avoid a false BLOCK on a legitimate artifact layout.
    if not os.path.exists(SKILLMD):
        block("METH", "SKILL.md is missing")
    else:
        skill = read(SKILLMD)
        for marker in ["L1", "L5", "E1", "E3"]:
            if marker not in skill:
                block("METH", f"SKILL.md lost tier/grade legend marker '{marker}'")
        # numbered guardrails: lines like `1. **...` or `5b. **...`
        guardrail_nums = len(re.findall(r"^\s*\d+[a-z]?\.\s+\*\*", skill, re.M))
        if guardrail_nums < 10:
            block("METH", f"SKILL.md numbered guardrails look reduced ({guardrail_nums} found, expect >=10)")
    SOURCES_INDEX = os.path.join(REF, "sources-index.md")
    if os.path.exists(SOURCES_INDEX):
        sidx = read(SOURCES_INDEX)
        for marker in ["①", "②", "③", "④"]:
            if marker not in sidx:
                block("METH", f"sources-index.md lost the ①②③④ route-legend marker '{marker}'")
    else:
        warn("METH", "reference/sources-index.md absent — cannot verify the ①②③④ route legend")

    # ---- NOHARDCODE (provenance lint; WARN) ----
    # CONSTITUTION I.7: a tax/duty/de-minimis rate or threshold in SKILL.md prose MUST resolve to a
    # reference/data/ row (or be stamped `(assumed)`), never typed from memory. We scan SKILL.md for a
    # money token (an N% rate or a $N amount) co-occurring on a line with a tax/duty keyword; if that
    # line neither points at `data/` nor carries `(assumed)`, it looks like an inline hard-coded fact.
    # WARN not BLOCK (per the conservative-add rule): a human confirms whether it's a real datum or
    # illustrative. Scoped to the {tax,duty,de-minimis,tariff} family on purpose so that shipping
    # analogies ("eBay $15 ship") and trust/depth thresholds ("<95% rating", "$500+") don't false-fire.
    if os.path.exists(SKILLMD):
        skill_lines = read(SKILLMD).splitlines()
        MONEY_RE = re.compile(r"(?<![\w.])\d+(?:\.\d+)?\s*%|\$\s?\d[\d,]*")
        TAXDUTY_RE = re.compile(r"\b(?:sales[\s-]?tax|de[\s-]?minimis|tariff|duty|duties|customs)\b",
                                re.IGNORECASE)
        # "safe" = the number resolves to a data table or is explicitly assumed. Recognise a direct
        # data-path citation, the table slugs, an (assumed) stamp, and the in-prose phrasing that
        # delegates to a data row ("...status row", "...HTS ... row", "look up reference/data/").
        SAFE_RE = re.compile(r"reference/data|data/[\w-]+\.json|\(assumed\)|us-sales-tax|"
                             r"cross-border-duty|shipping-baselines|fx-source-of-record|"
                             r"status row|HTS|de-minimis (?:status|row)", re.IGNORECASE)
        for i, ln in enumerate(skill_lines, 1):
            if not (MONEY_RE.search(ln) and TAXDUTY_RE.search(ln)):
                continue
            # look at the line plus 1 line of lookback: a wrapped sentence often carries the
            # data-table citation on the preceding physical line.
            window = ln + "\n" + (skill_lines[i - 2] if i >= 2 else "")
            if SAFE_RE.search(window):
                continue
            warn("NOHARDCODE", f"SKILL.md line {i} pairs a tax/duty number with no data-table "
                               f"reference and no (assumed) stamp — cite reference/data/ or mark "
                               f"it (assumed) (CONSTITUTION I.7): {ln.strip()[:90]}")

    # ---- SHARDSYNC (registration discipline; BLOCK) ----
    # A net-new domain shard (reference/domains/<x>.md absent at the git baseline) MUST be registered in
    # BOTH registries the triage path reads: (1) a row in reference/sources-index.md referencing
    # `domains/<x>.md` (the thin index Step 2a reads), and (2) the "README" row — the per-domain README
    # table at the top of reference/domains/ (the sources-index IS that domains README; we additionally
    # require the shard to carry its own `last_verified`-bearing header so it isn't a stub). An orphan
    # shard is invisible to the workflow -> BLOCK. Gates ONLY net-new files (vs baseline) so the current
    # tree, whose shards are already registered, stays PASS; skipped without a git baseline (can't tell
    # new from old). Data tables are governed by DATA + the data README, not SHARDSYNC (they are not
    # triage shards), so this does not fire on R2's newly-landed reference/data/*.json.
    if not have_base:
        warn("SHARDSYNC", f"git baseline '{BASE}' unavailable — skipped new-shard registration check")
    else:
        sidx_txt = read(SOURCES_INDEX) if os.path.exists(SOURCES_INDEX) else ""
        for d in sorted(fs_domains):
            rel = f"{SHARD_GIT_PREFIX}/{d}.md"
            if git_show(BASE, rel).strip():
                continue  # existed at baseline -> not a new shard
            if f"domains/{d}.md" not in sidx_txt:
                block("SHARDSYNC", f"new shard domains/{d}.md has no row in reference/sources-index.md "
                                   f"referencing `domains/{d}.md` — register it or it is invisible to triage")
            if not FRESH_RE.search(shard_text.get(d, "")):
                block("SHARDSYNC", f"new shard domains/{d}.md has no Last-verified header (README row) "
                                   f"— a registered shard MUST carry provenance, not land as a stub")

    # ================================================================= ADDED CHECK (data integrity)
    # ---- DATA: reference/data/*.json conform to the envelope + per-row provenance ----
    # Envelope (owned by reference/data/README.md): {schema_version, last_verified, rows:[{...}]}
    # Each row MUST carry source_url + verified_date. No data dir / no json => silent no-op so the
    # baseline stays green until the parallel agent lands the directory.
    if os.path.isdir(DATA_DIR):
        data_files = sorted(f for f in os.listdir(DATA_DIR) if f.endswith(".json"))
        for fn in data_files:
            path = os.path.join(DATA_DIR, fn)
            try:
                obj = json.loads(read(path))
            except Exception as e:
                block("DATA", f"data/{fn} is not valid JSON: {e}")
                continue
            if not isinstance(obj, dict):
                block("DATA", f"data/{fn} top-level is not a JSON object (expected envelope dict)")
                continue
            if "schema_version" not in obj:
                block("DATA", f"data/{fn} missing envelope key 'schema_version'")
            if "last_verified" not in obj:
                block("DATA", f"data/{fn} missing envelope key 'last_verified'")
            else:
                lv = str(obj["last_verified"])
                mlv = re.match(r"(\d{4})-(\d{2})", lv)
                if mlv and f"{mlv.group(1)}-{mlv.group(2)}" > this_month:
                    block("DATA", f"data/{fn} 'last_verified' {lv} is in the future")
            rows = obj.get("rows")
            if not isinstance(rows, list):
                block("DATA", f"data/{fn} envelope 'rows' is missing or not a list")
                continue
            for i, row in enumerate(rows):
                if not isinstance(row, dict):
                    block("DATA", f"data/{fn} rows[{i}] is not an object")
                    continue
                if not row.get("source_url"):
                    block("DATA", f"data/{fn} rows[{i}] missing non-empty 'source_url'")
                if not row.get("verified_date"):
                    block("DATA", f"data/{fn} rows[{i}] missing non-empty 'verified_date'")
                else:
                    vd = str(row["verified_date"])
                    mvd = re.match(r"(\d{4})-(\d{2})", vd)
                    if mvd and f"{mvd.group(1)}-{mvd.group(2)}" > this_month:
                        block("DATA", f"data/{fn} rows[{i}] 'verified_date' {vd} is in the future")


def main():
    try:
        run_checks()
    except Exception as e:  # fail-closed: any unexpected error is a BLOCK, never a silent pass
        import traceback
        traceback.print_exc()
        print(f"\nRESULT: BLOCK — gate raised an unexpected error (fail-closed): {e}")
        return 1

    for w in warns:
        print("WARN ", w)
    if fails:
        for f in fails:
            print("BLOCK", f)
        print(f"\nRESULT: BLOCK ({len(fails)} blocking issue(s), {len(warns)} warning(s)) — do NOT commit/push")
        return 1
    print(f"\nRESULT: PASS ({len(warns)} warning(s)) — matrix may land")
    return 0


if __name__ == "__main__":
    sys.exit(main())
