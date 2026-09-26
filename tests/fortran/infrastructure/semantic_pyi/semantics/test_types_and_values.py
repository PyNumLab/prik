"""Tests split by stable ownership concept from `test_python_ast_contracts.py`."""

import pytest
from prik.parsers.fortran import parse_fortran_file
from prik.printers import emit_module
from prik.pipeline.pyi import pyi_text_to_semantic_module
from prik.semantics.fortran2ir import fortran_file_to_semantic_modules
from prik.semantics.metadata import (
    ADDRESS_ROLE_METADATA,
    ADDRESS_ROLE_RAW,
    OPTIONAL_ABSENT_HANDLE_METADATA,
    USER_PRIVATE_METADATA,
)
from prik.semantics.models import (
    PYTHON_VALUE_IMMUTABLE,
    PYTHON_VALUE_MUTABILITY_METADATA,
    SemanticConstraint,
)
from prik.semantics.native_array_handles import (
    is_native_array_handle,
    native_array_data_type,
    native_array_descriptor_kind,
    native_array_handle_facts,
)
from prik.semantics.native_contract import native_contract_issues
from tests.fortran._support.pyi_conversion import parse_pyi_text


def test_convert_pyi_to_ir_dispatches_nested_and_qualified_semantic_types():
    """A declared `Addr(T)` is raw native address storage, unlike an `Addr(Arg)` projection."""
    module = parse_pyi_text(
        """
public_value: Int32
bounded: Final[Annotated[Int32, Bounded(1, 8)]]
pointer: Addr(Float64)
""",
        module_name="dispatch",
    )

    public_value, bounded, pointer = module.variables
    assert public_value.visibility == "public"
    assert public_value.semantic_type.storage is None
    assert bounded.semantic_type.constraints == [
        SemanticConstraint("Bounded", [1, 8]),
        SemanticConstraint("Constant"),
    ]
    assert pointer.semantic_type.storage.kind == "address"
    assert pointer.semantic_type.storage.metadata[ADDRESS_ROLE_METADATA] == ADDRESS_ROLE_RAW
    assert pointer.semantic_type.storage.read_only is False


def test_convert_pyi_to_ir_follows_arbitrary_contract_aliases():
    """Every contract helper, wrapper, and projection name resolves through its import alias."""
    module = pyi_text_to_semantic_module(
        """
from prik.contracts import Addr as AddressOf, Arg as PythonArg, Final as Frozen
from prik.contracts import Flat as Layout, Float64 as F64, Int32 as I32, native_call as call
from prik.contracts import Annotated as Metadata, SourceName as NativeName, Returns as Gives

Flat: Frozen[I32] = 10
alias: Metadata[F64[1:n], NativeName("native_alias")]

@call([AddressOf(PythonArg(0))])
def inspect(values: F64[Layout], dense: F64[Flat]) -> None: ...

def f() -> tuple[F64, Gives["y", F64]]: ...
""",
        module_name="aliases",
    )

    assert [variable.name for variable in module.variables] == ["Flat", "alias"]
    assert module.variables[1].origin.native_name == "native_alias"
    assert module.variables[1].semantic_type.shape == ["1:n"]
    inspect, returns = module.functions
    assert inspect.projection[0].value_kind == "addr"
    assert inspect.arguments[0].semantic_type.storage.array.category == "assumed_size"
    assert inspect.arguments[1].semantic_type.shape == ["Flat"]
    assert returns.return_type.name == "Float64"
    assert returns.arguments[0].name == "y"


def test_convert_pyi_to_ir_preserves_immutable_python_value_metadata():
    module = parse_pyi_text(
        """
def scale(
    values: Annotated[Float64[:], Immutable]
) -> Returns["values", Float64[:]]: ...
""",
        module_name="immutable_values",
    )

    values = module.functions[0].arguments[0].semantic_type
    assert values.metadata[PYTHON_VALUE_MUTABILITY_METADATA] == PYTHON_VALUE_IMMUTABLE

    emitted = emit_module(module)
    assert "Immutable" in emitted
    reparsed = parse_pyi_text(emitted, module_name="immutable_values")
    reparsed_values = reparsed.functions[0].arguments[0].semantic_type
    assert reparsed_values.metadata[PYTHON_VALUE_MUTABILITY_METADATA] == PYTHON_VALUE_IMMUTABLE


def test_rank_zero_scalar_storage_is_writable_scalar_array_storage():
    module = parse_pyi_text(
        """
def update_storage(value: Float64[()]) -> None: ...
""",
        module_name="scalar_storage",
    )

    update_type = module.functions[0].arguments[0].semantic_type
    assert update_type.rank == 0
    assert update_type.storage.kind == "array"
    assert update_type.storage.array.category == "scalar_storage"
    assert update_type.storage.read_only is False
    assert update_type.storage.mutable is True


def test_convert_pyi_to_ir_preserves_explicit_array_source_dimensions():
    """Explicit extents keep their source dimensions; an empty step marks a strided axis."""
    module = parse_pyi_text(
        """
def apply(
    A: Float64[LDA, N],
    work: Float64[::],
    bounded: Float64[0:n:],
    scratch: Float64[:]
) -> None: ...
""",
        module_name="explicit_dims",
    )

    args = {arg.name: arg.semantic_type.storage.array for arg in module.functions[0].arguments}
    assert args["A"].source_shape == ["LDA", "N"]
    assert args["A"].lower_bounds == [None, None]
    assert args["A"].upper_bounds == [None, None]
    assert [(args[name].axes, args[name].contiguous, args[name].source_shape) for name in ("work", "bounded")] == [
        (["strided"], False, []),
        (["strided"], False, []),
    ]
    assert args["bounded"].shape == ["0:n:"]
    assert (args["scratch"].axes, args["scratch"].contiguous) == (["dense"], True)


def test_convert_pyi_to_ir_rejects_a_dimension_step():
    """A dimension carries bounds only, so the step position spells nothing."""
    with pytest.raises(ValueError, match="not part of the contract grammar"):
        parse_pyi_text("x: Float64[::2]\n", module_name="rejected_step")


def test_convert_pyi_to_ir_uses_fortran_native_array_defaults():
    fortran = parse_pyi_text(
        """
def consume(
    a: Float64[:, :],
    c: Annotated[Float64[:, :], ORDER_C],
    any_order: Annotated[Float64[:, :], ORDER_ANY]
) -> None: ...
""",
        module_name="fortran_contract",
    )
    fortran_arrays = [arg.semantic_type.storage.array for arg in fortran.functions[0].arguments]
    assert [array.order for array in fortran_arrays] == ["ORDER_F", "ORDER_C", "ORDER_ANY"]
    assert fortran_arrays[0].category is None
    assert all(not arg.semantic_type.constraints for arg in fortran.functions[0].arguments)


def test_convert_pyi_to_ir_rejects_redundant_fortran_default_array_order():
    with pytest.raises(ValueError, match="ORDER_F is implicit for fortran"):
        parse_pyi_text(
            "value: Annotated[Float64[:, :], ORDER_F]\n",
            module_name="redundant_order",
            native_language="fortran",
        )


def test_convert_pyi_to_ir_accepts_flat_array_dimension():
    module = parse_pyi_text(
        """
flat: Float64[Flat]
matrix: Float64[3, Flat]
tensor: Float64[3, 4, Flat]
c_matrix: Annotated[Float64[Flat, 3], ORDER_C]
c_tensor: Annotated[Float64[Flat, 3, 4], ORDER_C]
""",
        module_name="flat_arrays",
    )

    arrays = [variable.semantic_type.storage.array for variable in module.variables]
    assert [variable.semantic_type.shape for variable in module.variables] == [
        [":"],
        ["3", ":"],
        ["3", "4", ":"],
        [":", "3"],
        [":", "3", "4"],
    ]
    assert [array.category for array in arrays] == [
        "assumed_size",
        "assumed_size",
        "assumed_size",
        "assumed_size",
        "assumed_size",
    ]
    assert [array.source_shape for array in arrays] == [
        ["*"],
        ["3", "*"],
        ["3", "4", "*"],
        ["*", "3"],
        ["*", "3", "4"],
    ]
    assert [array.upper_bounds for array in arrays] == [
        ["*"],
        [None, "*"],
        [None, None, "*"],
        ["*", None],
        ["*", None, None],
    ]
    assert [array.order for array in arrays] == [None, "ORDER_F", "ORDER_F", "ORDER_C", "ORDER_C"]


def test_convert_pyi_to_ir_preserves_rank_selector_and_character_allocatable_marker():
    module = parse_pyi_text(
        """
nested: Float64[:, :][rank, kind]
name: Annotated[String[16], FortranAllocatable]
""",
        module_name="metadata",
    )

    nested, name = [variable.semantic_type for variable in module.variables]
    assert nested.metadata["rank_selector"] == "rank, kind"
    assert nested.storage.array.metadata["rank_selector"] == "rank, kind"
    assert name.metadata["fortran_character_length"] == "16"
    assert name.metadata["fortran_allocatable"] is True


def test_convert_pyi_to_ir_accepts_array_descriptor_handle_wrappers():
    """`Allocatable[...]`/`Pointer[...]` wrap a plain array as a native descriptor handle."""
    module = pyi_text_to_semantic_module(
        """
from prik.contracts import Allocatable as A, Annotated, Float64 as F64, Pointer as P, SourceName, String as Str

values: A[F64[:]]
target: Annotated[P[F64[:, :]], SourceName("target_values")]
labels: P[Str[8][:]]
plain_values: F64[:]

def maybe_consume(values: A[F64[:]] | None = ..., target: P[F64[:]] | None = ...) -> None: ...
""",
        module_name="array_descriptors",
    )

    values, target, labels, plain_values = [variable.semantic_type for variable in module.variables]
    assert [native_array_descriptor_kind(item) for item in (values, target, labels)] == [
        "allocatable",
        "pointer",
        "pointer",
    ]
    assert is_native_array_handle(plain_values) is False
    assert native_array_data_type(values) == plain_values
    assert native_array_data_type(target).storage.array.pointer is False
    assert native_array_data_type(target).rank == 2

    labels_facts = native_array_handle_facts(labels)
    assert (labels_facts.dtype, labels_facts.rank, labels_facts.shape) == ("String", 1, (":",))
    assert labels_facts.fortran_character_length == "8"
    assert labels_facts.element_type.rank == 0
    with pytest.raises(ValueError, match="is not a native array handle"):
        native_array_handle_facts(plain_values)

    for argument in module.functions[0].arguments:
        assert argument.optional is True
        assert argument.semantic_type.metadata[OPTIONAL_ABSENT_HANDLE_METADATA] is True


def test_convert_pyi_to_ir_preserves_user_private_bound_function_contract():
    module = parse_pyi_text(
        """
@private
@bind("native_helper")
def helper(value: Int32) -> None: ...
""",
        module_name="edited",
    )

    helper = module.functions[0]
    assert native_contract_issues(module) == []
    assert helper.visibility == "private"
    assert helper.native_name == "native_helper"
    assert helper.origin.source_language == "fortran"
    assert helper.origin.metadata[USER_PRIVATE_METADATA] is True


@pytest.mark.parametrize(
    "source, message",
    [
        (
            "value: Float64[ORDER_F]\n",
            "Non-dimensional type subscriptions are not supported; use Final[...] for constants and "
            "Annotated[...] for constraints or array metadata",
        ),
        (
            "value: Float64[3, Flat, 4]\n",
            "Flat must appear exactly once at the first or final concrete array dimension",
        ),
        (
            "value: Float64[3, Flat, Flat]\n",
            "Flat must appear exactly once at the first or final concrete array dimension",
        ),
        (
            "value: Annotated[Float64[Flat, 3], ORDER_F]\n",
            "ORDER_F conflicts with ORDER_C implied by Flat placement",
        ),
        (
            "value: Annotated[Float64[3, Flat], ORDER_C]\n",
            "ORDER_C conflicts with ORDER_F implied by Flat placement",
        ),
        (
            "value: Annotated[Float64[:, :], COPY_F]\n",
            "COPY_F requires a C-order Python array and targets Fortran order",
        ),
        (
            "value: Annotated[Float64[:], COPY_F]\n",
            "COPY_F requires a concrete multidimensional array rank",
        ),
        (
            "value: Annotated[Float64[::, ::], ORDER_C, COPY_F]\n",
            "COPY_F initially supports only dense concrete-shape arrays",
        ),
        (
            "value: Annotated[Int32, Bounded(lower=1)]\n",
            "Constraint metadata expects positional arguments only: 'Bounded(lower=1)'",
        ),
        ("value: Annotated[Int32, 'bad']\n", "Unsupported Annotated metadata: \"'bad'\""),
        ("value: Float64[:, foo.bar]\n", "Unsupported array dimension expression: 'foo.bar'"),
        (
            "@native_call([Arg(0).other[0]])\ndef f(x: Int32) -> None: ...\n",
            "native_call expects projection entry calls",
        ),
    ],
)
def test_convert_pyi_to_ir_rejects_additional_invalid_storage_forms(source: str, message: str):
    with pytest.raises(ValueError) as error:
        parse_pyi_text(source, module_name="invalid")
    assert str(error.value) == message


def test_native_contract_structurally_accepts_declared_type_and_constraint_edits():
    parsed = parse_fortran_file(
        """
module solver_mod
contains
  function solve(value) result(result)
    real(8), intent(in) :: value
    real(8) :: result
  end function solve
end module solver_mod
"""
    )
    generated = emit_module(fortran_file_to_semantic_modules(parsed)[0])
    constrained = generated.replace(
        "from prik.contracts import ",
        "from prik.contracts import Annotated, Finite, ",
        1,
    ).replace("value: Float64", "value: Annotated[Float64, Finite]", 1)
    changed_abi = generated.replace(
        "from prik.contracts import ",
        "from prik.contracts import Int32, ",
        1,
    ).replace("value: Float64", "value: Int32", 1)

    assert native_contract_issues(parse_pyi_text(constrained, module_name="solver_mod")) == []
    assert native_contract_issues(parse_pyi_text(changed_abi, module_name="solver_mod")) == []


def test_source_name_binds_a_native_entity_without_taking_the_declared_name():
    """`SourceName` states what a declaration reaches, like `bind` on a callable.

    A contract is edited to give an entity the name Python should call it, and
    that name has to survive. Reading the source spelling as the declaration's
    own name discards the edit and exports the native spelling instead.
    """
    module = pyi_text_to_semantic_module(
        """
from prik.contracts import Annotated, Final, Int32, SourceName

tally: Annotated[Int32, SourceName("COUNTER")]

limit: Final[Annotated[Int32, SourceName("MAXFUN")]]
""",
        module_name="edited",
    )

    assert [(item.name, item.origin.native_name) for item in module.variables] == [
        ("tally", "COUNTER"),
        ("limit", "MAXFUN"),
    ]
    assert [constraint.name for constraint in module.variables[1].semantic_type.constraints] == ["Constant"]


def test_class_binds_a_native_type_under_its_own_python_name():
    """A class states the native type it reaches when the two names differ."""
    module = pyi_text_to_semantic_module(
        """
from prik.contracts import Float64, bind

@bind("POINT_T")
class PointType:
    x: Float64
""",
        module_name="edited",
    )

    assert (module.classes[0].name, module.classes[0].native_name) == ("PointType", "POINT_T")
