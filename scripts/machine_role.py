"""Machine role and id for a two-machine setup.

The role (CLAUDE_MACHINE_ROLE=secondary) decides which machine causes outside side effects; the id
(CLAUDE_MACHINE_ID, for example node-a) names this machine's own lane in a per-machine ledger. Both are
read on every call from this process's environment and from HKCU\\Environment, so a process started
before the value changed obeys it too. A missing role means primary; a missing id is an error.
"""
import os
import sys

MESSAGE = 'secondary machine: do this on the primary'


def _registry(name):
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Environment') as key:
            return str(winreg.QueryValueEx(key, name)[0])
    except (ImportError, OSError):
        return ''


def is_secondary():
    values = [os.environ.get('CLAUDE_MACHINE_ROLE', ''), _registry('CLAUDE_MACHINE_ROLE')]
    return any(value.strip().lower() == 'secondary' for value in values)


def machine_id():
    """This machine's fixed id: this process's environment first, then HKCU\\Environment.
    Unset raises; there is no default, because a guessed id writes into another machine's lane."""
    value = os.environ.get('CLAUDE_MACHINE_ID', '').strip() or _registry('CLAUDE_MACHINE_ID').strip()
    if not value:
        raise RuntimeError('CLAUDE_MACHINE_ID is not set: set it once per machine as a user '
                           'environment variable; there is no default')
    return value


def refuse_on_secondary():
    """On the secondary machine print one line and exit 3; otherwise return."""
    if is_secondary():
        sys.stderr.write(MESSAGE + '\n')
        raise SystemExit(3)
