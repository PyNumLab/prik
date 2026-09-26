"""Which native language, and which Fortran source form, a source path names.

Every stage that asks whether a path is a Fortran or C source, which Fortran
source form a file is written in, or which sources a list of files and
directories names reads the answer here, so discovery, parsing,
preprocessing, and builds never disagree about a path.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

#: Fortran sources written in fixed form: statements in columns 7 to 72, with
#: column 6 marking a continuation. ``.fpp`` is fixed-form source that is
#: preprocessed first, as the common Fortran compilers read it.
FORTRAN_FIXED_FORM_SUFFIXES = frozenset({".f", ".for", ".ftn", ".f77", ".fpp"})
#: Fortran sources written in free form.
FORTRAN_FREE_FORM_SUFFIXES = frozenset({".f90", ".f95", ".f03", ".f08"})
#: Every suffix a Fortran source may carry, in either case.
FORTRAN_SOURCE_SUFFIXES = FORTRAN_FIXED_FORM_SUFFIXES | FORTRAN_FREE_FORM_SUFFIXES
#: C inputs PRIK reads: implementation files, headers, and preprocessed units.
C_SOURCE_SUFFIXES = frozenset({".c", ".h", ".i"})
#: C files a native build compiles.
C_IMPLEMENTATION_SUFFIXES = frozenset({".c"})


def is_fortran_source(path: str | Path) -> bool:
    """Return whether ``path`` names a Fortran source by its suffix."""
    return Path(path).suffix.casefold() in FORTRAN_SOURCE_SUFFIXES


def is_c_source(path: str | Path) -> bool:
    """Return whether ``path`` names a C input by its suffix."""
    return Path(path).suffix.casefold() in C_SOURCE_SUFFIXES


def fortran_source_form(code: str, filename: str | None = None) -> str:
    """Return ``"fixed"`` or ``"free"``, the form one Fortran source is written in.

    The suffix decides when it names a form. Otherwise the text does: a line
    among the first twenty with blank columns 1 to 5 and a character in
    column 6 is a fixed-form continuation.
    """
    if filename:
        suffix = Path(filename).suffix.casefold()
        if suffix in FORTRAN_FIXED_FORM_SUFFIXES:
            return "fixed"
        if suffix in FORTRAN_FREE_FORM_SUFFIXES:
            return "free"
    for line in code.splitlines()[:20]:
        if len(line) >= 6 and line[:5].strip() == "" and line[5:6].strip():
            return "fixed"
    return "free"


def expand_source_paths(inputs: Iterable[str | Path], suffixes: Iterable[str]) -> tuple[Path, ...]:
    """Return the sources a list of files and directories names, in the caller's order.

    A file is kept as given. A directory contributes every file below it
    whose suffix is in ``suffixes``, in sorted order. A path named twice is
    kept once, at its first position. Whether a given path exists or has a
    supported suffix is for the caller to judge.
    """
    wanted = frozenset(suffix.casefold() for suffix in suffixes)
    paths: dict[Path, None] = {}
    for raw in inputs:
        path = Path(raw)
        if path.is_dir():
            for candidate in sorted(path.rglob("*")):
                if candidate.is_file() and candidate.suffix.casefold() in wanted:
                    paths.setdefault(candidate, None)
        else:
            paths.setdefault(path, None)
    return tuple(paths)


class SourceInputError(ValueError):
    """A list of wrapper inputs that does not name usable sources.

    ``reason`` is ``"empty"`` when nothing was named, ``"missing"`` for a file
    that does not exist, ``"unsupported"`` for a file whose suffix is not a
    source of the language, and ``"no_sources"`` for a directory holding
    none. ``path`` is the offending input, when there is one.
    """

    def __init__(self, reason: str, label: str, path: Path | None = None) -> None:
        messages = {
            "empty": f"wrapper build requires at least one {label} source file or directory",
            "missing": f"{label} source not found: {path}",
            "unsupported": f"Unrecognized {label} source suffix: {path}",
            "no_sources": f"No recognized {label} sources found under: {path}",
        }
        super().__init__(messages[reason])
        self.reason = reason
        self.label = label
        self.path = path


class MissingSourceError(SourceInputError, FileNotFoundError):
    """A named wrapper input that does not exist."""

    def __init__(self, label: str, path: Path) -> None:
        super().__init__("missing", label, path)


def validated_source_paths(
    inputs: str | Path | Iterable[str | Path],
    suffixes: Iterable[str],
    *,
    label: str,
) -> tuple[Path, ...]:
    """Return the sources wrapper inputs name, requiring each input to name some.

    This is :func:`expand_source_paths` for a build, which fails closed: every
    file must exist with one of ``suffixes``, every directory must hold such a
    file, and something must be named. ``label`` names the language in the
    :class:`SourceInputError` raised otherwise.
    """
    named = (Path(inputs),) if isinstance(inputs, str | Path) else tuple(Path(item) for item in inputs)
    if not named:
        raise SourceInputError("empty", label)
    wanted = frozenset(suffix.casefold() for suffix in suffixes)
    for path in named:
        if path.is_dir():
            if not expand_source_paths([path], wanted):
                raise SourceInputError("no_sources", label, path)
        elif path.suffix.casefold() not in wanted:
            raise SourceInputError("unsupported", label, path)
        elif not path.is_file():
            raise MissingSourceError(label, path)
    return expand_source_paths(named, wanted)
