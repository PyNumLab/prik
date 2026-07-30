"""Tests split by stable ownership concept from `test_compile_time_values.py`."""

from tests.fortran._support.semantic_conversion import (
    array_contract,
    fortran_module_to_semantic_module,
    get_function,
    parse_fortran_source,
)


def test_array_constraints():
    source = """
module array_mod

contains

subroutine scale(x)

    real(8), intent(inout) :: x(:)

end subroutine

end module
"""

    fmod = parse_fortran_source(source)

    smod = fortran_module_to_semantic_module(fmod)

    func = get_function(smod, "scale")

    x = func.arguments[0]

    assert x.semantic_type.name == "Float64"

    assert x.semantic_type.rank == 1

    contract = array_contract(x.semantic_type)
    assert contract.category == "assumed_shape"
    assert contract.shape == ["::Strided"]
    assert contract.source_shape == [":"]
    assert contract.order is None


def test_matrix_semantics():
    source = """
module linalg_mod

contains

subroutine matvec(A, x, y)

    real(8), intent(in) :: A(:, :)
    real(8), intent(in) :: x(:)
    real(8), intent(out) :: y(:)

end subroutine

end module
"""

    fmod = parse_fortran_source(source)

    smod = fortran_module_to_semantic_module(fmod)

    func = get_function(smod, "matvec")

    A = func.arguments[0]

    assert A.semantic_type.rank == 2

    contract = array_contract(A.semantic_type)
    assert A.semantic_type.shape == ["::Strided", "::Strided"]
    assert contract.source_shape == [":", ":"]
    assert contract.category == "assumed_shape"
    assert contract.order == "ORDER_F"


def test_explicit_bound_ranges_remain_shaped_storage_contracts():
    source = """
module bound_mod
contains
subroutine bounded(n, default_bound, zero_bound, shifted_bound)
  integer, intent(in) :: n
  real(8), intent(inout) :: default_bound(1:n)
  real(8), intent(inout) :: zero_bound(0:n-1)
  real(8), intent(inout) :: shifted_bound(2:n+1)
end subroutine bounded
end module bound_mod
"""
    module = fortran_module_to_semantic_module(parse_fortran_source(source))
    args = {arg.name: arg for arg in get_function(module, "bounded").arguments}

    default_bound = array_contract(args["default_bound"].semantic_type)
    assert default_bound.category == "explicit_shape"
    assert default_bound.shape == ["n"]

    zero_bound = array_contract(args["zero_bound"].semantic_type)
    assert zero_bound.category == "explicit_shape"
    assert zero_bound.shape == ["n"]

    shifted_bound = array_contract(args["shifted_bound"].semantic_type)
    assert shifted_bound.category == "explicit_shape"
    assert shifted_bound.shape == ["n"]


def test_explicit_shape():
    source = """
module shape_mod

contains

subroutine foo(A)

    real(8), intent(in) :: A(10, 20)

end subroutine

end module
"""

    fmod = parse_fortran_source(source)

    smod = fortran_module_to_semantic_module(fmod)

    func = get_function(smod, "foo")

    A = func.arguments[0]

    assert A.semantic_type.shape == ["10", "20"]
