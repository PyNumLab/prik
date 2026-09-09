"""Module variables, parameters, saved state, and synchronization tests."""

import gc
from pathlib import Path

import numpy as np
import pytest
from prik.runtime.handles import AllocatableArray
from tests.fortran._support.wrapper_build import (
    _build_source_or_generated_pyi_and_import,
    _build_text_and_import,
)

FIXTURES = Path(__file__).parent / "fixtures"
DERIVED_ALIAS_F90_SOURCE = FIXTURES / "native" / "fmodule_derived_alias_f90.f90"
CONTRACT_FIXTURES = FIXTURES / "contracts"
pytestmark = pytest.mark.fortran_end_to_end


def _module_variables_build_dir(tmp_path: Path, build_mode: str) -> Path:
    if build_mode == "source":
        return tmp_path / "source_build"
    return tmp_path / "generated_pyi_build" / "pyi_build"


def test_aliased_derived_module_object_borrows_native_state(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    module = _build_source_or_generated_pyi_and_import(
        DERIVED_ALIAS_F90_SOURCE,
        tmp_path,
        {
            "bind_c_fmodule_derived_alias_f90_wrapper.f90",
            "fmodule_derived_alias_f90_wrapper.c",
            "fmodule_derived_alias_f90_wrapper.h",
        },
        CONTRACT_FIXTURES / "fmodule_derived_alias_f90",
        pyi_parity_build_mode,
    )

    current = module.current
    assert isinstance(current, module.box)
    values = current.values
    assert isinstance(values, AllocatableArray)
    assert values.owner is current
    assert values.allocated is False
    assert values.to_numpy() is None

    module.allocate_current(np.int32(3))
    view = values.to_numpy()
    np.testing.assert_allclose(view, np.array([1.0, 2.0, 3.0], dtype=np.float64))

    view[0] = np.float64(10.0)
    assert module.current_sum() == np.float64(15.0)
    assert module.current.values_sum() == np.float64(15.0)

    owned = module.box()
    owned.allocate_values(np.int32(2))
    owned.values.to_numpy()[0] = np.float64(20.0)
    assert owned.values_sum() == np.float64(22.0)
    assert module.current_sum() == np.float64(15.0)

    del view
    del current
    gc.collect()
    assert module.current_sum() == np.float64(15.0)

    with np.testing.assert_raises(AttributeError):
        module.current = owned

    build_dir = _module_variables_build_dir(tmp_path, pyi_parity_build_mode)
    bridge_source = (build_dir / "bind_c_fmodule_derived_alias_f90_wrapper.f90").read_text(encoding="utf-8")
    assert "c_loc(native_current)" in bridge_source
    assert "bind_c_set_current" not in bridge_source

    module.deallocate_current()
    current_values = module.current.values
    assert isinstance(current_values, AllocatableArray)
    assert current_values.allocated is False
    assert current_values.to_numpy() is None


PLAIN_DERIVED_ARRAY_FIELD_SOURCE = """
module fplain_derived_fields_f90
  use iso_fortran_env, only: int32, real64
  implicit none

  type :: box
    real(real64) :: grid(2, 3)
    integer(int32) :: n
  end type box

  type(box) :: plain_box
  type(box), target :: tgt_box

contains
  function make_box(seed) result(value)
    real(real64), intent(in) :: seed
    type(box) :: value
    value%grid = seed
    value%n = 3
  end function make_box

  subroutine touch_plain()
    plain_box%grid(1, 1) = plain_box%grid(1, 1) + 1.0d0
  end subroutine touch_plain
end module fplain_derived_fields_f90
"""


def test_derived_array_fields_are_live_views_without_a_target_declaration(tmp_path: Path):
    """An ordinary array component is borrowed live wherever its owner comes from.

    A derived field's address never comes from `c_loc` on the field, so `target`
    on the component, the type, or the containing module variable changes
    nothing. The owner is reached as a Fortran pointer and its component is
    handed to a C consumer during the call, which is what makes the borrow work
    for a wrapper-owned instance and for a plain module object alike.
    """
    module = _build_text_and_import(
        PLAIN_DERIVED_ARRAY_FIELD_SOURCE,
        "fplain_derived_fields_f90.f90",
        tmp_path,
        {
            "bind_c_fplain_derived_fields_f90_wrapper.f90",
            "fplain_derived_fields_f90_wrapper.c",
            "fplain_derived_fields_f90_wrapper.h",
        },
    )

    # A wrapper-owned instance borrows its own component storage.
    instance = module.make_box(np.float64(2.0))
    assert instance.grid.shape == (2, 3)
    assert instance.grid.flags["F_CONTIGUOUS"] is True
    instance.grid[0, 0] = np.float64(9.0)
    assert instance.grid[0, 0] == np.float64(9.0)

    # A module object without `target` borrows the same way, in both directions.
    module.plain_box.grid[0, 0] = np.float64(5.0)
    module.touch_plain()
    assert module.plain_box.grid[0, 0] == np.float64(6.0)

    # The addressable module object is no different.
    module.tgt_box.grid[1, 2] = np.float64(4.5)
    assert module.tgt_box.grid[1, 2] == np.float64(4.5)
