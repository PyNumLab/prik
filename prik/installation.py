"""Filesystem facts about the installation PRIK runs from.

Installed data files -- the packaged CMake modules today, whatever a later
tool needs beside them -- all land under one prefix, so the question "where is
PRIK installed" belongs here rather than with any single consumer.
"""

from __future__ import annotations

from collections.abc import Callable
from importlib import metadata
import json
import os
from pathlib import Path
import site
import sys
import sysconfig
from urllib.parse import urlparse
from urllib.request import url2pathname

_PACKAGE_DIR = Path(__file__).resolve().parent
_RECORDED_CONFIG = ("share", "prik", "cmake", "PRIKConfig.cmake")


def data_roots() -> tuple[Path, ...]:
    """Return the prefixes an installation's ``share/prik`` data can sit under.

    These are candidates to search for a file, not an identity. A prefix that
    holds PRIK data may belong to another installation entirely, which is why
    `install_dir` reads its own installation's record instead.

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
    """Return the prefix this PRIK's own installation wrote its data files under.

    The prefix comes from the running distribution's recorded files rather than
    from searching candidate roots, so a second PRIK installed under another
    prefix -- a global one beside a ``pip install --user`` -- can never answer
    for this one. Nothing is invented when there is no such installation: a
    prefix holding no data of ours would only fail later, inside whichever tool
    consumed it.
    """
    distribution = _running_distribution()
    for recorded in distribution.files or ():
        if recorded.parts[-len(_RECORDED_CONFIG) :] != _RECORDED_CONFIG:
            continue
        located = Path(distribution.locate_file(recorded)).resolve()
        if located.is_file():
            return located.parents[len(_RECORDED_CONFIG) - 1]
    raise FileNotFoundError(
        "this PRIK installation recorded no share/prik/cmake data files; an editable install writes none"
    )


def _running_distribution() -> metadata.Distribution:
    """Return the installed distribution that provides the PRIK running here."""
    try:
        distribution = metadata.distribution("prik")
    except metadata.PackageNotFoundError as exc:
        raise FileNotFoundError("PRIK is not installed: no prik distribution metadata is importable") from exc
    if Path(distribution.locate_file("prik")).resolve() == _PACKAGE_DIR:
        return distribution
    editable_source = _editable_source(distribution)
    if editable_source is not None and _PACKAGE_DIR.is_relative_to(editable_source):
        return distribution
    raise FileNotFoundError(f"the installed prik distribution does not provide the PRIK running from {_PACKAGE_DIR}")


def cmake_discovery_report() -> dict[str, str]:
    """Return the facts that decide which PRIK a CMake build would use.

    Every value is observed, never inferred: which package is imported, which
    distribution's metadata answers for it, what the entry points a build
    backend reads resolve to, and whether anything else on the path could
    answer instead.
    """
    from prik import __version__
    from prik.cmake import cmake_module_dir

    report = {
        "prik version": __version__,
        "imported package": str(_PACKAGE_DIR),
        "python executable": sys.executable,
        "cmake-dir": str(cmake_module_dir()),
    }
    report.update(_distribution_facts())
    report["install-dir"] = _reported(install_dir)
    for group in ("cmake.root", "cmake.module"):
        report[f"entry point {group}"] = _entry_point_facts(group)
    conflicts = _discovery_conflicts()
    report["conflicts"] = "; ".join(conflicts) if conflicts else "none"
    return report


def _reported(answer: Callable[[], Path]) -> str:
    """Return one reported path, or the reason there is none."""
    try:
        return str(answer())
    except FileNotFoundError as exc:
        return f"unavailable ({exc})"


def _distribution_facts() -> dict[str, str]:
    """Return where the metadata answering for ``prik`` lives."""
    try:
        distribution = metadata.distribution("prik")
    except metadata.PackageNotFoundError:
        return {"distribution metadata": "none installed"}
    return {"distribution metadata": str(distribution.locate_file(""))}


def _entry_point_facts(group: str) -> str:
    """Return what one entry-point group resolves to for this installation."""
    from importlib import resources

    try:
        entries = [entry for entry in metadata.distribution("prik").entry_points if entry.group == group]
    except metadata.PackageNotFoundError:
        return "unavailable (prik is not installed)"
    if not entries:
        return "not declared"
    resolved = []
    for entry in entries:
        try:
            resolved.append(f"{entry.name} -> {resources.files(entry.load())}")
        except (ImportError, TypeError) as exc:  # pragma: no cover - a broken installation
            resolved.append(f"{entry.name} -> unresolvable ({exc})")
    return ", ".join(resolved)


def _discovery_conflicts() -> list[str]:
    """Return anything that could make another PRIK answer instead of this one."""
    conflicts = []
    try:
        _running_distribution()
    except FileNotFoundError as exc:
        conflicts.append(str(exc))
    installed = [
        distribution
        for distribution in metadata.distributions()
        if (distribution.metadata["Name"] or "").lower() == "prik"
    ]
    if len(installed) > 1:
        locations = ", ".join(sorted(str(distribution.locate_file("")) for distribution in installed))
        conflicts.append(f"{len(installed)} prik distributions are importable: {locations}")
    for entry in os.environ.get("PYTHONPATH", "").split(os.pathsep):
        if entry and (Path(entry) / "prik" / "__init__.py").is_file() and Path(entry).resolve() != _PACKAGE_DIR.parent:
            conflicts.append(f"PYTHONPATH entry holds another prik package: {entry}")
    return conflicts


def _editable_source(distribution: metadata.Distribution) -> Path | None:
    """Return the tree an editable installation points at, when it is one."""
    recorded = distribution.read_text("direct_url.json")
    if not recorded:
        return None
    try:
        direct_url = json.loads(recorded)
    except json.JSONDecodeError:
        return None
    if not direct_url.get("dir_info", {}).get("editable"):
        return None
    url = urlparse(str(direct_url.get("url", "")))
    if url.scheme != "file":
        return None
    return Path(url2pathname(url.path)).resolve()
