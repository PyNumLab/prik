"""Cross-extension allocatable descriptor and native-memory evidence."""

import ctypes
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
from prik.contracts import Allocatable, Float64, Pointer, String

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

CHARACTER_CROSS_A_SOURCE = """\
module fcharacter_cross_a
  use iso_c_binding, only: c_char
  character(kind=c_char, len=4), target, save :: pointer_target(3) = &
    [character(kind=c_char, len=4) :: 'one ', 'two ', 'tri ']
contains
  subroutine select_a(values)
    character(kind=c_char, len=4), allocatable, intent(inout) :: values(:)
    if (allocated(values)) deallocate(values)
    allocate(values(2))
    values = [character(kind=c_char, len=4) :: 'one ', 'two ']
  end subroutine select_a

  integer(4) function state_a(values) result(state)
    character(kind=c_char, len=4), allocatable, intent(in) :: values(:)
    state = 0
    if (allocated(values)) state = size(values) * 100 + len(values)
  end function state_a

  subroutine select_pointer_a(values)
    character(kind=c_char, len=4), pointer, intent(out) :: values(:)
    values => pointer_target
  end subroutine select_pointer_a

  integer(4) function pointer_state_a(values) result(state)
    character(kind=c_char, len=4), pointer, intent(in) :: values(:)
    state = 0
    if (associated(values)) state = size(values) * 100 + len(values)
  end function pointer_state_a
end module fcharacter_cross_a
"""

CHARACTER_CROSS_B_SOURCE = """\
module fcharacter_cross_b
  use iso_c_binding, only: c_char
  character(kind=c_char, len=4), target, save :: pointer_target(2) = &
    [character(kind=c_char, len=4) :: 'red ', 'blue']
contains
  subroutine select_b(values)
    character(kind=c_char, len=4), allocatable, intent(inout) :: values(:)
    if (allocated(values)) deallocate(values)
    allocate(values(3))
    values = [character(kind=c_char, len=4) :: 'red ', 'blue', 'sky ']
  end subroutine select_b

  integer(4) function state_b(values) result(state)
    character(kind=c_char, len=4), allocatable, intent(in) :: values(:)
    state = 0
    if (allocated(values)) state = size(values) * 100 + len(values)
  end function state_b

  subroutine select_pointer_b(values)
    character(kind=c_char, len=4), pointer, intent(out) :: values(:)
    values => pointer_target
  end subroutine select_pointer_b

  integer(4) function pointer_state_b(values) result(state)
    character(kind=c_char, len=4), pointer, intent(in) :: values(:)
    state = 0
    if (associated(values)) state = size(values) * 100 + len(values)
  end function pointer_state_b
end module fcharacter_cross_b
"""

CHARACTER_CROSS_WRONG_WIDTH_SOURCE = """\
module fcharacter_cross_wrong_width
  use iso_c_binding, only: c_char
contains
  integer(4) function state(values) result(value)
    character(kind=c_char, len=5), allocatable, intent(in) :: values(:)
    value = 0
    if (allocated(values)) value = size(values) * 100 + len(values)
  end function state
end module fcharacter_cross_wrong_width
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


def test_fortran_owned_character_handle_crosses_matching_extensions(tmp_path: Path):
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    first_dir.mkdir()
    second_dir.mkdir()
    first = _build_text_and_import(
        CHARACTER_CROSS_A_SOURCE,
        "fcharacter_cross_a.f90",
        first_dir,
        {
            "bind_c_fcharacter_cross_a_wrapper.f90",
            "fcharacter_cross_a_wrapper.c",
            "fcharacter_cross_a_wrapper.h",
        },
    )
    second = _build_text_and_import(
        CHARACTER_CROSS_B_SOURCE,
        "fcharacter_cross_b.f90",
        second_dir,
        {
            "bind_c_fcharacter_cross_b_wrapper.f90",
            "fcharacter_cross_b_wrapper.c",
            "fcharacter_cross_b_wrapper.h",
        },
    )
    values = Allocatable[String[4][:]]()

    assert first.select_a(values) is values
    assert second.state_b(values) == np.int32(204)
    assert second.select_b(values) is values
    assert first.state_a(values) == np.int32(304)
    assert values.to_numpy().tolist() == [b"red ", b"blue", b"sky "]

    values.close()

    # A caller-created pointer handle is an ordinary argument: it crosses as
    # itself, and an unassociated one reads as such in either extension.
    source = Pointer[String[4][:]]()
    alias = Pointer[String[4][:]]()
    assert first.pointer_state_a(source) == np.int32(0)
    assert second.pointer_state_b(alias) == np.int32(0)
    source.close()

    # `intent(out)` is a hidden argument projected as a result, exactly as it
    # is for a numeric pointer, so the association returns as its own handle.
    selected = first.select_pointer_a()
    assert selected is not None
    assert first.pointer_state_a(selected) == np.int32(304)
    # The target is borrowed rather than copied, so the other extension sees
    # the same one through the same handle.
    assert second.pointer_state_b(selected) == np.int32(304)

    alias.close()

    # Association happens between two owner-backed handles, so the target of
    # the assignment is one the second extension attached.
    alias = second.select_pointer_b()
    assert alias is not None
    alias.associate(selected)
    assert second.pointer_state_b(alias) == np.int32(304)
    assert first.pointer_state_a(alias) == np.int32(304)

    # Nullifying one handle leaves another association to the same target.
    selected.nullify()
    assert first.pointer_state_a(selected) == np.int32(0)
    assert second.pointer_state_b(alias) == np.int32(304)
    selected.close()
    alias.close()


def test_fortran_owned_character_handle_refuses_a_different_owner_layout(tmp_path: Path):
    producer_dir = tmp_path / "producer"
    consumer_dir = tmp_path / "consumer"
    producer_dir.mkdir()
    consumer_dir.mkdir()
    producer = _build_text_and_import(
        CHARACTER_CROSS_A_SOURCE,
        "fcharacter_cross_a.f90",
        producer_dir,
        {
            "bind_c_fcharacter_cross_a_wrapper.f90",
            "fcharacter_cross_a_wrapper.c",
            "fcharacter_cross_a_wrapper.h",
        },
    )
    consumer = _build_text_and_import(
        CHARACTER_CROSS_WRONG_WIDTH_SOURCE,
        "fcharacter_cross_wrong_width.f90",
        consumer_dir,
        {
            "bind_c_fcharacter_cross_wrong_width_wrapper.f90",
            "fcharacter_cross_wrong_width_wrapper.c",
            "fcharacter_cross_wrong_width_wrapper.h",
        },
    )
    values = Allocatable[String[4][:]]()
    producer.select_a(values)

    with pytest.raises(TypeError, match="owner does not match"):
        consumer.state(values)

    values.close()


def test_fortran_owned_character_handle_refuses_a_different_compiler_abi(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    gfortran = shutil.which("gfortran")
    ifx = shutil.which("ifx")
    if gfortran is None or ifx is None:
        pytest.skip("gfortran and ifx are both required for the cross-compiler owner check")

    first_dir = tmp_path / "gfortran"
    second_dir = tmp_path / "ifx"
    first_dir.mkdir()
    second_dir.mkdir()
    monkeypatch.setenv("PRIK_TEST_FORTRAN_COMPILER", gfortran)
    first = _build_text_and_import(
        CHARACTER_CROSS_A_SOURCE,
        "fcharacter_cross_a.f90",
        first_dir,
        {
            "bind_c_fcharacter_cross_a_wrapper.f90",
            "fcharacter_cross_a_wrapper.c",
            "fcharacter_cross_a_wrapper.h",
        },
    )
    monkeypatch.setenv("PRIK_TEST_FORTRAN_COMPILER", ifx)
    second = _build_text_and_import(
        CHARACTER_CROSS_B_SOURCE,
        "fcharacter_cross_b.f90",
        second_dir,
        {
            "bind_c_fcharacter_cross_b_wrapper.f90",
            "fcharacter_cross_b_wrapper.c",
            "fcharacter_cross_b_wrapper.h",
        },
    )
    values = Allocatable[String[4][:]]()
    first.select_a(values)

    with pytest.raises(TypeError, match="different Fortran compiler ABI"):
        second.state_b(values)

    values.close()


def test_a_backend_capsule_from_another_producer_is_refused_not_interpreted(tmp_path: Path):
    """A reader refuses a capsule with another ABI name before reading it."""
    module = _build_text_and_import(
        ALLOCATABLE_CROSS_A_SOURCE,
        "fallocatable_cross_a.f90",
        tmp_path,
        {
            "bind_c_fallocatable_cross_a_wrapper.f90",
            "fallocatable_cross_a_wrapper.c",
            "fallocatable_cross_a_wrapper.h",
        },
    )
    values = Allocatable[Float64[:]]()
    module.select_a(values)
    assert module.total_a(values) == np.float64(3.0)

    capsule_new = ctypes.pythonapi.PyCapsule_New
    capsule_new.restype = ctypes.py_object
    capsule_new.argtypes = (ctypes.c_void_p, ctypes.c_char_p, ctypes.c_void_p)
    capsule_get = ctypes.pythonapi.PyCapsule_GetPointer
    capsule_get.restype = ctypes.c_void_p
    capsule_get.argtypes = (ctypes.py_object, ctypes.c_char_p)
    capsule_name = ctypes.pythonapi.PyCapsule_GetName
    capsule_name.restype = ctypes.c_char_p
    capsule_name.argtypes = (ctypes.py_object,)

    published = capsule_name(values._native_backend)
    assert published.startswith(b"prik.native_array_backend.v2.")
    address = capsule_get(values._native_backend, published)
    assert address
    stranger = published[: published.rindex(b".")] + b".0000000000000000"
    values._native_backend = capsule_new(address, stranger, None)

    # Only the capsule name differs; the reader must reject it before using the
    # live backend address.
    with pytest.raises(ValueError, match="PyCapsule_GetPointer called with incorrect name"):
        module.total_a(values)


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
