"""Compiled evidence for distinct derived-object runtime mechanisms."""

from __future__ import annotations

import gc
from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import (
    _build_source_and_import,
    _compile_native_object,
    _import_from_build_dir,
    _sole_native_module,
)
from prik import build_pyi_extension
from prik.runtime.handles import AllocatableArray
from tests.fortran._support.paths import FORTRAN_ROOT

FIXTURES = Path(__file__).parent / "fixtures"
EDITED_CONTRACTS = FIXTURES / "edited_contracts"
DERIVED_BOUNDARY_F90_SOURCE = FIXTURES / "native" / "fderived_boundary_f90.f90"
CONTRACT = EDITED_CONTRACTS / "opaque_boundary" / "__init__.pyi"
PLAIN_MODULE_SOURCE = FIXTURES / "native" / "fmodule_derived_snapshot_f90.f90"
PLAIN_MODULE_CONTRACT = EDITED_CONTRACTS / "module_live_proxy" / "__init__.pyi"
ALIASED_MODULE_SOURCE = FIXTURES / "native" / "fmodule_derived_alias_f90.f90"
ALIASED_MODULE_CONTRACT = EDITED_CONTRACTS / "module_aliased_proxy" / "__init__.pyi"
DERIVED_CONSTANT_SOURCE = FORTRAN_ROOT / "modules" / "end_to_end" / "fixtures" / "native" / "fmodule_vars_f90.f90"
pytestmark = pytest.mark.fortran_end_to_end
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
module derived_string_fields
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
end module derived_string_fields
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
module derived_value_arguments
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
end module derived_value_arguments
"""
VALUE_AND_OPTIONAL_CONTRACT = """\
from prik.contracts import Arg, Float64, Returns, Value, native_abi, native_call

@native_abi("c")
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
module derived_borrowed_finalizer
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
end module derived_borrowed_finalizer
"""
BORROWED_FINALIZER_CONTRACT = """\
from prik.contracts import Int32, destroy

class child:
    @destroy
    def cleanup_child(self) -> None: ...

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


def test_scalar_derived_objects_use_canonical_plan(tmp_path: Path):
    module, result = _build_point_boundary(tmp_path)
    _exercise_point_boundary(module)
    with pytest.raises(TypeError):
        module.point()

    generated_c = (result.output_dir / "opaque_boundary_wrapper.c").read_text(encoding="utf-8")
    generated_fortran = (result.output_dir / "bind_c_opaque_boundary_wrapper.f90").read_text(encoding="utf-8")
    assert "static PyObject * wrap_point_sum" in generated_c
    assert "@x.setter\\n    def x(self, value):" in generated_c
    assert "bind_c_prik_field_point_x_get" in generated_fortran
    assert "bind_c_prik_field_point_x_set" in generated_fortran
    assert "call native_make_point_out(p, x, y)" in generated_fortran
    assert "result = c_null_ptr" in generated_fortran
    assert "allocate(result_value, stat=prik_allocation_status)" in generated_fortran


def test_plain_module_derived_proxy_reads_and_writes_live_members(tmp_path: Path):
    native_object = _compile_native_object(PLAIN_MODULE_SOURCE, tmp_path / "native")
    result = build_pyi_extension(
        PLAIN_MODULE_CONTRACT,
        native_objects=[native_object],
        native_include_dirs=[native_object.parent],
        output_dir=tmp_path / "wrapper_plan",
    )
    module = _sole_native_module(_import_from_build_dir(result.module_name, result.output_dir))

    module.initialise_current(np.int32(2))
    first = module.current
    second = module.current
    assert isinstance(first, module.box)
    assert isinstance(second, module.box)
    assert first is not second
    assert first._prik_owner is module
    assert second._prik_owner is module
    assert first.scalar == np.int32(7)
    first_fixed = first.fixed
    np.testing.assert_allclose(first_fixed, np.array([1.5, 2.5], dtype=np.float64))
    assert first_fixed.base is first
    values = first.values
    assert isinstance(values, AllocatableArray)
    assert values.owner is first
    values_view = values.to_numpy()
    np.testing.assert_allclose(values_view, np.array([1.0, 2.0], dtype=np.float64))
    assert first.nested.id == np.int32(11)
    with pytest.raises(AttributeError):
        first.fixed = np.array([0.0, 0.0], dtype=np.float64)
    with pytest.raises(AttributeError):
        first.values = values

    first.scalar = np.int32(20)
    first_fixed[0] = np.float64(4.5)
    values_view[1] = np.float64(8.0)
    first.nested.id = np.int32(30)
    assert second.scalar == np.int32(20)
    np.testing.assert_allclose(second.fixed, np.array([4.5, 2.5], dtype=np.float64))
    assert second.nested.id == np.int32(30)
    assert module.current_total() == np.float64(66.0)

    child = first.nested
    assert child._prik_owner is first
    del first
    child.id = np.int32(31)
    assert module.current.nested.id == np.int32(31)

    module.mutate_current()
    assert second.scalar == np.int32(30)
    np.testing.assert_allclose(first_fixed, np.array([104.5, 102.5], dtype=np.float64))
    np.testing.assert_allclose(values_view, np.array([1001.0, 1008.0], dtype=np.float64))
    assert child.id == np.int32(131)

    independent = values.to_numpy().copy()
    values.resize((3,))
    replacement = values.to_numpy()
    replacement[:] = np.array([3.0, 4.0, 5.0], dtype=np.float64)
    np.testing.assert_allclose(values.to_numpy(), np.array([3.0, 4.0, 5.0], dtype=np.float64))
    np.testing.assert_allclose(independent, np.array([1001.0, 1008.0], dtype=np.float64))
    values.deallocate()
    assert values.to_numpy() is None
    with pytest.raises(AttributeError):
        module.current = second

    generated_fortran = (result.output_dir / "bind_c_module_live_proxy_wrapper.f90").read_text(encoding="utf-8")
    assert "c_loc(native_current)" not in generated_fortran
    assert "native_current%scalar" in generated_fortran
    assert "native_current%nested%id" in generated_fortran


def test_aliased_module_derived_object_uses_direct_live_field_handles(tmp_path: Path):
    native_object = _compile_native_object(ALIASED_MODULE_SOURCE, tmp_path / "native")
    result = build_pyi_extension(
        ALIASED_MODULE_CONTRACT,
        native_objects=[native_object],
        native_include_dirs=[native_object.parent],
        output_dir=tmp_path / "wrapper_plan",
    )
    module = _sole_native_module(_import_from_build_dir(result.module_name, result.output_dir))

    first = module.current
    second = module.current
    assert isinstance(first, module.box)
    assert first is not second
    assert first._prik_owner is module
    assert second._prik_owner is module
    first_values = first.values
    assert first_values.owner is first
    assert first_values.to_numpy() is None

    module.allocate_current(np.int32(3))
    first_view = first_values.to_numpy()
    np.testing.assert_allclose(first_view, np.array([1.0, 2.0, 3.0], dtype=np.float64))
    first_view[0] = np.float64(10.0)
    assert module.current_sum() == np.float64(15.0)
    np.testing.assert_allclose(second.values.to_numpy(), np.array([10.0, 2.0, 3.0], dtype=np.float64))

    detached = first_values.to_numpy().copy()
    module.deallocate_current()
    assert first_values.to_numpy() is None
    np.testing.assert_allclose(detached, np.array([10.0, 2.0, 3.0], dtype=np.float64))
    with pytest.raises(AttributeError):
        module.current = second

    generated_fortran = (result.output_dir / "bind_c_module_aliased_proxy_wrapper.f90").read_text(encoding="utf-8")
    assert "c_loc(native_current)" in generated_fortran


def test_derived_module_constant_returns_independent_owned_values(tmp_path: Path):
    native_object = _compile_native_object(DERIVED_CONSTANT_SOURCE, tmp_path / "native")
    contract = tmp_path / "contract" / "fmodule_vars_f90.pyi"
    contract.parent.mkdir()
    contract.write_text(DERIVED_CONSTANT_CONTRACT, encoding="utf-8")
    result = build_pyi_extension(
        contract,
        native_objects=[native_object],
        native_include_dirs=[native_object.parent],
        output_dir=tmp_path / "build",
    )
    module = _sole_native_module(_import_from_build_dir(result.module_name, result.output_dir))

    first = module.black
    second = module.black
    assert first is not second
    first.r = np.int32(17)
    assert first.r == np.int32(17)
    assert second.r == np.int32(0)
    assert module.black.r == np.int32(0)
    assert module.black_sum() == np.int32(0)

    bridge = (result.output_dir / "bind_c_fmodule_vars_f90_wrapper.f90").read_text(encoding="utf-8")
    assert "result = c_null_ptr" in bridge
    assert "allocate(value, stat=prik_allocation_status)" in bridge
    assert "value = native_black" in bridge
    assert "result = c_loc(value)" in bridge


def test_fixed_string_fields_use_canonical_plan(tmp_path: Path):
    source = tmp_path / "native" / "derived_string_fields.f90"
    source.parent.mkdir()
    source.write_text(STRING_FIELD_SOURCE, encoding="utf-8")
    native_object = _compile_native_object(source, tmp_path / "native_build")

    contract = tmp_path / "contract" / "derived_string_fields.pyi"
    contract.parent.mkdir()
    contract.write_text(STRING_FIELD_CONTRACT, encoding="utf-8")
    result = build_pyi_extension(
        contract,
        native_objects=[native_object],
        native_include_dirs=[native_object.parent],
        output_dir=tmp_path / "build",
    )
    module = _sole_native_module(_import_from_build_dir(result.module_name, result.output_dir))

    current = module.current
    assert current.label == "start   "
    current.label = "edited  "
    assert module.current_label() == "edited  "
    module.reset_label()
    assert current.label == "native  "
    with pytest.raises(TypeError, match="exactly 8 bytes"):
        current.label = "short"


def test_value_copy_and_optional_derived_inputs_match_source_oracle(tmp_path: Path):
    source = tmp_path / "source" / "derived_value_arguments.f90"
    source.parent.mkdir()
    source.write_text(VALUE_AND_OPTIONAL_SOURCE, encoding="utf-8")
    source_module = _build_source_and_import(
        source,
        tmp_path / "source_build",
        {
            "bind_c_derived_value_arguments_wrapper.f90",
            "derived_value_arguments_wrapper.c",
            "derived_value_arguments_wrapper.h",
        },
    )

    native_object = _compile_native_object(source, tmp_path / "native")
    contract = tmp_path / "contract" / "derived_value_arguments.pyi"
    contract.parent.mkdir()
    contract.write_text(VALUE_AND_OPTIONAL_CONTRACT, encoding="utf-8")
    result = build_pyi_extension(
        contract,
        native_objects=[native_object],
        native_include_dirs=[native_object.parent],
        output_dir=tmp_path / "contract_build",
    )
    direct_module = _sole_native_module(_import_from_build_dir(result.module_name, result.output_dir))

    for module in (source_module, direct_module):
        point = module.make_point(np.float64(1.0), np.float64(2.0))
        assert module.score_by_value(point) == np.float64(103.0)
        assert point.x == np.float64(1.0)
        assert point.y == np.float64(2.0)
        assert module.optional_sum() == np.float64(-1.0)
        assert module.optional_sum(None) == np.float64(-1.0)
        assert module.optional_sum(point) == np.float64(3.0)

    source_point = source_module.make_point(np.float64(1.0), np.float64(2.0))
    assert source_module.update_point(source_point) is None
    assert source_point.x == np.float64(11.0)
    assert source_point.y == np.float64(22.0)
    source_filled = source_module.point()
    assert source_module.fill_point(source_filled) is None
    assert source_filled.x == np.float64(31.0)
    assert source_filled.y == np.float64(32.0)

    direct_point = direct_module.make_point(np.float64(1.0), np.float64(2.0))
    assert direct_module.update_point(direct_point) is direct_point
    assert direct_point.x == np.float64(11.0)
    assert direct_point.y == np.float64(22.0)
    assert direct_module.fill_point(direct_point) is direct_point
    assert direct_point.x == np.float64(31.0)
    assert direct_point.y == np.float64(32.0)

    with pytest.raises(TypeError, match="Expected exact wrapper type point"):
        direct_module.optional_sum(object())

    bridge = (result.output_dir / "bind_c_derived_value_arguments_wrapper.f90").read_text(encoding="utf-8")
    assert "type(prik_type_point), pointer :: value" in bridge
    assert "native_score_by_value(value)" in bridge


def test_borrowed_child_retains_owner_and_finalizes_exactly_once(tmp_path: Path):
    source = tmp_path / "source" / "derived_borrowed_finalizer.f90"
    source.parent.mkdir()
    source.write_text(BORROWED_FINALIZER_SOURCE, encoding="utf-8")
    native_object = _compile_native_object(source, tmp_path / "native")
    contract = tmp_path / "contract" / "derived_borrowed_finalizer.pyi"
    contract.parent.mkdir()
    contract.write_text(BORROWED_FINALIZER_CONTRACT, encoding="utf-8")
    result = build_pyi_extension(
        contract,
        native_objects=[native_object],
        native_include_dirs=[native_object.parent],
        output_dir=tmp_path / "build",
    )
    module = _sole_native_module(_import_from_build_dir(result.module_name, result.output_dir))

    owner = module.make_parent()
    module.reset_final_count()
    borrowed = owner.value
    assert borrowed._prik_owner is owner
    del owner
    gc.collect()
    assert module.get_final_count() == np.int32(0)

    del borrowed
    gc.collect()
    gc.collect()
    assert module.get_final_count() == np.int32(1)
