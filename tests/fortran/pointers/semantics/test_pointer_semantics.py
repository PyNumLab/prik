"""Fortran and edited-`.pyi` pointer semantic contracts."""

import re

import pytest

from tests.fortran._support.ownership_policy import parse_pyi_text
from tests.fortran._support.semantic_conversion import (
    array_contract,
    fortran_module_to_semantic_module,
    get_function,
    parse_fortran_source,
)
from x2py.semantics.metadata import NATIVE_ARRAY_DESCRIPTOR_METADATA, OPTIONAL_ABSENT_HANDLE_METADATA
from x2py.semantics.native_array_handles import native_array_descriptor_kind


def test_fortran_pointer_arrays_and_scalars_preserve_descriptor_semantics():
    source = """
module pointer_semantics
contains
  subroutine inspect(values, scalar)
    real(8), pointer, intent(inout) :: values(:)
    real(8), pointer, intent(in) :: scalar
  end subroutine inspect
end module pointer_semantics
"""

    module = fortran_module_to_semantic_module(parse_fortran_source(source))
    values, scalar = get_function(module, "inspect").arguments

    assert array_contract(values.semantic_type).pointer is True
    assert native_array_descriptor_kind(values.semantic_type) == "pointer"
    assert scalar.semantic_type.metadata["fortran_pointer"] is True
    assert scalar.semantic_type.metadata["fortran_pointer_association"] == "runtime"
    assert scalar.semantic_type.storage.pointer_depth == 1


def test_pyi_pointer_handles_preserve_rank_optionality_and_scalar_state():
    module = parse_pyi_text(
        """
module_values: Pointer[Float64[:, :]]
current: Pointer[Int32]

def consume(values: Pointer[Float64[:]], maybe_values: Pointer[Float64[:]] | None = ...) -> None: ...
""",
        module_name="pointer_contracts",
    )

    module_values, current = [variable.semantic_type for variable in module.variables]
    values, maybe_values = module.functions[0].arguments

    assert module_values.metadata[NATIVE_ARRAY_DESCRIPTOR_METADATA] == "pointer"
    assert module_values.storage.array.pointer is True
    assert module_values.rank == 2
    assert current.metadata["fortran_pointer"] is True
    assert current.storage.pointer_depth == 1
    assert values.semantic_type.metadata[NATIVE_ARRAY_DESCRIPTOR_METADATA] == "pointer"
    assert maybe_values.semantic_type.metadata[NATIVE_ARRAY_DESCRIPTOR_METADATA] == "pointer"
    assert maybe_values.semantic_type.metadata[OPTIONAL_ABSENT_HANDLE_METADATA] is True
    assert maybe_values.optional is True


@pytest.mark.parametrize(
    ("annotation", "message"),
    [("Annotated[Float64[:], Pointer]", "use Pointer")],
)
def test_convert_pyi_to_ir_rejects_legacy_array_descriptor_metadata(annotation: str, message: str):
    with pytest.raises(ValueError, match=message):
        parse_pyi_text(
            f"""
values: {annotation}
""",
            module_name="legacy_array_descriptors",
        )


@pytest.mark.parametrize(
    ("source", "message"),
    [
        (
            "def produce() -> Pointer[Float64]: ...\n",
            "Procedure scalar descriptor results use a nullable value annotation",
        ),
        (
            "@native_call([], result=Pointer(Return(0)))\ndef produce() -> Float64: ...\n",
            "must use a nullable T | None annotation",
        ),
    ],
)
def test_scalar_pointer_results_reject_legacy_descriptor_spellings(source: str, message: str):
    with pytest.raises(ValueError, match=re.escape(message)):
        parse_pyi_text(source, module_name="invalid_pointer_projection")
