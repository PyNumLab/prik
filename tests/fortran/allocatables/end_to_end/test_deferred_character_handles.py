"""Deferred-length character-array ownership and descriptor handoff."""

from pathlib import Path
import shutil

import numpy as np
import pytest
import sys

from tests.fortran._support.wrapper_build import (
    _build_text_and_import,
    _compile_native_object,
    _compiler,
    _import_from_build_dir,
    _sole_native_module,
)
from prik import build_pyi_extension
from prik.contracts import Allocatable, String

pytestmark = pytest.mark.fortran_end_to_end


def _build_contract_module(contract: Path, native_object: Path, output_dir: Path, symbol: str):
    """Build one edited character contract through the canonical wrapper plan."""
    result = build_pyi_extension(
        contract,
        input_compiler=_compiler(),
        native_objects=[native_object],
        native_include_dirs=[native_object.parent],
        output_dir=output_dir,
    )
    package = _import_from_build_dir(result.module_name, result.output_dir)
    return package if hasattr(package, symbol) else _sole_native_module(package)


def test_deferred_character_array_handles_use_canonical_plan(tmp_path: Path):
    """Keep runtime element width and projected identity on one shared handle path."""
    module_name = "deferred_character_handles_plan"
    source = tmp_path / f"{module_name}.f90"
    source.write_text(
        f"""
module {module_name}
  use iso_c_binding, only: c_char, c_intptr_t, c_loc
  integer(c_intptr_t) :: last_address = 0
contains
  function allocation_address() result(address)
    integer(c_intptr_t) :: address
    address = last_address
  end function

  subroutine make_names(names)
    character(kind=c_char, len=:), allocatable, target, intent(out) :: names(:)
    allocate(character(kind=c_char, len=3) :: names(2))
    names = [character(kind=c_char, len=3) :: "red", "sky"]
    last_address = transfer(c_loc(names), last_address)
  end subroutine make_names

  function make_names_function() result(names)
    character(kind=c_char, len=:), allocatable, target :: names(:)
    allocate(character(kind=c_char, len=4) :: names(2))
    names = [character(kind=c_char, len=4) :: "gold", "blue"]
    last_address = transfer(c_loc(names), last_address)
  end function make_names_function

  subroutine maybe_name(flag, name)
    integer(kind=4), intent(in) :: flag
    character(kind=c_char, len=:), allocatable, intent(out) :: name
    if (flag /= 0) then
      allocate(character(kind=c_char, len=4) :: name)
      name = "blue"
    end if
  end subroutine maybe_name

  subroutine replace_names(names)
    character(kind=c_char, len=:), allocatable, intent(inout) :: names(:)
    integer :: count
    count = 2
    if (allocated(names)) count = size(names)
    if (allocated(names)) deallocate(names)
    allocate(character(kind=c_char, len=5) :: names(count))
    names = "     "
    if (count >= 1) names(1) = "red"
    if (count >= 2) names(2) = "blue"
  end subroutine replace_names
end module {module_name}
""",
        encoding="utf-8",
    )
    contract = tmp_path / f"{module_name}.pyi"
    contract.write_text(
        """
from prik.contracts import Allocatable, Arg, Int32, Int64, Return, Returns, String, native_call

def allocation_address() -> Int64: ...

@native_call([Return("names", 0)])
def make_names() -> Allocatable[String[:][:]]: ...

def make_names_function() -> Allocatable[String[:][:]]: ...

@native_call([Arg(0), Allocatable(Return("name", 0))])
def maybe_name(flag: Int32) -> String | None: ...

def replace_names(
    names: Allocatable[String[:][:]],
) -> Returns["names", Allocatable[String[:][:]]]: ...
""",
        encoding="utf-8",
    )
    native_object = _compile_native_object(source, tmp_path / "native_character_handles")
    module = _build_contract_module(contract, native_object, tmp_path / "build", "make_names")
    handle = module.make_names()
    assert handle.allocated is True
    assert handle.dtype == np.dtype("S3")
    assert handle.to_numpy().tolist() == [b"red", b"sky"]
    assert handle.to_numpy().ctypes.data == module.allocation_address()

    handle.resize(3, element_length=4)
    assert handle.shape == (3,)
    assert handle.dtype == np.dtype("S4")
    with pytest.raises(TypeError, match="needs an element_length"):
        handle.resize(2)

    caller_created = Allocatable[String[:][:]]()
    assert module.replace_names(caller_created) is caller_created
    assert caller_created.dtype == np.dtype("S5")
    assert caller_created.to_numpy().tolist() == [b"red  ", b"blue "]

    fixed_width = Allocatable[String[4][:]]()
    with pytest.raises(TypeError, match="does not match a deferred-length character array"):
        module.replace_names(fixed_width)

    assert module.replace_names(handle) is handle
    assert handle.dtype == np.dtype("S5")
    assert handle.to_numpy().tolist() == [b"red  ", b"blue ", b"     "]

    direct_handle = module.make_names_function()
    assert direct_handle.allocated is True
    assert direct_handle.dtype == np.dtype("S4")
    assert direct_handle.to_numpy().tolist() == [b"gold", b"blue"]
    direct_handle.deallocate()
    assert not direct_handle.allocated
    assert direct_handle.shape is None
    assert direct_handle.to_numpy() is None
    assert module.replace_names(direct_handle) is direct_handle
    assert direct_handle.dtype == np.dtype("S5")
    events = []
    previous = sys.getprofile()
    try:
        sys.setprofile(lambda _frame, event, _arg: events.append(event) if event == "call" else None)
        module.replace_names(direct_handle)
    finally:
        sys.setprofile(previous)
    assert events == []
    assert module.maybe_name(np.int32(0)) is None
    assert module.maybe_name(np.int32(1)) == "blue"


def test_deferred_character_owners_compose_with_borrowed_matrix_handles(tmp_path: Path):
    """Owner results, module variables and fields share descriptor call semantics."""
    module = _build_text_and_import(
        """
module deferred_owner_matrix
  use iso_c_binding, only: c_char, c_int, c_int64_t, c_loc
  implicit none
  type container
    character(kind=c_char, len=:), allocatable :: values(:, :)
  end type
  type(container) :: parent
  character(kind=c_char, len=:), allocatable :: saved(:, :)
  integer(c_int64_t), private :: last_address = 0
contains
  subroutine setup()
    allocate(character(len=2) :: saved(1, 2), parent%values(2, 1))
    saved = 'ab'
    parent%values = 'cd'
  end subroutine
  subroutine make_matrix(n, values)
    integer(c_int), intent(in) :: n
    character(kind=c_char, len=:), allocatable, target, intent(out) :: values(:, :)
    if (n < 0) return
    allocate(character(len=4) :: values(n, 2))
    values = 'gold'
    last_address = transfer(c_loc(values), last_address)
  end subroutine
  function allocation_address() result(address)
    integer(c_int64_t) :: address
    address = last_address
  end function
  subroutine rewrite(a, b)
    character(kind=c_char, len=:), allocatable, intent(inout) :: a(:, :), b(:, :)
    if (allocated(a)) deallocate(a)
    if (allocated(b)) deallocate(b)
    allocate(character(len=3) :: a(2, 3), b(3, 2))
    a = 'one'
    b = 'two'
  end subroutine
  integer(c_int) function inspect(values) result(state)
    character(kind=c_char, len=:), allocatable, optional, intent(in) :: values(:, :)
    state = -1
    if (.not. present(values)) return
    state = 0
    if (allocated(values)) state = 100 * size(values, 1) + 10 * size(values, 2) + len(values)
  end function
  subroutine stamp(values) bind(c)
    character(kind=c_char, len=:), allocatable, intent(inout) :: values(:, :)
    if (allocated(values)) values(1, 1) = 'yes'
  end subroutine
end module
""",
        "deferred_owner_matrix.f90",
        tmp_path,
        {
            "bind_c_deferred_owner_matrix_wrapper.f90",
            "deferred_owner_matrix_wrapper.c",
            "deferred_owner_matrix_wrapper.h",
        },
    )
    module.setup()
    owner = module.make_matrix(np.int32(2))
    view = owner.to_numpy()
    assert view.ctypes.data == module.allocation_address()
    assert view.shape == (2, 2)
    assert view.tolist() == [[b"gold", b"gold"], [b"gold", b"gold"]]
    assert module.inspect(owner) == 224
    assert module.inspect() == -1
    assert module.inspect(None) == -1

    module.stamp(owner)
    assert view.tolist() == [[b"yes ", b"gold"], [b"gold", b"gold"]]
    del view
    module.rewrite(owner, module.saved)
    assert owner.shape == (2, 3)
    assert module.saved.shape == (3, 2)
    assert np.all(owner.to_numpy() == b"one")
    assert np.all(module.saved.to_numpy() == b"two")
    module.rewrite(module.parent.values, owner)
    assert module.parent.values.shape == (2, 3)
    assert np.all(module.parent.values.to_numpy() == b"one")
    assert owner.shape == (3, 2)

    empty = module.make_matrix(np.int32(0))
    assert empty.allocated
    assert empty.shape == (0, 2)
    assert empty.dtype == np.dtype("S4")
    assert empty.to_numpy().shape == (0, 2)
    absent = module.make_matrix(np.int32(-1))
    assert not absent.allocated
    assert module.inspect(absent) == 0
    assert absent.to_numpy() is None
    module.rewrite(absent, empty)
    assert absent.shape == (2, 3)
    assert empty.shape == (3, 2)
    absent.close()
    empty.close()
    owner.close()


@pytest.mark.parametrize("cross_compiler", [False, True], ids=["matching-compiler", "different-compiler"])
def test_deferred_owner_descriptor_exchange_checks_the_producer_abi(tmp_path, monkeypatch, cross_compiler):
    """An owner projects descriptors only to a compatible compiler runtime."""
    producer_compiler = _compiler()
    consumer_compiler = producer_compiler
    if cross_compiler:
        consumer_compiler = shutil.which("gfortran" if "ifx" in producer_compiler else "ifx")
        if consumer_compiler is None:
            pytest.skip("two Fortran compiler families are needed for this check")
    modules = []
    for index, compiler in enumerate((producer_compiler, consumer_compiler)):
        name = f"deferred_exchange_{index}"
        workdir = tmp_path / name
        workdir.mkdir()
        monkeypatch.setenv("PRIK_TEST_FORTRAN_COMPILER", compiler)
        modules.append(
            _build_text_and_import(
                f"""
module {name}
  use iso_c_binding, only: c_char, c_int
contains
  subroutine make(values)
    character(kind=c_char, len=:), allocatable, intent(out) :: values(:)
    allocate(character(len=4) :: values(2))
    values = 'abcd'
  end subroutine
  subroutine replace(values)
    character(kind=c_char, len=:), allocatable, intent(inout) :: values(:)
    if (allocated(values)) deallocate(values)
    allocate(character(len=3) :: values(3))
    values = 'xyz'
  end subroutine
  integer(c_int) function state(values) bind(c, name="state_{index}")
    character(kind=c_char, len=:), allocatable, intent(in) :: values(:)
    state = 0
    if (allocated(values)) state = size(values) * 100 + len(values)
  end function
end module
""",
                f"{name}.f90",
                workdir,
                {f"bind_c_{name}_wrapper.f90", f"{name}_wrapper.c", f"{name}_wrapper.h"},
            )
        )
    first, second = modules
    handle = first.make()
    try:
        if cross_compiler:
            with pytest.raises(TypeError, match="different Fortran compiler ABI"):
                second.state(handle)
        else:
            assert second.state(handle) == 204
            assert second.replace(handle) is handle
            assert first.state(handle) == 303
            assert handle.to_numpy().tolist() == [b"xyz"] * 3
            handle.deallocate()
            assert second.state(handle) == 0
            second.replace(handle)
            assert first.state(handle) == 303
    finally:
        handle.close()
