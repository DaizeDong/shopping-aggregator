"""Writer preflight for runtime DATA in the companion repository.

Runtime writes carry no PRIVATE visibility proof. The destination is decided by companion
resolution with no in-repository fallback, and a write is refused only by cheap path checks:
the data directory must resolve and exist, sit in a versioned repository of its own outside this
public tool tree (checked once, on that repository), and every destination must stay inside it,
outside Git metadata and nested repositories, and free of filesystem aliases. Commit-time Guards hooks keep the companion's history out of public
remotes.
"""
from contextlib import contextmanager
from functools import lru_cache
import os
from pathlib import Path
import stat
import uuid

TOOL_ROOT = Path(__file__).resolve().parents[1]
SKILL = "shopping-aggregator"


class StorageError(RuntimeError):
    """No companion output location could be established."""


@lru_cache(maxsize=None)
def _resolver():
    try:
        from fleet_guards.runtime import companion_resolver
    except ImportError as exc:
        raise ImportError('fleet_guards is not installed; run: pip install -e "$(git config --get fleet.guards)"') from exc
    return companion_resolver(source_root=TOOL_ROOT)


def resolve_base():
    """Discover the data directory with the shared resolver.

    A selection variable that is set but empty or missing would let the resolver fall through to
    the next candidate, possibly another person's root, so it is refused before discovery.
    """
    from config_selection import environment_problem
    problem = environment_problem()
    if problem:
        raise StorageError(problem)
    return _resolver().resolve_data_dir(SKILL, create=False)


def _plain_path(path):
    """Refuse aliases before resolution can hide them, including Windows junctions."""
    for node in (*reversed(path.parents), path):
        try:
            info = node.lstat()
        except FileNotFoundError:
            continue
        if (stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400
                or stat.S_ISREG(info.st_mode) and info.st_nlink != 1):
            raise StorageError("Companion storage path contains a filesystem alias")


def companion_repository(path):
    """The nearest enclosing directory with a `.git` entry, found without running git.

    Raises StorageError when the path is not in a versioned repository, or when that repository
    is this tool repository or contains it.
    """
    path = Path(path).expanduser().absolute()
    _plain_path(path)
    path = path.resolve()
    for candidate in (path, *path.parents):
        if os.path.lexists(candidate / ".git"):
            if candidate.is_relative_to(TOOL_ROOT) or TOOL_ROOT.is_relative_to(candidate):
                raise StorageError("Runtime DATA requires a separate versioned companion")
            return candidate
    raise StorageError("Runtime DATA requires a separate versioned companion: %s is not inside a "
                       "git repository" % path)


class PrivateStore:
    def __init__(self, base, repository):
        self.base = base
        self.repository = repository

    def _validate(self, requested):
        path = Path(requested).expanduser().absolute()
        _plain_path(path)
        path = path.resolve()
        if not path.is_relative_to(self.base):
            raise StorageError("Runtime path escapes the companion data directory")
        relative = path.relative_to(self.repository)
        if any(part.casefold() == ".git" for part in relative.parts):
            raise StorageError("Runtime paths cannot enter Git administration")
        for parent in (path, *path.parents):
            if parent == self.repository:
                break
            if os.path.lexists(parent / ".git"):
                raise StorageError("Runtime paths cannot enter a nested repository")
        return path

    def transcript(self, requested):
        path = self._validate(requested)
        if not path.is_file():
            raise StorageError("Transcript must be a file within the companion data directory")
        return path

    def output_path(self, relative):
        """A checked destination below the data directory."""
        return self._validate(self.base / relative)

    def new_run(self):
        path = self.output_path(Path("evaluation") / "runs" / uuid.uuid4().hex)
        path.mkdir(parents=True, exist_ok=False)
        return path

    @contextmanager
    def atomic_writer(self, relative, *, binary=False):
        """Stage beside the data, then replace; a failed write preserves the old file."""
        path = self.output_path(relative)
        temporary = self.output_path(Path('.write-staging') / (uuid.uuid4().hex + '.tmp'))
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary.parent.mkdir(parents=True, exist_ok=True)
        options = {} if binary else {"encoding": "utf-8", "newline": "\n"}
        # Failed publication retains staging bytes for the declared recovery review.
        with temporary.open(mode='xb' if binary else 'x', **options) as stream:
            opened = os.fstat(stream.fileno())
            if not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1:
                raise StorageError('Atomic staging must be a single regular file')
            yield stream
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)

    def write_bytes(self, relative, contents):
        with self.atomic_writer(relative, binary=True) as stream:
            stream.write(contents)


def prepare_store(base=None):
    """Check storage before opening any private transcript or creating output.

    `base` is an explicitly selected data directory (scripts/ledger.py passes <config root>/data for
    the root the buyer selected). It gets exactly the same checks as a discovered one; omitting it
    keeps the shared resolver as the only discovery path. Missing storage is an error with
    initialization guidance; there is no fallback location.
    """
    if base is None:
        try:
            base = resolve_base()
        except (OSError, RuntimeError) as exc:
            raise StorageError("Cannot resolve companion storage; initialize the companion") from exc
    if base is None or not Path(base).is_dir():
        raise StorageError("Uninitialized: clone the shopping-aggregator-config companion, create data/, "
                           "and configure SHOPPING_AGGREGATOR_CONFIG or SHOPPING_AGGREGATOR_DATA_DIR")
    base = Path(base).expanduser().absolute()
    repository = companion_repository(base)
    return PrivateStore(base.resolve(), repository)
