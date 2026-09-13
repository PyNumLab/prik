"""Canonical filenames for one module's generated wrapper sources.

Every generated compilation unit's name follows from the module name alone, so
a build integration can declare its source graph before any source is parsed.
This module is the single owner of that mapping: planning, code generation, and
build integration all read the names from here rather than repeating the
spelling. :func:`stub_identifier` supplies the bounded identifier a placeholder
unit needs when an optional unit is declared but not required.
"""

from __future__ import annotations

from hashlib import blake2b

_STUB_DIGEST_SIZE = 6


def binding_module_name(module_name: str) -> str:
    """Return the C module name of the always-present CPython binding unit."""
    return f"{module_name}_wrapper"


def adapter_module_name(module_name: str) -> str:
    """Return the C module name of the collision-adapter forwarder unit."""
    return f"{module_name}_adapters"


def bridge_module_name(module_name: str) -> str:
    """Return the Fortran module name of the generated bridge unit."""
    return f"bind_c_{module_name}_wrapper"


def binding_source_name(module_name: str) -> str:
    """Return the filename of the always-present CPython binding source."""
    return f"{binding_module_name(module_name)}.c"


def adapter_source_name(module_name: str) -> str:
    """Return the filename of the collision-adapter compilation unit."""
    return f"{adapter_module_name(module_name)}.c"


def bridge_source_name(module_name: str) -> str:
    """Return the filename of the generated Fortran bridge compilation unit."""
    return f"{bridge_module_name(module_name)}.f90"


def wrapper_header_name(module_name: str) -> str:
    """Return the filename of the generated wrapper header."""
    return f"{binding_module_name(module_name)}.h"


def stub_identifier(prefix: str, module_name: str) -> str:
    """Return a bounded identifier for a placeholder compilation unit.

    A Python module name may be long or carry characters a target language
    rejects, so the identity comes from a short digest of the name rather than
    the name itself. The result is stable for a given module.
    """
    digest = blake2b(module_name.encode("utf-8"), digest_size=_STUB_DIGEST_SIZE).hexdigest()
    return f"{prefix}_{digest}"
