"""Fixed-form and modern scalar character argument/result tests."""

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import (
    _compile_native_object,
    _import_from_build_dir,
    _sole_native_module,
)
from x2py import build_pyi_extension

pytestmark = pytest.mark.fortran_end_to_end


def _build_contract_module(contract: Path, native_object: Path, output_dir: Path, symbol: str):
    """Build one edited character contract through the canonical wrapper plan."""
    result = build_pyi_extension(
        contract,
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
  use iso_c_binding, only: c_char
contains
  subroutine make_names(names)
    character(kind=c_char, len=:), allocatable, intent(out) :: names(:)
    allocate(character(kind=c_char, len=3) :: names(2))
    names = [character(kind=c_char, len=3) :: "red", "sky"]
  end subroutine make_names

  function make_names_function() result(names)
    character(kind=c_char, len=:), allocatable :: names(:)
    allocate(character(kind=c_char, len=4) :: names(2))
    names = [character(kind=c_char, len=4) :: "gold", "blue"]
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
from x2py.contracts import Allocatable, Arg, Int32, Return, Returns, String, native_call

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

    assert module.replace_names(handle) is handle
    assert handle.dtype == np.dtype("S5")
    assert handle.to_numpy().tolist() == [b"red  ", b"blue "]

    direct_handle = module.make_names_function()
    assert direct_handle.allocated is True
    assert direct_handle.dtype == np.dtype("S4")
    assert direct_handle.to_numpy().tolist() == [b"gold", b"blue"]
    assert module.maybe_name(np.int32(0)) is None
    assert module.maybe_name(np.int32(1)) == "blue"
