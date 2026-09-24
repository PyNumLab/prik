"""Discover the Fortran sources that define the modules a project uses.

A Fortran ``use`` names a module, not a file, and no rule ties the two: a
module may live in any file under any directory. Given the sources a caller
names and the directories to search, this resolver follows each ``use`` to the
one file that defines that module, transitively, so a project can be supplied
by its entry file alone.

Which modules a source defines and uses are parser facts, read here exactly as
compile ordering reads them. The directory index only locates candidate files
by their ``module`` lines, since parsing every file under a search root to
find one module would be needlessly slow.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from pathlib import Path
import re

from prik.parsers.fortran.models import FortranFile, FortranParseError
from prik.parsers.fortran.parser import FortranParser
from prik.parsers.fortran.scope import used_module_names


# Suffixes a Fortran compiler accepts as free- or fixed-form source.
_FORTRAN_SOURCE_SUFFIXES = frozenset({".f", ".for", ".ftn", ".f77", ".f90", ".f95", ".f03", ".f08", ".fpp"})
_MODULE_LINE = re.compile(
    r"^[ \t]*module[ \t]+(?!(?:procedure|function|subroutine|pure|impure|elemental|recursive)\b)"
    r"(?P<name>[a-z][a-z0-9_]*)[ \t]*(?:!.*)?$",
    re.IGNORECASE | re.MULTILINE,
)
# Modules the processor supplies without a source file.
_INTRINSIC_MODULES = frozenset(
    {
        "iso_c_binding",
        "iso_fortran_env",
        "ieee_arithmetic",
        "ieee_exceptions",
        "ieee_features",
        "omp_lib",
        "omp_lib_kinds",
        "openacc",
    }
)


def resolve_fortran_module_sources(
    entries: Sequence[Path],
    search_dirs: Iterable[Path],
    read_source: Callable[[Path], str],
) -> tuple[Path, ...]:
    """Return ``entries`` with the sources of every module they use, dependencies first.

    ``read_source`` returns a file's preprocessed text, so a ``use`` inside an
    inactive conditional block is not followed. A used module that no source
    read so far defines must be defined by exactly one Fortran source under
    ``search_dirs``; otherwise a :class:`FortranParseError` names the module
    and the source that uses it.
    """
    candidates = _module_candidates(search_dirs)
    parser = FortranParser()
    facts: dict[Path, tuple[set[str], set[str]]] = {}
    owners: dict[str, Path] = {}

    def read(path: Path) -> tuple[set[str], set[str]]:
        if path not in facts:
            parsed = parser.parse_file(read_source(path), filename=str(path))
            facts[path] = _defined_and_used_modules(parsed)
            for name in facts[path][0]:
                owners.setdefault(name, path)
        return facts[path]

    for entry in entries:
        read(entry.resolve())
    ordered: list[Path] = []
    visiting: set[Path] = set()

    def visit(path: Path) -> None:
        if path in ordered or path in visiting:
            return
        visiting.add(path)
        defined, used = read(path)
        for name in sorted(used - defined - _INTRINSIC_MODULES):
            dependency = owners.get(name) or _defining_source(name, candidates, path, read)
            visit(dependency)
        visiting.discard(path)
        ordered.append(path)

    for entry in entries:
        visit(entry.resolve())
    originals = {entry.resolve(): entry for entry in entries}
    return tuple(originals.get(path, path) for path in ordered)


def _defining_source(
    name: str,
    candidates: dict[str, list[Path]],
    user: Path,
    read: Callable[[Path], tuple[set[str], set[str]]],
) -> Path:
    """Return the one searched source whose parsed modules define ``name``, or raise."""
    defining = [path for path in candidates.get(name, ()) if name in read(path)[0]]
    if len(defining) == 1:
        return defining[0]
    if not defining:
        raise FortranParseError(
            f"No Fortran source defines module '{name}' used by {user}; "
            "add the directory that contains it as a module source directory.",
            filename=str(user),
            code="PARSE_MODULE_SOURCE_NOT_FOUND",
        )
    listed = ", ".join(str(path) for path in defining)
    raise FortranParseError(
        f"Module '{name}' used by {user} is defined by several sources ({listed}); "
        "narrow the module source directories to one of them.",
        filename=str(user),
        code="PARSE_AMBIGUOUS_MODULE_SOURCE",
    )


def _module_candidates(search_dirs: Iterable[Path]) -> dict[str, list[Path]]:
    """Map each module name to the Fortran sources under ``search_dirs`` with a matching ``module`` line."""
    candidates: dict[str, list[Path]] = {}
    for directory in search_dirs:
        for path in sorted(Path(directory).rglob("*")):
            if path.suffix.casefold() not in _FORTRAN_SOURCE_SUFFIXES or not path.is_file():
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            for match in _MODULE_LINE.finditer(text):
                paths = candidates.setdefault(match.group("name").casefold(), [])
                if path.resolve() not in paths:
                    paths.append(path.resolve())
    return candidates


def _defined_and_used_modules(parsed: FortranFile) -> tuple[set[str], set[str]]:
    """Return the modules one parsed source defines and every module it uses."""
    defined = {str(module.name).casefold() for module in parsed.modules}
    used: set[str] = set()
    for owner in (*parsed.modules, *parsed.submodules, *parsed.programs, *parsed.procedures):
        used.update(used_module_names(owner))
    # A submodule extends the module it names first, which must be available.
    used.update(str(submodule.ancestor or submodule.parent).casefold() for submodule in parsed.submodules)
    return defined, used
