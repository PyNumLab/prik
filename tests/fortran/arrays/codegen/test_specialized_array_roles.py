"""Cross-feature optional, assumed-rank, and character-array lowering."""

from __future__ import annotations


from tests.fortran._support.ownership_policy import parse_pyi_text
from prik.policy.completion import complete_semantic_policies
from prik.policy.models import OptionalMode
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
    assumed = functions["any_rank"].arguments[0].array
    character = functions["labels"].arguments[0].array

    assert optional.binding.optional_mode is OptionalMode.NULLABLE_VALUE
    assert optional.entrypoint.optional_mode is OptionalMode.NULLABLE_VALUE
    assert assumed is not None
    assert assumed.rank is None
    assert assumed.contiguous is True
    assert assumed.runtime_rank_role == "later_array_buffers.any_rank.values:rank"
    assert len(assumed.extent_roles) == 15
    assert character is not None
    assert character.rank == 1
    assert character.itemsize == 8
    assert character.itemsize_role == "later_array_buffers.labels.values:itemsize"


def test_optional_assumed_rank_and_character_lowering_follow_named_plan_fields():
    artifacts = WrapperGenerator().generate(_later_array_plan())
    c_source = next(source.text for source in artifacts.sources if source.path.suffix == ".c")
    bridge_source = next(source.text for source in artifacts.sources if source.path.suffix == ".f90")

    assert "PyObject * bound_values_obj = Py_None;" in c_source
    assert "if (bound_values_obj != Py_None)" in c_source
    assert "prik_array_validate(bound_values_obj, NPY_FLOAT64, 1, 15, PRIK_ARRAY_LAYOUT_F_CONTIGUOUS" in c_source
    assert "NPY_FLOAT64, 1, 15, PRIK_ARRAY_LAYOUT_F_CONTIGUOUS" in c_source
    assert "bound_values_rank = (int64_t)PyArray_NDIM" in c_source
    assert "NPY_STRING, 1, 1, PRIK_ARRAY_LAYOUT_ANY_CONTIGUOUS" in c_source
    assert "bound_values_itemsize != 8" in c_source
    assert "if (c_associated(bound_values)) then" in bridge_source
    assert "select case (values_rank)" in bridge_source
    assert "case (1)" in bridge_source
    assert "case (15)" in bridge_source
    assert "character(kind=c_char, len=8), pointer, contiguous, dimension(:) :: values" in bridge_source
    assert max(map(len, bridge_source.splitlines())) <= 132


def test_native_array_fallback_unpacks_planned_runtime_rank_and_itemsize_roles():
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
