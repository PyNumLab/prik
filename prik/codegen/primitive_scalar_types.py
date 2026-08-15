"""Backend spelling registries for resolved primitive scalar identities.

``PrimitiveScalarTypeRegistry.type_for`` returns a fresh editable
``BackendScalarType`` containing the C, Fortran, NumPy, CPython, and descriptor
spellings required by direct lowering. ``NumpyDtypeRegistry.expression_for``
returns the corresponding generated Python expression. Both registries consume
an already-resolved semantic identity and fail for unknown names; neither
infers a scalar type from source syntax or a backend condition.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from types import MappingProxyType
from typing import ClassVar

from prik.codegen.nodes import BackendScalarType
from prik.semantics.scalar_types import BOOLEAN_SEMANTIC_TYPE_NAMES


class NumpyDtypeRegistry:
    """Project resolved semantic dtypes into emitted NumPy expressions."""

    TYPES: ClassVar[Mapping[str, str]] = MappingProxyType(
        {
            "Bool": "numpy.bool_",
            "Bool8": "numpy.bool_",
            "Bool16": "numpy.bool_",
            "Bool32": "numpy.bool_",
            "Bool64": "numpy.bool_",
            "Complex64": "numpy.complex64",
            "Complex128": "numpy.complex128",
            "Complex256": "numpy.clongdouble",
            "Float16": "numpy.float16",
            "Float32": "numpy.float32",
            "Float64": "numpy.float64",
            "Float128": "numpy.longdouble",
            "Int8": "numpy.int8",
            "Int16": "numpy.int16",
            "Int32": "numpy.int32",
            "Int64": "numpy.int64",
            "SizeT": "numpy.uintp",
            "String": "numpy.str_",
            "UInt8": "numpy.uint8",
            "UInt16": "numpy.uint16",
            "UInt32": "numpy.uint32",
            "UInt64": "numpy.uint64",
        }
    )

    @classmethod
    def expression_for(cls, semantic_dtype: str | None) -> str:
        """Return the emitted NumPy expression for one resolved semantic dtype.

        The lookup is code-generation vocabulary, not semantic inference.
        Unknown and unresolved names fail so callers cannot select a nearby
        NumPy dtype.
        """
        if semantic_dtype is None:
            raise KeyError("Semantic dtype is not resolved")
        dtype = str(semantic_dtype)
        try:
            return cls.TYPES[dtype]
        except KeyError:
            raise KeyError(f"No NumPy dtype mapping for semantic dtype {dtype!r}") from None


_BOOL_BACKEND_TYPE = BackendScalarType(
    semantic_name="Bool",
    c_spelling="bool",
    fortran_spelling="logical(c_bool)",
    python_parse_unit="O",
    numpy_type_macro="NPY_BOOL",
    python_result_kind="python",
    python_type_name="bool",
    python_module_result_kind="python",
    cfi_type_spelling="CFI_type_Bool",
)


class PrimitiveScalarTypeRegistry:
    """Return first-lane scalar facts without coupling binding and bridge emitters."""

    TYPES: ClassVar[dict[str, BackendScalarType]] = {
        **{name: replace(_BOOL_BACKEND_TYPE, semantic_name=name) for name in BOOLEAN_SEMANTIC_TYPE_NAMES},
        "Int8": BackendScalarType(
            semantic_name="Int8",
            c_spelling="int8_t",
            fortran_spelling="integer(c_int8_t)",
            python_parse_unit="O",
            numpy_type_macro="NPY_INT8",
            python_result_kind="numpy",
            python_type_name=NumpyDtypeRegistry.expression_for("Int8"),
            python_module_result_kind="numpy",
            cfi_type_spelling="CFI_type_int8_t",
        ),
        "Int16": BackendScalarType(
            semantic_name="Int16",
            c_spelling="int16_t",
            fortran_spelling="integer(c_int16_t)",
            python_parse_unit="O",
            numpy_type_macro="NPY_INT16",
            python_result_kind="numpy",
            python_type_name=NumpyDtypeRegistry.expression_for("Int16"),
            python_module_result_kind="numpy",
            cfi_type_spelling="CFI_type_int16_t",
        ),
        "Int32": BackendScalarType(
            semantic_name="Int32",
            c_spelling="int32_t",
            fortran_spelling="integer(c_int32_t)",
            python_parse_unit="O",
            numpy_type_macro="NPY_INT32",
            python_result_kind="numpy",
            python_type_name=NumpyDtypeRegistry.expression_for("Int32"),
            python_module_result_kind="numpy",
            cfi_type_spelling="CFI_type_int32_t",
        ),
        "Int64": BackendScalarType(
            semantic_name="Int64",
            c_spelling="int64_t",
            fortran_spelling="integer(c_int64_t)",
            python_parse_unit="O",
            numpy_type_macro="NPY_INT64",
            python_result_kind="numpy",
            python_type_name=NumpyDtypeRegistry.expression_for("Int64"),
            python_module_result_kind="numpy",
            cfi_type_spelling="CFI_type_int64_t",
        ),
        "SizeT": BackendScalarType(
            semantic_name="SizeT",
            c_spelling="size_t",
            fortran_spelling="integer(c_size_t)",
            python_parse_unit="O",
            numpy_type_macro="NPY_UINTP",
            python_result_kind="numpy",
            python_type_name=NumpyDtypeRegistry.expression_for("SizeT"),
            python_module_result_kind="numpy",
            cfi_type_spelling="CFI_type_size_t",
        ),
        "Float32": BackendScalarType(
            semantic_name="Float32",
            c_spelling="float",
            fortran_spelling="real(c_float)",
            python_parse_unit="O",
            numpy_type_macro="NPY_FLOAT32",
            python_result_kind="numpy",
            python_type_name=NumpyDtypeRegistry.expression_for("Float32"),
            python_module_result_kind="numpy",
            cfi_type_spelling="CFI_type_float",
        ),
        "Float64": BackendScalarType(
            semantic_name="Float64",
            c_spelling="double",
            fortran_spelling="real(c_double)",
            python_parse_unit="O",
            numpy_type_macro="NPY_FLOAT64",
            python_result_kind="numpy",
            python_type_name=NumpyDtypeRegistry.expression_for("Float64"),
            python_module_result_kind="numpy",
            cfi_type_spelling="CFI_type_double",
        ),
        "Complex64": BackendScalarType(
            semantic_name="Complex64",
            c_spelling="float complex",
            fortran_spelling="complex(c_float_complex)",
            python_parse_unit="O",
            numpy_type_macro="NPY_COMPLEX64",
            python_result_kind="numpy",
            python_type_name=NumpyDtypeRegistry.expression_for("Complex64"),
            python_module_result_kind="numpy",
            cfi_type_spelling="CFI_type_float_Complex",
        ),
        "Complex128": BackendScalarType(
            semantic_name="Complex128",
            c_spelling="double complex",
            fortran_spelling="complex(c_double_complex)",
            python_parse_unit="O",
            numpy_type_macro="NPY_COMPLEX128",
            python_result_kind="numpy",
            python_type_name=NumpyDtypeRegistry.expression_for("Complex128"),
            python_module_result_kind="numpy",
            cfi_type_spelling="CFI_type_double_Complex",
        ),
    }

    @classmethod
    def type_for(cls, semantic_type_name: str) -> BackendScalarType:
        """Return editable scalar backend facts or fail with one stable diagnostic."""
        try:
            return replace(cls.TYPES[semantic_type_name])
        except KeyError:
            raise ValueError(f"Unsupported first-lane scalar type {semantic_type_name!r}") from None


__all__ = (
    "NumpyDtypeRegistry",
    "PrimitiveScalarTypeRegistry",
)


if __name__ == "__main__":
    example_type = PrimitiveScalarTypeRegistry.type_for("Float64")
    second_lookup = PrimitiveScalarTypeRegistry.type_for("Float64")

    print(
        f"Float64: C={example_type.c_spelling}; "
        f"Fortran={example_type.fortran_spelling}; "
        f"NumPy={NumpyDtypeRegistry.expression_for('Float64')}"
    )
    print(f"NumPy C macro: {example_type.numpy_type_macro}")
    print(f"Fresh editable node per lookup: {example_type is not second_lookup}")
