"""Compiled scalar-reference and NumPy-array contracts for one-level C pointers.

The source-free contract mechanisms share one module-scoped build; the
generated-contract route keeps its own build because it starts from C source.
"""

import shutil
import subprocess
import sys
import warnings
from pathlib import Path

import numpy as np
import pytest

from prik import build_pyi_extension
from tests.c._support.runtime import sole_native_module


pytestmark = pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")

_CONTRACT = """from prik.contracts import Addr, Arg, CLongLong, Float64, Int32, Int64, Return, Returns, native_call

@native_call([Addr(Arg(0))])
def scale_scalar(value: Float64) -> Returns["value", Float64]: ...

def scale_zero(value: Float64[()]) -> None: ...

def scale_vector(values: Float64[n], n: Int32) -> None: ...

def scale_matrix(values: Float64[2, 2]) -> None: ...

@native_call([Arg(0).size, Arg(0)])
def scale_any_rank(values: Float64[...]) -> None: ...

@native_call([Arg(0).shape[0], Int64(Arg(0).strides[0]), Arg(0)])
def scale_strided(values: Float64[...]) -> None: ...

@native_call([Arg(0).shape[0], Arg(0)])
def scale_promoted(values: Float64[:]) -> None: ...

@native_call([Addr(CLongLong(Arg(0)))])
def increment_scalar(value: Int64) -> Returns["value", Int64]: ...

@native_call([CLongLong(Arg(0)), Arg(1)])
def increment(values: Int64[:], count: Int32) -> None: ...

@native_call([CLongLong(Arg(0))])
def increment_zero(value: Int64[()]) -> None: ...

@native_call([CLongLong(Return("out", 0))])
def read_exact() -> Int64: ...
"""

_SOURCE = """#include <stddef.h>
void scale_scalar(double *value) { *value *= 2.0; }
void scale_zero(double *value) { *value += 1.0; }
void scale_vector(double *values, int n) { for (int i = 0; i < n; ++i) values[i] *= 3.0; }
void scale_matrix(double *values) { for (int i = 0; i < 4; ++i) values[i] += 1.0; }
void scale_any_rank(size_t count, double *values) {
    for (size_t index = 0; index < count; ++index) values[index] *= 2.0;
}
void scale_strided(size_t count, long long stride_bytes, double *values) {
    char *base = (char *)values;
    for (size_t index = 0; index < count; ++index) {
        *(double *)(base + (ptrdiff_t)index * (ptrdiff_t)stride_bytes) *= 2.0;
    }
}
void scale_promoted(size_t n, double *values) { for (size_t i = 0; i < n; ++i) values[i] *= 2.0; }
void increment_scalar(long long *value) { *value += 1; }
void increment(long long *values, int count) {
    for (int i = 0; i < count; ++i) values[i] += 1;
}
void increment_zero(long long *value) { *value += 1; }
void read_exact(long long *out) { *out = 9000000000LL; }
"""


@pytest.fixture(scope="module")
def pointer_build(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("c_pointer_contracts")
    contract = tmp_path / "pointers.pyi"
    contract.write_text(_CONTRACT, encoding="utf-8")
    source = tmp_path / "pointers.c"
    source.write_text(_SOURCE, encoding="utf-8")
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        result = build_pyi_extension(
            contract,
            native_language="c",
            native_c_sources=[source],
            output_dir=tmp_path / "build",
        )
    binding = next(path.read_text(encoding="utf-8") for path in result.generated_sources if path.suffix == ".c")
    return result, binding, sole_native_module(result.import_module())


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


def test_c_pointer_supports_explicit_scalar_reference_and_exact_array_contracts(pointer_build):
    _result, _binding, module = pointer_build

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


def test_runtime_rank_c_pointer_uses_total_size_for_rank_zero_and_ranked_storage(pointer_build):
    _result, binding, module = pointer_build

    assert "void scale_any_rank(size_t size_0, double * values);" in binding
    assert "(size_t)PyArray_SIZE((PyArrayObject *)bound_values_obj)" in binding

    zero = np.array(3.0, dtype=np.float64)
    vector = np.array([1.0, 2.0, 3.0], dtype=np.float64)
    matrix = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float64, order="C")
    empty = np.empty((2, 0), dtype=np.float64)
    for values in (zero, vector, matrix, empty):
        expected = values.copy() * 2.0
        assert module.scale_any_rank(values) is None
        np.testing.assert_allclose(values, expected)

    # Runtime-rank storage constrains neither rank nor strides, so a
    # Fortran-ordered actual reaches the same contiguous buffer.
    fortran = np.asfortranarray(matrix)
    expected = fortran.copy() * 2.0
    assert module.scale_any_rank(fortran) is None
    np.testing.assert_allclose(fortran, expected)

    with pytest.raises(TypeError, match=r"numpy\.ndarray"):
        module.scale_any_rank(np.float64(3.0))
    with pytest.raises(TypeError, match=r"compatible numpy\.ndarray"):
        module.scale_any_rank(np.ones((1,) * 16, dtype=np.float64))


def test_runtime_rank_c_pointer_passes_a_strided_view_with_its_projected_layout(pointer_build):
    """``T[...]`` states no layout, so projected extents and strides carry it."""
    _result, binding, module = pointer_build

    assert "PRIK_ARRAY_LAYOUT_ANY_STRIDED" in binding
    assert "(int64_t)PyArray_STRIDE((PyArrayObject *)bound_values_obj, 0)" in binding

    base = np.arange(6, dtype=np.float64)
    assert module.scale_strided(base[::2]) is None
    np.testing.assert_allclose(base, np.array([0.0, 1.0, 4.0, 3.0, 8.0, 5.0]))

    # A projected axis cannot exist on rank-zero storage, so the caller is told
    # instead of the binding reading past the actual's shape.
    with pytest.raises(TypeError, match="has no axis 0"):
        module.scale_strided(np.array(1.0, dtype=np.float64))


def test_edited_c_array_contract_can_derive_the_native_extent_from_its_shape(pointer_build):
    """The documented promotion hides the count behind ``Arg(0).shape[0]``.

    The derived extent is a binding-owned producer, so it keeps its own
    ``size_t`` identity while the promoted buffer crosses by address.
    """
    result, binding, module = pointer_build

    assert "void scale_promoted(size_t shape_0, double * values);" in binding
    assert all(path.suffix != ".f90" for path in result.generated_sources)
    values = np.array([1.0, 2.0, 3.0], dtype=np.float64)
    assert module.scale_promoted(values) is None
    np.testing.assert_allclose(values, np.array([2.0, 4.0, 6.0]))
    assert module.scale_promoted(np.empty(0, dtype=np.float64)) is None


def test_exact_long_long_scalar_address_converts_while_arrays_require_native_storage(pointer_build):
    _result, binding, module = pointer_build

    # A converted scalar is materialized as native storage before its address is taken.
    assert "void increment_scalar(long long * value);" in binding
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

    # An exact output parameter is native storage converted to the contract result.
    assert "void read_exact(long long * out);" in binding
    output = module.read_exact()
    assert output == np.int64(9000000000)
    assert output.dtype == np.dtype(np.int64)

    if np.dtype(np.int64).num != np.dtype(np.longlong).num:
        with pytest.raises(TypeError, match=r"numpy\.longlong"):
            module.increment(np.array([1, 2, 3], dtype=np.int64), np.int32(3))
        with pytest.raises(TypeError, match=r"numpy\.longlong"):
            module.increment_zero(np.array(4, dtype=np.int64))
