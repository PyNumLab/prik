"""Standalone external procedure parity and contract validation."""

from __future__ import annotations

import importlib
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.pyi_fixtures import assert_generated_pyi_package_matches_fixture
from tests.fortran._support.wrapper_build import (
    REPO_ROOT,
    _sole_native_module,
    wrapper_source,
)
from prik import build_pyi_extension
from prik.pipeline.build import build_fortran_extension

FIXED_EXTERNAL = wrapper_source("fixed_external.f")
FREE_EXTERNAL = wrapper_source("free_external.f90")
EXTERNAL_BUNDLE = wrapper_source("external_bundle.f90")
C_ORDER_FLAT_BUFFER = wrapper_source("c_order_flat_buffer.f90")
BLAS_LIKE_FILENAMES = ("daxpy_like.f90", "ddot_like.f90")
BLAS_LIKE_SOURCES = tuple(wrapper_source(filename) for filename in BLAS_LIKE_FILENAMES)
BASIC_SOURCE = REPO_ROOT / "tests/fortran/source_parsing/parsing/fixtures/general/basic_subroutine.f90"
CONTRACT_FIXTURES = Path(__file__).parent / "fixtures" / "external" / "contracts"
C_ORDER_FLAT_CONTRACT = (
    REPO_ROOT
    / "tests/fortran/arrays/end_to_end/fixtures/baseline/edited_contracts/c_order_flat_buffer/c_order_flat_buffer.pyi"
)
pytestmark = pytest.mark.fortran_end_to_end


def _compiler() -> str:
    compiler = shutil.which("gfortran")
    if compiler is None:
        pytest.skip("gfortran is required for standalone external wrapper tests")
    return compiler


def _copy_sources(sources: tuple[Path, ...], workdir: Path) -> tuple[Path, ...]:
    workdir.mkdir(parents=True, exist_ok=True)
    copied = []
    for source in sources:
        target = workdir / source.name
        shutil.copyfile(source, target)
        copied.append(target)
    return tuple(copied)


def _compile_native_objects(sources: tuple[Path, ...], native_dir: Path) -> tuple[Path, ...]:
    native_dir.mkdir(parents=True, exist_ok=True)
    objects = []
    for source in sources:
        native_object = native_dir / f"{source.stem}.o"
        subprocess.run(
            [
                _compiler(),
                "-fPIC",
                "-c",
                str(source),
                "-o",
                str(native_object),
                "-J",
                str(native_dir),
                "-I",
                str(native_dir),
            ],
            check=True,
        )
        objects.append(native_object)
    return tuple(objects)


def _generated_contract_fixture(case: str) -> Path:
    return CONTRACT_FIXTURES / case


def _generate_contract(input_paths: tuple[Path, ...], package: Path, expected_package: Path | None = None) -> Path:
    language_args = ["--language", "fortran"] if any(path.is_dir() for path in input_paths) else []
    subprocess.run(
        [
            sys.executable,
            "-m",
            "prik",
            "generate",
            "--pyi",
            *(str(path) for path in input_paths),
            *language_args,
            "--out",
            str(package),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    if expected_package is not None:
        assert_generated_pyi_package_matches_fixture(package, expected_package)
    return package / "__init__.pyi"


def _import_extension(module_name: str, build_dir: Path):
    sys.modules.pop(module_name, None)
    sys.path.insert(0, str(build_dir))
    try:
        return importlib.import_module(module_name)
    finally:
        sys.path.remove(str(build_dir))


def _build_source(sources: tuple[Path, ...], build_dir: Path):
    result = build_fortran_extension(sources, output_dir=build_dir)
    return _import_extension(result.module_name, build_dir), result


def _build_generated_contract(
    sources: tuple[Path, ...],
    workdir: Path,
    *,
    output_name: str,
    contract_input: tuple[Path, ...] | None = None,
    expected_package: Path | None = None,
):
    entry = _generate_contract(contract_input or sources, workdir / "contracts", expected_package)
    native_objects = _compile_native_objects(sources, workdir / "native")
    result = build_pyi_extension(
        entry,
        native_objects=native_objects,
        native_include_dirs=[native_objects[0].parent],
        output_name=output_name,
        output_dir=workdir / "pyi_build",
    )
    return _import_extension(result.module_name, result.output_dir), result, entry


def _standalone_module_for_mode(
    source: Path,
    build_mode: str,
    tmp_path: Path,
):
    sources = _copy_sources((source,), tmp_path / "sources")
    if build_mode == "source":
        module, _result = _build_source(sources, tmp_path / "source_build")
        return module
    module, _result, _entry = _build_generated_contract(
        sources,
        tmp_path,
        output_name=source.stem,
        expected_package=_generated_contract_fixture(source.stem),
    )
    return module


@pytest.fixture
def fixed_external_module(pyi_parity_build_mode: str, tmp_path: Path):
    return _standalone_module_for_mode(FIXED_EXTERNAL, pyi_parity_build_mode, tmp_path)


@pytest.fixture
def free_external_module(pyi_parity_build_mode: str, tmp_path: Path):
    return _standalone_module_for_mode(FREE_EXTERNAL, pyi_parity_build_mode, tmp_path)


@pytest.fixture
def bundled_external_module(pyi_parity_build_mode: str, tmp_path: Path):
    sources = _copy_sources((EXTERNAL_BUNDLE,), tmp_path / "sources")
    if pyi_parity_build_mode == "source":
        module, _result = _build_source(sources, tmp_path / "source_build")
        return module
    module, _result, _entry = _build_generated_contract(
        sources,
        tmp_path,
        output_name=EXTERNAL_BUNDLE.stem,
        expected_package=_generated_contract_fixture(EXTERNAL_BUNDLE.stem),
    )
    return module


def test_fixed_form_standalone_external_runtime_parity(fixed_external_module):
    assert fixed_external_module.fixed_add(np.int32(4)) == (np.int32(5), np.int32(4))


def test_free_form_standalone_external_runtime_parity(free_external_module):
    assert free_external_module.free_square(np.int32(5)) == np.int32(25)


def test_one_source_with_several_standalone_externals_exports_each_at_root(bundled_external_module):
    assert bundled_external_module.triple_value(np.int32(4)) == np.int32(12)
    assert bundled_external_module.offset_value(np.int32(4)) == np.int32(14)


def test_generated_external_contracts_are_non_empty_root_fragments(tmp_path: Path):
    for source in (FIXED_EXTERNAL, FREE_EXTERNAL, EXTERNAL_BUNDLE):
        copied = _copy_sources((source,), tmp_path / source.stem)
        entry = _generate_contract(
            copied,
            tmp_path / f"{source.stem}_contracts",
            _generated_contract_fixture(source.stem),
        )
        text = entry.read_text(encoding="utf-8")

        assert entry.name == "__init__.pyi"
        assert text.strip()
        assert text.count("@external") == len([line for line in text.splitlines() if line.startswith("def ")])
        assert sorted(path.name for path in entry.parent.glob("*.pyi")) == ["__init__.pyi"]


def test_classic_external_bridge_uses_implicit_declaration_and_no_module_use(tmp_path: Path):
    sources = _copy_sources((FREE_EXTERNAL,), tmp_path / "sources")
    module, result, entry = _build_generated_contract(
        sources,
        tmp_path,
        output_name=FREE_EXTERNAL.stem,
        expected_package=_generated_contract_fixture(FREE_EXTERNAL.stem),
    )

    bridge = (result.output_dir / f"bind_c_{result.module_name}_wrapper.f90").read_text(encoding="utf-8").lower()
    assert module.free_square(np.int32(3)) == np.int32(9)
    assert entry.read_text(encoding="utf-8").startswith(
        "from prik.contracts import Addr, Arg, Int32, external, native_call\n\n@external\n"
    )
    assert "integer(c_int32_t), external :: free_square" in bridge
    assert "function free_square(" not in bridge
    assert "result = free_square(value)" in bridge
    assert "private\n" not in bridge
    assert "public :: bind_c_free_square" not in bridge
    assert "use free_external" not in bridge


def test_module_procedure_bridge_uses_native_module_scope(tmp_path: Path):
    source = _copy_sources((BASIC_SOURCE,), tmp_path / "sources")
    entry = _generate_contract(source, tmp_path / "contracts", _generated_contract_fixture(BASIC_SOURCE.stem))
    native_objects = _compile_native_objects(source, tmp_path / "native")
    result = build_pyi_extension(
        entry,
        native_objects=native_objects,
        native_include_dirs=[native_objects[0].parent],
        output_dir=tmp_path / "pyi_build",
    )

    bridge = (result.output_dir / f"bind_c_{result.module_name}_wrapper.f90").read_text(encoding="utf-8").lower()
    assert "use m1, only:" in bridge
    assert "add1" in bridge


def test_handwritten_c_order_flat_contract_passes_rank_preserving_bridge_view(tmp_path: Path):
    source = _copy_sources((C_ORDER_FLAT_BUFFER,), tmp_path / "sources")
    native_objects = _compile_native_objects(source, tmp_path / "native")
    result = build_pyi_extension(
        C_ORDER_FLAT_CONTRACT,
        native_objects=native_objects,
        output_name="c_order_flat_api",
        output_dir=tmp_path / "pyi_build",
    )
    module = _import_extension(result.module_name, result.output_dir)
    bridge = (result.output_dir / f"bind_c_{result.module_name}_wrapper.f90").read_text(encoding="utf-8")
    compact_bridge = "".join(bridge.lower().split())

    values = np.array([[1.0, 2.0, 3.0], [10.0, 20.0, 30.0]], dtype=np.float64, order="C")
    result_values = np.zeros(values.shape[0], dtype=np.float64)

    module.row_sums_c(np.int32(values.shape[0]), values, result_values)

    np.testing.assert_allclose(result_values, [6.0, 60.0])
    assert "external::row_sums_c" in compact_bridge
    assert "real(c_double),pointer,contiguous,dimension(:,:)::values" in compact_bridge

    with pytest.raises(TypeError, match=r"expected ordering \(C\)"):
        module.row_sums_c(np.int32(values.shape[0]), np.asfortranarray(values), result_values)

    strided = np.zeros((values.shape[0], values.shape[1] * 2), dtype=np.float64, order="C")[:, ::2]
    with pytest.raises(TypeError, match=r"expected ordering \(C\)"):
        module.row_sums_c(np.int32(values.shape[0]), strided, result_values)


def test_handwritten_fortran_order_flat_contract_flattens_the_final_python_axes(tmp_path: Path):
    source_dir = tmp_path / "sources"
    source_dir.mkdir()
    source = source_dir / "column_sums_f.f90"
    source.write_text(
        """
subroutine column_sums_f(rows, columns, values, result)
  integer, intent(in) :: rows
  integer, intent(in) :: columns
  double precision, intent(in) :: values(rows, *)
  double precision, intent(out) :: result(*)
  integer :: column

  do column = 1, columns
    result(column) = sum(values(:, column))
  end do
end subroutine column_sums_f

subroutine bump_storage(value)
  integer, intent(inout) :: value
  value = value + 1
end subroutine bump_storage

subroutine make_storage(value)
  integer, intent(out) :: value
  value = 42
end subroutine make_storage

function storage_value() result(value)
  integer :: value
  value = 43
end function storage_value
""",
        encoding="utf-8",
    )
    contract = tmp_path / "column_sums_f.pyi"
    contract.write_text(
        """from prik.contracts import Addr, Arg, Flat, Float64, Int32, Return, external, native_call

@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Arg(3)])
def column_sums_f(
    rows: Int32,
    columns: Int32,
    values: Float64[rows, Flat],
    result: Float64[Flat],
) -> None: ...

@external
def bump_storage(value: Int32[()]) -> None: ...

@external
@native_call([Return("value", 0)])
def make_storage() -> Int32[()]: ...

@external
def storage_value() -> Int32[()]: ...
""",
        encoding="utf-8",
    )
    native_objects = _compile_native_objects((source,), tmp_path / "native")
    built = build_pyi_extension(
        contract,
        native_objects=native_objects,
        output_name="fortran_order_flat_api",
        output_dir=tmp_path / "pyi_build",
    )
    module = _import_extension(built.module_name, built.output_dir)

    values = np.arange(24, dtype=np.float64).reshape((3, 2, 4), order="F")
    result = np.empty(8, dtype=np.float64)
    module.column_sums_f(np.int32(3), np.int32(8), values, result)

    expected = values.reshape((3, 8), order="F").sum(axis=0)
    np.testing.assert_allclose(result, expected)
    with pytest.raises(TypeError, match=r"expected ordering \(F\)"):
        module.column_sums_f(np.int32(3), np.int32(8), np.ascontiguousarray(values), result)
    with pytest.raises(TypeError, match="incompatible shape at axis 0"):
        module.column_sums_f(np.int32(2), np.int32(8), values, result)

    storage = np.array(8, dtype=np.int32)
    assert module.bump_storage(storage) is None
    assert storage[()] == np.int32(9)
    assert module.make_storage()[()] == np.int32(42)
    assert module.storage_value()[()] == np.int32(43)


def test_optional_flat_contracts_preserve_present_and_absent_calls(tmp_path: Path):
    source_dir = tmp_path / "sources"
    source_dir.mkdir()
    source = source_dir / "optional_flat.f90"
    source.write_text(
        """
module optional_flat
contains
  subroutine maybe_scale_f(rows, blocks, values)
    integer, intent(in) :: rows
    integer, intent(in) :: blocks
    double precision, intent(inout), optional :: values(rows, *)
    if (present(values)) values(:, 1:blocks) = values(:, 1:blocks) * 2.0d0
  end subroutine maybe_scale_f

  subroutine maybe_scale_c(blocks, columns, values)
    integer, intent(in) :: blocks
    integer, intent(in) :: columns
    double precision, intent(inout), optional :: values(columns, *)
    if (present(values)) values(:, 1:blocks) = values(:, 1:blocks) * 3.0d0
  end subroutine maybe_scale_c
end module optional_flat
""",
        encoding="utf-8",
    )
    contract = tmp_path / "optional_flat.pyi"
    contract.write_text(
        """from prik.contracts import Annotated, Flat, Float64, Int32, ORDER_C

def maybe_scale_f(
    rows: Int32,
    blocks: Int32,
    values: Float64[rows, Flat] | None = ...,
) -> None: ...

def maybe_scale_c(
    blocks: Int32,
    columns: Int32,
    values: Annotated[Float64[Flat, columns], ORDER_C] | None = ...,
) -> None: ...
""",
        encoding="utf-8",
    )
    native_objects = _compile_native_objects((source,), tmp_path / "native")
    built = build_pyi_extension(
        contract,
        native_objects=native_objects,
        native_include_dirs=[native_objects[0].parent],
        output_dir=tmp_path / "pyi_build",
    )
    module = _sole_native_module(_import_extension(built.module_name, built.output_dir))

    fortran_values = np.arange(24, dtype=np.float64).reshape((3, 2, 4), order="F")
    module.maybe_scale_f(np.int32(3), np.int32(8), fortran_values)
    np.testing.assert_allclose(
        fortran_values,
        np.arange(24, dtype=np.float64).reshape((3, 2, 4), order="F") * 2.0,
    )
    assert module.maybe_scale_f(np.int32(3), np.int32(8)) is None

    c_values = np.arange(24, dtype=np.float64).reshape((2, 3, 4), order="C")
    module.maybe_scale_c(np.int32(6), np.int32(4), c_values)
    np.testing.assert_allclose(
        c_values,
        np.arange(24, dtype=np.float64).reshape((2, 3, 4), order="C") * 3.0,
    )
    assert module.maybe_scale_c(np.int32(6), np.int32(4)) is None


def test_compact_blas_like_folder_generates_one_external_entry_and_preserves_separate_objects(tmp_path: Path):
    copied_sources = _copy_sources(BLAS_LIKE_SOURCES, tmp_path / "sources")
    source_module, source_result = _build_source(copied_sources, tmp_path / "source_build")

    x = np.array([1.0, 2.0, 3.0], dtype=np.float64)
    y_source = np.array([10.0, 20.0, 30.0], dtype=np.float64)
    source_module.daxpy_like(np.int32(x.size), np.float64(2.0), x, y_source)
    np.testing.assert_allclose(y_source, [12.0, 24.0, 36.0])
    source_dot = source_module.ddot_like(np.int32(x.size), x, y_source)

    generated_module, generated_result, entry = _build_generated_contract(
        copied_sources,
        tmp_path,
        output_name=source_result.module_name,
        contract_input=(tmp_path / "sources",),
        expected_package=_generated_contract_fixture("blas_like"),
    )

    assert sorted(path.relative_to(entry.parent).as_posix() for path in entry.parent.rglob("*.pyi")) == ["__init__.pyi"]
    text = entry.read_text(encoding="utf-8")
    assert "@external\n@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Arg(3)])\ndef daxpy_like(" in text
    assert "@external\n@native_call([Addr(Arg(0)), Arg(1), Arg(2)])\ndef ddot_like(" in text
    assert generated_result.native_build_plan.to_dict()["link_items"] == [
        {"kind": "object", "path": str(tmp_path / "native" / "daxpy_like.o")},
        {"kind": "object", "path": str(tmp_path / "native" / "ddot_like.o")},
    ]

    y_generated = np.array([10.0, 20.0, 30.0], dtype=np.float64)
    generated_module.daxpy_like(np.int32(x.size), np.float64(2.0), x, y_generated)
    np.testing.assert_allclose(y_generated, y_source)
    assert source_dot == generated_module.ddot_like(np.int32(x.size), x, y_generated)


def test_package_entry_rejects_non_external_root_declaration_before_codegen(tmp_path: Path):
    source = _copy_sources((FREE_EXTERNAL,), tmp_path / "sources")
    entry = _generate_contract(source, tmp_path / "contracts", _generated_contract_fixture(FREE_EXTERNAL.stem))
    entry.write_text(entry.read_text(encoding="utf-8").replace("@external\n", ""), encoding="utf-8")
    native_objects = _compile_native_objects(source, tmp_path / "native")
    build_dir = tmp_path / "pyi_build"

    with pytest.raises(ValueError, match="Package entry contracts cannot contain native module declarations"):
        build_pyi_extension(entry, native_objects=native_objects, output_dir=build_dir)

    assert not build_dir.exists()


def test_namespace_imported_module_rejects_external_marker_before_codegen(tmp_path: Path):
    source = _copy_sources((BASIC_SOURCE,), tmp_path / "sources")
    entry = _generate_contract(source, tmp_path / "contracts", _generated_contract_fixture(BASIC_SOURCE.stem))
    leaf = entry.parent / "m1.pyi"
    leaf_text = leaf.read_text(encoding="utf-8").replace(
        "from prik.contracts import ",
        "from prik.contracts import external, ",
        1,
    )
    leaf.write_text(leaf_text.replace("def add1", "@external\ndef add1"), encoding="utf-8")
    native_objects = _compile_native_objects(source, tmp_path / "native")
    build_dir = tmp_path / "pyi_build"

    with pytest.raises(ValueError, match="cannot contain @external declarations"):
        build_pyi_extension(
            entry,
            native_objects=native_objects,
            native_include_dirs=[native_objects[0].parent],
            output_dir=build_dir,
        )

    assert not build_dir.exists()
