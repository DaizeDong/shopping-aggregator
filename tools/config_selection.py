"""Which config root a run uses, and whether every command lands in the same one.

scripts/ commands take --config-dir; tools/ commands follow only the environment through the pinned
resolver (guards/tools/datadir.py), in which SHOPPING_AGGREGATOR_DATA_DIR outranks
SHOPPING_AGGREGATOR_CONFIG. Two rules keep them together, and both come from this one module so the
doctor, the ledger writer and the tools cannot disagree:

1. A selection variable that is set must be usable. The resolver skips an empty value and a path
   that does not exist, and carries on to the next candidate, which can be another person's root.
   A Windows path pasted unquoted into Git Bash loses its backslashes and becomes exactly such a
   path. So a set-but-empty or set-but-missing variable is an error for every command.
2. Whatever selects the root for a scripts/ command, the environment must select the same root for
   the tools/ commands that run beside it.
"""
import os
from pathlib import Path

SKILL = "shopping-aggregator"
PREFIX = "SHOPPING_AGGREGATOR"
DATA_DIR = PREFIX + "_DATA_DIR"
CONFIG_VARIABLES = (PREFIX + "_CONFIG", PREFIX + "_CONFIG_DIR")
SELECTION_VARIABLES = (DATA_DIR,) + CONFIG_VARIABLES
RESOLVER = "consumer guards/tools/datadir.py"


def environment_problem(environ=None):
    """A message for a selection variable that is set but empty or not a directory, else None."""
    environ = os.environ if environ is None else environ
    for name in SELECTION_VARIABLES:
        value = environ.get(name)
        if value is None:
            continue
        if not value.strip():
            return "%s is set but empty; unset it or point it at a config root" % name
        if not Path(value).expanduser().is_dir():
            return ("%s is set but is not an existing directory; check the path (quote Windows paths "
                    "or use forward slashes)" % name)
    return None


def same_path(left, right):
    return (os.path.normcase(str(Path(left).expanduser().resolve()))
            == os.path.normcase(str(Path(right).expanduser().resolve())))


def selection_checks(root, how, resolve_data_dir, environ=None):
    """(name, ok, detail) triples proving that scripts/ and tools/ commands share `root`."""
    environ = os.environ if environ is None else environ
    problem = environment_problem(environ)
    checks = [("selection variables are usable", problem is None, problem or "")]
    data_override = environ.get(DATA_DIR)
    if data_override is not None and data_override.strip():
        checks.append(("%s is the selected root's data/" % DATA_DIR,
                       same_path(data_override, Path(root) / "data"),
                       "unset it or set it to <root>/data; evaluation runs, the cache, refresh_priority "
                       "and verify_matrix follow it"))
    if how == "explicit CLI path":
        for name in CONFIG_VARIABLES:
            value = environ.get(name)
            if value is not None and value.strip():
                checks.append(("%s agrees with --config-dir" % name, same_path(value, root),
                               "the tools that follow the environment would use another root; "
                               "unset it or point it here"))
    if how == RESOLVER:
        try:
            resolved = resolve_data_dir(SKILL)
            detail = "the resolver's data dir is a data-only location, not this root's data/; migrate it"
        except Exception as exc:  # a resolver refusal is reported, never fallen through
            resolved, detail = None, str(exc).splitlines()[0]
        checks.append(("resolver data dir is the root's data/",
                       resolved is not None and same_path(resolved, Path(root) / "data"), detail))
    return checks
