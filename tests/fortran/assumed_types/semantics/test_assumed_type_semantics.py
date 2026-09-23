"""Assumed-type syntax and native semantic identity."""

import pytest

from prik.parsers.fortran import parse_fortran_file
from prik.parsers.fortran.models import FortranParseError
from prik.pipeline.pyi import pyi_text_to_semantic_module
from prik.policy import complete_semantic_policies
from prik.policy.construction import completed_function_wrapper_policy
from prik.printers import PyiPrinter
from prik.semantics.fortran2ir import fortran_module_to_semantic_module


SOURCE = """
module assumed_type_declarations
contains
  subroutine scalar(x)
    type(*), intent(in), optional :: x
  end subroutine
  subroutine size_one(x)
    type(*), dimension(*), intent(in), asynchronous :: x
  end subroutine
  subroutine shape_one(x)
    type(*), dimension(:), intent(in), contiguous, target :: x
  end subroutine
  subroutine shape_three(x)
    type(*), dimension(:,:,:), intent(in) :: x
  end subroutine
  subroutine any_rank(x)
    type(*), dimension(..), intent(in) :: x
  end subroutine
end module
"""


def test_assumed_type_forms_keep_native_identity_and_attributes():
    parsed = parse_fortran_file(SOURCE).modules[0]
    assert parsed.procedures[1].arguments[0].asynchronous
    semantic = fortran_module_to_semantic_module(parsed)
    expected = {
        "scalar": (0, None),
        "size_one": (1, "assumed_size"),
        "shape_one": (1, "assumed_shape"),
        "shape_three": (3, "assumed_shape"),
        "any_rank": (None, "assumed_rank"),
    }
    for function in semantic.functions:
        argument = function.arguments[0]
        rank, category = expected[function.name]
        assert argument.semantic_type.name == "NativeValue"
        assert argument.semantic_type.metadata["fortran_assumed_type"] is True
        if category is not None:
            assert argument.semantic_type.storage.array.category == category
        if rank is not None:
            assert argument.semantic_type.rank == rank
    assert semantic.functions[0].arguments[0].optional
    assert semantic.functions[1].arguments[0].semantic_type.metadata["fortran_asynchronous"] is True
    assert semantic.functions[2].arguments[0].semantic_type.storage.array.contiguous
    assert semantic.functions[2].arguments[0].semantic_type.metadata["fortran_target"] is True


@pytest.mark.parametrize(
    "declaration",
    [
        pytest.param("type(*), value :: x", id="value"),
        pytest.param("type(*), pointer :: x", id="pointer"),
        pytest.param("type(*), allocatable :: x", id="allocatable"),
        pytest.param("type(*), intent(out) :: x", id="intent-out"),
        pytest.param("type(*) :: x(4)", id="explicit-shape"),
        pytest.param("type(*) :: x(:, *)", id="assumed-size-colon-prefix"),
        pytest.param("type(*) :: x(4, *)", id="assumed-size-higher-rank"),
    ],
)
def test_invalid_assumed_type_dummy_is_diagnosed(declaration):
    source = f"module m\ncontains\nsubroutine f(x)\n{declaration}\nend subroutine\nend module"
    with pytest.raises(FortranParseError, match=r"TYPE\(\*\) dummy") as error:
        parse_fortran_file(source)
    if declaration == "type(*) :: x(4, *)":
        assert "higher-rank assumed-size" in str(error.value)


def test_assumed_type_cannot_declare_module_storage():
    with pytest.raises(FortranParseError, match="only valid for a procedure dummy"):
        parse_fortran_file("module m\ntype(*) :: value\nend module")


def test_generated_contract_replays_intent_and_asynchronous():
    source = fortran_module_to_semantic_module(parse_fortran_file(SOURCE).modules[0])
    contract = PyiPrinter().emit(source)
    replay = pyi_text_to_semantic_module(contract, module_name="assumed_type_declarations")
    arguments = {function.name: function.arguments[0] for function in replay.functions}
    assert arguments["scalar"].semantic_type.metadata["fortran_assumed_intent"] == "in"
    assert arguments["scalar"].semantic_type.storage.read_only
    assert arguments["size_one"].semantic_type.metadata["fortran_asynchronous"] is True
    assert arguments["shape_one"].semantic_type.storage.array.contiguous
    assert arguments["shape_one"].semantic_type.metadata["fortran_target"] is True
    assert all(argument.semantic_type.name == "NativeValue" for argument in arguments.values())


def test_edited_contract_rejects_assumed_type_intent_out():
    source = """from prik.contracts import Annotated, AssumedType, FortranIntent, NativeValue
def f(x: Annotated[NativeValue, AssumedType, FortranIntent('out')]) -> None: ...
"""
    with pytest.raises(ValueError, match=r"FortranIntent.*in or inout"):
        pyi_text_to_semantic_module(source, module_name="m")


def test_edited_contract_rejects_higher_rank_assumed_size_before_planning():
    source = """from prik.contracts import Annotated, ArrayCategory, AssumedType, NativeValue
def f(x: Annotated[NativeValue[:, :], AssumedType, ArrayCategory("assumed_size")]) -> None: ...
"""
    module = pyi_text_to_semantic_module(source, module_name="m")
    complete_semantic_policies(module)
    with pytest.raises(ValueError, match="rank-one TYPE\\(\\*\\) assumed-size"):
        completed_function_wrapper_policy(module.functions[0])


def test_assumed_type_is_distinct_from_c_pointer_value():
    source = """module m
use iso_c_binding
contains
subroutine f(assumed, address) bind(C)
  type(*) :: assumed
  type(c_ptr), value :: address
end subroutine
end module"""
    semantic = fortran_module_to_semantic_module(parse_fortran_file(source).modules[0])
    assumed, address = semantic.functions[0].arguments
    assert assumed.semantic_type.name == "NativeValue"
    assert address.semantic_type.name != assumed.semantic_type.name
    assert "fortran_assumed_type" not in address.semantic_type.metadata
