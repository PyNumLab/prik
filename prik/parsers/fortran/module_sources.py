"""Discover the Fortran sources that define the modules a project uses.

A Fortran ``use`` names a module, not a file, and no rule ties the two: a
module may live in any file under any directory. Given the sources a caller
names and the directories to search, this resolver follows each ``use`` and
each submodule's parent to the one file that defines it, transitively, so a
project can be supplied by its entry file alone.

Which modules a source defines and uses are parser facts, read here exactly as
compile ordering reads them. The directory index only locates candidate files
by their ``module`` lines, since parsing every file under a search root to
find one module would be needlessly slow.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from pathlib import Path
import re

from prik.parsers.fortran.intrinsic_modules import INTRINSIC_FORTRAN_MODULES
from prik.parsers.fortran.models import FortranFile, FortranParseError
from prik.parsers.fortran.parser import FortranParser
from prik.parsers.fortran.scope import used_module_statements


# Suffixes a Fortran compiler accepts as free- or fixed-form source.
_FORTRAN_SOURCE_SUFFIXES = frozenset({".f", ".for", ".ftn", ".f77", ".f90", ".f95", ".f03", ".f08", ".fpp"})
_SUBMODULE_LINE = re.compile(
    r"^[ \t]*submodule[ \t]*\([ \t]*(?P<ancestor>[a-z][a-z0-9_]*)[ \t]*(?::[ \t]*[a-z][a-z0-9_]*[ \t]*)?\)"
    r"[ \t]*(?P<name>[a-z][a-z0-9_]*)",
    re.IGNORECASE | re.MULTILINE,
)
_MODULE_LINE = re.compile(
    r"^[ \t]*module[ \t]+(?!(?:procedure|function|subroutine|pure|impure|elemental|recursive)\b)"
    r"(?P<name>[a-z][a-z0-9_]*)[ \t]*(?:!.*)?$",
    re.IGNORECASE | re.MULTILINE,
)


def resolve_fortran_module_sources(
    entries: Sequence[Path],
    search_dirs: Iterable[Path],
    read_source: Callable[[Path], str],
) -> tuple[Path, ...]:
    """Return ``entries`` with the sources of every module they use, dependencies first.

    ``read_source`` returns a file's preprocessed text, so a ``use`` inside an
    inactive conditional block is not followed. An ``intrinsic`` module is
    never searched. Any other used module, and a submodule's parent, that no
    source read so far defines must be defined by exactly one Fortran source
    under ``search_dirs``; otherwise a :class:`FortranParseError` names it and
    the source that needs it.
    """
    candidates, searched_files = _unit_candidates(search_dirs)
    parser = FortranParser()
    facts: dict[Path, tuple[set[str], dict[str, str | None]]] = {}
    owners: dict[str, Path] = {}

    def read(path: Path) -> tuple[set[str], dict[str, str | None]]:
        if path not in facts:
            parsed = parser.parse_file(read_source(path), filename=str(path))
            facts[path] = _defined_and_required_units(parsed)
            for unit in facts[path][0]:
                owners.setdefault(unit, path)
        return facts[path]

    scanned: set[Path] = set()

    def parsed_definers(unit: str) -> list[Path]:
        """Parse every searched source not yet read and return those defining ``unit``.

        A module named through a macro or an included line has no ``module``
        line the fast index can see, so the preprocessed sources are read
        once, when a needed unit is otherwise missing. A source that cannot
        be preprocessed or parsed cannot define it.
        """
        for path in searched_files:
            if path in scanned:
                continue
            scanned.add(path)
            try:
                read(path)
            except Exception:  # an unreadable candidate defines nothing
                continue
        return [path for path in searched_files if path in facts and unit in facts[path][0]]

    for entry in entries:
        read(entry.resolve())
    ordered: list[Path] = []
    visiting: set[Path] = set()

    def visit(path: Path) -> None:
        if path in ordered or path in visiting:
            return
        visiting.add(path)
        defined, required = read(path)
        for unit, nature in sorted(required.items()):
            if unit in defined or nature == "intrinsic":
                continue
            dependency = owners.get(unit) or _defining_source(unit, nature, candidates, path, read, parsed_definers)
            if dependency is not None:
                visit(dependency)
        visiting.discard(path)
        ordered.append(path)

    for entry in entries:
        visit(entry.resolve())
    originals = {entry.resolve(): entry for entry in entries}
    return tuple(originals.get(path, path) for path in ordered)


def _defining_source(
    unit: str,
    nature: str | None,
    candidates: dict[str, list[Path]],
    user: Path,
    read: Callable[[Path], tuple[set[str], dict[str, str | None]]],
    parsed_definers: Callable[[str], list[Path]],
) -> Path | None:
    """Return the one searched source whose parsed units define ``unit``, or raise.

    A ``use`` that states no nature names an intrinsic module only when no
    other module of that name is accessible, so a known intrinsic name is
    satisfied by the processor when no source defines it. Only a unit that is
    still missing reads every searched source in full.
    """
    defining = [path for path in candidates.get(unit, ()) if unit in read(path)[0]]
    if len(defining) == 1:
        return defining[0]
    if not defining and nature is None and unit in INTRINSIC_FORTRAN_MODULES:
        return None
    if not defining:
        defining = parsed_definers(unit)
    if len(defining) == 1:
        return defining[0]
    kind = "submodule" if ":" in unit else "module"
    if not defining:
        raise FortranParseError(
            f"No Fortran source defines {kind} '{unit}' used by {user}; "
            "add the directory that contains it as a module source directory.",
            filename=str(user),
            code="PARSE_MODULE_SOURCE_NOT_FOUND",
        )
    listed = ", ".join(str(path) for path in defining)
    raise FortranParseError(
        f"{kind.capitalize()} '{unit}' used by {user} is defined by several sources ({listed}); "
        "narrow the module source directories to one of them.",
        filename=str(user),
        code="PARSE_AMBIGUOUS_MODULE_SOURCE",
    )


def _unit_candidates(search_dirs: Iterable[Path]) -> tuple[dict[str, list[Path]], list[Path]]:
    """Map each module or submodule to the sources under ``search_dirs`` that open it, and list every source.

    The map reads raw ``module`` and ``submodule`` lines, the fast path; the
    list lets a unit those lines cannot show be found by parsing.
    """
    candidates: dict[str, list[Path]] = {}
    searched: list[Path] = []
    for directory in search_dirs:
        for path in sorted(Path(directory).rglob("*")):
            if path.suffix.casefold() not in _FORTRAN_SOURCE_SUFFIXES or not path.is_file():
                continue
            resolved = path.resolve()
            if resolved not in searched:
                searched.append(resolved)
            text = path.read_text(encoding="utf-8", errors="replace")
            units = [match.group("name").casefold() for match in _MODULE_LINE.finditer(text)]
            units.extend(
                f"{match.group('ancestor')}:{match.group('name')}".casefold()
                for match in _SUBMODULE_LINE.finditer(text)
            )
            for unit in units:
                paths = candidates.setdefault(unit, [])
                if resolved not in paths:
                    paths.append(resolved)
    return candidates, searched


def _defined_and_required_units(parsed: FortranFile) -> tuple[set[str], dict[str, str | None]]:
    """Return the units one parsed source defines and the units it requires, with each ``use`` nature.

    A module is named by itself and a submodule by ``ancestor:name``. A
    submodule requires its direct parent: the submodule it names after its
    ancestor, or the ancestor module itself.
    """
    defined = {str(module.name).casefold() for module in parsed.modules}
    defined.update(
        f"{submodule.ancestor or submodule.parent}:{submodule.name}".casefold() for submodule in parsed.submodules
    )
    required: dict[str, str | None] = {}
    for owner in (*parsed.modules, *parsed.submodules, *parsed.programs, *parsed.procedures):
        for statement in used_module_statements(owner):
            name = statement.module.casefold()
            # An explicit nature is kept over a statement that states none.
            if required.get(name) is None:
                required[name] = statement.nature
    for submodule in parsed.submodules:
        parent = (
            f"{submodule.ancestor}:{submodule.parent}" if submodule.ancestor else str(submodule.parent)
        ).casefold()
        required[parent] = "non_intrinsic"
    return defined, required
