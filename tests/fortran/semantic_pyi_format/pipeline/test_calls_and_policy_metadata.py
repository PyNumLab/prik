"""Tests split by stable ownership concept from `test_imports_and_packages.py`."""

from tests.fortran._support.printer_models import (
    ProjectionMapping,
    PyiPrinter,
    SemanticArgument,
    SemanticArrayContract,
    SemanticConstraint,
    SemanticFunction,
    SemanticModule,
    SemanticStorageContract,
    SemanticType,
    SemanticVariable,
    emit_module,
    fortran_module_to_semantic_module,
    generate_pyi,
    generate_wrapper_artifacts,
    normalize,
    parse_fortran_source,
    parse_pyi_text,
    pytest,
    rendered_source,
)
from x2py.semantics.metadata import MAYBE_UNALLOCATED_METADATA


def test_emit_optional_scalar_output_as_visible_scalar_storage():
    source = """
module opt_out_mod
contains
subroutine maybe_status(status)
    integer(4), intent(out), optional :: status
end subroutine maybe_status
end module opt_out_mod
"""

    code = generate_pyi(source)

    assert "Return('status'" not in code
    assert "status: Int32[()] = ..." in code
    assert ') -> Returns["status", Int32[()]] | None: ...' in code


def test_emit_scalar_character_inout_as_replacement_return():
    source = """
module m
contains
subroutine normalize(name)
    character(len=8), intent(inout) :: name
end subroutine
end module
"""

    code = generate_pyi(source)

    annotation = "String[8]"
    assert "@native_call([Arg(0)])" not in code
    assert f"name: {annotation}" in code
    assert f') -> Returns["name", {annotation}]: ...' in code


def test_emit_primitive_scalar_inout_as_visible_replacement_return():
    source = """
module outputs
contains
subroutine scale_in_place(value, factor)
    real(8), intent(inout) :: value
    real(8), intent(in) :: factor
end subroutine scale_in_place
end module outputs
"""

    code = generate_pyi(source)

    assert "@native_call([Addr(Arg(0)), Addr(Arg(1))])" in code
    assert "value: Float64" in code
    assert "factor: Float64" in code
    assert ') -> Returns["value", Float64]: ...' in code


def test_emit_exact_output():
    source = """
module simple_mod

contains

subroutine scale(x)

    real(8), intent(inout) :: x(:)

end subroutine

end module
"""

    code = normalize(generate_pyi(source))

    expected = normalize(
        """
def scale(
    x: Float64[::]
) -> None: ...
"""
    )

    assert expected in code


def test_output_argument_uses_plain_return_annotation():
    source = """
module output_name_mod

contains

subroutine add(a, b, c)

    real(8), intent(in) :: a
    real(8), intent(in) :: b
    real(8), intent(out) :: c

end subroutine

end module
"""

    fmod = parse_fortran_source(source)
    smod = fortran_module_to_semantic_module(fmod)

    code = PyiPrinter().emit(smod)

    assert "c: Annotated[Addr(Float64)" not in code
    assert 'Returns["c"' not in code
    assert ") -> Float64: ..." in code


def test_emit_module_with_projection_helpers_and_private_function():
    module = SemanticModule(
        name="projection_mod",
        functions=[
            SemanticFunction(
                name="wrapper",
                native_name="wrapper",
                arguments=[
                    SemanticArgument("x", SemanticType("Float64", dtype="Float64")),
                    SemanticArgument("b", SemanticType("Int32", dtype="Int32"), optional=True),
                ],
                projection=[
                    ProjectionMapping(native_position=0, python_position=0),
                    ProjectionMapping(
                        native_position=1,
                        value_kind="literal",
                        value={"type": "Int32", "value": 1},
                    ),
                    ProjectionMapping(
                        native_position=2,
                        value_kind="len",
                        value={"kind": "arg", "position": 0},
                    ),
                    ProjectionMapping(
                        native_position=3,
                        value_kind="shape",
                        value={"value": {"kind": "arg", "position": 0}, "dim": 0},
                    ),
                    ProjectionMapping(
                        native_position=4,
                        value_kind="is_present",
                        value={"kind": "arg", "position": 1},
                    ),
                    ProjectionMapping(native_position=5, value_kind="work", value="tmp"),
                ],
            )
        ],
    )

    code = emit_module(module)

    assert "@native_call([Arg(0), Int32(1), Len(Arg(0)), Arg(0).shape[0], IsPresent(Arg(1)), Work('tmp')])" in code


def test_emit_native_call_supports_return_and_work_value_references():
    module = SemanticModule(
        name="projection_refs_mod",
        functions=[
            SemanticFunction(
                name="wrapper",
                native_name="wrapper",
                return_type=SemanticType("Float64", dtype="Float64"),
                projection=[
                    ProjectionMapping(
                        native_position=0,
                        value_kind="len",
                        value={"kind": "return", "position": 0},
                    ),
                    ProjectionMapping(
                        native_position=1,
                        value_kind="shape",
                        value={"value": {"kind": "work", "name": "tmp"}, "dim": 1},
                    ),
                ],
            )
        ],
    )

    code = emit_module(module)

    assert "@native_call([Len(Return(0)), Work('tmp').shape[1]])" in code
    assert "def wrapper() -> Float64: ..." in code


@pytest.mark.parametrize(
    "projection, message",
    [
        (
            [ProjectionMapping(native_position=0)],
            "native-only projection entry",
        ),
        (
            [ProjectionMapping(native_position=0, value_kind="unknown", value=None)],
            "Unsupported native_call projection entry",
        ),
        (
            [
                ProjectionMapping(
                    native_position=0,
                    value_kind="len",
                    value={"kind": "unknown"},
                )
            ],
            "Unsupported native_call value reference",
        ),
    ],
)
def test_emit_native_call_rejects_unrepresentable_projection_entries(projection, message):
    module = SemanticModule(
        name="bad_projection_mod",
        functions=[
            SemanticFunction(
                name="wrapper",
                native_name="wrapper",
                projection=projection,
            )
        ],
    )

    with pytest.raises(ValueError, match=message):
        emit_module(module)


def test_printer_rejects_optional_absent_array_handles_outside_callable_arguments():
    variable = SemanticVariable(
        "values",
        SemanticType(
            "Float64",
            rank=1,
            storage=SemanticStorageContract(
                kind="array",
                array=SemanticArrayContract(rank=1, shape=[":"], allocatable=True),
            ),
        ),
    )
    variable.optional = True
    module = SemanticModule(
        name="bad_optional_handle_mod",
        variables=[variable],
    )

    with pytest.raises(ValueError, match="only be emitted for callable arguments"):
        emit_module(module)


def test_printer_emits_extended_storage_and_callable_forms():
    printer = PyiPrinter()
    readonly_value = SemanticType(
        "Int32",
        storage=SemanticStorageContract(kind="value", read_only=True),
    )
    mutable_value = SemanticType("Int32", storage=SemanticStorageContract(kind="value"))
    deep_pointer = SemanticType(
        "Float64",
        storage=SemanticStorageContract(kind="pointer", read_only=True, pointer_depth=3),
    )
    double_pointer = SemanticType(
        "Float64",
        storage=SemanticStorageContract(kind="pointer", pointer_depth=2),
    )
    unspecified_storage = SemanticType("Int32", storage=SemanticStorageContract(kind="custom"))
    inferred_array = SemanticType(
        "Float64",
        rank=2,
        storage=SemanticStorageContract(kind="array"),
    )
    allocatable_handle = SemanticType(
        "Float64",
        rank=2,
        storage=SemanticStorageContract(
            kind="array",
            array=SemanticArrayContract(
                rank=2,
                shape=[":", ":"],
                order="ORDER_F",
                allocatable=True,
            ),
        ),
    )
    constrained_allocatable_handle = SemanticType(
        "Bool",
        rank=1,
        constraints=[SemanticConstraint("Finite")],
        storage=SemanticStorageContract(
            kind="array",
            array=SemanticArrayContract(rank=1, shape=["1"], allocatable=True),
        ),
    )
    maybe_unallocated_handle = SemanticType(
        "Float64",
        rank=1,
        metadata={MAYBE_UNALLOCATED_METADATA: True},
        storage=SemanticStorageContract(
            kind="array",
            array=SemanticArrayContract(rank=1, shape=[":"], allocatable=True),
        ),
    )
    pointer_handle = SemanticType(
        "Float64",
        rank=1,
        metadata={"fortran_pointer_association": "runtime"},
        storage=SemanticStorageContract(
            kind="array",
            array=SemanticArrayContract(rank=1, shape=[":"], pointer=True),
        ),
    )
    string_pointer_handle = SemanticType(
        "String",
        rank=1,
        metadata={"fortran_character_length": "8"},
        storage=SemanticStorageContract(
            kind="array",
            array=SemanticArrayContract(rank=1, shape=[":"], pointer=True),
        ),
    )
    annotated_array = SemanticType(
        "Float64",
        constraints=[SemanticConstraint("Finite"), SemanticConstraint("Range", [1, 3])],
        storage=SemanticStorageContract(
            kind="array",
            array=SemanticArrayContract(
                rank=2,
                shape=[":", ":"],
                order="ORDER_ANY",
            ),
        ),
    )
    character = SemanticType(
        "String",
        metadata={"fortran_character_length": "16"},
        storage=SemanticStorageContract(kind="reference", mutable=True, pointer_depth=1),
    )
    allocatable_character = SemanticType(
        "String",
        metadata={"fortran_character_length": ":", "fortran_allocatable": True},
    )
    pointer_scalar = SemanticType(
        "Int32",
        metadata={"fortran_pointer": True, "fortran_pointer_association": "runtime"},
        storage=SemanticStorageContract(kind="reference", mutable=True, pointer_depth=1),
    )

    canonical_constant = SemanticArgument(
        "answer",
        SemanticType("Int32", constraints=[SemanticConstraint("Constant")]),
    )
    assert printer.emit(canonical_constant) == "answer: Final[Int32]"
    with pytest.raises(ValueError, match=r"Final\[\.\.\.\]"):
        printer.emit(canonical_constant.semantic_type)
    assert printer.emit(readonly_value) == "Int32"
    assert printer.emit(mutable_value) == "Int32"
    assert printer.emit(deep_pointer) == "Addr[3](Float64)"
    assert printer.emit(double_pointer) == "Addr[2](Float64)"
    assert printer.emit(unspecified_storage) == "Int32"
    assert printer.emit(inferred_array) == "Float64[:, :]"
    assert printer.emit(allocatable_handle) == "Allocatable[Annotated[Float64[:, :], ORDER_F]]"
    assert printer.emit(constrained_allocatable_handle) == "Allocatable[Annotated[Bool[1], Finite]]"
    assert printer.emit(maybe_unallocated_handle) == "Annotated[Allocatable[Float64[:]], MaybeUnallocated]"
    assert printer.emit(pointer_handle) == 'Annotated[Pointer[Float64[:]], PointerAssociation("runtime")]'
    assert printer.emit(string_pointer_handle) == "Pointer[String[8][:]]"
    assert printer.emit(annotated_array) == "Annotated[Float64[:, :], ORDER_ANY, Finite, Range(1, 3)]"
    assert printer.emit(character) == "String[16]"
    assert printer.emit(allocatable_character) == "Allocatable[String]"
    assert printer.emit(pointer_scalar) == "Pointer[Int32]"


@pytest.mark.parametrize(
    ("argument_type", "projection"),
    [
        (
            SemanticType(
                "Float64",
                metadata={"fortran_pointer": True, "fortran_pointer_association": "runtime"},
                storage=SemanticStorageContract(kind="reference", mutable=True, pointer_depth=1),
            ),
            "Pointer",
        ),
    ],
    ids=["argument_type1-Pointer"],
)
def test_printer_emits_nullable_scalar_descriptor_boundary_projections(argument_type, projection):
    module = SemanticModule(
        name="pointer_descriptor_mod",
        functions=[
            SemanticFunction(
                name="read_pointer",
                native_name="read_pointer",
                arguments=[SemanticArgument("value", argument_type)],
                return_type=argument_type,
                projection=[ProjectionMapping(native_position=0, python_position=0)],
            )
        ],
    )

    code = emit_module(module)

    assert f"@native_call([{projection}(Arg(0))], result={projection}(Return(0)))" in code
    assert "value: Float64 | None" in code
    assert ") -> Float64 | None: ..." in code


def test_defaulted_scalar_descriptors_preserve_omitted_vs_none_in_generated_wrappers():
    loaded = parse_pyi_text(
        """
@native_call([Allocatable(Arg(0)), Pointer(Arg(1))])
def update(scale: Float64 | None = ..., target: Float64 | None = ...) -> None: ...
""",
        module_name="optional_scalar_descriptors",
    )
    artifacts = generate_wrapper_artifacts(loaded)
    bridge_source = rendered_source(artifacts, ".f90")
    c_wrapper = rendered_source(artifacts, ".c")

    assert "bound_scale_present" in bridge_source
    assert "bound_target_present" in bridge_source
    assert "if (c_associated(bound_scale_present)) then" in bridge_source
    assert "if (c_associated(bound_target_present)) then" in bridge_source
    assert "call native_update()" in bridge_source
    assert "call native_update(scale=scale_descriptor)" in bridge_source
    assert "call native_update(target=target_descriptor)" in bridge_source
    assert "call native_update(scale=scale_descriptor, target=target_descriptor" in bridge_source

    assert "bound_scale_obj = NULL;" in c_wrapper
    assert "bound_target_obj = NULL;" in c_wrapper
    assert "if (bound_scale_obj != NULL)" in c_wrapper
    assert "bound_scale_present = &bound_scale;" in c_wrapper
    assert "if ((bound_scale_obj != NULL) && (bound_scale_obj != Py_None))" in c_wrapper
    assert "bound_scale_nullable = &bound_scale;" in c_wrapper
    assert (
        "bind_c_update(bound_scale_nullable, bound_scale_present, bound_target_nullable, bound_target_present);"
        in c_wrapper
    )
    assert "Omit to make the native optional dummy absent." in c_wrapper
    assert "Pass None for a present unallocated or unassociated descriptor." in c_wrapper
    assert "Default is None." not in c_wrapper


def test_printer_projection_return_helpers_and_keyword_data_members():
    printer = PyiPrinter()
    argument = SemanticArgument(
        "x",
        SemanticType(
            "Float64",
            storage=SemanticStorageContract(kind="reference", mutable=True, pointer_depth=1),
        ),
        optional=True,
    )
    plain = SemanticArgument("value", SemanticType("Int32"))
    module = SemanticModule(
        name="returns",
        variables=[SemanticArgument("class", SemanticType("Int32"))],
        functions=[
            SemanticFunction(
                name="created",
                projection=[ProjectionMapping(native_position=0, result_position=0)],
            )
        ],
    )

    assert printer._projected_argument_return(argument, visible=True) == 'Returns["x", Addr(Float64)] | None'
    assert printer._named_return(plain) == 'Returns["value", Int32]'
    assert printer._projected_argument_return(argument, visible=False) == "Float64 | None"
    assert printer._projected_argument_return(plain, visible=False) == "Int32"
    assert "var['class']: Int32" in emit_module(module)
    assert "@native_call([Return(0)])" in emit_module(module)


def test_native_call_sorts_synthetic_entries_before_native_positions():
    projection = [
        ProjectionMapping(native_position=0, value_kind="literal", value={"type": "Int32", "value": 1}),
        ProjectionMapping(result_position=0),
    ]

    assert PyiPrinter()._native_call(projection) == "@native_call([Return(0), Int32(1)])"
