"""Filesystem facts about the installation PRIK runs from.

Installed data files -- the packaged CMake modules today, whatever a later
tool needs beside them -- all land under one prefix, so the question "where is
PRIK installed" belongs here rather than with any single consumer.
"""

from __future__ import annotations

from pathlib import Path
import sys
import sysconfig


def data_roots() -> tuple[Path, ...]:
    """Return the prefixes an installation's ``share/prik`` data can sit under."""
    data_root = sysconfig.get_path("data")
    roots = [Path(data_root)] if data_root else []
    roots.append(Path(sys.prefix))
    unique: list[Path] = []
    for root in roots:
        if root not in unique:
            unique.append(root)
    return tuple(unique)


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
