"""Runtime evidence for documented ORDER_C and COPY_F semantic-contract edits."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import (
    _compile_native_object,
    _import_from_build_dir,
    _sole_native_module,
)
from x2py import build_pyi_extension

pytestmark = pytest.mark.fortran_end_to_end

SOURCE = Path(__file__).parent / "fixtures" / "array_ops.f90"


def test_edited_pyi_selects_direct_c_storage_or_fortran_copy_semantics(tmp_path: Path):
    native_object = _compile_native_object(SOURCE, tmp_path / "native")
    contract = tmp_path / "contract"
    contract.mkdir()
    (contract / "__init__.pyi").write_text(
        "from .array_ops import scale_without_intent, sum_columns_copy_f, sum_columns_direct_c\n",
        encoding="utf-8",
    )
    (contract / "array_ops.pyi").write_text(
        """from x2py.contracts import (
    Addr,
    Annotated,
    Arg,
    COPY_F,
    Float64,
    Immutable,
    Int32,
    ORDER_C,
    Returns,
    bind,
    native_call,
)

@bind("sum_columns")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def sum_columns_direct_c(
    size: Int32,
    values: Annotated[Float64[size, size], ORDER_C],
    result: Float64[size],
) -> None: ...

@bind("sum_columns")
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def sum_columns_copy_f(
    size: Int32,
    values: Annotated[Float64[size, size], ORDER_C, COPY_F],
    result: Float64[size],
) -> None: ...

def scale_without_intent(
    values: Annotated[Float64[:], Immutable],
) -> Returns["values", Float64[:]]: ...
""",
        encoding="utf-8",
    )
    result = build_pyi_extension(
        contract / "__init__.pyi",
        native_objects=[native_object],
        native_include_dirs=[native_object.parent],
        output_dir=tmp_path / "build",
    )
    module = _sole_native_module(_import_from_build_dir(result.module_name, result.output_dir))

    values = np.array(
        [[1.0, 2.0, 3.0], [10.0, 20.0, 30.0], [100.0, 200.0, 300.0]],
        dtype=np.float64,
        order="C",
    )
    direct_result = np.empty(3, dtype=np.float64)
    assert module.sum_columns_direct_c(np.int32(3), values, direct_result) is None
    np.testing.assert_array_equal(direct_result, np.array([6.0, 60.0, 600.0]))

    copied_result = np.empty(3, dtype=np.float64)
    assert module.sum_columns_copy_f(np.int32(3), values, copied_result) is None
    np.testing.assert_array_equal(copied_result, np.array([111.0, 222.0, 333.0]))
    assert values.flags.c_contiguous

    with pytest.raises(TypeError, match=r"expected ordering \(C\)"):
        module.sum_columns_copy_f(np.int32(3), np.asfortranarray(values), copied_result)

    original = np.array([2.0, 5.0, 7.0], dtype=np.float64)
    original.flags.writeable = False
    replacement = module.scale_without_intent(original)
    np.testing.assert_array_equal(original, np.array([2.0, 5.0, 7.0]))
    np.testing.assert_array_equal(replacement, np.array([4.0, 10.0, 14.0]))
    assert replacement is not original
