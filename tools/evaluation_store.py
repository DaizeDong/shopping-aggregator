"""Writer preflight for runtime DATA in a versioned PRIVATE companion."""
from datetime import datetime, timezone
import importlib.util
from pathlib import Path
import re
import subprocess
from urllib.parse import urlsplit
import uuid

TOOL_ROOT = Path(__file__).resolve().parents[1]


class StorageError(RuntimeError):
    """No private output boundary could be established."""


def _run(args):
    try:
        result = subprocess.run(args, capture_output=True, text=True, encoding="utf-8",
                                timeout=20, check=False)
    except (OSError, ValueError, UnicodeError, subprocess.TimeoutExpired) as exc:
        raise StorageError(f"Private storage verification unavailable: {args[0]}") from exc
    if result.returncode:
        raise StorageError(f"Private storage verification failed: {args[0]}")
    return result.stdout.strip()


def repository_identity(remote):
    if "://" in remote:
        parsed = urlsplit(remote)
        if (parsed.scheme not in ("https", "ssh") or parsed.password or parsed.query
                or parsed.fragment or (parsed.scheme == "https" and parsed.username)
                or parsed.port not in (None, 22, 443)):
            raise StorageError("Unsupported companion origin")
        host, path = parsed.hostname, parsed.path.lstrip("/")
    else:
        match = re.fullmatch(r"(?:[^@/:\s]+@)?([^/:\s]+):([^\s]+)", remote)
        if not match:
            raise StorageError("Companion origin must identify a GitHub repository")
        host, path = match.groups()
    if host != "github.com":
        if remote.startswith("https://") or not re.fullmatch(r"[A-Za-z0-9_.-]+", host or ""):
            raise StorageError("Cannot prove companion visibility")
        names = [line.split(None, 1)[1].lower() for line in _run(["ssh", "-G", host]).splitlines()
                 if line.lower().startswith("hostname ")]
        if names != ["github.com"]:
            raise StorageError("Companion SSH alias must resolve to github.com")
    identity = path.removesuffix(".git")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", identity):
        raise StorageError("Companion origin must identify one owner/repository")
    return identity


def resolve_base():
    """Discover only; the shared resolver's result is not visibility proof."""
    module_path = TOOL_ROOT / "guards/tools/datadir.py"
    if not module_path.is_file():
        raise StorageError("Initialize the guards submodule before evaluating")
    spec = importlib.util.spec_from_file_location("shopping_datadir", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.resolve_data_dir("shopping-aggregator", create=False)


def repo_root(path):
    return Path(_run(["git", "-C", str(path), "rev-parse", "--show-toplevel"])).resolve()


class PrivateStore:
    def __init__(self, base, repository, identity):
        self.base = base
        self.repository = repository
        self.identity = identity
        self.checked_at = datetime.now(timezone.utc).isoformat()

    def transcript(self, requested):
        path = Path(requested).expanduser().resolve()
        if not path.is_file() or not path.is_relative_to(self.base):
            raise StorageError("Transcript must be a file within the verified private data directory")
        if repo_root(path.parent) != self.repository:
            raise StorageError("Transcript crosses into a different repository")
        return path

    def output_path(self, relative):
        resolved = (self.base / relative).resolve()
        if not resolved.is_relative_to(self.base):
            raise StorageError("Runtime output escapes the private data directory")
        existing = resolved.parent
        while not existing.exists():
            existing = existing.parent
        if repo_root(existing) != self.repository:
            raise StorageError("Runtime output crosses into a different repository")
        return resolved

    def new_run(self):
        resolved = self.output_path(Path("evaluation") / "runs" / uuid.uuid4().hex)
        resolved.mkdir(parents=True, exist_ok=False)
        return resolved


def prepare_store():
    """Verify storage before opening any private transcript or creating output."""
    try:
        base = resolve_base()
    except (OSError, RuntimeError) as exc:
        raise StorageError("Cannot resolve private evaluation storage; initialize the companion") from exc
    if base is None or not Path(base).is_dir():
        raise StorageError("Uninitialized: clone a PRIVATE companion, create data/, and configure "
                           "SHOPPING_AGGREGATOR_CONFIG or SHOPPING_AGGREGATOR_DATA_DIR")
    base = Path(base).resolve()
    if base.is_relative_to(TOOL_ROOT) or TOOL_ROOT.is_relative_to(base):
        raise StorageError("Evaluation DATA must be outside the public tool worktree")
    repository = repo_root(base)
    if (not base.is_relative_to(repository) or repository.is_relative_to(TOOL_ROOT)
            or TOOL_ROOT.is_relative_to(repository)):
        raise StorageError("Evaluation requires a separate versioned companion")
    identity = repository_identity(_run(["git", "-C", str(repository), "config", "--get", "remote.origin.url"]))
    if _run(["gh", "api", "--hostname", "github.com", "repos/" + identity, "--jq", ".private"]) != "true":
        raise StorageError("Companion is PUBLIC or visibility is unknown; refusing evaluation")
    return PrivateStore(base, repository, identity)
