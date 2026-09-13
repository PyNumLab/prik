"""Filesystem facts about the installation PRIK runs from.

Installed data files -- the packaged CMake modules today, whatever a later
tool needs beside them -- all land under one prefix, so the question "where is
PRIK installed" belongs here rather than with any single consumer.
"""

from __future__ import annotations

from pathlib import Path
import site
import sys
import sysconfig


def data_roots() -> tuple[Path, ...]:
    """Return the prefixes an installation's ``share/prik`` data can sit under.

    ``pip install --user`` writes data files under the user base instead of
    under ``sys.prefix``, so that root belongs here too -- but only while this
    interpreter would import from the user site at all. A virtual environment,
    ``-s``, and ``-I`` all switch it off, and the files there then belong to an
    installation this interpreter cannot use.
    """
    candidates = [sysconfig.get_path("data"), sys.prefix]
    if site.ENABLE_USER_SITE:
        candidates.append(site.getuserbase())
    roots: list[Path] = []
    for candidate in candidates:
        root = Path(candidate) if candidate else None
        if root is not None and root not in roots:
            roots.append(root)
    return tuple(roots)


def install_dir() -> Path:
    """Return the prefix holding this environment's installed PRIK data files.

    A source checkout installs nothing, so there is no such prefix and none is
    invented: an answer that named a directory without PRIK's data in it would
    only fail later, inside whichever tool consumed it.
    """
    roots = data_roots()
    for root in roots:
        if (root / "share" / "prik").is_dir():
            return root
    searched = ", ".join(str(root) for root in roots)
    raise FileNotFoundError(f"PRIK is not installed with data files; no share/prik under: {searched}")
