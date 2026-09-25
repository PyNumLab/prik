"""Discover the Fortran sources that define the modules a project uses.

A Fortran ``use`` names a module, not a file, and no rule ties the two: a
module may live in any file under any directory. Given the sources a caller
names and the directories to search, this resolver follows each ``use`` and
each submodule's parent to the one file that defines it, transitively, so a
project can be supplied by its entry file alone.

What a source defines is decided by its preprocessed text, never by its raw
text: a macro or an ``#include`` can name a module, and a conditional block can
remove one. Every searched source is therefore located by the program units
the parser's own unit scanner finds in its preprocessed text -- the same first
step parsing takes, with the same logical lines in either source form -- and a
source whose raw text has nothing a preprocessor could change is read as it
stands, which spares the preprocessor for it. The sources located for a unit
are then parsed, and their parsed units are the definition. A source is selected into the project
only once it is the unit's one definition, so reading a candidate never makes
it part of the project.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
import re

from prik.parsers.fortran.intrinsic_modules import INTRINSIC_FORTRAN_MODULES
from prik.parsers.fortran.models import FortranParseError
from prik.parsers.fortran.parser import FortranParser
from prik.parsers.fortran.scope import file_defined_units, file_unit_requirements

# Suffixes a Fortran compiler accepts as free- or fixed-form source.
_FORTRAN_SOURCE_SUFFIXES = frozenset({".f", ".for", ".ftn", ".f77", ".f90", ".f95", ".f03", ".f08", ".fpp"})
# Raw text a preprocessor can change: a directive, or a Fortran ``include``,
# which PRIK's preprocessing expands as well.
_PREPROCESSED_TEXT = re.compile(r"^[ \t]*(?:#|include[ \t]*['\"])", re.IGNORECASE | re.MULTILINE)
# Sources are preprocessed by separate compiler processes, which is I/O-bound
# work for this process, so a few run at once.
_LOCATE_WORKERS = 4


def resolve_fortran_module_sources(
    entries: Sequence[Path],
    search_dirs: Iterable[Path],
    read_source: Callable[[Path], str],
    *,
    command_line_macros: bool = True,
) -> tuple[Path, ...]:
    """Return ``entries`` with the sources of every module they use, dependencies first.

    ``read_source`` returns a file's preprocessed text. ``command_line_macros``
    states whether the preprocessing defines macros of its own, such as ``-D``
    flags; then every searched source is preprocessed, since any of its names
    may be one, and otherwise a source without directives is read as written.

    Every submodule descending from a selected module is selected as well,
    since it implements that module's separate module procedures. A unit
    every scope uses as ``intrinsic`` is the processor's and is never
    searched. A ``use`` stating no nature reads a module's source when one is
    defined, and the processor's module of that name only when none is. Any
    other needed module, and a submodule's parent, must be defined by exactly
    one searched source; otherwise a :class:`FortranParseError` names it and
    the source that needs it.
    """
    searched = _SearchedSources(tuple(search_dirs), read_source, command_line_macros=command_line_macros)
    project = _SelectedSources(searched)
    for entry in entries:
        project.select(entry.resolve(), requested_by=None)
    ordered: list[Path] = []
    visiting: set[Path] = set()

    def visit(path: Path) -> None:
        if path in ordered or path in visiting:
            return
        visiting.add(path)
        facts = searched.facts(path)
        for unit, nature in sorted(facts.required.items(), key=lambda item: item[0]):
            if unit in facts.defined or nature == "intrinsic":
                continue
            dependency = project.provider(unit, nature, user=path)
            if dependency is not None:
                visit(dependency)
        visiting.discard(path)
        ordered.append(path)

    for entry in entries:
        visit(entry.resolve())
    # A separate module procedure is implemented in a submodule, which no
    # ``use`` names, so every submodule descending from a selected module is
    # part of the project too, however deeply nested.
    added = True
    while added:
        added = False
        for unit in searched.located_units():
            ancestor = unit.partition(":")[0]
            if ":" not in unit or project.owner(unit) is not None or project.owner(ancestor) is None:
                continue
            if searched.definers(unit):
                descendant = project.provider(unit, "non_intrinsic", user=project.owner(ancestor))
                if descendant is not None:
                    visit(descendant)
                    added = True
    originals = {entry.resolve(): entry for entry in entries}
    return tuple(originals.get(path, path) for path in ordered)


@dataclass(frozen=True)
class _UnitFacts:
    """The units one parsed source defines, and those it requires with their natures."""

    defined: frozenset[str]
    required: dict[str, str | None]


class _SearchedSources:
    """What every searched source defines, read once and never selected here."""

    def __init__(
        self,
        search_dirs: tuple[Path, ...],
        read_source: Callable[[Path], str],
        *,
        command_line_macros: bool,
    ) -> None:
        self._read_source = read_source
        self._command_line_macros = command_line_macros
        self.files = _searched_files(search_dirs)
        self._located: dict[Path, frozenset[str]] | None = None
        self._texts: dict[Path, str] = {}
        self._facts: dict[Path, _UnitFacts] = {}
        self.unreadable: dict[Path, Exception] = {}
        self._parser = FortranParser()

    def facts(self, path: Path) -> _UnitFacts:
        """Parse one source once and return its units."""
        if path not in self._facts:
            text = self._texts.pop(path, None)
            parsed = self._parser.parse_file(self._read_source(path) if text is None else text, filename=str(path))
            self._facts[path] = _UnitFacts(frozenset(file_defined_units(parsed)), file_unit_requirements(parsed))
        return self._facts[path]

    def definers(self, unit: str) -> list[Path]:
        """Return every searched source whose parsed units define ``unit``, in search order."""
        located = self._locate()
        return [path for path in self.files if unit in located.get(path, ()) and unit in self.facts(path).defined]

    def located_units(self) -> list[str]:
        """Return every unit some searched source's text states, sorted."""
        return sorted({unit for units in self._locate().values() for unit in units})

    def raw_definers(self, unit: str) -> list[Path]:
        """Return the unreadable sources whose raw text shows ``unit``, to explain a missing one."""
        return [path for path in self.unreadable if unit in self._scan(path, path.read_text(errors="replace"))]

    def _locate(self) -> dict[Path, frozenset[str]]:
        """Return the units each searched source's preprocessed text states, computed once."""
        if self._located is None:
            located: dict[Path, frozenset[str]] = {}
            opaque: list[Path] = []
            for path in self.files:
                raw = path.read_text(encoding="utf-8", errors="replace")
                if self._command_line_macros or _PREPROCESSED_TEXT.search(raw):
                    opaque.append(path)
                else:
                    located[path] = self._scan(path, raw)
            with ThreadPoolExecutor(max_workers=_LOCATE_WORKERS) as pool:
                for path, text in zip(opaque, pool.map(self._preprocessed_text, opaque), strict=True):
                    if isinstance(text, Exception):
                        # A source that cannot be preprocessed here defines
                        # nothing; it is named if a needed unit stays missing.
                        self.unreadable[path] = text
                        continue
                    located[path] = self._scan(path, text)
                    if located[path]:
                        self._texts[path] = text
            self._located = located
        return self._located

    def _scan(self, path: Path, text: str) -> frozenset[str]:
        """Return the units one source's text opens; text the parser rejects opens none."""
        try:
            return self._parser.defined_units(text, str(path))
        except FortranParseError as error:
            self.unreadable.setdefault(path, error)
            return frozenset()

    def _preprocessed_text(self, path: Path) -> str | Exception:
        try:
            return self._read_source(path)
        except Exception as error:  # reported through ``unreadable``
            return error


class _SelectedSources:
    """The sources chosen into the project, and the units each one provides."""

    def __init__(self, searched: _SearchedSources) -> None:
        self._searched = searched
        self._owners: dict[str, Path] = {}

    def select(self, path: Path, *, requested_by: Path | None) -> None:
        """Add one source to the project; a unit another selected source defines is ambiguous."""
        for unit in sorted(self._searched.facts(path).defined):
            owner = self._owners.setdefault(unit, path)
            if owner != path:
                _raise_ambiguous(unit, requested_by or path, [owner, path])

    def owner(self, unit: str) -> Path | None:
        """Return the selected source defining ``unit``, if one is selected."""
        return self._owners.get(unit)

    def provider(self, unit: str, nature: str | None, *, user: Path) -> Path | None:
        """Return the one source defining ``unit``, or ``None`` for the processor's module."""
        if unit in self._owners:
            return self._owners[unit]
        definers = self._searched.definers(unit)
        if len(definers) > 1:
            _raise_ambiguous(unit, user, definers)
        if definers:
            self.select(definers[0], requested_by=user)
            return definers[0]
        if nature is None and unit in INTRINSIC_FORTRAN_MODULES:
            return None
        kind = "submodule" if ":" in unit else "module"
        unreadable = self._searched.raw_definers(unit)
        detail = "".join(
            f" {path} names it but could not be preprocessed: {self._searched.unreadable[path]}" for path in unreadable
        )
        raise FortranParseError(
            f"No Fortran source defines {kind} '{unit}' used by {user}; "
            f"add the directory that contains it as a module source directory.{detail}",
            filename=str(user),
            code="PARSE_MODULE_SOURCE_NOT_FOUND",
        )


def _raise_ambiguous(unit: str, user: Path, definers: Sequence[Path]) -> None:
    kind = "submodule" if ":" in unit else "module"
    listed = ", ".join(str(path) for path in definers)
    raise FortranParseError(
        f"{kind.capitalize()} '{unit}' used by {user} is defined by several sources ({listed}); "
        "narrow the module source directories to one of them.",
        filename=str(user),
        code="PARSE_AMBIGUOUS_MODULE_SOURCE",
    )


def _searched_files(search_dirs: Iterable[Path]) -> tuple[Path, ...]:
    """Return every Fortran source under ``search_dirs`` once, in a stable order."""
    files: dict[Path, None] = {}
    for directory in search_dirs:
        for path in sorted(Path(directory).rglob("*")):
            if path.suffix.casefold() in _FORTRAN_SOURCE_SUFFIXES and path.is_file():
                files.setdefault(path.resolve(), None)
    return tuple(files)
