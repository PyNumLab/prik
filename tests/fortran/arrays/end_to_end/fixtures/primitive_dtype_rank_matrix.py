"""Generate one Fortran module crossing every primitive dtype with representative ranks."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class PrimitiveArrayCase:
    name: str
    fortran_type: str
    dtype: type[np.generic]
    assignment: str
    values: tuple[object, object]
    expected: tuple[object, object]


PRIMITIVE_ARRAY_CASES = (
    PrimitiveArrayCase("bool", "logical(c_bool)", np.bool_, "values = .not. values", (False, True), (True, False)),
    PrimitiveArrayCase("int8", "integer(c_int8_t)", np.int8, "values = values + 1", (-2, 3), (-1, 4)),
    PrimitiveArrayCase("int16", "integer(c_int16_t)", np.int16, "values = values + 1", (-20, 30), (-19, 31)),
    PrimitiveArrayCase("int32", "integer(c_int32_t)", np.int32, "values = values + 1", (-200, 300), (-199, 301)),
    PrimitiveArrayCase("int64", "integer(c_int64_t)", np.int64, "values = values + 1", (-2000, 3000), (-1999, 3001)),
    PrimitiveArrayCase(
        "float32",
        "real(c_float)",
        np.float32,
        "values = values + 1.0_c_float",
        (-1.25, 2.5),
        (-0.25, 3.5),
    ),
    PrimitiveArrayCase(
        "float64",
        "real(c_double)",
        np.float64,
        "values = values + 1.0_c_double",
        (-1.25, 2.5),
        (-0.25, 3.5),
    ),
    PrimitiveArrayCase(
        "complex64",
        "complex(c_float_complex)",
        np.complex64,
        "values = values + cmplx(1.0_c_float, -0.5_c_float, kind=c_float)",
        (1 + 2j, -2 + 0.5j),
        (2 + 1.5j, -1 + 0j),
    ),
    PrimitiveArrayCase(
        "complex128",
        "complex(c_double_complex)",
        np.complex128,
        "values = values + cmplx(1.0_c_double, -0.5_c_double, kind=c_double)",
        (1 + 2j, -2 + 0.5j),
        (2 + 1.5j, -1 + 0j),
    ),
)


# The element-type mapping does not depend on rank, and descriptor rank handling
# does not depend on the element type. Every dtype therefore meets a vector, a
# matrix, and the first rank with an interior axis. The highest ranks are
# exercised for float64 by the contract-validation, array-result, and
# assumed-rank tests; optimizing whole-array expressions at every high rank for
# every dtype dominated this build without adding a failure mode.
PRIMITIVE_ARRAY_RANKS = (1, 2, 3)


def primitive_dtype_rank_source() -> str:
    """Return deterministic source for nine dtypes at the representative ranks."""
    procedures: list[str] = []
    for case in PRIMITIVE_ARRAY_CASES:
        for rank in PRIMITIVE_ARRAY_RANKS:
            dimensions = ", ".join(":" for _ in range(rank))
            procedures.append(
                "\n".join(
                    (
                        f"  subroutine bump_{case.name}_r{rank}(values)",
                        f"    {case.fortran_type}, intent(inout) :: values({dimensions})",
                        f"    {case.assignment}",
                        f"  end subroutine bump_{case.name}_r{rank}",
                    )
                )
            )
    return "\n".join(
        (
            "module farray_dtype_rank_matrix",
            "  use iso_c_binding",
            "  implicit none",
            "contains",
            *procedures,
            "end module farray_dtype_rank_matrix",
            "",
        )
    )
