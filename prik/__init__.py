"""Normal-user PRIK build entrypoints.

Import advanced parser, semantic, probe, runtime, and planning APIs from the
package that owns them instead of from this root facade.
"""

from importlib import import_module
from importlib.metadata import version as _distribution_version


__version__ = _distribution_version("prik")

_BUILD_EXPORTS = {
    "build_c_extension",
    "build_fortran_extension",
    "build_pyi_extension",
    "build_pyi_extension_from_manifest",
}


def __getattr__(name: str):
    """Load a public build entrypoint only when a caller requests it."""
    if name in _BUILD_EXPORTS:
        module = import_module("prik.pipeline.build")
        return getattr(module, name)
    raise AttributeError(f"module 'prik' has no attribute {name!r}")


__all__ = (
    "__version__",
    "build_c_extension",
    "build_fortran_extension",
    "build_pyi_extension",
    "build_pyi_extension_from_manifest",
)
