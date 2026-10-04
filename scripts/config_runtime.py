"""Bind emitted config commands to their consumer and its pinned guard resolver."""
import hashlib
import fnmatch
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess


class ConfigError(RuntimeError):
    """Config discovery cannot safely identify its consumer or destination."""


def env_var(skill):
    return skill.upper().replace("-", "_") + "_CONFIG"


def secrets_ignore_problems(text):
    """Check ordered root ignore rules against representative secret paths.

    Supports component globs, **, anchoring, directories and negation. Escaped patterns
    remain unresolved. This is a root-rule check, not a scan of Git's index or history.
    """
    rules, problems = [], []
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.rstrip(" ")
        if not line or line.startswith("#"):
            continue
        excluded = not line.startswith("!")
        pattern = line if excluded else line[1:]
        if not pattern:
            continue
        if "\\" in pattern:
            problems.append("unsupported escaped ignore rule on line %d" % number)
            continue
        anchored = pattern.startswith("/")
        directory = pattern.endswith("/")
        parts = pattern.strip("/").split("/")
        rules.append((parts, anchored or len(parts) > 1, directory, excluded))

    def match_parts(pattern, path):
        if not pattern:
            return not path
        if pattern[0] == "**":
            return match_parts(pattern[1:], path) or bool(path and match_parts(pattern, path[1:]))
        return bool(path and fnmatch.fnmatchcase(path[0], pattern[0])
                    and match_parts(pattern[1:], path[1:]))

    def ignored(path):
        parts = path.split("/")
        for length in range(1, len(parts) + 1):
            node, is_directory = parts[:length], length < len(parts)
            excluded = False
            for pattern, anchored, directory, value in rules:
                if directory and not is_directory:
                    continue
                matches = match_parts(pattern, node) if anchored else fnmatch.fnmatchcase(node[-1], pattern[0])
                if matches:
                    excluded = value
            if excluded:
                return True  # Git cannot reinclude a child beneath an excluded directory.
        return False

    for path in ("secrets/fixture-secret.txt", "secrets/nested/fixture-secret.txt",
                 ".env", "settings.env", "config/settings.env"):
        if not ignored(path):
            problems.append("root ignore rules do not exclude %s" % path)
    return problems


_GIT_SELECTORS = {
    "GIT_DIR", "GIT_COMMON_DIR", "GIT_WORK_TREE", "GIT_IMPLICIT_WORK_TREE",
    "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_GRAFT_FILE", "GIT_SHALLOW_FILE", "GIT_PREFIX", "GIT_INTERNAL_SUPER_PREFIX",
    "GIT_CEILING_DIRECTORIES", "GIT_DISCOVERY_ACROSS_FILESYSTEM", "GIT_CONFIG",
    "GIT_REPLACE_REF_BASE",
}


def _git(root, *args, binary=False):
    env = {key: value for key, value in os.environ.items() if key.upper() not in _GIT_SELECTORS}
    env["GIT_NO_REPLACE_OBJECTS"] = "1"
    env["GIT_OPTIONAL_LOCKS"] = "0"
    output = {} if binary else {"text": True, "encoding": "utf-8", "errors": "replace"}
    try:
        result = subprocess.run(["git", "-C", str(root), *args], capture_output=True,
                                env=env, timeout=30, **output)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ConfigError("Cannot verify consumer Git state: %s" % exc) from exc
    if result.returncode:
        error = result.stderr.decode("utf-8", "replace") if binary else result.stderr
        raise ConfigError("Cannot verify consumer Git state (%s): %s" %
                          (" ".join(args), error.strip() or "exit %d" % result.returncode))
    return result.stdout if binary else result.stdout.strip()


class ConfigRuntime:
    """A separate resolver instance for one emitted consumer, including linked worktrees."""

    def __init__(self, requested_skill=None):
        self.consumer = Path(__file__).resolve().parent.parent
        actual_root = Path(_git(self.consumer, "rev-parse", "--show-toplevel")).resolve()
        if actual_root != self.consumer:
            raise ConfigError("Config commands must live in the consumer's scripts/ directory.")
        try:
            plugin = json.loads((self.consumer / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise ConfigError("Cannot read the consuming plugin identity: %s" % exc) from exc
        self.skill = plugin.get("name") if isinstance(plugin, dict) else None
        if not isinstance(self.skill, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", self.skill):
            raise ConfigError("The consuming plugin.json must declare a kebab-case skill name.")
        if requested_skill and requested_skill != self.skill:
            raise ConfigError("--skill must match the consuming plugin identity: %s" % self.skill)

        kit = self.consumer / "guards"
        resolver = kit / "tools/datadir.py"
        if not (kit / ".git").is_file() or not resolver.is_file():
            raise ConfigError("Pinned guards resolver missing; run git submodule update --init --recursive guards.")
        gitlink = _git(self.consumer, "ls-files", "--stage", "--", "guards").split()
        if len(gitlink) != 4 or gitlink[0] != "160000" or gitlink[2:] != ["0", "guards"]:
            raise ConfigError("The consumer must track guards as a pinned submodule.")
        if Path(_git(kit, "rev-parse", "--show-toplevel")).resolve() != kit:
            raise ConfigError("The guards worktree is not the consumer's pinned kit.")
        if _git(kit, "rev-parse", "--verify", "HEAD") != gitlink[1]:
            raise ConfigError("guards HEAD differs from the consumer gitlink; restore the pinned kit.")
        _git(kit, "ls-files", "--error-unmatch", "--", "tools/datadir.py")
        pinned_bytes = _git(kit, "cat-file", "blob", gitlink[1] + ":tools/datadir.py", binary=True)
        try:
            resolver_bytes = resolver.read_bytes()
        except OSError as exc:
            raise ConfigError("Cannot read the pinned guards resolver: %s" % exc) from exc
        if resolver_bytes != pinned_bytes:
            raise ConfigError("guards resolver bytes differ from the consumer gitlink; restore the pinned kit.")
        module_name = "_config_datadir_" + hashlib.sha256(str(self.consumer).encode()).hexdigest()
        spec = importlib.util.spec_from_file_location(module_name, resolver)
        if spec is None or spec.loader is None:
            raise ConfigError("Cannot load the consumer's pinned guards resolver.")
        self.resolver = importlib.util.module_from_spec(spec)
        exec(compile(resolver_bytes, str(resolver), "exec"), self.resolver.__dict__)
        for name in ("resolve_companion_root", "assert_outside_own_repo", "_own_repo_root"):
            if not callable(getattr(self.resolver, name, None)):
                raise ConfigError("Pinned guards resolver lacks %s; update the kit deliberately." % name)
        # The pinned helper skips .git files, including linked consumer worktrees. Bind only
        # this private module instance so discovery and containment share the verified consumer.
        self.resolver._own_repo_root = lambda: str(self.consumer)

    def _destination(self, value):
        root = Path(value).expanduser().resolve()
        self.resolver.assert_outside_own_repo(root, self.skill)
        return str(root)

    def discover(self, override=None, initialize=False):
        """Explicit config selections never fall through; defaults use the pinned resolver.

        An empty selection is an error, not an absent one: `--config-dir "$ROOT"` with ROOT unset,
        or a variable exported empty, must not quietly hand the run to whichever root comes next.
        """
        if override is not None:
            if not str(override).strip():
                raise ConfigError("The explicit config selection is empty.")
            return self._destination(override), "explicit CLI path"
        for variable in (env_var(self.skill), env_var(self.skill) + "_DIR"):
            value = os.environ.get(variable)
            if value is not None:
                if not value.strip():
                    raise ConfigError("%s is set but empty; unset it or point it at a config root." % variable)
                return self._destination(value), "env:%s" % variable
        root = self.resolver.resolve_companion_root(self.skill)
        if root is not None:
            return self._destination(root), "consumer guards/tools/datadir.py"
        if initialize:
            return self._destination("~/.%s-config" % self.skill), "new home config skeleton"
        return None, None
