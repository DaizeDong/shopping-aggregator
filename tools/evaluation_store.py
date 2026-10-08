"""Writer preflight for runtime DATA in a versioned PRIVATE companion."""
from contextlib import contextmanager
from datetime import datetime, timezone
from functools import lru_cache
import importlib.util
import os
from pathlib import Path
import stat
import sys
import uuid

TOOL_ROOT = Path(__file__).resolve().parents[1]


class StorageError(RuntimeError):
    """No private output boundary could be established."""


@lru_cache(maxsize=None)
def _guards_module(name):
    module_path = TOOL_ROOT / "guards/tools" / (name + ".py")
    if not module_path.is_file():
        raise StorageError("Initialize the guards submodule before evaluating")
    spec = importlib.util.spec_from_file_location("shopping_" + name, module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def resolve_base():
    """Discover only; the shared resolver's result is not visibility proof.

    A selection variable that is set but empty or missing would let the resolver fall through to
    the next candidate, possibly another person's root, so it is refused before discovery.
    """
    from config_selection import environment_problem
    problem = environment_problem()
    if problem:
        raise StorageError(problem)
    return _guards_module("datadir").resolve_data_dir("shopping-aggregator", create=False)


def _prove(path):
    guard = _guards_module("data_boundary")
    try:
        proof = guard.prove_private_companion(path)
        guard.read_private_companion_git(proof, "rev-parse", "--verify", "HEAD")
        return proof
    except guard.GitError as exc:
        raise StorageError("Cannot prove a versioned PRIVATE companion: " + str(exc)) from exc


def prove_private(path):
    """Public form of the proof for callers that only need to know, such as the config doctor."""
    return _prove(Path(path))


def _plain_path(path):
    """Refuse aliases before resolution can hide them, including Windows junctions."""
    for node in (*reversed(path.parents), path):
        try:
            info = node.lstat()
        except FileNotFoundError:
            continue
        if (stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400
                or stat.S_ISREG(info.st_mode) and info.st_nlink != 1):
            raise StorageError("Private storage path contains a filesystem alias")


class PrivateStore:
    def __init__(self, base, proof):
        self.base = base
        self.repository = Path(proof.root).resolve()
        self.identity = ", ".join(proof.repositories)
        self.checked_at = datetime.now(timezone.utc).isoformat()
        self._proof = proof

    def _validate(self, requested, *, check_versioning=True):
        path = Path(requested).expanduser().absolute()
        _plain_path(path)
        path = path.resolve()
        if not path.is_relative_to(self.base):
            raise StorageError("Runtime path escapes the private data directory")
        existing = path if path.is_dir() else path.parent
        while not existing.exists():
            existing = existing.parent
        proof = _prove(existing)
        if (proof.root, proof.repositories, proof.signature) != (
                self._proof.root, self._proof.repositories, self._proof.signature):
            raise StorageError("Private storage repository or configuration changed")
        relative = path.relative_to(self.repository)
        if any(part.casefold() == ".git" for part in relative.parts):
            raise StorageError("Runtime paths cannot enter Git administration")
        guard = _guards_module("data_boundary")
        try:
            ignored = guard.read_private_companion_git(
                proof, "check-ignore", "--no-index", "-q", "--",
                relative.as_posix())
        except guard.GitError as exc:
            raise StorageError("Cannot verify private output versioning") from exc
        if ignored.returncode == 0 and check_versioning:
            raise StorageError("Private runtime paths must be eligible for version control")
        self.checked_at = datetime.now(timezone.utc).isoformat()
        return path

    def transcript(self, requested):
        path = self._validate(requested)
        if not path.is_file():
            raise StorageError("Transcript must be a file within the verified private data directory")
        return path

    def output_path(self, relative, *, directory=False, transient=False):
        path = self._validate(self.base / relative, check_versioning=not transient)
        try:
            admission = _guards_module('storage_contract').authorize_artifact_write(
                TOOL_ROOT, self.repository, path.relative_to(self.repository).as_posix(),
                directory=directory)
        except (OSError, RuntimeError, ValueError) as exc:
            raise StorageError('Artifact admission refused: ' + str(exc)) from exc
        if (admission.proof.root, admission.proof.repositories, admission.proof.signature) != (
                self._proof.root, self._proof.repositories, self._proof.signature):
            raise StorageError('Private storage authority changed during artifact admission')
        return admission.path

    def new_run(self):
        path = self.output_path(Path("evaluation") / "runs" / uuid.uuid4().hex, directory=True)
        path.mkdir(parents=True, exist_ok=False)
        return path

    @contextmanager
    def atomic_writer(self, relative, *, binary=False):
        """Reprove before opening and replacing; a failed write preserves the old file."""
        path = self.output_path(relative)
        temporary = self.output_path(Path('.write-staging') / (uuid.uuid4().hex + '.tmp'),
                                     transient=True)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary.parent.mkdir(parents=True, exist_ok=True)
        options = {} if binary else {"encoding": "utf-8", "newline": "\n"}
        # Failed publication retains staging bytes for the declared recovery review.
        with temporary.open(mode='xb' if binary else 'x', **options) as stream:
            opened = os.fstat(stream.fileno())
            identity = (opened.st_dev, opened.st_ino)
            if not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1:
                raise StorageError('Atomic staging must be a single regular file')
            self.output_path(temporary.relative_to(self.base), transient=True)
            current = temporary.lstat()
            if (current.st_dev, current.st_ino) != identity:
                raise StorageError('Atomic staging changed before open')
            self.output_path(relative)
            yield stream
            stream.flush()
            os.fsync(stream.fileno())
        self.output_path(relative)
        self.output_path(temporary.relative_to(self.base), transient=True)
        current = temporary.lstat()
        if (current.st_dev, current.st_ino) != identity:
            raise StorageError('Atomic staging changed before publication')
        temporary.replace(path)

    def write_bytes(self, relative, contents):
        with self.atomic_writer(relative, binary=True) as stream:
            stream.write(contents)


def prepare_store(base=None):
    """Verify storage before opening any private transcript or creating output.

    `base` is an explicitly selected data directory (scripts/ledger.py passes <config root>/data for
    the root the buyer selected). It gets exactly the same proof as a discovered one; omitting it
    keeps the shared resolver as the only discovery path.
    """
    if base is None:
        try:
            base = resolve_base()
        except (OSError, RuntimeError) as exc:
            raise StorageError("Cannot resolve private evaluation storage; initialize the companion") from exc
    if base is None or not Path(base).is_dir():
        raise StorageError("Uninitialized: clone a PRIVATE companion, create data/, and configure "
                           "SHOPPING_AGGREGATOR_CONFIG or SHOPPING_AGGREGATOR_DATA_DIR")
    base = Path(base).expanduser().absolute()
    _plain_path(base)
    base = base.resolve()
    if base.is_relative_to(TOOL_ROOT) or TOOL_ROOT.is_relative_to(base):
        raise StorageError("Evaluation DATA must be outside the public tool worktree")
    proof = _prove(base)
    repository = Path(proof.root).resolve()
    if (not base.is_relative_to(repository) or repository.is_relative_to(TOOL_ROOT)
            or TOOL_ROOT.is_relative_to(repository)):
        raise StorageError("Evaluation requires a separate versioned companion")
    store = PrivateStore(base, proof)
    store._validate(base)
    return store
