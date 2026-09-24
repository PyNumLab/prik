from prik.contracts import Aliased, Allocatable, Annotated, Final, Pointer, String

deferred: Allocatable[String[:]]

fixed: Allocatable[String[6]]

link: Pointer[String[:]]

store: Annotated[String[6][()], Aliased]

pair: Final[String[2][2]] = ['ab', 'cd']

grid: Final[String[3][2, 2]]

inferred: Final[String[...][3]] = ['alpha', 'beta ', 'gamma']

def setup() -> None: ...

def grow() -> None: ...

def clear() -> None: ...

__all__ = ["deferred", "fixed", "link", "store", "pair", "grid", "inferred", "setup", "grow", "clear"]
