"""Verified baseline runtime wrapper tests."""

from pathlib import Path
import shutil

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import (
    _assert_array_rejects_strided_views,
    _assert_fmath_array_examples,
    _assert_fmath_examples,
    _build_source_or_generated_pyi_and_import,
    _build_source_wrapper_plan_and_import,
    _compile_native_object,
    _import_from_build_dir,
    _sole_native_module,
    wrapper_source,
)
from x2py import build_pyi_extension
from x2py.runtime.handles import _NativeArrayHandoff, AllocatableArray, PointerArray

DATA_TYPE_CONTRACTS = Path(__file__).parent / "fixtures" / "baseline" / "contracts"
ARRAY_CONTRACTS = Path(__file__).parents[2] / "arrays" / "end_to_end" / "fixtures" / "baseline" / "contracts"
SCALAR_FIXED_SOURCE = wrapper_source("fmath.f")
ARRAY_FIXED_SOURCE = wrapper_source("fmath_arrays.f")
SCALAR_F90_SOURCE = wrapper_source("fmath_f90.f90")
ARRAY_F90_SOURCE = wrapper_source("fmath_arrays_f90.f90")
pytestmark = pytest.mark.fortran_end_to_end


def _native_array_actual(value: np.ndarray, *, pointer: bool):
    state_name = "associated" if pointer else "allocated"
    operations = {
        "array_actual": lambda _handle: _NativeArrayHandoff(value.ctypes.data),
        "descriptor": lambda _handle: _NativeArrayHandoff(value.ctypes.data),
        "shape": lambda _handle: value.shape,
        "layout": lambda _handle: "F" if value.flags.f_contiguous else "C",
        "writeable": lambda _handle: value.flags.writeable,
        "native_byte_order": lambda _handle: value.dtype.isnative,
        "aligned": lambda _handle: value.flags.aligned,
        "to_numpy": lambda _handle: value,
        state_name: lambda _handle: True,
        "nullify" if pointer else "deallocate": lambda _handle: None,
    }
    handle_type = PointerArray if pointer else AllocatableArray
    return handle_type(dtype=value.dtype, rank=value.ndim, ops=operations)


def test_fortran_wrapper_pipeline_builds_importable_extension(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    module = _build_source_or_generated_pyi_and_import(
        SCALAR_FIXED_SOURCE,
        tmp_path,
        {
            "bind_c_fmath_wrapper.f90",
            "fmath_wrapper.c",
            "fmath_wrapper.h",
        },
        DATA_TYPE_CONTRACTS / "fmath",
        pyi_parity_build_mode,
    )

    _assert_fmath_examples(module)


@pytest.mark.parametrize(
    "source",
    [SCALAR_FIXED_SOURCE, SCALAR_F90_SOURCE],
    ids=["fixed-form-externals", "free-form-module"],
)
def test_fmath_scalar_sources_use_canonical_wrapper_plan(
    tmp_path: Path,
    source: Path,
):
    expected_generated_sources = {
        f"bind_c_{source.stem}_wrapper.f90",
        f"{source.stem}_wrapper.c",
        f"{source.stem}_wrapper.h",
    }
    wrapper_root, wrapper_result = _build_source_wrapper_plan_and_import(
        source,
        tmp_path / "build",
        unwrap_namespace=False,
    )

    if source == SCALAR_F90_SOURCE:
        assert not hasattr(wrapper_root, "add_r8")
        assert hasattr(wrapper_root, "fmath_f90")
        module = wrapper_root.fmath_f90
    else:
        assert hasattr(wrapper_root, "add_r8")
        module = wrapper_root

    assert {path.name for path in wrapper_result.generated_sources} == expected_generated_sources
    assert any(path.name == f"{source.stem}_wrapper.h" for path in wrapper_result.generated_files)
    assert any(
        path.name == "x2py_binding.h" and path.parent.name == "binding_support"
        for path in wrapper_result.generated_files
    )
    assert wrapper_result.compiled is True
    assert wrapper_result.shared_library.exists()

    _assert_fmath_examples(module)
    error_type, message = _scalar_conversion_failure(module)
    assert error_type is TypeError
    assert "argument" in message


def _scalar_conversion_failure(module) -> tuple[type[BaseException], str]:
    with pytest.raises(TypeError) as error_info:
        module.add_r8("not-a-real", np.float64(1.0))

    np.testing.assert_allclose(
        module.add_r8(np.float64(1.5), np.float64(2.25)),
        (np.float64(3.75), np.float64(1.5), np.float64(2.25)),
    )
    return type(error_info.value), str(error_info.value)


def test_f90_wrapper_pipeline_builds_importable_extension(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    module = _build_source_or_generated_pyi_and_import(
        SCALAR_F90_SOURCE,
        tmp_path,
        {
            "bind_c_fmath_f90_wrapper.f90",
            "fmath_f90_wrapper.c",
            "fmath_f90_wrapper.h",
        },
        DATA_TYPE_CONTRACTS / "fmath_f90",
        pyi_parity_build_mode,
    )

    _assert_fmath_examples(module)


def test_fortran_array_wrapper_pipeline_matches_fmath_results_with_contiguous_arrays(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    module = _build_source_or_generated_pyi_and_import(
        ARRAY_FIXED_SOURCE,
        tmp_path,
        {
            "bind_c_fmath_arrays_wrapper.f90",
            "fmath_arrays_wrapper.c",
            "fmath_arrays_wrapper.h",
        },
        ARRAY_CONTRACTS / "fmath_arrays",
        pyi_parity_build_mode,
    )

    _assert_fmath_array_examples(module, strided=False)
    _assert_array_rejects_strided_views(module, "SQUARE_R4")


def test_f90_array_wrapper_distinguishes_contiguous_and_strided_contracts(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    module = _build_source_or_generated_pyi_and_import(
        ARRAY_F90_SOURCE,
        tmp_path,
        {
            "bind_c_fmath_arrays_f90_wrapper.f90",
            "fmath_arrays_f90_wrapper.c",
            "fmath_arrays_f90_wrapper.h",
        },
        ARRAY_CONTRACTS / "fmath_arrays_f90",
        pyi_parity_build_mode,
    )

    _assert_fmath_array_examples(module, suffix="_CONTIGUOUS", strided=False)
    _assert_array_rejects_strided_views(module, "SQUARE_R4_CONTIGUOUS")
    _assert_fmath_array_examples(module, suffix="_STRIDED", strided=True)


def test_required_array_buffers_use_canonical_wrapper_plan(tmp_path: Path):
    """Replay one existing dense rank-one routine through a reduced contract."""
    native_object = _compile_native_object(ARRAY_F90_SOURCE, tmp_path / "native")
    contract_package = tmp_path / "required_array"
    shutil.copytree(ARRAY_CONTRACTS / "fmath_arrays_f90", contract_package)
    (contract_package / "__init__.pyi").write_text(
        "from .fmath_arrays_f90 import square_r8_contiguous\n",
        encoding="utf-8",
    )
    result = build_pyi_extension(
        contract_package / "__init__.pyi",
        native_objects=[native_object],
        native_include_dirs=[native_object.parent],
        output_dir=tmp_path / "build",
    )
    package = _import_from_build_dir(result.module_name, result.output_dir)
    module = package if hasattr(package, "square_r8_contiguous") else _sole_native_module(package)

    values = np.array([2.0, 3.0, -4.0], dtype=np.float64)
    output = np.zeros_like(values)
    assert module.square_r8_contiguous(np.int32(values.size), values, output) == np.int32(values.size)
    np.testing.assert_array_equal(output, values**2)

    handle_output = np.zeros_like(values)
    assert module.square_r8_contiguous(
        np.int32(values.size),
        _native_array_actual(values, pointer=False),
        _native_array_actual(handle_output, pointer=True),
    ) == np.int32(values.size)
    np.testing.assert_array_equal(handle_output, values**2)

    empty = np.empty(0, dtype=np.float64)
    assert module.square_r8_contiguous(np.int32(0), empty, empty.copy()) == np.int32(0)

    valid = np.arange(4, dtype=np.float64)
    output = np.zeros_like(valid)
    invalid_cases = (
        np.arange(4, dtype=np.float32),
        valid.reshape(2, 2),
        np.arange(8, dtype=np.float64)[::2],
        np.arange(4, dtype=">f8"),
        np.ndarray(4, dtype=np.float64, buffer=bytearray(33), offset=1),
    )
    for invalid in invalid_cases:
        with pytest.raises((TypeError, ValueError)):
            module.square_r8_contiguous(np.int32(4), invalid, output)

    read_only = valid.copy()
    read_only.flags.writeable = False
    with pytest.raises(TypeError, match="writeable"):
        module.square_r8_contiguous(np.int32(4), read_only, output)
