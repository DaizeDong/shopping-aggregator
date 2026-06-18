#!/usr/bin/env python3
"""Deterministic lint gate for the shopping-aggregator skill — the skill's FIRST executable gate.

PHILOSOPHY P2 (mechanism-not-intention): the skill is full of advisory "MUST" with no executable
check behind them. This script is the cheap, real mechanism the skill lacked. It implements ONLY
deterministic, non-judgemental checks on DURABLE CONTRACTS / ARTIFACTS — never on prose line numbers,
guardrail numbering, or anything an LLM would have to "judge". It must keep passing while a parallel
agent restructures SKILL.md prose, so it gates on schema/artifact facts, not wording.

Run from the repo root:  python tools/verify_matrix.py
Exit 0 = PASS · non-zero = FAIL (BLOCK). FAIL-CLOSED: any uncaught exception => FAIL, never a silent
pass (a gate that can't run is a BLOCK, not a green light).

Checks:
  THREEWAY  every slug in reference/tools/registry.json has a reference/tools/<slug>.md AND a row in
            reference/tools/index.md, and vice-versa (BLOCK on any mismatch). registry.json may list
            a slug once per domain, so slugs are de-duplicated before comparison. This is
            EXISTENCE-only (each slug present in all three places); per-domain PLACEMENT (which slug
            sits under which domain heading) is advisory, not gated.
  FRESH     every reference/domains/*.md and reference/tools/*.md carries a `Last verified:` /
            `last_verified` line (WARN — see rationale below — never BLOCK).
  TEMPLATE  reference/report-template.md has a "Coverage gaps" section heading AND an "Ev" column in
            the ranking table (BLOCK — these are the I.3 evidence-grade + I.6 coverage-gap contracts
            made visible in the deliverable).
  VERSION   CHANGELOG.md top version == .claude-plugin/plugin.json version (BLOCK on mismatch).
  RENAME    the snake_case token `source_tier` does NOT appear in any live skill file under skills/
            (it was split into seller_tier + evidence_grade in 0.2.0). A leak in SKILL.md or a shard
            means a rename was left half-done (BLOCK). The prose column label "Source tier:" is a
            DIFFERENT, allowed token and is not matched. CHANGELOG.md (repo root, not under skills/)
            legitimately records the rename in its history and is exempt by being out of scope.

Why FRESH is WARN, not BLOCK: a missing freshness stamp is a documentation-rot signal, not a broken
contract — surfacing it for a human to fix is the right severity, and a hard block here would make
the gate brittle to the kind of prose edits another agent may be making concurrently. A FUTURE-dated
stamp WOULD be a lie, but cross-checking dates against "now" is out of scope for this first
deterministic pass (and would couple the gate to wall-clock time); the parent skill's richer gate
owns that. This gate stays narrow and durable on purpose.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS = os.path.join(ROOT, "skills")
SKILL = os.path.join(SKILLS, "shopping-aggregator")
REF = os.path.join(SKILL, "reference")
DOMAINS = os.path.join(REF, "domains")
TOOLS_DIR = os.path.join(REF, "tools")
TOOLS_INDEX = os.path.join(TOOLS_DIR, "index.md")
REGISTRY = os.path.join(TOOLS_DIR, "registry.json")
REPORT_TEMPLATE = os.path.join(REF, "report-template.md")
CHANGELOG = os.path.join(ROOT, "CHANGELOG.md")
PLUGIN_JSON = os.path.join(ROOT, ".claude-plugin", "plugin.json")

fails, warns = [], []


def block(code, msg):
    fails.append(f"[{code}] {msg}")


def warn(code, msg):
    warns.append(f"[{code}] {msg}")


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def run_checks():
    # ---- THREEWAY: registry.json <-> tools/<slug>.md files <-> tools/index.md rows ----
    # registry.json is authoritative (CONSTITUTION III.5). It may list a slug once PER DOMAIN, so we
    # de-duplicate to a set of distinct slugs before comparing against the doc files and index rows.
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

    # doc files on disk (every *.md except index.md)
    fs_slugs = {
        f[:-3]
        for f in os.listdir(TOOLS_DIR)
        if f.endswith(".md") and f != "index.md"
    }

    # index rows: markdown links like [Name](slug.md)
    idx_text = read(TOOLS_INDEX)
    idx_slugs = set(re.findall(r"\(([a-z0-9][a-z0-9-]*)\.md\)", idx_text))

    # registry -> doc / index
    reg_no_doc = reg_slugs - fs_slugs
    reg_no_idx = reg_slugs - idx_slugs
    if reg_no_doc:
        block("THREEWAY", f"registry slugs with no reference/tools/<slug>.md: {sorted(reg_no_doc)}")
    if reg_no_idx:
        block("THREEWAY", f"registry slugs missing from index.md: {sorted(reg_no_idx)}")

    # doc -> registry / index
    doc_no_reg = fs_slugs - reg_slugs
    doc_no_idx = fs_slugs - idx_slugs
    if doc_no_reg:
        block("THREEWAY", f"tool docs not in registry.json (it is authoritative — add them): {sorted(doc_no_reg)}")
    if doc_no_idx:
        block("THREEWAY", f"tool docs not listed in index.md: {sorted(doc_no_idx)}")

    # index -> registry / doc
    idx_no_reg = idx_slugs - reg_slugs
    idx_no_doc = idx_slugs - fs_slugs
    if idx_no_reg:
        block("THREEWAY", f"index.md rows with no registry slug: {sorted(idx_no_reg)}")
    if idx_no_doc:
        block("THREEWAY", f"index.md rows with no reference/tools/<slug>.md: {sorted(idx_no_doc)}")

    # ---- FRESH: every domain shard + tool doc carries a Last verified / last_verified line (WARN) ----
    FRESH_RE = re.compile(r"last[ _]verified", re.IGNORECASE)
    if os.path.isdir(DOMAINS):
        for f in sorted(os.listdir(DOMAINS)):
            if not f.endswith(".md"):
                continue
            if not FRESH_RE.search(read(os.path.join(DOMAINS, f))):
                warn("FRESH", f"domains/{f} has no 'Last verified:' / 'last_verified' line")
    for slug in sorted(fs_slugs):
        if not FRESH_RE.search(read(os.path.join(TOOLS_DIR, slug + ".md"))):
            warn("FRESH", f"tools/{slug}.md has no 'Last verified:' / 'last_verified' line")

    # ---- TEMPLATE: report-template.md has a Coverage gaps heading + an Ev column (BLOCK) ----
    if not os.path.exists(REPORT_TEMPLATE):
        block("TEMPLATE", "reference/report-template.md is missing")
    else:
        tmpl = read(REPORT_TEMPLATE)
        # Coverage gaps section heading (any markdown heading level), case-insensitive, allow "gap"/"gaps".
        if not re.search(r"^#{1,6}\s+coverage gaps?\b", tmpl, re.IGNORECASE | re.MULTILINE):
            block("TEMPLATE", "report-template.md is missing a 'Coverage gaps' section heading (CONSTITUTION I.6)")
        # An "Ev" column in the ranking table: a table-cell whose trimmed content is Ev / **Ev** / `Ev`.
        # Matches "| **Ev** |", "| Ev |", "| `Ev` |" — the evidence_grade column the I.3 contract requires.
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

    # ---- RENAME: the snake_case token `source_tier` must not appear in any live skill file ----
    # It was split into seller_tier + evidence_grade in 0.2.0. We match the literal snake_case token
    # with a word boundary so the allowed prose column label "Source tier:" (space, capital S) is NOT
    # caught. Scope is skills/ only — CHANGELOG.md at repo root legitimately records the rename.
    RENAME_RE = re.compile(r"\bsource_tier\b")
    for dirpath, _dirnames, filenames in os.walk(SKILLS):
        for fn in filenames:
            if not fn.endswith(".md"):
                continue
            fp = os.path.join(dirpath, fn)
            if RENAME_RE.search(read(fp)):
                rel = os.path.relpath(fp, ROOT).replace("\\", "/")
                block("RENAME", f"token `source_tier` leaked into {rel} — it was renamed to seller_tier + evidence_grade")


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
