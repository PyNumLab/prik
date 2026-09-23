"""Assumed-type syntax and native semantic identity."""

import pytest

from prik.parsers.fortran import parse_fortran_file
from prik.parsers.fortran.models import FortranParseError
from prik.pipeline.pyi import pyi_text_to_semantic_module
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
  subroutine matrix(x)
    type(*), dimension(:,:), intent(in) :: x
  end subroutine
  subroutine any_rank(x)
    type(*), dimension(..), intent(in) :: x
  end subroutine
  subroutine unspecified(x)
    type(*) :: x
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
        "matrix": (2, "assumed_shape"),
        "any_rank": (None, "assumed_rank"),
        "unspecified": (0, None),
    }
    for function in semantic.functions:
        argument = function.arguments[0]
        rank, category = expected[function.name]
        assert argument.semantic_type.name == "AnyNative"
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


def test_generated_contract_uses_public_any_native_forms():
    source = fortran_module_to_semantic_module(parse_fortran_file(SOURCE).modules[0])
    contract = PyiPrinter().emit(source)
    assert "x: AnyNative" in contract
    assert "Annotated[AnyNative, ReadOnly]" in contract
    assert "AnyNative[Flat]" in contract
    assert "AnyNative[:, :, :]" in contract
    assert "AnyNative[:, :]" in contract
    assert "AnyNative[:]" in contract
    assert "AnyNative[...]" in contract
    assert not any(name in contract for name in ("NativeValue", "AssumedType", "FortranIntent", "Asynchronous"))
    replay = pyi_text_to_semantic_module(contract, module_name="assumed_type_declarations")
    arguments = {function.name: function.arguments[0] for function in replay.functions}
    assert arguments["scalar"].semantic_type.metadata["fortran_assumed_type"] is True
    assert arguments["size_one"].semantic_type.storage.array.category == "assumed_size"
    assert arguments["shape_three"].semantic_type.storage.array.category == "assumed_shape"
    assert arguments["any_rank"].semantic_type.storage.array.category == "assumed_rank"
    assert arguments["shape_one"].semantic_type.storage.array.contiguous
    assert arguments["shape_one"].semantic_type.metadata["fortran_target"] is True
    assert all(argument.semantic_type.name == "AnyNative" for argument in arguments.values())


def test_generated_contract_uses_bare_shape_forms_without_extra_metadata():
    forms = (
        ("scalar", "", "AnyNative"),
        ("raw", ", dimension(*)", "AnyNative[Flat]"),
        ("vector", ", dimension(:)", "AnyNative[:]"),
        ("matrix", ", dimension(:,:)", "AnyNative[:, :]"),
        ("cube", ", dimension(:,:,:)", "AnyNative[:, :, :]"),
        ("rank", ", dimension(..)", "AnyNative[...]"),
    )
    source = (
        "module m\ncontains\n"
        + "\n".join(f"subroutine {name}(x)\n  type(*){shape} :: x\nend subroutine" for name, shape, _ in forms)
        + "\nend module"
    )
    semantic = fortran_module_to_semantic_module(parse_fortran_file(source).modules[0])
    contract = PyiPrinter().emit(semantic)
    for _name, _shape, annotation in forms:
        assert f"x: {annotation}\n" in contract
    assert "Annotated" not in contract


def test_edited_contract_rejects_higher_rank_assumed_size():
    source = """from prik.contracts import AnyNative, Flat
def f(x: AnyNative[:, Flat]) -> None: ...
"""
    with pytest.raises(ValueError, match="rank-one assumed-size"):
        pyi_text_to_semantic_module(source, module_name="m")


@pytest.mark.parametrize(
    "annotation",
    [
        pytest.param("AnyNative[4]", id="explicit-shape"),
        pytest.param("AnyNative[::]", id="strided-spelling"),
    ],
)
def test_any_native_shape_is_the_single_array_category_authority(annotation):
    source = f"from prik.contracts import AnyNative\ndef f(x: {annotation}) -> None: ..."
    with pytest.raises(ValueError, match="AnyNative"):
        pyi_text_to_semantic_module(source, module_name="m")


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
    assert assumed.semantic_type.name == "AnyNative"
    assert address.semantic_type.name != assumed.semantic_type.name
    assert "fortran_assumed_type" not in address.semantic_type.metadata
