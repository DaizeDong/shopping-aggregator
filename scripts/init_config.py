#!/usr/bin/env python3
"""Initialize a deterministic shopping-aggregator config root outside the tool repo.

A config root is one person's settings plus their run data. The default root is the private
companion found by the pinned guards resolver; another person gets their own root, by convention
<companion>/people/<id>/, selected with --out here and with SHOPPING_AGGREGATOR_CONFIG or
--config-dir everywhere else. CONFIG.md is the contract for every file written here.

Explicit --out, CONFIG and CONFIG_DIR selections take precedence. Without one, reuse an existing
companion; create ~/.shopping-aggregator-config only when no companion exists. Existing files are
kept (SKIP) unless --force. The profile skeleton is deliberately incomplete, down to the
subscription policy: the doctor reports NOT READY until a person fills it, because a profile
nobody filled, or a commitment nobody chose, must never pass as one.

Usage: python scripts/init_config.py [--skill shopping-aggregator] [--out <dir>] [--force]
Stdlib only. Never writes secrets or personal values.
"""
import argparse
import json
import os
from pathlib import Path
import stat
import sys
import tempfile

from config_runtime import ConfigRuntime, env_var

GITIGNORE = """\
# Default credential exclusions; selected PRIVATE backup files may be tracked explicitly.
secrets/*
!secrets/README.md
!secrets/.gitkeep
*.env
!*.env.template
!env.template
claude.json
.claude.json
*credentials*.json
*.key
*.pem
!*.key.template
!*.pem.template

# Everything under data/ is versioned, caches included: the private writer refuses ignored paths.
__pycache__/
*.pyc
"""

SECRETS_README = """\
# secrets/ and private backups

Default ignore rules prevent accidental staging (see ../.gitignore). Keep real credentials out of
the public tool repository. Before storing them here, verify that this separate companion and
every effective push destination are PRIVATE.

Choose a separate backup or deliberately include selected credentials in this PRIVATE versioned
companion. Retain the default ignore rules for unselected files and document the chosen backup
and restore procedure here. Ignore rules do not prevent explicit tracking. Committed credentials
remain in history; rotate the credential itself when required. Never echo values in logs or reports.

Per tool, create `secrets/<slug>.env` with the KEY=VALUE pairs its `tools/<slug>/env.template` lists.
Files MUST be UTF-8 without BOM.
"""

ROOT_README = """\
# shopping-aggregator config root

One person's shopping-aggregator settings and run data. The layout, every field and every rule
is defined by CONFIG.md in the public shopping-aggregator repository; do not add files that it
does not define.

- `profile.json`: who is buying (market, ship-to ZIP and state, memberships, purchase defaults).
- `registry.json`: which optional sources this root has set up.
- `data/`: run DATA (observation ledger, purchases ledger, evaluation runs, a rebuildable cache), all versioned.
- `people/<id>/`: another person's complete root with this same layout.
- `tools/`, `secrets/`: per-tool templates and ignored credentials.

Check it with `python scripts/verify_config.py --config-dir <this directory>` from the tool repo.
"""

PEOPLE_README = """\
# people/

Each subdirectory is one more person's complete config root, with the same layout as the
parent: profile.json, registry.json, data/. Create one with

    python scripts/init_config.py --out <this directory>/<person-id>

and select it for a run with SHOPPING_AGGREGATOR_CONFIG=<that path> or --config-dir <that path>.
Their purchases and observations then land in their own data/, never in the parent's.
"""

PROFILE_SKELETON = {
    "schema_version": 1,
    "profile_id": "",
    "label": "",
    "market": {"country": "", "currency": "", "locale": ""},
    "ship_to": {"zip": "", "state": "", "effective_from": ""},
    "memberships": [],
    "not_held": [],
    "store_credit": [],
    "purchase_defaults": {"subscriptions": "", "subscription_interval": "page-default"},
    "risk": {"marketplace_min_rating_pct": 95, "marketplace_min_ratings": 500, "deep_depth_usd": 500},
    "accounts": [],
    "off_limits": [],
}


def checked_destination(path):
    """Reject linked files and redirected parents without following their aliases."""
    path = Path(os.path.abspath(path))
    for node in (*reversed(path.parents), path):
        try:
            info = node.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 1024:
            raise ValueError("Generated config destination contains a link or reparse alias: %s" % node)
        if node == path:
            if not stat.S_ISREG(info.st_mode):
                raise ValueError("Generated config destination is not a file: %s" % node)
            if info.st_nlink != 1:
                raise ValueError("Generated config destination contains a hardlink alias: %s" % node)
        elif not stat.S_ISDIR(info.st_mode):
            raise ValueError("Generated config parent is not a directory: %s" % node)
    return path


def write(path, content, force):
    path = checked_destination(path)
    if path.exists() and not force:
        print("  SKIP (exists): %s" % path)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    checked_destination(path)
    temporary, identity = None, None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n",
                                         prefix=".init-config-", dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            info = os.fstat(stream.fileno())
            identity = info.st_dev, info.st_ino
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        checked_destination(temporary)
        current = temporary.stat()
        if (current.st_dev, current.st_ino) != identity:
            raise ValueError("Generated config temporary changed ownership")
        checked_destination(path)
        if path.exists() and not force:
            print("  SKIP (exists): %s" % path)
            return
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            checked_destination(temporary)
            current = temporary.stat()
            if (current.st_dev, current.st_ino) != identity:
                raise ValueError("Refusing to remove another writer's config temporary")
            temporary.unlink()
    print("  wrote: %s" % path)


def validate_destinations(root, paths, runtime):
    """Check every physical destination and parent before creating or replacing files."""
    root = Path(root).resolve()
    for path in paths:
        target = checked_destination(path)
        runtime.resolver.assert_outside_own_repo(target, runtime.skill)
        if not target.is_relative_to(root):
            raise ValueError("Generated config destination escapes the selected root: %s" % path)
        if target.exists() and not target.is_file():
            raise ValueError("Generated config destination is not a file: %s" % path)
        parent = target.parent
        while not parent.exists():
            parent = parent.parent
        if not parent.is_dir():
            raise ValueError("Generated config parent is not a directory: %s" % path)


def main():
    ap = argparse.ArgumentParser(description="Stamp a shopping-aggregator config root (CONFIG.md).")
    ap.add_argument("--skill", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()

    try:
        runtime = ConfigRuntime(a.skill)
        out, how = runtime.discover(a.out, initialize=True)
    except (OSError, ValueError, RuntimeError) as exc:
        print("ERROR: %s" % exc)
        return 1
    skill = runtime.skill
    print("Init config for skill '%s' at %s" % (skill, out))
    print("Resolved via %s; discovery env var: %s" % (how, env_var(skill)))

    registry = {"schema_version": 1, "skill": skill, "tools": []}
    generated = {
        "registry.json": json.dumps(registry, indent=2, ensure_ascii=False) + "\n",
        "profile.json": json.dumps(PROFILE_SKELETON, indent=2, ensure_ascii=False) + "\n",
        ".gitignore": GITIGNORE,
        "README.md": ROOT_README,
        "data/.gitkeep": "",
        "people/README.md": PEOPLE_README,
        "tools/.gitkeep": "",
        "secrets/README.md": SECRETS_README,
        "secrets/.gitkeep": "",
    }
    destinations = {os.path.join(out, name): content for name, content in generated.items()}
    try:
        validate_destinations(out, destinations, runtime)
        for path, content in destinations.items():
            write(path, content, a.force)
    except (OSError, ValueError, RuntimeError) as exc:
        print("ERROR: %s" % exc)
        return 1

    print("\nNext:")
    print("  1) Make the root a git repository whose only remotes are PRIVATE, before adding real values")
    print("     (CONFIG.md, First-time setup), and keep ~/.pii-guard/visibility.json current.")
    print("  2) Fill profile.json: profile_id, label, market, ship_to, purchase_defaults.subscriptions.")
    shown = Path(out).as_posix()
    print("  3) Only for a root the resolver does not find by itself, select it in each shell:")
    print("       export %s='%s'                (Git Bash)" % (env_var(skill), shown))
    print("       $env:%s='%s'                  (PowerShell)" % (env_var(skill), shown))
    print("  4) python scripts/verify_config.py   # NOT READY until all of the above holds")
    return 0


if __name__ == "__main__":
    sys.exit(main())
