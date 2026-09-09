"""Compiled behavior of character allocatable and pointer arguments."""

from __future__ import annotations

import gc
import subprocess
import sys
import threading
import time
import weakref
from pathlib import Path

import numpy as np
import pytest

from prik import build_pyi_extension
from prik.contracts import Allocatable, Pointer, String
from prik.runtime.handles import AllocatableArray
from tests.fortran._support.wrapper_build import (
    _build_text_and_import,
    _compile_native_object,
    _compiler,
    _import_from_build_dir,
    _sole_native_module,
)


pytestmark = pytest.mark.fortran_end_to_end


ALLOCATABLE_SOURCE = """\
module fcharacter_owner_allocatable
  use iso_c_binding, only: c_char
  implicit none
contains
  integer(4) function inspect(values) result(state)
    character(kind=c_char, len=4), allocatable, intent(in) :: values(:)
    state = 0
    if (allocated(values)) state = size(values) * 100 + len(values)
  end function inspect

  subroutine replace(values)
    character(kind=c_char, len=4), allocatable, intent(inout) :: values(:)
    if (allocated(values)) deallocate(values)
    allocate(values(3))
    values = [character(kind=c_char, len=4) :: 'red ', 'blue', 'sky ']
  end subroutine replace

  subroutine fill(values)
    character(kind=c_char, len=4), allocatable, intent(out) :: values(:)
    allocate(values(2))
    values = [character(kind=c_char, len=4) :: 'left', 'rght']
  end subroutine fill

  subroutine optional_fill(values, was_allocated)
    character(kind=c_char, len=4), allocatable, intent(out), optional :: values(:)
    integer(4), intent(out) :: was_allocated
    was_allocated = -1
    if (present(values)) then
      was_allocated = merge(1, 0, allocated(values))
      allocate(values(2))
      values = [character(kind=c_char, len=4) :: 'new1', 'new2']
    end if
  end subroutine optional_fill

  integer(4) function optional_state(values) result(state)
    character(kind=c_char, len=4), allocatable, intent(in), optional :: values(:)
    state = -1
    if (present(values)) then
      state = 0
      if (allocated(values)) state = size(values) * 100 + len(values)
    end if
  end function optional_state

  integer(4) function mixed(first, plain, second, scale) result(state)
    character(kind=c_char, len=4), allocatable, intent(in) :: first(:)
    character(kind=c_char, len=4), intent(in) :: plain(:)
    character(kind=c_char, len=4), allocatable, intent(in) :: second(:)
    integer(4), intent(in) :: scale
    state = scale + size(plain) * 10
    if (allocated(first)) state = state + size(first) * 100
    if (allocated(second)) state = state + size(second) * 1000
  end function mixed

  integer(4) function inspect_rank2(values) result(state)
    character(kind=c_char, len=3), allocatable, intent(in) :: values(:, :)
    state = 0
    if (allocated(values)) state = size(values, 1) * 1000 + size(values, 2) * 100 + len(values)
  end function inspect_rank2

  subroutine fill_rank2(values)
    character(kind=c_char, len=3), allocatable, intent(inout) :: values(:, :)
    if (allocated(values)) deallocate(values)
    allocate(values(2, 4))
    values = 'abc'
  end subroutine fill_rank2

end module fcharacter_owner_allocatable
"""


@pytest.fixture(scope="module")
def allocatable_owner_module(tmp_path_factory: pytest.TempPathFactory):
    workdir = tmp_path_factory.mktemp("character-owner-allocatable")
    module = _build_text_and_import(
        ALLOCATABLE_SOURCE,
        "fcharacter_owner_allocatable.f90",
        workdir,
        {
            "bind_c_fcharacter_owner_allocatable_wrapper.f90",
            "fcharacter_owner_allocatable_wrapper.c",
            "fcharacter_owner_allocatable_wrapper.h",
        },
    )
    return module, workdir


def test_fixed_character_allocatable_handles_cover_intent_and_optional_state(allocatable_owner_module):
    module, _workdir = allocatable_owner_module
    values = Allocatable[String[4][:]]()

    assert module.inspect(values) == np.int32(0)
    assert module.optional_state() == np.int32(-1)
    assert module.optional_state(None) == np.int32(-1)
    assert module.optional_state(values) == np.int32(0)

    assert module.replace(values) is values
    assert values.to_numpy().tolist() == [b"red ", b"blue", b"sky "]

    returned, was_allocated = module.optional_fill(values)
    assert returned is values
    assert was_allocated == np.int32(0)
    assert values.to_numpy().tolist() == [b"new1", b"new2"]

    produced = module.fill()
    assert isinstance(produced, AllocatableArray)
    assert produced.dtype == np.dtype("S4")
    assert produced.to_numpy().tolist() == [b"left", b"rght"]


def test_owner_handoff_composes_across_arguments_and_ranks(allocatable_owner_module):
    module, _workdir = allocatable_owner_module
    first = Allocatable[String[4][:]]()
    second = Allocatable[String[4][:]]()
    module.replace(first)
    module.replace(second)
    plain = np.array([b"one ", b"two "], dtype="S4")

    assert module.mixed(first, plain, second, np.int32(7)) == np.int32(3327)

    matrix = Allocatable[String[3][:, :]]()
    assert module.fill_rank2(matrix) is matrix
    assert matrix.shape == (2, 4)
    assert module.inspect_rank2(matrix) == np.int32(2403)


def test_owner_close_is_idempotent_and_finalization_is_safe(allocatable_owner_module):
    module, workdir = allocatable_owner_module
    values = Allocatable[String[4][:]]()
    module.inspect(values)
    values.close()
    values.close()
    assert values.closed is True

    finalized = Allocatable[String[4][:]]()
    module.inspect(finalized)
    reference = weakref.ref(finalized)
    del finalized
    gc.collect()
    assert reference() is None

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from prik.contracts import Allocatable, String; "
                "from fcharacter_owner_allocatable import fcharacter_owner_allocatable as api; "
                "value = Allocatable[String[4][:]](); api.inspect(value)"
            ),
        ],
        cwd=workdir,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


POINTER_SOURCE = """\
module fcharacter_owner_pointer
  use iso_c_binding, only: c_char
  implicit none
  character(kind=c_char, len=4), target, save :: fixed_target(3) = &
    [character(kind=c_char, len=4) :: 'one ', 'two ', 'tri ']
  character(kind=c_char, len=:), pointer, save :: deferred_target(:)
contains
  subroutine repoint_fixed(values)
    character(kind=c_char, len=4), pointer, intent(out) :: values(:)
    values => fixed_target
  end subroutine repoint_fixed

  integer(4) function fixed_state(values) result(state)
    character(kind=c_char, len=4), pointer, intent(in) :: values(:)
    state = 0
    if (associated(values)) state = size(values) * 100 + len(values)
  end function fixed_state

  integer(4) function ordinary_width(values) result(width)
    character(kind=c_char, len=*), intent(in) :: values(:)
    width = 0
    if (size(values) > 0) width = len(values)
  end function ordinary_width

  subroutine repoint_deferred(values)
    character(kind=c_char, len=:), pointer, intent(out) :: values(:)
    if (.not. associated(deferred_target)) then
      allocate(character(kind=c_char, len=6) :: deferred_target(2))
      deferred_target = [character(kind=c_char, len=6) :: 'alpha ', 'beta  ']
    end if
    values => deferred_target
  end subroutine repoint_deferred

  integer(4) function deferred_state(values) result(state)
    character(kind=c_char, len=:), pointer, intent(in) :: values(:)
    state = 0
    if (associated(values)) then
      state = size(values) * 100 + len(values) + iachar(values(1)(1:1))
    end if
  end function deferred_state
end module fcharacter_owner_pointer
"""


POINTER_POLICY = """Annotated[
    Pointer[{element}],
    PointerAssociation("runtime"),
    PointerPolicy(
        nullable=True,
        transfer="call_local",
        target_owner="wrapper",
        lifetime="wrapper",
        deallocation="deallocate_resize",
        shape_source="pointer_bounds",
        contiguity="contiguous",
        reassociation="allocate_resize",
        aliasing="descriptor",
        mutability="mutable",
    ),
]"""


def _build_pointer_owner_module(tmp_path: Path):
    source = tmp_path / "fcharacter_owner_pointer.f90"
    source.write_text(POINTER_SOURCE, encoding="utf-8")
    native_object = _compile_native_object(source, tmp_path / "native")
    contract = tmp_path / "fcharacter_owner_pointer.pyi"
    fixed = POINTER_POLICY.format(element="String[4][:]")
    deferred = POINTER_POLICY.format(element="String[:][:]")
    contract.write_text(
        f"""from prik.contracts import Annotated, Int32, Pointer, PointerAssociation, PointerPolicy, Returns, String, bind

def repoint_fixed(values: {fixed}) -> Returns["values", {fixed}]: ...
def fixed_state(values: Pointer[String[4][:]]) -> Int32: ...
def ordinary_width(values: String[...][:]) -> Int32: ...
@bind("fixed_state")
def managed_state(values: {fixed}) -> Int32: ...
def repoint_deferred(values: {deferred}) -> Returns["values", {deferred}]: ...
def deferred_state(values: {deferred}) -> Int32: ...
""",
        encoding="utf-8",
    )
    result = build_pyi_extension(
        contract,
        input_compiler=_compiler(),
        native_objects=[native_object],
        native_include_dirs=[native_object.parent],
        output_dir=tmp_path / "build",
    )
    return _sole_native_module(_import_from_build_dir(result.module_name, result.output_dir))


def _gnu_fortran_version() -> tuple[int, int, int] | None:
    compiler = _compiler()
    identity = subprocess.run(
        [compiler, "--version"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    if "GNU Fortran" not in identity:
        return None
    result = subprocess.run(
        [compiler, "-dumpfullversion"],
        capture_output=True,
        text=True,
        check=True,
    )
    parts = result.stdout.strip().split(".")
    return tuple(int(parts[index]) if index < len(parts) else 0 for index in range(3))


def test_fixed_character_pointer_owner_supports_association_and_target_mutation(tmp_path: Path):
    module = _build_pointer_owner_module(tmp_path)
    source = Pointer[String[4][:]]()
    alias = Pointer[String[4][:]]()

    assert module.fixed_state(source) == np.int32(0)
    assert module.fixed_state(alias) == np.int32(0)
    assert module.repoint_fixed(source) is source
    assert source.shape == (3,)
    assert source.to_numpy().tolist() == [b"one ", b"two ", b"tri "]
    assert module.ordinary_width(source) == np.int32(4)

    alias.associate(source)
    source.nullify()
    assert source.associated is False
    assert module.fixed_state(alias) == np.int32(304)

    managed = Pointer[String[4][:]]()
    assert module.managed_state(managed) == np.int32(0)
    managed.allocate(2)
    with pytest.raises(RuntimeError, match="failed to allocate Fortran array owner"):
        managed.allocate(1)
    managed.to_numpy()[:] = [b"aa  ", b"bb  "]
    assert module.managed_state(managed) == np.int32(204)
    managed.resize(3)
    assert managed.shape == (3,)
    managed.deallocate()
    assert managed.associated is False
    managed.close()
    managed.close()


def test_deferred_character_pointer_owner_supports_zero_copy_view(tmp_path: Path):
    if (gnu_version := _gnu_fortran_version()) is not None and gnu_version < (13, 3, 0):
        pytest.skip("deferred-length character pointer reassociation requires GNU Fortran 13.3 or newer")
    module = _build_pointer_owner_module(tmp_path)
    values = Pointer[String[:][:]]()
    assert module.deferred_state(values) == np.int32(0)
    assert module.repoint_deferred(values) is values
    assert values.dtype == np.dtype("S6")
    assert values.shape == (2,)
    assert module.deferred_state(values) == np.int32(303)
    view = values.to_numpy()
    assert view.dtype == np.dtype("S6")
    assert view.shape == (2,)
    assert view.tolist() == [b"alpha ", b"beta  "]
    assert view.ctypes.data != 0
    view[:] = [b"changed", b"values"]
    assert module.deferred_state(values) == np.int32(305)


NOGIL_SOURCE = """\
module fcharacter_owner_nogil
  use iso_c_binding, only: c_char, c_int
  implicit none
  logical, volatile, save :: call_entered = .false.
  interface
    function c_usleep(microseconds) bind(c, name="usleep") result(status)
      import c_int
      integer(c_int), value :: microseconds
      integer(c_int) :: status
    end function c_usleep
  end interface
contains
  subroutine initialize(values)
    character(kind=c_char, len=4), allocatable, intent(inout) :: values(:)
    if (allocated(values)) deallocate(values)
    allocate(values(1))
    values = 'safe'
  end subroutine initialize

  subroutine hold(values)
    character(kind=c_char, len=4), allocatable, intent(in) :: values(:)
    integer(c_int) :: ignored
    call_entered = .true.
    ignored = c_usleep(250000_c_int)
    if (allocated(values) .and. size(values) < 0) error stop
    call_entered = .false.
  end subroutine hold

  subroutine hold_plain(values)
    character(kind=c_char, len=4), intent(in) :: values(:)
    integer(c_int) :: ignored
    call_entered = .true.
    ignored = c_usleep(250000_c_int)
    if (size(values) < 0) error stop
    call_entered = .false.
  end subroutine hold_plain

  subroutine hold_flat(values)
    character(kind=c_char, len=4), intent(in) :: values(*)
    integer(c_int) :: ignored
    call_entered = .true.
    ignored = c_usleep(250000_c_int)
    if (len(values(1)) < 0) error stop
    call_entered = .false.
  end subroutine hold_flat

  subroutine hold_explicit(values)
    character(kind=c_char, len=4), intent(in) :: values(1)
    integer(c_int) :: ignored
    call_entered = .true.
    ignored = c_usleep(250000_c_int)
    if (len(values(1)) < 0) error stop
    call_entered = .false.
  end subroutine hold_explicit

  logical function entered() result(value)
    value = call_entered
  end function entered
end module fcharacter_owner_nogil
"""


@pytest.mark.parametrize("deferred", [False, True], ids=["fixed-width", "deferred-width"])
def test_close_waits_for_active_nogil_owner_and_ordinary_calls(tmp_path: Path, deferred: bool):
    source = tmp_path / "fcharacter_owner_nogil.f90"
    native_source = NOGIL_SOURCE
    if deferred:
        native_source = native_source.replace("len=4), allocatable", "len=:), allocatable").replace(
            "allocate(values(1))", "allocate(character(kind=c_char, len=4) :: values(1))"
        )
    source.write_text(native_source, encoding="utf-8")
    native_object = _compile_native_object(source, tmp_path / "native")
    contract = tmp_path / "fcharacter_owner_nogil.pyi"
    contract_source = """from prik.contracts import Allocatable, Bool, Flat, String, nogil

@nogil
def hold(values: Allocatable[String[4][:]]) -> None: ...
@nogil
def hold_plain(values: String[4][:]) -> None: ...
@nogil
def hold_flat(values: String[4][Flat]) -> None: ...
@nogil
def hold_explicit(values: String[4][1]) -> None: ...
def initialize(values: Allocatable[String[4][:]]) -> None: ...
def entered() -> Bool: ...
"""
    if deferred:
        contract_source = contract_source.replace("Allocatable[String[4]", "Allocatable[String[:]")
    contract.write_text(contract_source, encoding="utf-8")
    result = build_pyi_extension(
        contract,
        input_compiler=_compiler(),
        native_objects=[native_object],
        native_include_dirs=[native_object.parent],
        output_dir=tmp_path / "build",
    )
    module = _sole_native_module(_import_from_build_dir(result.module_name, result.output_dir))

    def call_native(operation_name: str, values, failures: list[BaseException]) -> None:
        try:
            getattr(module, operation_name)(values)
        except BaseException as error:  # pragma: no cover - asserted below
            failures.append(error)

    for operation_name in ("hold", "hold_plain", "hold_flat", "hold_explicit"):
        values = Allocatable[String[:][:]]() if deferred else Allocatable[String[4][:]]()
        module.initialize(values)
        failures: list[BaseException] = []

        worker = threading.Thread(target=call_native, args=(operation_name, values, failures))
        worker.start()
        deadline = time.monotonic() + 2.0
        while not module.entered() and time.monotonic() < deadline:
            time.sleep(0.005)
        assert module.entered() is True, (operation_name, failures)

        values.close()
        worker.join(timeout=2.0)

        assert worker.is_alive() is False
        assert failures == []
        assert values.closed is True
