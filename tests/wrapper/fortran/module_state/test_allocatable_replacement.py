"""Allocatable ``intent(inout)`` replacement and ownership tests."""

import gc
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from x2py import build_pyi_extension
from x2py.contracts import Allocatable, Float64
from x2py.runtime.handles import AllocatableArray
from tests.wrapper.fortran._support import (
    WRAPPER_TEST_ROOT,
    _build_text_and_import,
    _compile_native_object,
    _import_from_build_dir,
    _build_source_or_generated_pyi_and_import,
    _sole_native_module,
    wrapper_source,
)

ALLOCATABLE_INOUT_F90_SOURCE = wrapper_source("fallocatable_inout_f90.f90")
ALLOCATABLE_FACTORY_F90_SOURCE = wrapper_source("fallocatable_views_f90.f90")
CONTRACT_FIXTURES = Path(__file__).parent / "contracts"
ALLOCATABLE_CROSS_A_SOURCE = """\
module fallocatable_cross_a
contains
  subroutine select_a(values)
    real(8), allocatable, intent(inout) :: values(:)
    if (allocated(values)) deallocate(values)
    allocate(values(2))
    values = [1.0_8, 2.0_8]
  end subroutine select_a

  function total_a(values) result(total)
    real(8), allocatable, intent(in) :: values(:)
    real(8) :: total
    if (allocated(values)) then
      total = sum(values)
    else
      total = -1.0_8
    end if
  end function total_a
end module fallocatable_cross_a
"""
ALLOCATABLE_CROSS_B_SOURCE = """\
module fallocatable_cross_b
contains
  subroutine select_b(values)
    real(8), allocatable, intent(inout) :: values(:)
    if (allocated(values)) deallocate(values)
    allocate(values(3))
    values = [10.0_8, 20.0_8, 30.0_8]
  end subroutine select_b

  function total_b(values) result(total)
    real(8), allocatable, intent(in) :: values(:)
    real(8) :: total
    if (allocated(values)) then
      total = sum(values)
    else
      total = -1.0_8
    end if
  end function total_b
end module fallocatable_cross_b
"""


def _allocatable_replacement_build_dir(tmp_path: Path, build_mode: str) -> Path:
    if build_mode == "source":
        return tmp_path / "source_build"
    return tmp_path / "generated_pyi_build" / "pyi_build"


def _build_allocatable_factory(build_mode: str, tmp_path: Path):
    return _build_source_or_generated_pyi_and_import(
        ALLOCATABLE_FACTORY_F90_SOURCE,
        tmp_path,
        {
            "bind_c_fallocatable_views_f90_wrapper.f90",
            "fallocatable_views_f90_wrapper.c",
            "fallocatable_views_f90_wrapper.h",
        },
        CONTRACT_FIXTURES / "fallocatable_views_f90",
        build_mode,
    )


def test_allocatable_inout_arrays_mutate_and_return_the_same_handle(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    module = _build_source_or_generated_pyi_and_import(
        ALLOCATABLE_INOUT_F90_SOURCE,
        tmp_path / "replacement",
        {
            "bind_c_fallocatable_inout_f90_wrapper.f90",
            "fallocatable_inout_f90_wrapper.c",
            "fallocatable_inout_f90_wrapper.h",
        },
        CONTRACT_FIXTURES / "fallocatable_inout_f90",
        pyi_parity_build_mode,
    )

    factory = _build_allocatable_factory(pyi_parity_build_mode, tmp_path / "factory")

    assert "replace_values(values, mode) -> AllocatableArray[float64]" in module.replace_values.__doc__
    assert "values : AllocatableArray[float64]" in module.replace_values.__doc__

    values = factory.build_values(np.int32(2))
    assert isinstance(values, AllocatableArray)
    returned = module.replace_values(values, np.int32(1))
    assert returned is values
    np.testing.assert_allclose(values.to_numpy(), np.array([12.0, 14.0], dtype=np.float64))

    returned = module.replace_values(values, np.int32(3))
    assert returned is values
    np.testing.assert_allclose(values.to_numpy(), np.array([3.0, 6.0, 9.0], dtype=np.float64))

    returned = module.replace_values(values, np.int32(0))
    assert returned is values
    assert values.allocated is False
    assert values.to_numpy() is None

    returned = module.replace_values(values, np.int32(1))
    assert returned is values
    np.testing.assert_allclose(values.to_numpy(), np.array([1.0, 2.0], dtype=np.float64))

    fresh = Allocatable[Float64[:]]()
    assert fresh.allocated is False
    assert module.replace_values(fresh, np.int32(3)) is fresh
    np.testing.assert_allclose(fresh.to_numpy(), np.array([3.0, 6.0, 9.0], dtype=np.float64))
    fresh.close()
    assert fresh.closed is True

    del values
    gc.collect()

    with pytest.raises(TypeError):
        module.replace_values(np.array([1.0], dtype=np.float32), np.int32(1))
    with pytest.raises(TypeError):
        module.replace_values(np.array([[1.0]], dtype=np.float64), np.int32(1))


def test_projected_allocatable_descriptor_preserves_same_handle_identity(tmp_path: Path):
    """Replay direct persistent-descriptor mutation with same-handle identity."""
    replacement_object = _compile_native_object(ALLOCATABLE_INOUT_F90_SOURCE, tmp_path / "native_replacement")
    factory_object = _compile_native_object(ALLOCATABLE_FACTORY_F90_SOURCE, tmp_path / "native_factory")
    replacement_contract = tmp_path / "replacement_contract"
    shutil.copytree(CONTRACT_FIXTURES / "fallocatable_inout_f90", replacement_contract)
    replacement_result = build_pyi_extension(
        replacement_contract / "__init__.pyi",
        native_objects=[replacement_object],
        native_include_dirs=[replacement_object.parent],
        output_dir=tmp_path / "replacement",
    )
    replacement_module = _import_from_build_dir(
        replacement_result.module_name,
        replacement_result.output_dir,
    )
    module = (
        replacement_module if hasattr(replacement_module, "replace_values") else _sole_native_module(replacement_module)
    )

    factory_contract = tmp_path / "factory_contract"
    factory_contract.mkdir()
    (factory_contract / "__init__.pyi").write_text(
        "from .fallocatable_views_f90 import build_values\n",
        encoding="utf-8",
    )
    (factory_contract / "fallocatable_views_f90.pyi").write_text(
        """from x2py.contracts import Addr, Allocatable, Arg, Float64, Int32, Return, native_call

@native_call([Addr(Arg(0)), Return("values", 0)])
def build_values(n: Int32) -> Allocatable[Float64[:]]: ...
""",
        encoding="utf-8",
    )
    factory_result = build_pyi_extension(
        factory_contract / "__init__.pyi",
        native_objects=[factory_object],
        native_include_dirs=[factory_object.parent],
        output_dir=tmp_path / "factory",
    )
    factory_module = _import_from_build_dir(factory_result.module_name, factory_result.output_dir)
    factory = factory_module if hasattr(factory_module, "build_values") else _sole_native_module(factory_module)

    values = factory.build_values(np.int32(2))
    assert module.replace_values(values, np.int32(3)) is values
    np.testing.assert_allclose(values.to_numpy(), np.array([3.0, 6.0, 9.0]))
    assert module.replace_values(values, np.int32(0)) is values
    assert values.allocated is False
    assert module.replace_values(values, np.int32(1)) is values
    np.testing.assert_allclose(values.to_numpy(), np.array([1.0, 2.0]))
    values.close()


def test_caller_created_allocatable_crosses_separately_built_extensions(tmp_path: Path):
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    first_dir.mkdir()
    second_dir.mkdir()
    first = _build_text_and_import(
        ALLOCATABLE_CROSS_A_SOURCE,
        "fallocatable_cross_a.f90",
        first_dir,
        {
            "bind_c_fallocatable_cross_a_wrapper.f90",
            "fallocatable_cross_a_wrapper.c",
            "fallocatable_cross_a_wrapper.h",
        },
    )
    second = _build_text_and_import(
        ALLOCATABLE_CROSS_B_SOURCE,
        "fallocatable_cross_b.f90",
        second_dir,
        {
            "bind_c_fallocatable_cross_b_wrapper.f90",
            "fallocatable_cross_b_wrapper.c",
            "fallocatable_cross_b_wrapper.h",
        },
    )
    values = Allocatable[Float64[:]]()

    assert first.select_a(values) is values
    np.testing.assert_array_equal(values.to_numpy(), np.array([1.0, 2.0]))
    assert second.total_b(values) == np.float64(3.0)

    assert second.select_b(values) is values
    np.testing.assert_array_equal(values.to_numpy(), np.array([10.0, 20.0, 30.0]))
    assert first.total_a(values) == np.float64(60.0)

    values.close()
    assert values.closed is True


@pytest.mark.skipif(shutil.which("valgrind") is None, reason="Valgrind is required for native ownership checks")
def test_allocatable_replacement_has_no_native_memory_errors(pyi_parity_build_mode: str, tmp_path: Path):
    _build_source_or_generated_pyi_and_import(
        ALLOCATABLE_INOUT_F90_SOURCE,
        tmp_path / "replacement",
        {
            "bind_c_fallocatable_inout_f90_wrapper.f90",
            "fallocatable_inout_f90_wrapper.c",
            "fallocatable_inout_f90_wrapper.h",
        },
        CONTRACT_FIXTURES / "fallocatable_inout_f90",
        pyi_parity_build_mode,
    )
    _build_allocatable_factory(pyi_parity_build_mode, tmp_path / "factory")
    build_dir = _allocatable_replacement_build_dir(tmp_path / "replacement", pyi_parity_build_mode)
    factory_build_dir = _allocatable_replacement_build_dir(tmp_path / "factory", pyi_parity_build_mode)
    script = f"""
import gc
import numpy as np
import sys

sys.path.insert(0, {str(factory_build_dir)!r})
import fallocatable_inout_f90 as module
import fallocatable_views_f90 as factory

module = module.fallocatable_inout_f90
factory = factory.fallocatable_views_f90
value = factory.build_values(np.int32(2))

for mode in (1, 2, 0) * 50:
    returned = module.replace_values(value, np.int32(mode))
    assert returned is value
value.close()
gc.collect()
"""
    result = subprocess.run(
        [
            "valgrind",
            "--quiet",
            f"--suppressions={WRAPPER_TEST_ROOT / 'valgrind.supp'}",
            "--error-exitcode=99",
            "--leak-check=full",
            "--show-leak-kinds=definite",
            "--errors-for-leak-kinds=definite",
            "--track-origins=yes",
            sys.executable,
            "-c",
            script,
        ],
        cwd=build_dir,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
