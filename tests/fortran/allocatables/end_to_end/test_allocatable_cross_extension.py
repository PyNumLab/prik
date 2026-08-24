"""Cross-extension allocatable descriptor and native-memory evidence."""

import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import (
    WRAPPER_TEST_ROOT,
    _build_source_or_generated_pyi_and_import,
    _build_text_and_import,
)
from prik.contracts import Allocatable, Float64

FIXTURES = Path(__file__).parent / "fixtures"
SOURCE = FIXTURES / "native" / "fallocatable_views_f90.f90"
CONTRACT_FIXTURES = FIXTURES / "contracts"
pytestmark = pytest.mark.fortran_end_to_end

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


def _source_build_dir(tmp_path: Path, build_mode: str) -> Path:
    if build_mode == "source":
        return tmp_path / "source_build"
    return tmp_path / "generated_pyi_build" / "pyi_build"


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
def test_allocatable_replacement_has_no_native_memory_errors(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    _build_source_or_generated_pyi_and_import(
        SOURCE,
        tmp_path,
        {
            "bind_c_fallocatable_views_f90_wrapper.f90",
            "fallocatable_views_f90_wrapper.c",
            "fallocatable_views_f90_wrapper.h",
        },
        CONTRACT_FIXTURES / "fallocatable_views_f90",
        pyi_parity_build_mode,
    )
    build_dir = _source_build_dir(tmp_path, pyi_parity_build_mode)
    script = """
import gc
import numpy as np

import fallocatable_views_f90 as package

module = package.fallocatable_views_f90
value = module.build_values(np.int32(2))

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
