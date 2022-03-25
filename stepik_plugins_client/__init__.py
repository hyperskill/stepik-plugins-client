from __future__ import annotations

import datetime
import subprocess  # noqa: S404
from pathlib import Path

VERSION = (1, 0, 2, 'final', 0)


def get_version(version: tuple[int, int, int, str, int] | None = None) -> str:
    """Return a PEP 386-compliant version number from VERSION."""
    version = version or VERSION
    assert len(version) == 5
    assert version[3] in ('alpha', 'beta', 'rc', 'final')

    # Now build the two parts of the version number:
    # main = X.Y[.Z]
    # sub = .devN - for pre-alpha releases
    #     | {a|b|c}N - for alpha, beta and rc releases

    parts = 2 if version[2] == 0 else 3
    main = '.'.join(str(x) for x in version[:parts])

    sub = ''
    if version[3] == 'alpha' and version[4] == 0:
        git_changeset = get_git_changeset()
        if git_changeset:
            sub = f'.dev{git_changeset}'
    elif version[3] != 'final':
        mapping = {'alpha': 'a', 'beta': 'b', 'rc': 'c'}
        sub = mapping[version[3]] + str(version[4])

    return str(main + sub)


def get_git_changeset() -> str | None:
    """Return a numeric identifier of the latest git changeset.

    The result is the UTC timestamp of the changeset in YYYYMMDDHHMMSS format.
    This value isn't guaranteed to be unique, but collisions are very unlikely,
    so it's sufficient for generating the development version numbers.
    """
    repo_dir = Path(__file__).absolute().parent.parent
    git_log = subprocess.Popen(  # noqa: S607
        'git log --pretty=format:%ct --quiet -1 HEAD',
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,  # noqa: S602
        cwd=repo_dir,
        universal_newlines=True
    )
    git_log_timestamp = git_log.communicate()[0]
    try:
        timestamp = datetime.datetime.fromtimestamp(  # noqa: DTZ006
            int(git_log_timestamp)
        )
    except ValueError:
        return None

    return timestamp.strftime('%Y%m%d%H%M%S')
