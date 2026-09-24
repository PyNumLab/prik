from prik.contracts import Final, String

label: String[8][()]

code: String[3][()]

tag: Final[String] = 'fixed'

def relabel() -> None: ...

def read_label() -> String[8]: ...

__all__ = ["label", "code", "tag", "relabel", "read_label"]
