"""Compiled scalar-reference and NumPy-array contracts for one-level C pointers."""

import shutil
import subprocess
import sys
import warnings
from pathlib import Path

import numpy as np
import pytest

from prik import build_pyi_extension
from tests.c._support.runtime import sole_native_module


@pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")
def test_generated_c_int_array_uses_its_probed_primitive_storage(tmp_path: Path):
    """The public ``Int`` spelling retains its probed dtype for array policy."""
    source = tmp_path / "integer_array.c"
    source.write_text(
        "void fill_indices(int values[4]) { for (int i = 0; i < 4; ++i) values[i] = i + 1; }\n",
        encoding="utf-8",
    )

    contract = tmp_path / "integer_array.pyi"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "prik",
            "generate",
            "--pyi",
            "--language",
            "c",
            str(source),
            "--out",
            str(contract),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "values: Int[4]" in contract.read_text(encoding="utf-8")

    result = build_pyi_extension(
        contract,
        native_language="c",
        native_c_sources=[source],
        output_dir=tmp_path / "build_integer_array",
        output_name="integer_array",
    )
    module = sole_native_module(result.import_module())
    values = np.zeros(4, dtype=np.intc)

    assert module.fill_indices(values) is None
    np.testing.assert_array_equal(values, np.array([1, 2, 3, 4], dtype=np.intc))


@pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")
def test_c_pointer_supports_explicit_scalar_reference_and_exact_array_contracts(tmp_path: Path):
    contract = tmp_path / "pointers.pyi"
    contract.write_text(
        """from prik.contracts import Addr, Arg, Float64, Int32, Returns, native_call

@native_call([Addr(Arg(0))])
def scale_scalar(value: Float64) -> Returns["value", Float64]: ...

def scale_zero(value: Float64[()]) -> None: ...

def scale_vector(values: Float64[n], n: Int32) -> None: ...

def scale_matrix(values: Float64[2, 2]) -> None: ...
""",
        encoding="utf-8",
    )
    source = tmp_path / "pointers.c"
    source.write_text(
        """void scale_scalar(double *value) { *value *= 2.0; }
void scale_zero(double *value) { *value += 1.0; }
void scale_vector(double *values, int n) { for (int i = 0; i < n; ++i) values[i] *= 3.0; }
void scale_matrix(double *values) { for (int i = 0; i < 4; ++i) values[i] += 1.0; }
""",
        encoding="utf-8",
    )

    result = build_pyi_extension(
        contract,
        native_language="c",
        native_c_sources=[source],
        output_dir=tmp_path / "build",
    )
    module = sole_native_module(result.import_module())

    assert module.scale_scalar(np.float64(2.5)) == np.float64(5.0)
    zero = np.array(4.0, dtype=np.float64)
    assert module.scale_zero(zero) is None
    assert zero[()] == np.float64(5.0)
    values = np.array([1.0, 2.0, 3.0], dtype=np.float64)
    assert module.scale_vector(values, np.int32(3)) is None
    np.testing.assert_allclose(values, np.array([3.0, 6.0, 9.0]))
    empty = np.empty(0, dtype=np.float64)
    assert module.scale_vector(empty, np.int32(0)) is None
    matrix = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float64, order="C")
    assert module.scale_matrix(matrix) is None
    np.testing.assert_allclose(matrix, np.array([[2.0, 3.0], [4.0, 5.0]]))
    with pytest.raises(TypeError, match=r"expected ordering \(C\)"):
        module.scale_matrix(np.asfortranarray(matrix))


@pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")
def test_runtime_rank_c_pointer_uses_total_size_for_rank_zero_and_ranked_storage(tmp_path: Path):
    contract = tmp_path / "runtime_rank.pyi"
    contract.write_text(
        """from prik.contracts import Arg, Float64, native_call

@native_call([Arg(0).size, Arg(0)])
def scale(values: Float64[...]) -> None: ...
""",
        encoding="utf-8",
    )
    source = tmp_path / "runtime_rank.c"
    source.write_text(
        """#include <stddef.h>
void scale(size_t count, double *values) {
    for (size_t index = 0; index < count; ++index) values[index] *= 2.0;
}
""",
        encoding="utf-8",
    )

    result = build_pyi_extension(
        contract,
        native_language="c",
        native_c_sources=[source],
        output_dir=tmp_path / "build_runtime_rank",
        output_name="runtime_rank",
    )
    module = sole_native_module(result.import_module())
    binding = next(path.read_text(encoding="utf-8") for path in result.generated_sources if path.suffix == ".c")

    assert "void scale(size_t size_0, double * values);" in binding
    assert "(size_t)PyArray_SIZE((PyArrayObject *)bound_values_obj)" in binding

    zero = np.array(3.0, dtype=np.float64)
    vector = np.array([1.0, 2.0, 3.0], dtype=np.float64)
    matrix = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float64, order="C")
    empty = np.empty((2, 0), dtype=np.float64)
    for values in (zero, vector, matrix, empty):
        expected = values.copy() * 2.0
        assert module.scale(values) is None
        np.testing.assert_allclose(values, expected)

    # Runtime-rank storage constrains neither rank nor strides, so a
    # Fortran-ordered actual reaches the same contiguous buffer.
    fortran = np.asfortranarray(matrix)
    expected = fortran.copy() * 2.0
    assert module.scale(fortran) is None
    np.testing.assert_allclose(fortran, expected)

    with pytest.raises(TypeError, match=r"numpy\.ndarray"):
        module.scale(np.float64(3.0))
    with pytest.raises(TypeError, match=r"compatible numpy\.ndarray"):
        module.scale(np.ones((1,) * 16, dtype=np.float64))


@pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")
def test_runtime_rank_c_pointer_passes_a_strided_view_with_its_projected_layout(tmp_path: Path):
    """``T[...]`` states no layout, so projected extents and strides carry it."""
    contract = tmp_path / "strided_rank.pyi"
    contract.write_text(
        """from prik.contracts import Arg, Float64, Int64, native_call

@native_call([Arg(0).shape[0], Int64(Arg(0).strides[0]), Arg(0)])
def scale(values: Float64[...]) -> None: ...
""",
        encoding="utf-8",
    )
    source = tmp_path / "strided_rank.c"
    source.write_text(
        """#include <stddef.h>
void scale(size_t count, long long stride_bytes, double *values) {
    char *base = (char *)values;
    for (size_t index = 0; index < count; ++index) {
        *(double *)(base + (ptrdiff_t)index * (ptrdiff_t)stride_bytes) *= 2.0;
    }
}
""",
        encoding="utf-8",
    )

    result = build_pyi_extension(
        contract,
        native_language="c",
        native_c_sources=[source],
        output_dir=tmp_path / "build_strided_rank",
        output_name="strided_rank",
    )
    module = sole_native_module(result.import_module())
    binding = next(path.read_text(encoding="utf-8") for path in result.generated_sources if path.suffix == ".c")

    assert "PRIK_ARRAY_LAYOUT_ANY_STRIDED" in binding
    assert "(int64_t)PyArray_STRIDE((PyArrayObject *)bound_values_obj, 0)" in binding

    base = np.arange(6, dtype=np.float64)
    assert module.scale(base[::2]) is None
    np.testing.assert_allclose(base, np.array([0.0, 1.0, 4.0, 3.0, 8.0, 5.0]))

    # A projected axis cannot exist on rank-zero storage, so the caller is told
    # instead of the binding reading past the actual's shape.
    with pytest.raises(TypeError, match="has no axis 0"):
        module.scale(np.array(1.0, dtype=np.float64))


@pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")
def test_edited_c_array_contract_can_derive_the_native_extent_from_its_shape(tmp_path: Path):
    """The documented promotion hides the count behind ``Arg(0).shape[0]``.

    The derived extent is a binding-owned producer, so it keeps its own
    ``size_t`` identity while the promoted buffer crosses by address.
    """
    contract = tmp_path / "promotion.pyi"
    contract.write_text(
        """from prik.contracts import Arg, Float64, native_call

@native_call([Arg(0).shape[0], Arg(0)])
def scale(values: Float64[:]) -> None: ...
""",
        encoding="utf-8",
    )
    source = tmp_path / "promotion.c"
    source.write_text(
        """#include <stddef.h>
void scale(size_t n, double *values) { for (size_t i = 0; i < n; ++i) values[i] *= 2.0; }
""",
        encoding="utf-8",
    )

    result = build_pyi_extension(
        contract,
        native_language="c",
        native_c_sources=[source],
        output_dir=tmp_path / "build",
    )
    module = sole_native_module(result.import_module())
    binding = next(path.read_text(encoding="utf-8") for path in result.generated_sources if path.suffix == ".c")

    assert "void scale(size_t shape_0, double * values);" in binding
    assert all(path.suffix != ".f90" for path in result.generated_sources)
    values = np.array([1.0, 2.0, 3.0], dtype=np.float64)
    assert module.scale(values) is None
    np.testing.assert_allclose(values, np.array([2.0, 4.0, 6.0]))
    assert module.scale(np.empty(0, dtype=np.float64)) is None


@pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")
def test_exact_long_long_scalar_address_converts_while_arrays_require_native_storage(tmp_path: Path):
    contract = tmp_path / "exact_long_long.pyi"
    contract.write_text(
        """from prik.contracts import Addr, Arg, CLongLong, Int32, Int64, Returns, native_call

@native_call([Addr(CLongLong(Arg(0)))])
def increment_scalar(value: Int64) -> Returns["value", Int64]: ...

@native_call([CLongLong(Arg(0)), Arg(1)])
def increment(values: Int64[:], count: Int32) -> None: ...

@native_call([CLongLong(Arg(0))])
def increment_zero(value: Int64[()]) -> None: ...
""",
        encoding="utf-8",
    )
    source = tmp_path / "exact_long_long.c"
    source.write_text(
        """void increment_scalar(long long *value) { *value += 1; }
void increment(long long *values, int count) {
    for (int i = 0; i < count; ++i) values[i] += 1;
}
void increment_zero(long long *value) { *value += 1; }
""",
        encoding="utf-8",
    )

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        result = build_pyi_extension(
            contract,
            native_language="c",
            native_c_sources=[source],
            output_dir=tmp_path / "build",
        )
    module = sole_native_module(result.import_module())

    scalar = module.increment_scalar(np.int64(4))
    assert scalar == np.int64(5)
    assert scalar.dtype == np.dtype(np.int64)
    # A scalar is converted rather than aliased, so either 64-bit spelling is
    # accepted and cast to the exact native storage the call needs.
    exact = module.increment_scalar(np.longlong(4))
    assert exact == np.int64(5)
    assert exact.dtype == np.dtype(np.int64)

    values = np.array([1, 2, 3], dtype=np.longlong)
    assert module.increment(values, np.int32(values.size)) is None
    np.testing.assert_array_equal(values, np.array([2, 3, 4], dtype=np.longlong))

    zero = np.array(4, dtype=np.longlong)
    assert module.increment_zero(zero) is None
    assert zero[()] == np.longlong(5)

    if np.dtype(np.int64).num != np.dtype(np.longlong).num:
        with pytest.raises(TypeError, match=r"numpy\.longlong"):
            module.increment(np.array([1, 2, 3], dtype=np.int64), np.int32(3))
        with pytest.raises(TypeError, match=r"numpy\.longlong"):
            module.increment_zero(np.array(4, dtype=np.int64))
