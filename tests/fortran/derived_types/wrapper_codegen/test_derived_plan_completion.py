"""Compiled canonical wrapper-plan coverage for derived-object lanes."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import (
    _compile_native_object,
    _import_from_build_dir,
    _sole_native_module,
)
from prik import build_pyi_extension

FINAL_FIXTURES = Path(__file__).parents[2] / "derived_types" / "end_to_end" / "fixtures"
DERIVED_BOUNDARY_F90_SOURCE = FINAL_FIXTURES / "fderived_boundary_f90.f90"
CONTRACT = FINAL_FIXTURES / "edited_contracts" / "opaque_boundary" / "__init__.pyi"
PLAIN_MODULE_SOURCE = FINAL_FIXTURES / "fmodule_derived_snapshot_f90.f90"
PLAIN_MODULE_CONTRACT = FINAL_FIXTURES / "edited_contracts" / "module_live_proxy" / "__init__.pyi"
ALIASED_MODULE_SOURCE = FINAL_FIXTURES / "fmodule_derived_alias_f90.f90"
ALIASED_MODULE_CONTRACT = FINAL_FIXTURES / "edited_contracts" / "module_aliased_proxy" / "__init__.pyi"
DERIVED_CONSTANT_SOURCE = Path(__file__).parents[2] / "modules" / "end_to_end" / "fixtures" / "fmodule_vars_f90.f90"
DERIVED_CONSTANT_CONTRACT = """\
from prik.contracts import Final, Int32

class rgb_color:
    r: Int32
    g: Int32
    b: Int32

black: Final[rgb_color]

def black_sum() -> Int32: ...
"""
STRING_FIELD_SOURCE = """\
module fderived_string_plan
  implicit none

  type :: record
    character(len=8) :: label = 'start   '
  end type record

  type(record), target :: current
contains
  function current_label() result(value)
    character(len=8) :: value
    value = current%label
  end function current_label

  subroutine reset_label()
    current%label = 'native  '
  end subroutine reset_label
end module fderived_string_plan
"""
STRING_FIELD_CONTRACT = """\
from prik.contracts import Aliased, Annotated, String

class record:
    label: String[8]

current: Annotated[record, Aliased]

def current_label() -> String[8]: ...
def reset_label() -> None: ...
"""
VALUE_AND_OPTIONAL_SOURCE = """\
module fderived_value_plan
  use iso_c_binding
  implicit none

  type, bind(c) :: point
    real(c_double) :: x
    real(c_double) :: y
  end type point
contains
  function make_point(x, y) result(value)
    real(c_double), intent(in) :: x
    real(c_double), intent(in) :: y
    type(point) :: value
    value%x = x
    value%y = y
  end function make_point

  function score_by_value(value) result(total)
    type(point), value :: value
    real(c_double) :: total
    value%x = value%x + 100.0_c_double
    total = value%x + value%y
  end function score_by_value

  function optional_sum(value) result(total)
    type(point), optional, intent(in) :: value
    real(c_double) :: total
    if (present(value)) then
      total = value%x + value%y
    else
      total = -1.0_c_double
    end if
  end function optional_sum

  subroutine update_point(value)
    type(point), intent(inout) :: value
    value%x = value%x + 10.0_c_double
    value%y = value%y + 20.0_c_double
  end subroutine update_point

  subroutine fill_point(value)
    type(point), intent(out) :: value
    value%x = 31.0_c_double
    value%y = 32.0_c_double
  end subroutine fill_point
end module fderived_value_plan
"""
VALUE_AND_OPTIONAL_CONTRACT = """\
from prik.contracts import Arg, Float64, Returns, Value, native_call, native_type

@native_type(attributes=("bind(c)",))
class point:
    x: Float64
    y: Float64

def make_point(x: Float64, y: Float64) -> point: ...
@native_call([Value(Arg(0))])
def score_by_value(value: point) -> Float64: ...
def optional_sum(value: point | None = ...) -> Float64: ...
def update_point(value: point) -> Returns["value", point]: ...
def fill_point(value: point) -> Returns["value", point]: ...
"""
# GCC 13.2 PR113885 ICEs on function-result assignment when a finalizable type
# has no data components. The marker keeps this lifetime test on its intended path.
BORROWED_FINALIZER_SOURCE = """\
module fderived_finalizer_plan
  implicit none
  integer :: final_count = 0

  type :: child
    integer :: marker = 0
  contains
    final :: cleanup_child
  end type child

  type :: parent
    type(child) :: value
  end type parent
contains
  subroutine cleanup_child(self)
    type(child) :: self
    final_count = final_count + 1
  end subroutine cleanup_child

  function make_parent() result(value)
    type(parent) :: value
  end function make_parent

  function get_final_count() result(value)
    integer :: value
    value = final_count
  end function get_final_count

  subroutine reset_final_count()
    final_count = 0
  end subroutine reset_final_count
end module fderived_finalizer_plan
"""
BORROWED_FINALIZER_CONTRACT = """\
from prik.contracts import Int32, native_type

@native_type(finalizers=("cleanup_child",))
class child:
    pass

class parent:
    value: child

def make_parent() -> parent: ...
def get_final_count() -> Int32: ...
def reset_final_count() -> None: ...
"""


def _build_point_boundary(tmp_path: Path):
    native_object = _compile_native_object(DERIVED_BOUNDARY_F90_SOURCE, tmp_path / "native")
    result = build_pyi_extension(
        CONTRACT,
        native_objects=[native_object],
        native_include_dirs=[native_object.parent],
        output_dir=tmp_path / "build",
    )
    module = _sole_native_module(_import_from_build_dir(result.module_name, result.output_dir))
    return module, result


def _exercise_point_boundary(module):
    point = module.make_point(np.float64(1.0), np.float64(2.0))
    assert isinstance(point, module.point)
    assert point.x == np.float64(1.0)
    assert point.y == np.float64(2.0)
    assert module.point_sum(point) == np.float64(3.0)

    point.x = np.float64(4.0)
    point.y = np.float64(5.0)
    assert module.point_sum(point) == np.float64(9.0)

    identity = id(point)
    assert module.move_point(point, np.float64(2.0), np.float64(3.0)) is None
    assert id(point) == identity
    assert point.x == np.float64(6.0)
    assert point.y == np.float64(8.0)

    output = module.make_point(np.float64(0.0), np.float64(0.0))
    assert module.make_point_out(output, np.float64(10.0), np.float64(11.0)) is None
    assert output.x == np.float64(10.0)
    assert output.y == np.float64(11.0)

    with pytest.raises(TypeError, match="Expected"):
        point.x = 12.0
