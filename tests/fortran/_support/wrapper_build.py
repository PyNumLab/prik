"""Shared compilation, import, and runtime assertions for Fortran features."""

import gc
import importlib
import json
import os
import shlex
import shutil
import subprocess
import sys
from collections.abc import Sequence
from functools import cache
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType

import numpy as np
import pytest

from tests.fortran._support.pyi_fixtures import assert_generated_pyi_package_matches_fixture
from tests.fortran._support.fmath_cases import fmath_cases
from prik import build_pyi_extension
from prik.compiling.objects import ObjectFile
from prik.parsers.fortran.parser import parse_fortran_project
from prik.pipeline.build import (
    NativeBuildPlan,
    _apply_source_python_exports,
    _build_rendered_wrapper_extension,
    _fortran_source_for_pipeline,
    _merge_wrapper_modules,
    _new_compiler,
)
from prik.pipeline.preprocessing import PreprocessingConfig
from prik.pipeline.build import build_fortran_extension
from prik.runtime.handles import AllocatableArray
from prik.semantics.fortran2ir import fortran_project_to_semantic_modules
from prik.semantics.policy_completion import complete_semantic_policies
from prik.codegen import WrapperCodeGenerator, WrapperPlanner

REPO_ROOT = Path(__file__).resolve().parents[3]
WRAPPER_TEST_ROOT = Path(__file__).resolve().parent
WRAPPER_SOURCE_PATHS = {
    "c_order_flat_buffer.f90": REPO_ROOT
    / "tests/fortran/arrays/end_to_end/fixtures/baseline/native/c_order_flat_buffer.f90",
    "daxpy_like.f90": REPO_ROOT / "tests/fortran/functions/end_to_end/fixtures/external/native/daxpy_like.f90",
    "ddot_like.f90": REPO_ROOT / "tests/fortran/functions/end_to_end/fixtures/external/native/ddot_like.f90",
    "external_bundle.f90": REPO_ROOT
    / "tests/fortran/functions/end_to_end/fixtures/external/native/external_bundle.f90",
    "fbind_value_f90.f90": REPO_ROOT
    / "tests/fortran/data_types/end_to_end/fixtures/baseline/native/fbind_value_f90.f90",
    "fixed_external.f": REPO_ROOT / "tests/fortran/functions/end_to_end/fixtures/external/native/fixed_external.f",
    "fmath.f": REPO_ROOT / "tests/fortran/data_types/end_to_end/fixtures/baseline/native/fmath.f",
    "fmath_arrays.f": REPO_ROOT / "tests/fortran/arrays/end_to_end/fixtures/baseline/native/fmath_arrays.f",
    "fmath_arrays_f90.f90": REPO_ROOT / "tests/fortran/arrays/end_to_end/fixtures/baseline/native/fmath_arrays_f90.f90",
    "fmath_f90.f90": REPO_ROOT / "tests/fortran/data_types/end_to_end/fixtures/baseline/native/fmath_f90.f90",
    "fnaming_f90.f90": REPO_ROOT
    / "tests/fortran/pyi_contracts/exports_and_modules/end_to_end/fixtures/visibility/native/fnaming_f90.f90",
    "fopenmp_runtime_f90.f90": REPO_ROOT
    / "tests/fortran/error_handling/end_to_end/fixtures/runtime/native/fopenmp_runtime_f90.f90",
    "free_external.f90": REPO_ROOT / "tests/fortran/functions/end_to_end/fixtures/external/native/free_external.f90",
    "fruntime_recursion_f90.f90": REPO_ROOT
    / "tests/fortran/error_handling/end_to_end/fixtures/runtime/native/fruntime_recursion_f90.f90",
}


@cache
def wrapper_source(filename: str) -> Path:
    try:
        return WRAPPER_SOURCE_PATHS[filename]
    except KeyError as exc:
        raise FileNotFoundError(f"No final Fortran feature owns wrapper fixture {filename!r}") from exc


def _assert_fmath_examples(module):
    cases = fmath_cases()
    missing = sorted(name.lower() for name, _, _ in cases if not hasattr(module, name.lower()))
    assert missing == []

    for name, args, expected in cases:
        public_name = name.lower()
        actual, *replacements = getattr(module, public_name)(*args)
        assert len(replacements) == len(args), public_name
        for replacement, argument in zip(replacements, args, strict=True):
            np.testing.assert_equal(replacement, argument, err_msg=public_name)
        if isinstance(expected, bool):
            assert bool(actual) is expected, public_name
        elif isinstance(expected, int):
            assert actual == expected, public_name
        else:
            np.testing.assert_allclose(actual, expected, rtol=1e-6, atol=1e-6, err_msg=public_name)


def _sole_native_module(module):
    children = [
        value
        for value in vars(module).values()
        if isinstance(value, ModuleType) and value.__name__.startswith(f"{module.__name__}.")
    ]
    return children[0] if len(children) == 1 else module


def _run_captured_command(
    command: Sequence[str],
    *,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a test build command while preserving actionable failure output."""
    result = subprocess.run(command, capture_output=True, text=True, check=False, cwd=cwd)
    if result.returncode:
        stdout = result.stdout.rstrip() or "<empty>"
        stderr = result.stderr.rstrip() or "<empty>"
        raise RuntimeError(
            f"Captured command failed with exit code {result.returncode}:\n"
            f"{shlex.join(command)}\n"
            f"stdout:\n{stdout}\n"
            f"stderr:\n{stderr}"
        )
    return result


def _build_and_import(source_template: Path, workdir: Path, expected_generated_sources: set[str]):
    source = workdir / source_template.name
    module_name = source_template.stem
    shutil.copyfile(source_template, source)

    cmd = [
        sys.executable,
        "-m",
        "prik",
        str(source),
        "--out-dir",
        str(workdir),
        "--compiler",
        _compiler(),
        "--json",
    ]
    result = _run_captured_command(cmd, cwd=workdir)
    payload = json.loads(result.stdout)

    shared_library = Path(payload["shared_library"])
    assert shared_library.exists()
    assert Path(payload["output_dir"]) == workdir
    assert shared_library.parent == workdir
    assert {Path(path).name for path in payload["generated_sources"]} == expected_generated_sources
    generated_files = [Path(path) for path in payload["generated_files"]]
    assert any(path.name == "prik_binding.h" and path.parent.name == "binding_support" for path in generated_files)

    sys.modules.pop(module_name, None)
    sys.path.insert(0, str(workdir))
    try:
        return _sole_native_module(importlib.import_module(module_name))
    finally:
        sys.path.remove(str(workdir))


def _compiler() -> str:
    requested = os.environ.get("PRIK_TEST_FORTRAN_COMPILER", "gfortran")
    compiler = shutil.which(requested)
    if compiler is None:
        pytest.skip(f"requested Fortran compiler is unavailable: {requested}")
    return compiler


@cache
def _supports_maybe_unallocated_function_result() -> bool:
    """Check the GNU extension used to inspect an allocatable function result."""
    source = """
module probe
contains
  function make_value() result(value)
    real, allocatable :: value(:)
  end function make_value
  subroutine collect(value)
    real, allocatable :: value(:)
  end subroutine collect
  subroutine call_collect()
    call collect(make_value())
  end subroutine call_collect
end module probe
"""
    with TemporaryDirectory() as directory:
        result = subprocess.run(
            [_compiler(), "-x", "f95", "-c", "-o", str(Path(directory) / "probe.o"), "-"],
            input=source,
            capture_output=True,
            text=True,
            check=False,
        )
    return result.returncode == 0


def _require_maybe_unallocated_function_result_support() -> None:
    if not _supports_maybe_unallocated_function_result():
        pytest.skip("gfortran rejects allocatable function results as allocatable helper arguments")


def _compile_native_object(source: Path, native_dir: Path) -> Path:
    native_dir.mkdir(parents=True, exist_ok=True)
    native_source = native_dir / source.name
    shutil.copyfile(source, native_source)
    native_object = native_dir / f"{source.stem}.o"
    compiler = _new_compiler(input_compiler=_compiler())
    compiler.compile_object(
        ObjectFile(
            source=native_source,
            object_path=native_object,
            language="fortran",
            include_dirs=(native_dir,),
        )
    )
    return native_object


def _generate_checked_pyi_contract(source: Path, package_dir: Path, expected_package: Path) -> Path:
    _run_captured_command(
        [
            sys.executable,
            "-m",
            "prik",
            "generate",
            "--pyi",
            str(source),
            "--out",
            str(package_dir),
            "--compiler",
            _compiler(),
        ],
    )
    assert_generated_pyi_package_matches_fixture(package_dir, expected_package)
    return package_dir / "__init__.pyi"


def _import_from_build_dir(module_name: str, build_dir: Path):
    sys.modules.pop(module_name, None)
    sys.path.insert(0, str(build_dir))
    try:
        return importlib.import_module(module_name)
    finally:
        sys.path.remove(str(build_dir))


def _build_inline_pyi_contract_module(
    tmp_path: Path,
    *,
    module_name: str,
    source_text: str,
    contract_text: str,
):
    """Compile an inline native implementation and build its semantic contract."""
    source = tmp_path / f"{module_name}.f90"
    source.write_text(source_text, encoding="utf-8")
    contract = tmp_path / f"{module_name}.pyi"
    contract.write_text(contract_text, encoding="utf-8")
    native_object = _compile_native_object(source, tmp_path / "native")
    result = build_pyi_extension(
        contract,
        input_compiler=_compiler(),
        native_objects=[native_object],
        native_include_dirs=[native_object.parent],
        output_dir=tmp_path / "build",
    )
    module = _sole_native_module(_import_from_build_dir(result.module_name, result.output_dir))
    return module, result


def _build_generated_pyi_and_import(source_template: Path, workdir: Path, expected_contract_package: Path):
    source_dir = workdir / "source"
    source_dir.mkdir(parents=True)
    source = source_dir / source_template.name
    shutil.copyfile(source_template, source)

    entry = _generate_checked_pyi_contract(source, workdir / "contracts" / source.stem, expected_contract_package)
    native_object = _compile_native_object(source, workdir / "native")
    result = build_pyi_extension(
        entry,
        input_compiler=_compiler(),
        native_objects=[native_object],
        native_include_dirs=[native_object.parent],
        output_dir=workdir / "pyi_build",
    )

    assert result.sources[0] == entry
    assert source not in result.sources
    assert result.native_build_plan.compilation_units == ()
    assert result.native_build_plan.produced_objects == ()
    assert result.native_build_plan.prebuilt_artifacts[0].path == native_object
    return _sole_native_module(_import_from_build_dir(result.module_name, result.output_dir))


def _build_source_or_generated_pyi_and_import(
    source_template: Path,
    workdir: Path,
    expected_generated_sources: set[str],
    expected_contract_package: Path,
    build_mode: str,
):
    if build_mode == "source":
        source_build_dir = workdir / "source_build"
        source_build_dir.mkdir(parents=True)
        return _build_and_import(source_template, source_build_dir, expected_generated_sources)
    return _build_generated_pyi_and_import(source_template, workdir / "generated_pyi_build", expected_contract_package)


def _build_source_and_import(
    source_template: Path,
    workdir: Path,
    expected_generated_sources: set[str],
):
    """Build one source entry through the canonical production generator."""
    result = build_fortran_extension(
        source_template,
        output_dir=workdir,
        preprocessing=PreprocessingConfig(mode="compiler", compiler=_compiler()),
    )
    assert result.shared_library.exists()
    assert {path.name for path in result.generated_sources} == expected_generated_sources
    return _sole_native_module(_import_from_build_dir(result.module_name, result.output_dir))


def _build_source_wrapper_plan_and_import(
    source_template: Path,
    workdir: Path,
    *,
    unwrap_namespace: bool = True,
):
    source_dir = workdir / "source"
    source_dir.mkdir(parents=True)
    source = source_dir / source_template.name
    shutil.copyfile(source_template, source)

    native_object = _compile_native_object(source, workdir / "native")
    native_compile_obj = ObjectFile(
        source=source,
        object_path=native_object,
        language="fortran",
        include_dirs=(native_object.parent,),
    )
    parsed = parse_fortran_project(
        {
            str(source): _fortran_source_for_pipeline(
                source,
                PreprocessingConfig(mode="compiler", compiler=_compiler()),
            )
        }
    )
    modules = fortran_project_to_semantic_modules(parsed)
    _apply_source_python_exports(modules)
    module = _merge_wrapper_modules(modules, name=source.stem)
    complete_semantic_policies(module)

    plan = WrapperPlanner().build(module)
    rendered = WrapperCodeGenerator().generate(plan)
    native_build_plan = NativeBuildPlan(
        produced_objects=(native_object,),
        module_dirs=(native_object.parent,),
        include_dirs=(native_object.parent,),
    )
    result = _build_rendered_wrapper_extension(
        rendered,
        output_dir=workdir / "wrapper_plan_build",
        sources=(source,),
        native_build_plan=native_build_plan,
        native_dependencies=(native_compile_obj,),
        compiler=_new_compiler(input_compiler=_compiler()),
    )
    module = _import_from_build_dir(result.module_name, result.output_dir)
    return (_sole_native_module(module) if unwrap_namespace else module), result


def _build_text_and_import(source_text: str, filename: str, workdir: Path, expected_generated_sources: set[str]):
    source = workdir / filename
    source.write_text(source_text, encoding="utf-8")
    module_name = source.stem

    cmd = [
        sys.executable,
        "-m",
        "prik",
        str(source),
        "--out-dir",
        str(workdir),
        "--compiler",
        _compiler(),
        "--json",
    ]
    result = _run_captured_command(cmd, cwd=workdir)
    payload = json.loads(result.stdout)

    shared_library = Path(payload["shared_library"])
    assert shared_library.exists()
    assert {Path(path).name for path in payload["generated_sources"]} == expected_generated_sources

    sys.modules.pop(module_name, None)
    sys.path.insert(0, str(workdir))
    try:
        return _sole_native_module(importlib.import_module(module_name))
    finally:
        sys.path.remove(str(workdir))


def _build_sources_and_import(source_texts: list[tuple[str, str]], workdir: Path):
    sources = []
    for filename, source_text in source_texts:
        source = workdir / filename
        source.write_text(source_text, encoding="utf-8")
        sources.append(source)

    cmd = [
        sys.executable,
        "-m",
        "prik",
        *(str(source) for source in sources),
        "--out-dir",
        str(workdir),
        "--compiler",
        _compiler(),
        "--json",
    ]
    result = _run_captured_command(cmd, cwd=workdir)
    payload = json.loads(result.stdout)
    module_name = payload["module_name"]

    assert payload["sources"] == [str(source) for source in sources]
    assert payload["compiled"] is True
    assert payload["build_makefile"] is None
    assert Path(payload["shared_library"]).exists()
    for source in sources:
        assert any(Path(path).name == f"{source.stem}.o" for path in payload["generated_files"])

    sys.modules.pop(module_name, None)
    sys.path.insert(0, str(workdir))
    try:
        return importlib.import_module(module_name), payload
    finally:
        sys.path.remove(str(workdir))


def _normalized_fortran_source(source: Path):
    return " ".join(source.read_text().replace("&", "").split())


def _result_dtype(expected):
    if isinstance(expected, bool):
        return np.dtype(np.bool_)
    if isinstance(expected, int):
        return np.dtype(np.int32)
    return np.asarray(expected).dtype


def _array_argument(value, size: int, *, strided: bool):
    dtype = np.asarray(value).dtype
    if strided:
        storage = np.zeros(2 * size, dtype=dtype)
        array = storage[::2]
    else:
        array = np.zeros(size, dtype=dtype)
    array[:] = value
    return array


def _array_result(expected, size: int, *, strided: bool):
    dtype = _result_dtype(expected)
    if strided:
        storage = np.zeros(2 * size, dtype=dtype)
        return storage[1::2]
    return np.zeros(size, dtype=dtype)


def _assert_array_result(function_name, result, expected, size):
    expected_array = np.full(size, expected, dtype=result.dtype)
    if result.dtype == np.dtype(np.bool_):
        np.testing.assert_array_equal(result, expected_array, err_msg=function_name)
    else:
        np.testing.assert_allclose(
            result,
            expected_array,
            rtol=1e-6,
            atol=1e-6,
            err_msg=function_name,
        )


def _assert_fmath_array_examples(module, *, suffix="", strided=False):
    cases = fmath_cases()
    missing = sorted(
        f"{name}{suffix}".lower() for name, _, _ in cases if not hasattr(module, f"{name}{suffix}".lower())
    )
    assert missing == []

    size = 4
    for function_name, scalar_args, expected in cases:
        wrapped_name = f"{function_name}{suffix}".lower()
        array_args = [_array_argument(scalar_arg, size, strided=strided) for scalar_arg in scalar_args]
        result = _array_result(expected, size, strided=strided)

        replacement_size = getattr(module, wrapped_name)(np.int32(size), *array_args, result)

        assert replacement_size == np.int32(size), wrapped_name
        _assert_array_result(wrapped_name, result, expected, size)


def _assert_array_rejects_strided_views(module, function_name):
    size = 4
    values = _array_argument(np.float32(2.0), size, strided=True)
    result = _array_result(np.float32(4.0), size, strided=True)

    with pytest.raises(TypeError, match="contiguous"):
        getattr(module, function_name.lower())(np.int32(size), values, result)


def _assert_legacy_string_examples(module):
    assert module.char_code_default("A") == ord("A")
    assert module.char_code_star1(np.str_("B")) == ord("B")
    assert module.string_len_star8("short   ") == 5
    with pytest.raises(TypeError, match="exactly 8 bytes"):
        module.string_len_star8("short")
    with pytest.raises(TypeError, match="exactly 8 bytes"):
        module.string_len_star8("too-long-value")
    assert module.string_len_assumed("variable length") == 15
    assert module.string_len_entity("python") == 6
    assert module.char_result_default() == "L"
    assert module.string_result_star8() == "LEGACY!!"
    assert module.string_result_padded() == "PAD     "
    assert module.string_result_declared() == "STRING"


def _assert_modern_string_examples(module):
    assert module.char_code_default("A") == ord("A")
    assert module.char_code_len1(np.str_("B")) == ord("B")
    assert module.char_code_kind1("C") == ord("C")
    assert module.char_code_c_char("D") == ord("D")
    assert module.string_len_fixed("short   ") == 5
    with pytest.raises(TypeError, match="exactly 8 bytes"):
        module.string_len_fixed("short")
    with pytest.raises(TypeError, match="exactly 8 bytes"):
        module.string_len_fixed("too-long-value")
    assert module.string_len_assumed("variable length") == 15
    assert module.string_len_c_char("c-char  ") == 6
    assert module.char_result_default() == "M"
    assert module.char_result_c_char() == "C"
    assert module.string_result_fixed() == "MODERN!!"
    assert module.string_result_padded() == "PAD     "
    assert module.string_result_c_char() == "C-CHAR!!"
    assert module.string_result_deferred("dynamic") == "dynamic-deferred"
    assert module.string_result_deferred("café") == "café-deferred"
    labels = np.array([b"first", b"second"], dtype="S8")
    assert module.fixed_array_extent(labels) == 16
    assert module.rewrite_storage("abcdefgh") == "Ybcdefg?"


def _assert_modern_class_examples(module):
    assert hasattr(module, "vector")
    value = module.vector()
    value.x = np.float64(3.0)
    value.y = np.float64(4.0)

    assert value.magnitude() == np.float64(5.0)
    value.scale(np.float64(2.0))
    assert value.x == np.float64(6.0)
    assert value.y == np.float64(8.0)
    assert value.magnitude() == np.float64(10.0)
    value.shift(np.float64(1.5), np.float64(-2.0))
    assert value.x == np.float64(7.5)
    assert value.y == np.float64(6.0)
    module.scale(value, np.float64(0.5))
    assert value.x == np.float64(3.75)
    assert value.y == np.float64(3.0)

    assert hasattr(module, "vector_store")
    store = module.vector_store()
    values = store.values
    matrix_values = store.matrix
    assert isinstance(values, AllocatableArray)
    assert isinstance(matrix_values, AllocatableArray)
    assert values.owner is store
    assert matrix_values.owner is store
    assert values.allocated is False
    assert matrix_values.allocated is False
    assert values.to_numpy() is None
    assert matrix_values.to_numpy() is None

    with pytest.raises(AttributeError):
        store.values = np.array([9.0], dtype=np.float64)

    store.allocate_values(np.int64(3))
    assert values.allocated is True
    assert values.shape == (3,)
    values_view = values.to_numpy()
    values_view[:] = np.array([1.0, 2.0, 3.0], dtype=np.float64)
    np.testing.assert_allclose(values.to_numpy(), np.array([1.0, 2.0, 3.0]))

    store.set_values(np.array([4.0, 5.0], dtype=np.float64))
    assert values.shape == (2,)
    np.testing.assert_allclose(values.to_numpy(), np.array([4.0, 5.0]))

    values.resize((4,))
    assert values.allocated is True
    assert values.shape == (4,)
    resized_values = values.to_numpy()
    resized_values[:] = np.array([6.0, 7.0, 8.0, 9.0], dtype=np.float64)
    np.testing.assert_allclose(values.to_numpy(), resized_values)

    values.deallocate()
    assert values.allocated is False
    assert values.shape is None
    assert values.to_numpy() is None
    store.set_values(np.array([4.0, 5.0], dtype=np.float64))

    matrix = np.asfortranarray(np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]], dtype=np.float64))
    store.allocate_matrix(np.int64(2), np.int64(3))
    assert matrix_values.shape == (2, 3)
    matrix_view = matrix_values.to_numpy()
    matrix_view[:, :] = matrix
    np.testing.assert_allclose(matrix_values.to_numpy(), matrix)
    assert matrix_view.flags.f_contiguous

    replacement = np.asfortranarray(matrix * 2.0)
    store.set_matrix(replacement)
    replacement_view = matrix_values.to_numpy()
    np.testing.assert_allclose(replacement_view, replacement)
    assert replacement_view.flags.f_contiguous

    with pytest.raises(TypeError, match=r"expected ordering \(F\)"):
        store.set_matrix(np.array(replacement, order="C"))

    made = module.vector_store.make(np.int64(4), np.float64(1.5))
    made_values = made.values
    assert isinstance(made_values, AllocatableArray)
    assert made_values.owner is made
    np.testing.assert_allclose(made_values.to_numpy(), np.full(4, 1.5, dtype=np.float64))
    made_owner_id = id(made)
    del made
    gc.collect()
    assert id(made_values.owner) == made_owner_id
    np.testing.assert_allclose(made_values.to_numpy(), np.full(4, 1.5, dtype=np.float64))
