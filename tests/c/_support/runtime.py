"""C-owned helpers for imported direct-C extension assertions."""

from types import ModuleType


def sole_native_module(module):
    """Return the only generated native child module, when one is present."""
    children = [
        value
        for value in vars(module).values()
        if isinstance(value, ModuleType) and value.__name__.startswith(f"{module.__name__}.")
    ]
    return children[0] if len(children) == 1 else module
