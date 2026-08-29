"""Stable primitive scalar vocabulary shared by semantic consumers.

This module owns language-neutral scalar identities and intrinsic storage
facts.  It intentionally does not import NumPy or contain generated C or
Fortran spellings; those are boundary representations owned by codegen.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Final


class SemanticScalarFamily(str, Enum):
    """Classify one scalar identity without selecting a backend spelling."""

    BOOLEAN = "boolean"
    SIGNED_INTEGER = "signed_integer"
    UNSIGNED_INTEGER = "unsigned_integer"
    REAL = "real"
    COMPLEX = "complex"
    CHARACTER = "character"
    BYTE = "byte"
    ENUM = "enum"
    VOID = "void"


@dataclass(frozen=True)
class SemanticScalarSpec:
    """Describe intrinsic facts attached to one stable semantic scalar name.

    ``family`` groups identities used by semantic conversion and policy.
    ``storage_bits`` is present only when the semantic name itself fixes the
    storage width; target-dependent names such as ``Int`` and ``SizeT`` leave
    it unresolved.
    """

    family: SemanticScalarFamily
    storage_bits: int | None = None


SEMANTIC_SCALAR_TYPES: Final[Mapping[str, SemanticScalarSpec]] = MappingProxyType(
    {
        "Bool": SemanticScalarSpec(SemanticScalarFamily.BOOLEAN, 8),
        "Bool8": SemanticScalarSpec(SemanticScalarFamily.BOOLEAN, 8),
        "Bool16": SemanticScalarSpec(SemanticScalarFamily.BOOLEAN, 16),
        "Bool32": SemanticScalarSpec(SemanticScalarFamily.BOOLEAN, 32),
        "Bool64": SemanticScalarSpec(SemanticScalarFamily.BOOLEAN, 64),
        "Byte": SemanticScalarSpec(SemanticScalarFamily.BYTE, 8),
        "CEnum": SemanticScalarSpec(SemanticScalarFamily.ENUM),
        "Char": SemanticScalarSpec(SemanticScalarFamily.CHARACTER),
        "Complex64": SemanticScalarSpec(SemanticScalarFamily.COMPLEX, 64),
        "Complex128": SemanticScalarSpec(SemanticScalarFamily.COMPLEX, 128),
        "Complex256": SemanticScalarSpec(SemanticScalarFamily.COMPLEX),
        "Float16": SemanticScalarSpec(SemanticScalarFamily.REAL, 16),
        "Float32": SemanticScalarSpec(SemanticScalarFamily.REAL, 32),
        "Float64": SemanticScalarSpec(SemanticScalarFamily.REAL, 64),
        "Float128": SemanticScalarSpec(SemanticScalarFamily.REAL),
        "Int": SemanticScalarSpec(SemanticScalarFamily.SIGNED_INTEGER),
        "Int8": SemanticScalarSpec(SemanticScalarFamily.SIGNED_INTEGER, 8),
        "Int16": SemanticScalarSpec(SemanticScalarFamily.SIGNED_INTEGER, 16),
        "Int32": SemanticScalarSpec(SemanticScalarFamily.SIGNED_INTEGER, 32),
        "Int64": SemanticScalarSpec(SemanticScalarFamily.SIGNED_INTEGER, 64),
        "SizeT": SemanticScalarSpec(SemanticScalarFamily.UNSIGNED_INTEGER),
        "String": SemanticScalarSpec(SemanticScalarFamily.CHARACTER),
        "UInt": SemanticScalarSpec(SemanticScalarFamily.UNSIGNED_INTEGER),
        "UInt8": SemanticScalarSpec(SemanticScalarFamily.UNSIGNED_INTEGER, 8),
        "UInt16": SemanticScalarSpec(SemanticScalarFamily.UNSIGNED_INTEGER, 16),
        "UInt32": SemanticScalarSpec(SemanticScalarFamily.UNSIGNED_INTEGER, 32),
        "UInt64": SemanticScalarSpec(SemanticScalarFamily.UNSIGNED_INTEGER, 64),
        "Void": SemanticScalarSpec(SemanticScalarFamily.VOID),
    }
)

SEMANTIC_SCALAR_TYPE_NAMES: Final[frozenset[str]] = frozenset(SEMANTIC_SCALAR_TYPES)
BOOLEAN_SEMANTIC_TYPE_NAMES: Final[frozenset[str]] = frozenset(
    name for name, spec in SEMANTIC_SCALAR_TYPES.items() if spec.family is SemanticScalarFamily.BOOLEAN
)
BOOLEAN_STORAGE_BITS: Final[Mapping[str, int]] = MappingProxyType(
    {name: spec.storage_bits for name, spec in SEMANTIC_SCALAR_TYPES.items() if name in BOOLEAN_SEMANTIC_TYPE_NAMES}
)
INTEGER_SEMANTIC_TYPE_NAMES: Final[frozenset[str]] = frozenset(
    name
    for name, spec in SEMANTIC_SCALAR_TYPES.items()
    if spec.family in {SemanticScalarFamily.SIGNED_INTEGER, SemanticScalarFamily.UNSIGNED_INTEGER}
)


def is_boolean_semantic_type_name(name: str | None) -> bool:
    """Return whether ``name`` identifies a supported Boolean storage contract."""
    return name in BOOLEAN_SEMANTIC_TYPE_NAMES


def is_integer_semantic_type_name(name: str | None) -> bool:
    """Return whether ``name`` identifies a signed or unsigned integer identity."""
    return name in INTEGER_SEMANTIC_TYPE_NAMES


def boolean_storage_bits(name: str) -> int:
    """Return the fixed native storage width of one Boolean semantic name.

    Unknown and non-Boolean names raise ``KeyError`` so callers cannot invent
    a native representation when target measurement is required.
    """
    return BOOLEAN_STORAGE_BITS[name]


__all__ = (
    "BOOLEAN_SEMANTIC_TYPE_NAMES",
    "BOOLEAN_STORAGE_BITS",
    "SEMANTIC_SCALAR_TYPES",
    "SEMANTIC_SCALAR_TYPE_NAMES",
    "SemanticScalarFamily",
    "SemanticScalarSpec",
    "boolean_storage_bits",
    "is_boolean_semantic_type_name",
)


if __name__ == "__main__":
    for example_name in ("Float64", "Int"):
        example_spec = SEMANTIC_SCALAR_TYPES[example_name]
        storage = f"{example_spec.storage_bits} bits" if example_spec.storage_bits is not None else "target-dependent"
        print(f"{example_name}: family={example_spec.family.value}, storage={storage}")
    print("Backend spelling stored here: False")
