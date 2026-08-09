"""End-to-end declaration expressions across every array declaration owner."""

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import (
    _build_inline_pyi_contract_module,
    _build_sources_and_import,
    _build_text_and_import,
)


pytestmark = pytest.mark.fortran_end_to_end


SOURCE = """
module declaration_extent_expressions
  use, intrinsic :: iso_c_binding, only: c_double
  implicit none

  integer, parameter :: base_extent = 2
  integer, parameter :: field_extent = max(3, base_extent + 1)

  type :: record
    real(c_double) :: values(field_extent)
  end type record

  real(c_double), target :: module_values(base_extent ** 2)
  type(record), target :: current

contains

  pure integer function local_extent(n) result(extent)
    integer, intent(in) :: n
    extent = max(0, n)
  end function local_extent

  subroutine initialize_state()
    module_values = [1.0_c_double, 2.0_c_double, 3.0_c_double, 4.0_c_double]
    current%values = [5.0_c_double, 6.0_c_double, 7.0_c_double]
  end subroutine initialize_state

  subroutine exercise_inquiries( &
      source, destination, total, rank_values, reduced, constructed, conditional, lower_bound, upper_bound)
    real(c_double), intent(in) :: source(2:, 2:)
    real(c_double), intent(out) :: destination( &
      ubound(source, 1) - lbound(source, 1) + 1, &
      max(1, size(source, dim=2, kind=8)))
    real(c_double), intent(out) :: total(size(source, kind=8))
    real(c_double), intent(out) :: rank_values(2 ** rank(source))
    real(c_double), intent(out) :: reduced(sum(shape(source, kind=8)))
    real(c_double), intent(out) :: constructed(product((/ size(source, 1), 1 /)))
    real(c_double), intent(out) :: conditional(merge(size(source, 1), 1, size(source, 2) > 0))
    real(c_double), intent(out) :: lower_bound(lbound(source, 1))
    real(c_double), intent(out) :: upper_bound(ubound(source, 1))

    destination = source
    total = reshape(source, [size(source)])
    rank_values = 8.0_c_double
    reduced = 9.0_c_double
    constructed = 10.0_c_double
    conditional = 11.0_c_double
    lower_bound = 12.0_c_double
    upper_bound = 13.0_c_double
  end subroutine exercise_inquiries

  function copied(source) result(values)
    real(c_double), intent(in) :: source(:, :)
    real(c_double) :: values(size(source, 1), size(source, 2))
    values = source
  end function copied

  function local_extent_values(n) result(values)
    integer, intent(in) :: n
    real(c_double) :: values(local_extent(n))
    values = 14.0_c_double
  end function local_extent_values

  subroutine fill_local_extent(n, values)
    integer, intent(in) :: n
    real(c_double), intent(out) :: values(local_extent(n))
    values = 15.0_c_double
  end subroutine fill_local_extent

end module declaration_extent_expressions
"""


def test_all_array_declaration_owners_and_supported_extent_forms_execute(tmp_path: Path):
    module = _build_text_and_import(
        SOURCE,
        "declaration_extent_expressions.f90",
        tmp_path,
        {
            "bind_c_declaration_extent_expressions_wrapper.f90",
            "declaration_extent_expressions_wrapper.c",
            "declaration_extent_expressions_wrapper.h",
        },
    )

    assert module.initialize_state() is None
    np.testing.assert_array_equal(module.module_values, np.arange(1.0, 5.0, dtype=np.float64))
    np.testing.assert_array_equal(module.current.values, np.arange(5.0, 8.0, dtype=np.float64))

    source = np.asfortranarray(np.arange(1.0, 7.0, dtype=np.float64).reshape((2, 3), order="F"))
    destination = np.empty(source.shape, dtype=np.float64, order="F")
    total = np.empty(source.size, dtype=np.float64)
    rank_values = np.empty(2**source.ndim, dtype=np.float64)
    reduced = np.empty(sum(source.shape), dtype=np.float64)
    constructed = np.empty(source.shape[0], dtype=np.float64)
    conditional = np.empty(source.shape[0], dtype=np.float64)
    lower_bound = np.empty(2, dtype=np.float64)
    upper_bound = np.empty(source.shape[0] + 1, dtype=np.float64)

    assert (
        module.exercise_inquiries(
            source,
            destination,
            total,
            rank_values,
            reduced,
            constructed,
            conditional,
            lower_bound,
            upper_bound,
        )
        is None
    )
    np.testing.assert_array_equal(destination, source)
    np.testing.assert_array_equal(total, source.reshape(-1, order="F"))
    np.testing.assert_array_equal(rank_values, np.full(2**source.ndim, 8.0))
    np.testing.assert_array_equal(reduced, np.full(sum(source.shape), 9.0))
    np.testing.assert_array_equal(constructed, np.full(source.shape[0], 10.0))
    np.testing.assert_array_equal(conditional, np.full(source.shape[0], 11.0))
    np.testing.assert_array_equal(lower_bound, np.full(2, 12.0))
    np.testing.assert_array_equal(upper_bound, np.full(source.shape[0] + 1, 13.0))

    empty_source = np.empty((0, 3), dtype=np.float64, order="F")
    empty_destination = np.empty(empty_source.shape, dtype=np.float64, order="F")
    empty_total = np.empty(0, dtype=np.float64)
    empty_rank_values = np.empty(2**empty_source.ndim, dtype=np.float64)
    empty_reduced = np.empty(sum(empty_source.shape), dtype=np.float64)
    empty_constructed = np.empty(empty_source.shape[0], dtype=np.float64)
    empty_conditional = np.empty(0, dtype=np.float64)
    empty_lower_bound = np.empty(1, dtype=np.float64)
    empty_upper_bound = np.empty(0, dtype=np.float64)

    assert (
        module.exercise_inquiries(
            empty_source,
            empty_destination,
            empty_total,
            empty_rank_values,
            empty_reduced,
            empty_constructed,
            empty_conditional,
            empty_lower_bound,
            empty_upper_bound,
        )
        is None
    )
    np.testing.assert_array_equal(empty_destination, empty_source)
    np.testing.assert_array_equal(empty_total, np.empty(0, dtype=np.float64))
    np.testing.assert_array_equal(empty_rank_values, np.full(2**empty_source.ndim, 8.0))
    np.testing.assert_array_equal(empty_reduced, np.full(sum(empty_source.shape), 9.0))
    np.testing.assert_array_equal(empty_constructed, np.full(empty_source.shape[0], 10.0))
    np.testing.assert_array_equal(empty_conditional, np.empty(0, dtype=np.float64))
    np.testing.assert_array_equal(empty_lower_bound, np.full(1, 12.0))
    np.testing.assert_array_equal(empty_upper_bound, np.empty(0, dtype=np.float64))

    copied = module.copied(source)
    assert copied.flags.f_contiguous
    np.testing.assert_array_equal(copied, source)

    local_values = module.local_extent_values(np.int32(4))
    np.testing.assert_array_equal(local_values, np.full(4, 14.0))
    caller_values = np.empty(4, dtype=np.float64)
    assert module.fill_local_extent(np.int32(4), caller_values) is None
    np.testing.assert_array_equal(caller_values, np.full(4, 15.0))


IMPORTED_EXTENT_PROVIDER = """
module imported_extent_provider
  implicit none
contains
  pure integer function extent_for(n) result(extent)
    integer, intent(in) :: n
    extent = max(0, n + 1)
  end function extent_for
end module imported_extent_provider
"""


IMPORTED_EXTENT_OWNER = """
module imported_extent_owner
  use, intrinsic :: iso_c_binding, only: c_double
  use imported_extent_provider, only: imported_extent => extent_for
  implicit none
contains
  function values(n) result(output)
    integer, intent(in) :: n
    real(c_double) :: output(imported_extent(n))
    output = 16.0_c_double
  end function values
end module imported_extent_owner
"""


def test_imported_module_specification_function_uses_its_mod_interface(tmp_path: Path):
    module, _payload = _build_sources_and_import(
        [
            ("imported_extent_provider.f90", IMPORTED_EXTENT_PROVIDER),
            ("imported_extent_owner.f90", IMPORTED_EXTENT_OWNER),
        ],
        tmp_path,
    )

    values = module.imported_extent_owner.values(np.int32(3))
    np.testing.assert_array_equal(values, np.full(4, 16.0))
    bridge = (tmp_path / "bind_c_imported_extent_provider_wrapper.f90").read_text(encoding="utf-8").lower()
    assert "use imported_extent_provider, only:" in bridge
    assert "=> extent_for" in bridge
    assert "pure function extent_for(" not in bridge


STANDALONE_EXTENT_SOURCE = """
pure integer function standalone_extent(n) result(extent)
  implicit none
  integer, intent(in) :: n
  extent = max(0, n + 2)
end function standalone_extent

pure integer function standalone_value_extent(n) result(extent)
  implicit none
  integer, value, intent(in) :: n
  extent = max(0, n + 3)
end function standalone_value_extent

module standalone_extent_contract
  use, intrinsic :: iso_c_binding, only: c_double
  implicit none
  interface
    pure integer function standalone_extent(n) result(extent)
      integer, intent(in) :: n
    end function standalone_extent
    pure integer function standalone_value_extent(n) result(extent)
      integer, value, intent(in) :: n
    end function standalone_value_extent
  end interface
contains
  function values(n) result(output)
    integer, intent(in) :: n
    real(c_double) :: output(standalone_extent(n))
    output = 17.0_c_double
  end function values
  function value_values(n) result(output)
    integer, intent(in) :: n
    real(c_double) :: output(standalone_value_extent(n))
    output = 18.0_c_double
  end function value_values
end module standalone_extent_contract
"""


STANDALONE_EXTENT_CONTRACT = """
from prik.contracts import Addr, Float64, In, Int32, prototype, pure

@pure
@prototype
def standalone_extent(n: In(Addr(Int32))) -> Int32: ...

@pure
@prototype
def standalone_value_extent(n: In(Int32)) -> Int32: ...

def values(n: Int32) -> Float64[standalone_extent(n)]: ...

def value_values(n: Int32) -> Float64[standalone_value_extent(n)]: ...
"""


def test_prototype_emits_standalone_extent_entity(tmp_path: Path):
    module, result = _build_inline_pyi_contract_module(
        tmp_path,
        module_name="standalone_extent_contract",
        source_text=STANDALONE_EXTENT_SOURCE,
        contract_text=STANDALONE_EXTENT_CONTRACT,
    )

    values = module.values(np.int32(3))
    np.testing.assert_array_equal(values, np.full(5, 17.0))
    value_values = module.value_values(np.int32(3))
    np.testing.assert_array_equal(value_values, np.full(6, 18.0))

    bridge = (result.output_dir / "bind_c_standalone_extent_contract_wrapper.f90").read_text(encoding="utf-8").lower()
    binding = (result.output_dir / "standalone_extent_contract_wrapper.c").read_text(encoding="utf-8").lower()
    interface_line = next(
        line.strip() for line in bridge.splitlines() if line.strip().startswith("pure function prik_standalone_extent_")
    )
    interface_symbol = interface_line.split("(", maxsplit=1)[0].split()[-1]
    assert bridge.count(f"pure function {interface_symbol}(") == 1
    assert f"procedure({interface_symbol}) :: standalone_extent" in bridge
    assert "integer(c_int32_t), intent(in) :: n" in bridge
    assert "integer(c_int32_t), value, intent(in) :: n" in bridge
    assert "external :: standalone_extent" not in bridge
    assert "prik_decl_extent_0_0 = int(standalone_extent(n), c_int64_t)" in bridge
    assert "real(c_double), allocatable, dimension(:) :: result_value" in bridge
    assert "allocate(result_value(prik_decl_extent_0_0))" in bridge
    executable_binding = binding.split("static pyobject * wrap_values", maxsplit=1)[1]
    assert "standalone_extent(" not in executable_binding
    assert "&prik_decl_extent_0_0" in binding
    assert "shape: (standalone_extent(n))" in binding
    assert "__prik_callable_" not in binding


STANDALONE_TARGET_SOURCE = """
pure integer function external_extent(n) result(extent)
  implicit none
  integer, intent(in) :: n
  extent = max(0, n + 4)
end function external_extent

function external_values(n) result(output)
  use, intrinsic :: iso_c_binding, only: c_double
  implicit none
  interface
    pure integer function external_extent(n) result(extent)
      integer, intent(in) :: n
    end function external_extent
  end interface
  integer, intent(in) :: n
  real(c_double) :: output(external_extent(n))
  output = 19.0_c_double
end function external_values
"""


STANDALONE_TARGET_CONTRACT = """
from prik.contracts import Addr, Float64, In, Int32, standalone, prototype, pure

@pure
@prototype
def external_extent(n: In(Addr(Int32))) -> Int32: ...

@standalone
def external_values(n: Int32) -> Float64[external_extent(n)]: ...
"""


def test_prototype_entity_is_visible_inside_a_standalone_target_interface(tmp_path: Path):
    module, result = _build_inline_pyi_contract_module(
        tmp_path,
        module_name="standalone_target_extent",
        source_text=STANDALONE_TARGET_SOURCE,
        contract_text=STANDALONE_TARGET_CONTRACT,
    )

    values = module.external_values(np.int32(3))
    np.testing.assert_array_equal(values, np.full(7, 19.0))

    bridge = (result.output_dir / "bind_c_standalone_target_extent_wrapper.f90").read_text(encoding="utf-8").lower()
    interface_line = next(
        line.strip() for line in bridge.splitlines() if line.strip().startswith("pure function prik_external_extent_")
    )
    interface_symbol = interface_line.split("(", maxsplit=1)[0].split()[-1]
    assert bridge.index(f"pure function {interface_symbol}(") < bridge.index("function external_values(")
    assert f"procedure({interface_symbol}) :: external_extent" in bridge
    assert "import :: c_int32_t, external_extent, c_double" in bridge
    assert "real(c_double), dimension(external_extent(n)) :: native_result" in bridge
