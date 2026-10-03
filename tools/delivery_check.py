"""Check resource delivery against Git's index, including dynamic domain shards."""
from pathlib import Path
import re
import subprocess

SKILL = "skills/shopping-aggregator"
DOMAIN = re.compile(r"(?:reference/)?domains/([a-z0-9-]+)\.md")
REQUIRED = {f"{SKILL}/SKILL.md", f"{SKILL}/reference/sources-index.md",
            f"{SKILL}/reference/domains/air-travel.md",
            f"{SKILL}/reference/data/airline-baggage.json", "README.md", "README_CN.md"}


def baggage_errors(obj):
    required = {"fare_brand", "checked_bags", "cabin_bags", "tax", "seat_selection", "payment_fx", "refund_terms"}
    allowed = {"schema_version", "kind", "status", "last_verified", "review_cadence_days",
               "rows", "required_terms", "source_types", "policy"}
    terms = obj.get("required_terms")
    sources = obj.get("source_types")
    if (obj.get("schema_version") != 2 or obj.get("kind") != "collection_requirements"
            or obj.get("status") != "unverified" or obj.get("last_verified") is not None
            or "last_verified" not in obj or obj.get("rows") != []
            or not isinstance(terms, list) or not all(isinstance(t, str) for t in terms)
            or len(terms) != len(required) or set(terms) != required
            or not isinstance(sources, list) or not sources
            or not all(isinstance(s, str) and s.strip() for s in sources)
            or set(obj) != allowed or not isinstance(obj.get("policy"), str) or not obj["policy"].strip()
            or obj.get("review_cadence_days") != 30):
        return ["airline-baggage.json must be an unverified collection checklist without fee rows"]
    return []


def delivery_errors(root, tracked=None):
    root = Path(root).resolve()
    if tracked is None:
        result = subprocess.run(["git", "-C", str(root), "ls-files", "-z"],
                                capture_output=True, check=True)
        tracked = set(result.stdout.decode("utf-8").split("\0")) - {""}
        if not tracked:
            return ["Empty Git delivery index; no resources were verified"]
    required = set(REQUIRED)
    index = root / SKILL / "reference/sources-index.md"
    domains = set(DOMAIN.findall(index.read_text(encoding="utf-8"))) if index.is_file() else set()
    errors = []
    if "air-travel" not in domains:
        errors.append("sources-index.md must route flight intents to air-travel")
    required.update(f"{SKILL}/reference/domains/{domain}.md" for domain in domains)
    for readme in ("README.md", "README_CN.md"):
        path = root / readme
        coverage = set(DOMAIN.findall(path.read_text(encoding="utf-8"))) if path.is_file() else set()
        if coverage != domains:
            errors.append(f"{readme} domain coverage differs from sources-index.md")
    for folder in (root / SKILL / "reference", root / "tools"):
        if folder.is_dir():
            required.update(p.relative_to(root).as_posix() for p in folder.rglob("*")
                            if p.is_file() and p.suffix in (".md", ".json", ".jsonl", ".py"))
    # Index entries remain obligations when their worktree files have been removed.
    required.update(p for p in tracked if p.startswith(f"{SKILL}/reference/")
                    and Path(p).suffix in (".md", ".json", ".jsonl"))
    for rel in sorted(required):
        if rel not in tracked:
            errors.append(f"Missing from Git delivery index: {rel}")
        path = root / rel
        if not path.is_file() or not path.resolve().is_relative_to(root):
            errors.append(f"Missing or escaping delivery resource: {rel}")
    return errors
