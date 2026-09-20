"""Tests split by stable ownership concept from `test_compile_time_values.py`."""

from pathlib import Path

from prik.semantics.fortran2ir import (
    fortran_file_to_semantic_modules,
    fortran_module_to_semantic_module,
)
from tests.fortran._support.semantic_conversion import (
    array_contract,
    get_function,
)
from prik.semantics.models import SemanticExpressionCallable
from prik.policy.contract_imports import complete_contract_imports
from prik.policy.exports import complete_python_export_policy
from prik.printers import PyiPrinter
from prik.parsers.fortran import parse_fortran_file as parse_fortran_source
from prik.pipeline.pyi import pyi_text_to_semantic_module as parse_pyi_text

NATIVE_FIXTURES = Path(__file__).parent / "fixtures" / "native"


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
    assert contract.shape == ["::"]
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
    assert A.semantic_type.shape == ["::", "::"]
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


def test_fortran_inquiries_become_python_array_expressions_and_keep_source_bounds():
    source = """
module inquiry_mod
contains
function transformed(source) result(values)
  real(8), intent(in) :: source(0:, 2:)
  real(8) :: values( &
    ubound(source, 1) - lbound(source, 1) + 1, &
    max(1, size(source, dim=2)), &
    size(source), &
    2 ** rank(source), &
    lbound(source, 2), &
    ubound(source, 2))
end function transformed
end module inquiry_mod
"""
    module = fortran_module_to_semantic_module(parse_fortran_source(source))
    result = get_function(module, "transformed").return_type.storage.array

    assert result.source_shape == [
        "ubound(source, 1) - lbound(source, 1) + 1",
        "max(1, size(source, dim=2))",
        "size(source)",
        "2 ** rank(source)",
        "lbound(source, 2)",
        "ubound(source, 2)",
    ]
    assert result.shape == [
        "source.shape[0]",
        "max(1, source.shape[1])",
        "source.size",
        "2 ** source.ndim",
        "2 if source.shape[1] > 0 else 1",
        "2 + source.shape[1] - 1 if source.shape[1] > 0 else 0",
    ]
    complete_python_export_policy(module)
    complete_contract_imports([module])
    generated = PyiPrinter().emit(module)
    assert "source.shape[0], max(1, source.shape[1]), source.size, 2 ** source.ndim" in generated
    assert "2 if source.shape[1] > 0 else 1" in generated
    assert "2 + source.shape[1] - 1 if source.shape[1] > 0 else 0" in generated


def test_specification_function_calls_keep_local_and_imported_native_identity():
    source = (NATIVE_FIXTURES / "specification_function_calls_keep_local_and_imported_native_identity.f90").read_text(
        encoding="utf-8"
    )
    modules = fortran_file_to_semantic_modules(parse_fortran_source(source))
    module = next(item for item in modules if item.name == "expression_owner")
    array = get_function(module, "values").return_type.storage.array

    assert array.expression_callables == [
        [
            SemanticExpressionCallable(
                name="imported_extent",
                native_name="extent_for",
                native_scope="extent_helpers",
                source_language="fortran",
                placement="module",
            )
        ],
        [
            SemanticExpressionCallable(
                name="local_extent",
                native_name="local_extent",
                native_scope="expression_owner",
                source_language="fortran",
                placement="module",
            )
        ],
    ]

    complete_python_export_policy(module)
    complete_contract_imports([module])
    generated = PyiPrinter().emit(module)
    reloaded = parse_pyi_text(generated, module_name="expression_owner")
    reloaded_array = get_function(reloaded, "values").return_type.storage.array

    assert "from .extent_helpers import extent_for as imported_extent" in generated
    assert "Float64[imported_extent(n), local_extent(n)]" in generated
    assert reloaded_array.expression_callables == array.expression_callables


def test_wildcard_specification_function_origin_round_trips_unambiguously():
    source = (NATIVE_FIXTURES / "wildcard_specification_function_origin_round_trips_unambiguously.f90").read_text(
        encoding="utf-8"
    )
    modules = fortran_file_to_semantic_modules(parse_fortran_source(source))
    module = next(item for item in modules if item.name == "expression_owner")
    array = get_function(module, "values").return_type.storage.array

    assert array.expression_callables[0][0].native_scope == "extent_helpers"

    complete_python_export_policy(module)
    complete_contract_imports([module])
    generated = PyiPrinter().emit(module)
    reloaded = parse_pyi_text(generated, module_name="expression_owner")
    reloaded_array = get_function(reloaded, "values").return_type.storage.array

    assert "from .extent_helpers import extent_for" in generated
    assert reloaded_array.expression_callables == array.expression_callables


def test_non_only_rename_does_not_choose_between_specification_function_routes():
    """Ambiguous and renamed-away procedure names keep no invented origin."""
    source = (NATIVE_FIXTURES / "non_only_rename_does_not_choose_between_specification_function_routes.f90").read_text(
        encoding="utf-8"
    )
    modules = fortran_file_to_semantic_modules(parse_fortran_source(source))
    module = next(item for item in modules if item.name == "expression_owner")
    callables = get_function(module, "values").return_type.storage.array.expression_callables

    assert callables == [
        [SemanticExpressionCallable(name="x", native_name="x", source_language="fortran")],
        [SemanticExpressionCallable(name="y", native_name="y", source_language="fortran")],
    ]


def test_unindexed_wildcard_specification_function_origin_is_not_guessed():
    source = """
module expression_owner
  use unavailable_helpers
contains
function values(n) result(output)
  integer, intent(in) :: n
  real(8) :: output(extent_for(n))
end function values
end module expression_owner
"""
    module = fortran_module_to_semantic_module(parse_fortran_source(source))
    reference = get_function(module, "values").return_type.storage.array.expression_callables[0][0]

    assert reference.name == "extent_for"
    assert reference.native_name == "extent_for"
    assert reference.native_scope is None


def test_standalone_specification_interface_round_trips_as_one_pure_prototype_signature():
    source = """
module expression_owner
  interface
    pure integer function extent_for(n) result(extent)
      integer, intent(in) :: n
    end function extent_for
  end interface
contains
  function values(n) result(output)
    integer, intent(in) :: n
    real(8) :: output(extent_for(n))
  end function values
end module expression_owner
"""
    module = fortran_module_to_semantic_module(parse_fortran_source(source))
    generated = PyiPrinter().emit(module)
    reloaded = parse_pyi_text(generated, module_name="expression_owner")

    assert "@pure\n@prototype\ndef extent_for(" in generated
    assert "n: In(Addr(Int32))" in generated
    assert "@standalone" not in generated
    prototype = reloaded.prototypes[0]
    assert prototype.pure is True
    assert prototype.origin.native_scope == "expression_owner"
    assert (
        get_function(reloaded, "values").return_type.storage.array.expression_callables[0][0].placement == "standalone"
    )


def test_a_pure_function_contract_states_its_purity_and_reads_it_back():
    """A specification function must be pure, so its contract has to say it is.

    The contract wrote `@pure` only on prototypes, so a pure module function
    read back impure and a contract calling it in a declaration expression
    could not be built.
    """
    module = fortran_module_to_semantic_module(
        parse_fortran_source("""
module extent_provider
contains
pure integer function extent_for(n)
  integer, intent(in) :: n
  extent_for = n + 1
end function extent_for
integer function plain(n)
  integer, intent(in) :: n
  plain = n
end function plain
end module extent_provider
""")
    )
    complete_python_export_policy(module)
    complete_contract_imports([module])
    contract = PyiPrinter(normalize_public_names=True).emit(module)

    assert "@pure\n@native_call([Addr(Arg(0))])\ndef extent_for(" in contract
    assert "@pure\n@native_call([Addr(Arg(0))])\ndef plain(" not in contract
    reloaded = parse_pyi_text(contract, module_name="extent_provider")
    assert [function.metadata.get("fortran_attributes") for function in reloaded.functions] == [["pure"], None]
