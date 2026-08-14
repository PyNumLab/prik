"""Public printers for the three representations that PRIK serializes.

``CSourcePrinter`` and ``FortranSourcePrinter`` render lowered backend nodes;
``PyiPrinter`` and ``emit_module`` render semantic IR as an editable contract.
These APIs format already-formed representations and do not construct plans,
choose wrapper policy, write files, or compile sources.
"""

from .c import CSourcePrinter
from .fortran import FortranSourcePrinter
from .pyi import PyiPrinter, emit_module

__all__ = (
    "CSourcePrinter",
    "FortranSourcePrinter",
    "PyiPrinter",
    "emit_module",
)
