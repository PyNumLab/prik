"""NumPy dtype mappings for resolved semantic dtype names."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final

if TYPE_CHECKING:
    from prik.semantics.models import SemanticType


BOOLEAN_STORAGE_BITS: Final[dict[str, int]] = {
    "Bool": 8,
    "Bool8": 8,
    "Bool16": 16,
    "Bool32": 32,
    "Bool64": 64,
}
BOOLEAN_SEMANTIC_TYPE_NAMES: Final[frozenset[str]] = frozenset(BOOLEAN_STORAGE_BITS)


SEMANTIC_DTYPE_TO_NUMPY_DTYPE: Final[dict[str, str]] = {
    **dict.fromkeys(BOOLEAN_SEMANTIC_TYPE_NAMES, "numpy.bool_"),
    "Int8": "numpy.int8",
    "Int16": "numpy.int16",
    "Int32": "numpy.int32",
    "Int64": "numpy.int64",
    "UInt8": "numpy.uint8",
    "UInt16": "numpy.uint16",
    "UInt32": "numpy.uint32",
    "UInt64": "numpy.uint64",
    "Float16": "numpy.float16",
    "Float32": "numpy.float32",
    "Float64": "numpy.float64",
    "Float128": "numpy.longdouble",
    "Complex64": "numpy.complex64",
    "Complex128": "numpy.complex128",
    "Complex256": "numpy.clongdouble",
    "String": "numpy.str_",
    "SizeT": "numpy.uintp",
}


def is_boolean_semantic_type_name(name: str | None) -> bool:
    """Return whether ``name`` identifies a supported Boolean storage contract.

    All supported names share NumPy's one-byte ``bool_`` boundary.  Their
    numeric suffix records native storage bits for language-specific lowering.
    """
    return name in BOOLEAN_SEMANTIC_TYPE_NAMES


def boolean_storage_bits(name: str) -> int:
    """Return the native storage bits represented by one Boolean contract.

    ``Bool`` and ``Bool8`` both return eight.  Unknown names raise ``KeyError``
    so callers cannot silently invent a native Boolean representation.
    """
    return BOOLEAN_STORAGE_BITS[name]


SEMANTIC_SCALAR_TYPE_NAMES: Final[frozenset[str]] = frozenset(
    {
        *SEMANTIC_DTYPE_TO_NUMPY_DTYPE,
        "Byte",
        "CEnum",
        "Char",
        "Int",
        "UInt",
        "Void",
    }
)


def numpy_dtype_expression(semantic_dtype: str | None) -> str:
    """Return the qualified NumPy dtype expression for a resolved semantic dtype."""
    if semantic_dtype is None:
        raise KeyError("Semantic dtype is not resolved")
    dtype = str(semantic_dtype)
    try:
        return SEMANTIC_DTYPE_TO_NUMPY_DTYPE[dtype]
    except KeyError:
        raise KeyError(f"No NumPy dtype mapping for semantic dtype {dtype!r}") from None


def semantic_dtype_to_numpy_dtype(semantic_dtype: str | None) -> Any:
    """Return a live ``numpy.dtype`` for a resolved semantic dtype."""
    import numpy

    expression = numpy_dtype_expression(semantic_dtype)
    return numpy.dtype(getattr(numpy, expression.removeprefix("numpy.")))


def semantic_dtype_to_numpy_dtype_map() -> dict[str, Any]:
    """Return a dictionary mapping resolved semantic dtypes to live ``numpy.dtype`` objects."""
    return {
        semantic_dtype: semantic_dtype_to_numpy_dtype(semantic_dtype)
        for semantic_dtype in SEMANTIC_DTYPE_TO_NUMPY_DTYPE
    }


def semantic_type_to_numpy_dtype(semantic_type: SemanticType) -> Any:
    """Return a live ``numpy.dtype`` using ``SemanticType.dtype``, not ``SemanticType.name``."""
    return semantic_dtype_to_numpy_dtype(semantic_type.dtype)


__all__ = (
    "BOOLEAN_SEMANTIC_TYPE_NAMES",
    "BOOLEAN_STORAGE_BITS",
    "SEMANTIC_DTYPE_TO_NUMPY_DTYPE",
    "SEMANTIC_SCALAR_TYPE_NAMES",
    "boolean_storage_bits",
    "is_boolean_semantic_type_name",
    "numpy_dtype_expression",
    "semantic_dtype_to_numpy_dtype",
    "semantic_dtype_to_numpy_dtype_map",
    "semantic_type_to_numpy_dtype",
)
