"""Explicit object-file inputs for native wrapper builds."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

__all__ = ("ObjectFile",)


@dataclass(frozen=True)
class ObjectFile:
    """Describe one source file and the object file it must produce.

    Build orchestration owns the order in which objects are compiled and linked.
    This value only carries the complete inputs for one compiler invocation.
    """

    source: Path
    object_path: Path
    language: str
    flags: tuple[str, ...] = ()
    include_dirs: tuple[Path, ...] = ()
    library_dirs: tuple[Path, ...] = ()
    libraries: tuple[str, ...] = ()
    tools: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if self.language not in {"c", "fortran"}:
            raise ValueError(f"Unsupported compilation language: {self.language!r}")
        object.__setattr__(self, "source", Path(self.source))
        object.__setattr__(self, "object_path", Path(self.object_path))
        object.__setattr__(self, "flags", tuple(str(flag) for flag in self.flags))
        object.__setattr__(self, "include_dirs", tuple(Path(path) for path in self.include_dirs))
        object.__setattr__(self, "library_dirs", tuple(Path(path) for path in self.library_dirs))
        object.__setattr__(self, "libraries", tuple(str(library) for library in self.libraries))
        object.__setattr__(self, "tools", frozenset(str(tool) for tool in self.tools))
