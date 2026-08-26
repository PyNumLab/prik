"""Compiled direct-C primitive scalar evidence."""

import shutil
from pathlib import Path

import numpy as np
import pytest

from prik import build_c_extension, build_pyi_extension
from tests.c._support.runtime import sole_native_module


@pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")
def test_c_source_build_calls_renamed_user_symbol_without_a_fortran_adapter(tmp_path: Path):
    source = tmp_path / "scalar_api.c"
    source.write_text(
        """double native_add(double left, double right) { return left + right; }
double native_scale(double *value) { *value *= 2.0; return *value; }
""",
        encoding="utf-8",
    )

    result = build_c_extension(source, output_dir=tmp_path / "build", output_name="c_scalar_api")
    module = sole_native_module(result.import_module())

    assert module.native_add(np.float64(1.5), np.float64(2.0)) == np.float64(3.5)
    assert module.native_scale(np.float64(3.0)) == np.float64(6.0)
    assert all(path.suffix != ".f90" for path in result.generated_sources)
    binding = next(path for path in result.generated_sources if path.suffix == ".c")
    text = binding.read_text(encoding="utf-8")
    assert "double native_add(double left, double right);" in text
    assert "native_add(" in text


@pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")
def test_c_native_language_is_explicit_for_a_source_free_pyi_contract(tmp_path: Path):
    contract = tmp_path / "contract.pyi"
    contract.write_text(
        """from prik.contracts import Float64, Int, bind

@bind("native_add")
def add(left: Float64, right: Float64) -> Float64: ...

@bind("native_increment")
def increment(value: Int) -> Int: ...
""",
        encoding="utf-8",
    )
    source = tmp_path / "implementation.c"
    source.write_text(
        """double native_add(double left, double right) { return left + right; }
int native_increment(int value) { return value + 1; }
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

    assert module.add(np.float64(4.0), np.float64(2.5)) == np.float64(6.5)
    assert module.increment(np.int32(4)) == np.int32(5)
    assert result.native_build_plan.compilation_units[0].language == "c"
    assert result.manifest["extension"]["native_language"] == "c"
    assert result.manifest["compiler"]["c_flags"] == []


@pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")
def test_c_contract_defaults_matching_python_name_to_native_symbol(tmp_path: Path):
    """A C contract needs ``@bind`` only when the names differ."""
    contract = tmp_path / "matching_name.pyi"
    contract.write_text(
        """from prik.contracts import Int32

def increment(value: Int32) -> Int32: ...
""",
        encoding="utf-8",
    )
    source = tmp_path / "matching_name.c"
    source.write_text("int increment(int value) { return value + 1; }\n", encoding="utf-8")

    result = build_pyi_extension(
        contract,
        native_language="c",
        native_c_sources=[source],
        output_dir=tmp_path / "build",
    )
    module = sole_native_module(result.import_module())

    assert module.increment(np.int32(4)) == np.int32(5)
    binding = next(path.read_text(encoding="utf-8") for path in result.generated_sources if path.suffix == ".c")
    assert "int32_t increment(int32_t value);" in binding
    assert "result = increment(bound_value);" in binding


@pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")
def test_c_contract_reuses_direct_projection_value_address_literal_and_hidden_output_paths(tmp_path: Path):
    contract = tmp_path / "projection.pyi"
    contract.write_text(
        """from prik.contracts import Addr, Arg, Int32, Return, Value, bind, native_call

@bind("projected_native")
@native_call([Value(Arg(1)), Addr(Arg(0)), Int32(5)])
def projected(left: Int32, right: Int32) -> Int32: ...

@bind("projected_output_native")
@native_call([Value(Arg(1)), Addr(Arg(0)), Int32(5), Return("output", 0)])
def projected_output(left: Int32, right: Int32) -> Int32: ...
""",
        encoding="utf-8",
    )
    source = tmp_path / "projection.c"
    source.write_text(
        """int projected_native(int right, int *left, int bias) { return 100 * right + 10 * *left + bias; }
void projected_output_native(int right, int *left, int bias, int *output) {
    *output = 100 * right + 10 * *left + bias;
}
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

    assert module.projected(np.int32(2), np.int32(3)) == np.int32(325)
    assert module.projected_output(np.int32(2), np.int32(3)) == np.int32(325)
    binding = next(path.read_text(encoding="utf-8") for path in result.generated_sources if path.suffix == ".c")
    assert "int32_t projected_native(int32_t right, int32_t * left, int32_t literal_2);" in binding
    assert (
        "void projected_output_native(int32_t right, int32_t * left, int32_t literal_2, int32_t * output);" in binding
    )


@pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")
def test_reordered_c_projection_keeps_each_argument_its_own_declared_type(tmp_path: Path):
    """A route-neutral reorder must not resolve one argument against another."""
    contract = tmp_path / "reordered.pyi"
    contract.write_text(
        """from prik.contracts import Arg, Float64, Int32, native_call

@native_call([Arg(1), Arg(0)])
def combine(scale: Float64, count: Int32) -> Float64: ...
""",
        encoding="utf-8",
    )
    source = tmp_path / "reordered.c"
    source.write_text("double combine(int count, double scale) { return count * scale; }\n", encoding="utf-8")

    result = build_pyi_extension(
        contract,
        native_language="c",
        native_c_sources=[source],
        output_dir=tmp_path / "build",
    )
    module = sole_native_module(result.import_module())
    binding = next(path.read_text(encoding="utf-8") for path in result.generated_sources if path.suffix == ".c")

    assert module.combine(np.float64(2.5), np.int32(4)) == np.float64(10.0)
    assert "double combine(int32_t count, double scale);" in binding
    with pytest.raises(TypeError, match=r"numpy\.float64 for argument scale"):
        module.combine(np.int32(4), np.int32(4))


@pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")
def test_c_source_directives_are_expanded_before_the_wrapper_reads_declarations(tmp_path: Path):
    """A C wrapper build preprocesses its sources like the inspection routes."""
    source = tmp_path / "directives.c"
    source.write_text(
        """#include <stddef.h>
#define PRIK_TEST_GAIN 3.0

double scaled(double value) { return value * PRIK_TEST_GAIN; }
size_t total(size_t value) { return value + 1; }
""",
        encoding="utf-8",
    )

    result = build_c_extension(source, output_dir=tmp_path / "build", output_name="c_directives")
    module = sole_native_module(result.import_module())
    binding = next(path.read_text(encoding="utf-8") for path in result.generated_sources if path.suffix == ".c")

    assert module.scaled(np.float64(2.0)) == np.float64(6.0)
    output = module.total(np.uintp(4))
    assert type(output) is type(np.uintp(0))
    assert output == np.uintp(5)
    assert module.total(output) == np.uintp(6)
    # A typedef-written parameter declares the exact underlying builtin, which
    # the binding can always spell; the typedef itself is source provenance.
    assert "unsigned long total(unsigned long value);" in binding


@pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")
def test_default_c_pointer_scalar_documents_that_native_mutation_is_discarded(tmp_path: Path):
    """The conservative ``T *`` default passes a call-local scalar address."""
    source = tmp_path / "discarded.c"
    source.write_text("void twice(double *value) { *value *= 2.0; }\n", encoding="utf-8")

    result = build_c_extension(source, output_dir=tmp_path / "build", output_name="c_discarded")
    module = sole_native_module(result.import_module())

    value = np.float64(3.0)
    assert module.twice(value) is None
    assert value == np.float64(3.0)
    assert "The update is not visible in Python." in module.twice.__doc__
    assert "update the supplied storage in place" not in module.twice.__doc__


@pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")
def test_c_typedef_declarations_resolve_to_their_exact_underlying_builtin(tmp_path: Path):
    """A user typedef only the source's headers define cannot enter the binding."""
    source = tmp_path / "aliases.c"
    source.write_text(
        """#include <stddef.h>
typedef long my_int;
my_int alias_step(my_int value) { return value + 1; }
ptrdiff_t alias_offset(const ptrdiff_t *value) { return *value + 1; }
""",
        encoding="utf-8",
    )

    result = build_c_extension(source, output_dir=tmp_path / "build", output_name="c_aliases")
    module = sole_native_module(result.import_module())
    binding = next(path.read_text(encoding="utf-8") for path in result.generated_sources if path.suffix == ".c")

    assert "long alias_step(long value);" in binding
    assert "long alias_offset(const long * value);" in binding
    assert "my_int" not in binding
    assert module.alias_step(np.int64(4)) == np.int64(5)
    assert module.alias_offset(np.int64(4)) == np.int64(5)


@pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")
def test_source_free_c_contract_keeps_the_standard_typedef_it_names(tmp_path: Path):
    """``SizeT`` is a contract spelling, so the binding declares ``size_t``."""
    contract = tmp_path / "sizes.pyi"
    contract.write_text(
        """from prik.contracts import SizeT

def total(value: SizeT) -> SizeT: ...
""",
        encoding="utf-8",
    )
    source = tmp_path / "sizes.c"
    source.write_text(
        """#include <stddef.h>
size_t total(size_t value) { return value + 1; }
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

    assert "size_t total(size_t value);" in binding
    assert "#include <stddef.h>" in binding
    assert module.total(np.uint64(4)) == np.uint64(5)


@pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")
def test_c_contract_supports_private_candidates_behind_one_overloaded_name(tmp_path: Path):
    """An unexported concrete procedure is a shared contract feature, not a C limit."""
    contract = tmp_path / "overloads.pyi"
    contract.write_text(
        """from prik.contracts import Float64, Int32, overload, private

@private
def scale_integer(value: Int32) -> Int32: ...

@private
def scale_real(value: Float64) -> Float64: ...

@overload("scale_integer")
def scale(value: Int32) -> Int32: ...

@overload("scale_real")
def scale(value: Float64) -> Float64: ...
""",
        encoding="utf-8",
    )
    source = tmp_path / "overloads.c"
    source.write_text(
        """int scale_integer(int value) { return value * 2; }
double scale_real(double value) { return value * 2.0; }
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

    assert module.scale(np.int32(21)) == np.int32(42)
    assert module.scale(np.float64(1.5)) == np.float64(3.0)
    assert [name for name in dir(module) if not name.startswith("_")] == ["scale"]
