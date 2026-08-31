"""Optional IPython and Jupyter integration.

Load this package with ``%load_ext prik.jupyter``.  Importing it does not
require IPython until the extension registration hook is called.
"""


def load_ipython_extension(ipython) -> None:
    """Register PRIK's cell magics without replacing another extension's names."""
    from IPython.core.error import UsageError

    from prik.jupyter.magic import PrikMagics

    find_cell_magic = getattr(ipython, "find_cell_magic", None)
    conflicts: list[str] = []
    if callable(find_cell_magic):
        for name in PrikMagics.magic_names:
            existing = find_cell_magic(name)
            owner = None if existing is None else getattr(existing, "__self__", None)
            if existing is not None and not getattr(owner, "owns_prik_cell_magics", False):
                conflicts.append(f"%%{name}")
    if conflicts:
        joined = ", ".join(conflicts)
        raise UsageError(f"Cannot load PRIK because these cell magics are already registered: {joined}")
    ipython.register_magics(PrikMagics)


__all__ = ("load_ipython_extension",)
