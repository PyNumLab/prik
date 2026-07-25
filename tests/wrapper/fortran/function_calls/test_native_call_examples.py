"""Native call metadata examples covering scalar, array, string, and object projections."""

from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from x2py import build_pyi_extension
from tests.wrapper.fortran._support import _build_source_or_generated_pyi_and_import, wrapper_source
from tests.wrapper.fortran._support import (
    _compiler,
    _generate_checked_pyi_contract,
    _import_from_build_dir,
    _sole_native_module,
)

NATIVE_CALL_EXAMPLES_F90_SOURCE = wrapper_source("fnative_call_examples_f90.f90")
CONTRACT_FIXTURES = Path(__file__).parent / "contracts"
EXPECTED_GENERATED_SOURCES = {
    "bind_c_fnative_call_examples_f90_wrapper.f90",
    "fnative_call_examples_f90_wrapper.c",
    "fnative_call_examples_f90_wrapper.h",
}


def _assert_native_call_examples(module) -> None:
    assert module.scalar_status(np.int32(4)) == np.int32(15)

    vector = np.empty(4, dtype=np.float64)
    assert module.fill_vector(np.int32(4), vector) is None
    np.testing.assert_allclose(vector, np.array([1.5, 3.0, 4.5, 6.0], dtype=np.float64))

    matrix = np.array([[1.0, 3.0, 5.0], [2.0, 4.0, 6.0]], dtype=np.float64, order="F")
    shifted = np.empty((2, 3), dtype=np.float64, order="F")
    assert module.shift_matrix(np.int32(2), np.int32(3), matrix, shifted) is None
    np.testing.assert_allclose(shifted, matrix + 10.0)

    inout = np.array([2.0, 5.0, 7.0], dtype=np.float64)
    assert module.scale_with_status(inout) == np.int32(3)
    np.testing.assert_allclose(inout, np.array([4.0, 10.0, 14.0], dtype=np.float64))

    assert module.fixed_inout("abc     ") == "Xbc    !"
    with pytest.raises(TypeError, match="exactly 8 bytes"):
        module.fixed_inout("abc")
    assert module.make_label() == "done  "

    mixed_values = np.empty(3, dtype=np.float64)
    total, status, label = module.summarize_mixed(np.int32(3), mixed_values)
    assert total == np.float64(3.75)
    assert status == np.int32(23)
    assert label == "mix   "
    np.testing.assert_allclose(mixed_values, np.array([11.0, 12.0, 13.0], dtype=np.float64))

    point = module.summary_point()
    assert module.make_point(np.int32(7), point) is None
    assert point.total == np.float64(7.5)
    assert point.code == np.int32(107)


def _compile_native_shared_library(source: Path, native_dir: Path) -> Path:
    native_dir.mkdir(parents=True, exist_ok=True)
    shared_library = native_dir / f"lib{source.stem}.so"
    subprocess.run(
        [
            _compiler(),
            "-shared",
            "-fPIC",
            str(source),
            "-o",
            str(shared_library),
            "-J",
            str(native_dir),
            "-I",
            str(native_dir),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return shared_library


def test_native_call_examples_cover_scalar_array_string_and_object_projection(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    module = _build_source_or_generated_pyi_and_import(
        NATIVE_CALL_EXAMPLES_F90_SOURCE,
        tmp_path,
        EXPECTED_GENERATED_SOURCES,
        CONTRACT_FIXTURES / "fnative_call_examples_f90",
        pyi_parity_build_mode,
    )

    _assert_native_call_examples(module)


@pytest.mark.skipif(sys.platform == "win32", reason="direct native shared-library loading differs on Windows")
def test_native_call_examples_build_from_generated_pyi_and_native_shared_library(tmp_path: Path):
    entry = _generate_checked_pyi_contract(
        NATIVE_CALL_EXAMPLES_F90_SOURCE,
        tmp_path / "contracts" / NATIVE_CALL_EXAMPLES_F90_SOURCE.stem,
        CONTRACT_FIXTURES / "fnative_call_examples_f90",
    )
    native_shared = _compile_native_shared_library(NATIVE_CALL_EXAMPLES_F90_SOURCE, tmp_path / "native")
    result = build_pyi_extension(
        entry,
        native_objects=[native_shared],
        native_include_dirs=[native_shared.parent],
        output_dir=tmp_path / "pyi_shared_build",
    )
    module = _sole_native_module(_import_from_build_dir(result.module_name, result.output_dir))
    native_plan = result.native_build_plan.to_dict()

    assert native_shared.is_file()
    assert native_plan["prebuilt_artifacts"] == [{"kind": "shared_library", "path": str(native_shared)}]
    assert native_plan["link_items"] == [{"kind": "shared_library", "path": str(native_shared)}]
    assert str(native_shared.parent) in native_plan["library_dirs"]
    _assert_native_call_examples(module)
