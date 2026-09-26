"""Tests split by stable ownership concept from `test_compile_time_values.py`."""

from dataclasses import asdict
from prik.parsers.fortran.models import (
    FortranArgument,
    FortranVariable,
)
from prik.semantics.fortran2ir import (
    FortranToIRConverter,
    fortran_module_to_semantic_module,
)
from tests.fortran._support.semantic_conversion import (
    array_contract,
    get_function,
)
from prik.parsers.fortran import parse_fortran_file as parse_fortran_source


def test_fortran_native_storage_contracts_cover_array_categories_and_scalars():
    source = """
module contract_mod
contains
subroutine contracts(n, m, explicit, legacy, assumed, contig, alloc, ptr, scalar_ptr, scalar_value, scalar_ref, scalar_out)
  integer, intent(in) :: n
  integer, intent(in) :: m
  real(8), intent(in) :: explicit(n, m)
  real(8), intent(inout) :: legacy(n, *)
  real(8), intent(in) :: assumed(:, :)
  real(8), contiguous, intent(inout) :: contig(:, :)
  real(8), allocatable, intent(out) :: alloc(:)
  real(8), pointer, intent(inout) :: ptr(:)
  real(8), pointer, intent(in) :: scalar_ptr
  real(8), value, intent(in) :: scalar_value
  real(8), intent(in) :: scalar_ref
  real(8), intent(out) :: scalar_out
end subroutine contracts
end module contract_mod
"""
    module = fortran_module_to_semantic_module(parse_fortran_source(source))
    func = get_function(module, "contracts")
    args = {arg.name: arg for arg in func.arguments}

    explicit = array_contract(args["explicit"].semantic_type)
    assert explicit.category == "explicit_shape"
    assert explicit.shape == ["n", "m"]
    assert explicit.order == "ORDER_F"
    assert args["explicit"].semantic_type.storage.read_only is True

    legacy = array_contract(args["legacy"].semantic_type)
    assert legacy.category == "assumed_size"
    assert legacy.shape == ["n", ":"]
    assert legacy.source_shape == ["n", "*"]
    assert legacy.order == "ORDER_F"

    assumed = array_contract(args["assumed"].semantic_type)
    assert assumed.category == "assumed_shape"
    assert assumed.shape == ["::", "::"]
    assert assumed.order == "ORDER_F"

    contig = array_contract(args["contig"].semantic_type)
    assert contig.category == "assumed_shape"
    assert contig.shape == [":", ":"]
    assert contig.order == "ORDER_F"
    assert contig.contiguous is True

    assert array_contract(args["alloc"].semantic_type).allocatable is True
    assert array_contract(args["ptr"].semantic_type).pointer is True
    scalar_ptr = args["scalar_ptr"].semantic_type
    assert scalar_ptr.metadata["fortran_pointer"] is True
    assert scalar_ptr.metadata["fortran_pointer_association"] == "runtime"
    assert scalar_ptr.storage.pointer_depth == 1
    assert args["scalar_ptr"].origin.metadata == {
        "rank": 0,
        "shape": [],
        "lower_bounds": [],
        "upper_bounds": [],
        "allocatable": False,
        "pointer": True,
        "target": False,
        "contiguous": False,
        "optional": False,
        "value": False,
        "association": "runtime",
    }
    assert args["scalar_value"].semantic_type.storage is None
    assert args["scalar_ref"].semantic_type.storage.read_only is True
    assert args["scalar_out"].semantic_type.storage.mutable is True


def test_fortran_native_storage_contracts_preserve_exact_bounds_and_member_flags():
    converter = FortranToIRConverter(compile_time_values={"n": 4})
    matrix = FortranArgument(
        name="matrix",
        base_type="real",
        kind="8",
        rank=2,
        shape=["0:n - 1", "*"],
    )
    matrix.contiguous = True
    member = FortranArgument(
        name="items",
        base_type="real",
        kind="8",
        rank=1,
        shape=[":"],
        optional=True,
        allocatable=True,
        pointer=True,
        visibility="private",
    )

    matrix_type = converter.visit(matrix).semantic_type
    assumed_rank = converter.visit(FortranVariable(name="any_rank", base_type="real", rank=1, shape=[".."]))
    semantic_member = converter.visit(member, as_data_member=True)
    plain_member = converter.visit(
        FortranVariable(name="plain", base_type="real", rank=1, shape=[":"]),
        as_data_member=True,
    )
    mixed_bounds = converter.visit(FortranVariable(name="mixed", base_type="real", rank=3, shape=["3", "1:n", "0:n"]))

    assert asdict(matrix_type.storage) == {
        "kind": "array",
        "read_only": False,
        "mutable": True,
        "pointer_depth": 0,
        "ownership": "borrowed",
        "array": {
            "rank": 2,
            "shape": ["4", ":"],
            "lower_bounds": ["0", None],
            "upper_bounds": ["4 - 1", "*"],
            "source_shape": ["0:4 - 1", "*"],
            "category": "assumed_size",
            "order": "ORDER_F",
            "copy_order": None,
            "axes": ["dense", "dense"],
            "contiguous": True,
            "allocatable": False,
            "pointer": False,
            "metadata": {},
        },
        "calling_convention": None,
        "metadata": {},
    }
    assert asdict(assumed_rank.storage.array) == {
        "rank": 1,
        "shape": ["..."],
        "lower_bounds": [],
        "upper_bounds": [],
        "source_shape": [".."],
        "category": "assumed_rank",
        "order": None,
        "copy_order": None,
        "axes": ["dense"],
        "contiguous": None,
        "allocatable": False,
        "pointer": False,
        "metadata": {},
    }
    assert semantic_member.name == "items"
    assert semantic_member.optional is True
    assert semantic_member.visibility == "private"
    assert semantic_member.semantic_type.storage.array.category == "deferred_shape"
    assert semantic_member.semantic_type.storage.array.allocatable is True
    assert semantic_member.semantic_type.storage.array.pointer is True
    assert plain_member.optional is False
    assert plain_member.visibility == "public"
    assert plain_member.semantic_type.storage.array.shape == ["::"]
    assert plain_member.semantic_type.storage.array.allocatable is False
    assert plain_member.semantic_type.storage.array.pointer is False
    assert plain_member.origin.source_language == "fortran"
    assert plain_member.origin.native_name == "plain"
    assert plain_member.origin.source_kind == "variable"
    assert mixed_bounds.storage.array.lower_bounds == [None, None, "0"]
    assert mixed_bounds.storage.array.upper_bounds == [None, "4", "4"]
