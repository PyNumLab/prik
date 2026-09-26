"""Compiled direct-C primitive scalar evidence.

One C source build and one source-free contract build carry every scalar
mechanism: source declarations, preprocessing, typedef resolution, the default
``T *`` storage, and contract-side binding, projection, and overloads.
"""

import shutil

import numpy as np
import pytest

from prik import build_c_extension, build_pyi_extension
from tests.c._support.runtime import sole_native_module


pytestmark = pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")

_C_SOURCE = """#include <stddef.h>
#define PRIK_TEST_GAIN 3.0

typedef long my_int;

double native_add(double left, double right) { return left + right; }
double native_scale(double *value) { *value *= 2.0; return *value; }
double scaled(double value) { return value * PRIK_TEST_GAIN; }
size_t total(size_t value) { return value + 1; }
void twice(double *value) { *value *= 2.0; }
my_int alias_step(my_int value) { return value + 1; }
ptrdiff_t alias_offset(const ptrdiff_t *value) { return *value + 1; }
"""

_CONTRACT = """from prik.contracts import (
    Addr, Arg, Float64, Int, Int32, Return, SizeT, Value, bind, native_call, overload, private,
)

@bind("native_add")
def add(left: Float64, right: Float64) -> Float64: ...

@bind("native_increment")
def increment(value: Int) -> Int: ...

def bump(value: Int32) -> Int32: ...

@bind("projected_native")
@native_call([Value(Arg(1)), Addr(Arg(0)), Int32(5)])
def projected(left: Int32, right: Int32) -> Int32: ...

@bind("projected_output_native")
@native_call([Value(Arg(1)), Addr(Arg(0)), Int32(5), Return("output", 0)])
def projected_output(left: Int32, right: Int32) -> Int32: ...

@native_call([Arg(1), Arg(0)])
def combine(scale: Float64, count: Int32) -> Float64: ...

def total(value: SizeT) -> SizeT: ...

@private
def scale_integer(value: Int32) -> Int32: ...

@private
def scale_real(value: Float64) -> Float64: ...

@overload("scale_integer")
def scale(value: Int32) -> Int32: ...

@overload("scale_real")
def scale(value: Float64) -> Float64: ...
"""

_CONTRACT_SOURCE = """#include <stddef.h>
double native_add(double left, double right) { return left + right; }
int native_increment(int value) { return value + 1; }
int bump(int value) { return value + 1; }
int projected_native(int right, int *left, int bias) { return 100 * right + 10 * *left + bias; }
void projected_output_native(int right, int *left, int bias, int *output) {
    *output = 100 * right + 10 * *left + bias;
}
double combine(int count, double scale) { return count * scale; }
size_t total(size_t value) { return value + 1; }
int scale_integer(int value) { return value * 2; }
double scale_real(double value) { return value * 2.0; }
"""


def _binding(result) -> str:
    return next(path.read_text(encoding="utf-8") for path in result.generated_sources if path.suffix == ".c")


@pytest.fixture(scope="module")
def source_build(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("c_scalar_source")
    source = tmp_path / "scalar_api.c"
    source.write_text(_C_SOURCE, encoding="utf-8")
    result = build_c_extension(source, output_dir=tmp_path / "build", output_name="c_scalar_api")
    return result, sole_native_module(result.import_module())


@pytest.fixture(scope="module")
def contract_build(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("c_scalar_contract")
    contract = tmp_path / "direct_c_contract.pyi"
    contract.write_text(_CONTRACT, encoding="utf-8")
    source = tmp_path / "implementation.c"
    source.write_text(_CONTRACT_SOURCE, encoding="utf-8")
    result = build_pyi_extension(
        contract,
        native_language="c",
        native_c_sources=[source],
        output_dir=tmp_path / "build",
    )
    return result, sole_native_module(result.import_module())


def test_c_source_build_calls_the_user_symbol_without_a_fortran_adapter(source_build):
    result, module = source_build

    assert module.native_add(np.float64(1.5), np.float64(2.0)) == np.float64(3.5)
    assert module.native_scale(np.array(3.0, dtype=np.float64)) == np.float64(6.0)
    assert all(path.suffix != ".f90" for path in result.generated_sources)
    assert "double native_add(double left, double right);" in _binding(result)


def test_c_source_directives_are_expanded_before_the_wrapper_reads_declarations(source_build):
    """A C wrapper build preprocesses its sources like the inspection routes."""
    result, module = source_build

    assert module.scaled(np.float64(2.0)) == np.float64(6.0)
    output = module.total(np.uintp(4))
    assert type(output) is type(np.uintp(0))
    assert output == np.uintp(5)
    assert module.total(output) == np.uintp(6)
    # A typedef-written parameter declares the exact underlying builtin, which
    # the binding can always spell; the typedef itself is source provenance.
    assert "unsigned long total(unsigned long value);" in _binding(result)


def test_c_typedef_declarations_resolve_to_their_exact_underlying_builtin(source_build):
    """A user typedef only the source's headers define cannot enter the binding."""
    result, module = source_build
    binding = _binding(result)

    assert "long alias_step(long value);" in binding
    assert "long alias_offset(const long * value);" in binding
    assert "my_int" not in binding
    assert module.alias_step(np.int64(4)) == np.int64(5)
    assert module.alias_offset(np.array(4, dtype=np.int64)) == np.int64(5)


def test_default_c_pointer_writes_back_into_caller_owned_runtime_rank_storage(source_build):
    """The ``T *`` default passes caller-owned storage of whatever rank arrived."""
    _result, module = source_build

    value = np.array(3.0, dtype=np.float64)
    assert module.twice(value) is None
    assert value == np.float64(3.0) * 2

    values = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float64)
    module.twice(values)
    assert values[0, 0] == np.float64(2.0)

    assert "Rank: 0..15" in module.twice.__doc__
    assert "Layout: Any strides" in module.twice.__doc__
    assert "update the supplied storage in place" in module.twice.__doc__
    with pytest.raises(TypeError, match=r"numpy\.float64 for argument value"):
        module.twice(np.float64(3.0))


def test_c_native_language_is_explicit_for_a_source_free_pyi_contract(contract_build):
    result, module = contract_build
    binding = _binding(result)

    assert module.add(np.float64(4.0), np.float64(2.5)) == np.float64(6.5)
    assert module.increment(np.int32(4)) == np.int32(5)
    assert result.native_build_plan.compilation_units[0].language == "c"
    assert result.manifest["extension"]["native_language"] == "c"
    assert result.manifest["compiler"]["c_flags"] == []
    # A contract needs ``@bind`` only when the Python and native names differ.
    assert module.bump(np.int32(4)) == np.int32(5)
    assert "int32_t bump(int32_t value);" in binding
    assert "result = bump(bound_value);" in binding


def test_c_contract_reuses_direct_projection_value_address_literal_and_hidden_output_paths(contract_build):
    result, module = contract_build
    binding = _binding(result)

    assert module.projected(np.int32(2), np.int32(3)) == np.int32(325)
    assert module.projected_output(np.int32(2), np.int32(3)) == np.int32(325)
    assert "int32_t projected_native(int32_t right, int32_t * left, int32_t literal_2);" in binding
    assert (
        "void projected_output_native(int32_t right, int32_t * left, int32_t literal_2, int32_t * output);" in binding
    )


def test_reordered_c_projection_keeps_each_argument_its_own_declared_type(contract_build):
    """A route-neutral reorder must not resolve one argument against another."""
    result, module = contract_build

    assert module.combine(np.float64(2.5), np.int32(4)) == np.float64(10.0)
    assert "double combine(int32_t count, double scale);" in _binding(result)
    with pytest.raises(TypeError, match=r"numpy\.float64 or rank-zero array for argument scale"):
        module.combine(np.int32(4), np.int32(4))


def test_source_free_c_contract_keeps_the_standard_typedef_it_names(contract_build):
    """``SizeT`` is a contract spelling, so the binding declares ``size_t``."""
    result, module = contract_build
    binding = _binding(result)

    assert "size_t total(size_t value);" in binding
    assert "#include <stddef.h>" in binding
    assert module.total(np.uint64(4)) == np.uint64(5)


def test_c_contract_supports_private_candidates_behind_one_overloaded_name(contract_build):
    """An unexported concrete procedure is a shared contract feature, not a C limit."""
    _result, module = contract_build

    assert module.scale(np.int32(21)) == np.int32(42)
    assert module.scale(np.float64(1.5)) == np.float64(3.0)
    published = {name for name in dir(module) if not name.startswith("_")}
    assert "scale" in published
    assert not {"scale_integer", "scale_real"} & published
