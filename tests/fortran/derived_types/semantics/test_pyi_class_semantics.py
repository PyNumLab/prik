"""Core `.pyi` class semantics retained by Derived Types."""

from tests.fortran._support.pyi_conversion import (
    PROJECTED_OUTPUT_METADATA,
    SUPPRESS_DEFAULT_CONSTRUCTOR_METADATA,
    emit_module,
    parse_pyi_text,
)


def test_convert_pyi_to_ir_self_only_generated_constructor_keeps_default_initializer():
    module = parse_pyi_text(
        """
class state:
    def __init__(self) -> None: ...

    values: Allocatable[Float64[:]]
""",
        module_name="edited",
    )

    cls = module.classes[0]
    assert cls.origin.source_language == "fortran"
    assert SUPPRESS_DEFAULT_CONSTRUCTOR_METADATA not in cls.origin.metadata
    assert cls.methods == []
    assert "    def __init__(self) -> None: ..." in emit_module(module)


def test_compact_assignment_overload_projects_visible_destination_without_direction_label():
    from_pyi = parse_pyi_text(
        """
class vector:
    value: Float64

    @overload("assign_vector_real")
    def assign(
        self,
        right: Float64
    ) -> vector: ...

@private
@native_call([Arg(0), Addr(Arg(1))])
def assign_vector_real(
    left: vector,
    right: Float64
) -> Returns["left", vector]: ...
""",
        module_name="edited",
    )
    func = from_pyi.functions[0]

    assert func.arguments[0].metadata[PROJECTED_OUTPUT_METADATA] is True
    assert func.projection[0].result_position == 0
    assert from_pyi.classes[0].overload_sets[0].procedures[0].metadata["overload_kind"] == "assignment"


def test_pyi_keyword_normalized_type_bound_method_keeps_native_binding_name():
    module = parse_pyi_text(
        """
class visible_t:
    @bind("visible_from")
    def from_(self) -> Int32: ...
""",
        module_name="fnaming_f90",
    )

    method = module.classes[0].methods[0]

    assert method.name == "from_"
    assert method.native_name == "visible_from"


def test_method_equality_treats_argument_names_as_placeholders():
    left = parse_pyi_text(
        """
class vector:
    def scale(
        self,
        n: Int32,
        x: Float64[1:n]
    ) -> None: ...
""",
        module_name="edited",
    )
    right = parse_pyi_text(
        """
class vector:
    def scale(
        self,
        extent: Int32,
        values: Float64[1:extent]
    ) -> None: ...
""",
        module_name="edited",
    )

    assert left == right
