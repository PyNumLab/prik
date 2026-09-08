"""Cross-feature optional, assumed-rank, and character-array lowering."""

from __future__ import annotations


from tests.fortran._support.ownership_policy import parse_pyi_text
from prik.policy.completion import complete_semantic_policies
from prik.policy.models import (
    ArrayEntrypointABI,
    EntrypointPassingConvention,
    NativeArraySourceKind,
    OptionalMode,
)
from prik.codegen import CBindingGenerator
from prik.pipeline.wrapper import WrapperGenerator
from prik.planning import WrapperPlanner


def _later_array_plan():
    module = parse_pyi_text(
        """
from prik.contracts import Float64, String

def optional(values: Float64[:] = ...) -> None: ...
def any_rank(values: Float64[...]) -> Float64: ...
def labels(values: String[8][:]) -> None: ...
def labels_any_width(values: String[...][:]) -> None: ...
""",
        module_name="later_array_buffers",
    )
    complete_semantic_policies(module)
    return WrapperPlanner().build(module)


def _character_array_result_plan():
    module = parse_pyi_text(
        """
def direct_labels() -> String[5][3]: ...

@native_call([Return("labels", 0)])
def hidden_labels() -> String[4][2]: ...
""",
        module_name="character_array_results",
    )
    complete_semantic_policies(module)
    return WrapperPlanner().build(module)


def test_optional_assumed_rank_and_character_arrays_have_explicit_distinct_roles():
    functions = {function.binding.python_name: function for function in _later_array_plan().namespaces[0].functions}
    optional = functions["optional"].arguments[0]
    assumed_argument = functions["any_rank"].arguments[0]
    assumed = assumed_argument.array
    character_argument = functions["labels"].arguments[0]
    character = character_argument.array
    assumed_width_argument = functions["labels_any_width"].arguments[0]
    handle_sources = (
        NativeArraySourceKind.NDARRAY,
        NativeArraySourceKind.ALLOCATABLE_HANDLE,
        NativeArraySourceKind.POINTER_HANDLE,
    )

    assert optional.binding.optional_mode is OptionalMode.NULLABLE_VALUE
    assert optional.entrypoint.optional_mode is OptionalMode.NULLABLE_VALUE
    assert optional.native_array_actual is not None
    assert optional.native_array_actual.accepted_sources == handle_sources
    assert assumed is not None
    assert assumed.rank is None
    assert assumed.contiguous is False
    assert assumed.entrypoint_abi is ArrayEntrypointABI.C_DESCRIPTOR
    assert assumed.signed_strides is True
    assert assumed_argument.entrypoint.passing is EntrypointPassingConvention.C_DESCRIPTOR_POINTER
    assert assumed_argument.entrypoint.pass_array_metadata is False
    assert assumed.runtime_rank_role == "later_array_buffers.any_rank.values:rank"
    assert len(assumed.extent_roles) == 15
    assert assumed_argument.native_array_actual is not None
    assert assumed_argument.native_array_actual.rank is None
    assert assumed_argument.native_array_actual.accepted_sources == handle_sources
    assert character is not None
    assert character.rank == 1
    assert character.entrypoint_abi is ArrayEntrypointABI.RAW_ADDRESS
    assert character.itemsize == 8
    assert character.itemsize_role == "later_array_buffers.labels.values:itemsize"
    assert character_argument.native_array_actual is not None
    assert character_argument.native_array_actual.accepted_sources == handle_sources
    assert assumed_width_argument.native_array_actual is not None
    assert assumed_width_argument.native_array_actual.dtype == "S"
    assert assumed_width_argument.native_array_actual.accepted_sources == handle_sources


def test_optional_assumed_rank_and_character_lowering_follow_named_plan_fields():
    artifacts = WrapperGenerator().generate(_later_array_plan())
    c_source = next(source.text for source in artifacts.sources if source.path.suffix == ".c")
    bridge_source = next(source.text for source in artifacts.sources if source.path.suffix == ".f90")

    assert "PyObject * bound_values_obj = Py_None;" in c_source
    assert "if (bound_values_obj != Py_None)" in c_source
    assert ("prik_array_validate(bound_values_obj, NPY_FLOAT64, 1, 15, PRIK_ARRAY_LAYOUT_SIGNED_STRIDED_F") in c_source
    assert (
        "prik_native_array_backend_for_actual(bound_values_capsule, 1, 15, "
        'CFI_type_double, sizeof(double), "float64", "values")'
    ) in c_source
    assert "NPY_FLOAT64, 1, 15, PRIK_ARRAY_LAYOUT_SIGNED_STRIDED_F" in c_source
    assert "bound_values_rank = (int64_t)PyArray_NDIM" in c_source
    # The shared binder takes the declared character width alongside the rank
    # bounds, so a fixed-width character array is checked there rather than by
    # a separate itemsize comparison.
    assert "NPY_STRING, 8, 1, 1, 1, PRIK_ARRAY_LAYOUT_ANY_CONTIGUOUS" in c_source
    assert "real(c_double), dimension(..) :: values" in bridge_source
    assert "select case (values_rank)" not in bridge_source
    assert "character(kind=c_char, len=8), pointer, contiguous, dimension(:) :: values" in bridge_source
    assert max(map(len, bridge_source.splitlines())) <= 132


def test_native_array_descriptor_result_unpacks_planned_runtime_rank_and_itemsize_roles():
    functions = {function.binding.python_name: function for function in _later_array_plan().namespaces[0].functions}
    generator = CBindingGenerator()

    rank_function = functions["any_rank"]
    rank_argument = rank_function.arguments[0]
    rank_names = generator._function_context(rank_function).arguments[rank_argument.owner_path]
    rank_nodes = generator._native_array_actual_unpack_nodes(rank_argument, rank_names)

    itemsize_function = functions["labels"]
    itemsize_argument = itemsize_function.arguments[0]
    itemsize_names = generator._function_context(itemsize_function).arguments[itemsize_argument.owner_path]
    itemsize_nodes = generator._native_array_actual_unpack_nodes(itemsize_argument, itemsize_names)

    assert any(node.expression.text == "bound_values_rank = bound_values_actual.rank" for node in rank_nodes)
    assert any(
        node.expression.text == "bound_values_itemsize = bound_values_actual.itemsize" for node in itemsize_nodes
    )
