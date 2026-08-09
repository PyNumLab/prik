"""Primitive rank-zero backend type facts shared by wrapper generators."""

from __future__ import annotations

from dataclasses import replace
from typing import ClassVar

from prik.types.numpy import BOOLEAN_SEMANTIC_TYPE_NAMES
from prik.codegen.nodes import BackendScalarType


_BOOL_BACKEND_TYPE = BackendScalarType(
    "Bool",
    "bool",
    "logical(c_bool)",
    "O",
    "NPY_BOOL",
    "python",
    "bool",
    "python",
    "CFI_type_Bool",
)


class PrimitiveScalarTypeRegistry:
    """Return first-lane scalar facts without coupling binding and bridge emitters."""

    TYPES: ClassVar[dict[str, BackendScalarType]] = {
        **{name: replace(_BOOL_BACKEND_TYPE, semantic_name=name) for name in BOOLEAN_SEMANTIC_TYPE_NAMES},
        "Int8": BackendScalarType(
            "Int8",
            "int8_t",
            "integer(c_int8_t)",
            "O",
            "NPY_INT8",
            "numpy",
            "numpy.int8",
            "numpy",
            "CFI_type_int8_t",
        ),
        "Int16": BackendScalarType(
            "Int16",
            "int16_t",
            "integer(c_int16_t)",
            "O",
            "NPY_INT16",
            "numpy",
            "numpy.int16",
            "numpy",
            "CFI_type_int16_t",
        ),
        "Int32": BackendScalarType(
            "Int32",
            "int32_t",
            "integer(c_int32_t)",
            "O",
            "NPY_INT32",
            "python",
            "numpy.int32",
            "numpy",
            "CFI_type_int32_t",
        ),
        "Int64": BackendScalarType(
            "Int64",
            "int64_t",
            "integer(c_int64_t)",
            "O",
            "NPY_INT64",
            "python",
            "numpy.int64",
            "numpy",
            "CFI_type_int64_t",
        ),
        "Float32": BackendScalarType(
            "Float32",
            "float",
            "real(c_float)",
            "O",
            "NPY_FLOAT32",
            "numpy",
            "numpy.float32",
            "numpy",
            "CFI_type_float",
        ),
        "Float64": BackendScalarType(
            "Float64",
            "double",
            "real(c_double)",
            "O",
            "NPY_FLOAT64",
            "python",
            "numpy.float64",
            "numpy",
            "CFI_type_double",
        ),
        "Complex64": BackendScalarType(
            "Complex64",
            "float complex",
            "complex(c_float_complex)",
            "O",
            "NPY_COMPLEX64",
            "numpy",
            "numpy.complex64",
            "numpy",
            "CFI_type_float_Complex",
        ),
        "Complex128": BackendScalarType(
            "Complex128",
            "double complex",
            "complex(c_double_complex)",
            "O",
            "NPY_COMPLEX128",
            "python",
            "numpy.complex128",
            "numpy",
            "CFI_type_double_Complex",
        ),
    }

    @classmethod
    def type_for(cls, semantic_type_name: str) -> BackendScalarType:
        """Return editable scalar backend facts or fail with one stable diagnostic."""
        try:
            return replace(cls.TYPES[semantic_type_name])
        except KeyError:
            raise ValueError(f"Unsupported first-lane scalar type {semantic_type_name!r}") from None
