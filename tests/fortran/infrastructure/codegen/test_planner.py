"""Internal semantic-policy to wrapper-plan projection contracts."""

from __future__ import annotations


import pytest

from tests.fortran._support.ownership_policy import parse_pyi_text
from prik.semantics.models import PYTHON_EXPORTS_METADATA
from prik.policy.completion import complete_semantic_policies
from prik.planning import WrapperPlanner


def _plan(source: str, *, module_name: str = "fmath"):
    module = parse_pyi_text(source, module_name=module_name)
    complete_semantic_policies(module)
    return WrapperPlanner().build(module)


def _hidden_result_plan():
    return _plan(
        """
@native_call([Int32(1), Arg(0), Bool(False), Return("result", 0)])
def scale(x: Float64) -> Float64: ...
""",
        module_name="hidden_values",
    )


def test_planner_groups_completed_exports_into_explicit_namespace_nodes():
    module = parse_pyi_text(
        """
def left_value(x: Int32) -> Int32: ...
def right_value(x: Int32) -> Int32: ...
""",
        module_name="namespaced",
    )
    module.functions[0].metadata[PYTHON_EXPORTS_METADATA] = [{"namespace": ("left",), "name": "shared_value"}]
    module.functions[1].metadata[PYTHON_EXPORTS_METADATA] = [{"namespace": ("right",), "name": "shared_value"}]
    complete_semantic_policies(module)

    plan = WrapperPlanner().build(module)

    assert [namespace.python_path for namespace in plan.namespaces] == [(), ("left",), ("right",)]
    assert plan.namespaces[0].functions == ()
    assert [function.binding.python_name for function in plan.namespaces[1].functions] == ["shared_value"]
    assert [function.binding.python_name for function in plan.namespaces[2].functions] == ["shared_value"]
    assert plan.namespaces[1].functions[0].symbol_name == "left_shared_value"
    assert plan.namespaces[2].functions[0].symbol_name == "right_shared_value"


def test_module_variable_owner_is_its_native_identity_not_a_publication_path():
    """Adding a facade changes publications without moving native ownership."""

    def planned_owner(*namespaces: str):
        module = parse_pyi_text("values: Int32\n", module_name="package")
        variable = module.variables[0]
        variable.origin.native_scope = "home"
        variable.origin.native_name = "values"
        variable.metadata[PYTHON_EXPORTS_METADATA] = [
            {"namespace": (namespace,), "name": "values"} for namespace in namespaces
        ]
        complete_semantic_policies(module)
        return WrapperPlanner().build(module)

    facade_only = planned_owner("facade")
    facade_and_api = planned_owner("facade", "api")

    assert [variable.owner_path for variable in facade_only.variables] == ["home.values"]
    assert [variable.owner_path for variable in facade_and_api.variables] == ["home.values"]
    # Every publication references the one plan that owns native access.
    assert all(
        publication.variable is facade_and_api.variables[0]
        for namespace in facade_and_api.namespaces
        for publication in namespace.variable_publications
    )
    assert [variable.binding.support_namespace for variable in facade_only.variables] == [()]
    assert [variable.binding.support_namespace for variable in facade_and_api.variables] == [()]
    assert facade_only.entrypoint.support_procedures
    assert [
        (procedure.owner_path, procedure.role, procedure.symbol_name)
        for procedure in facade_only.entrypoint.support_procedures
    ] == [
        (procedure.owner_path, procedure.role, procedure.symbol_name)
        for procedure in facade_and_api.entrypoint.support_procedures
    ]
    assert {
        (namespace.python_path, publication.variable.owner_path)
        for namespace in facade_and_api.namespaces
        for publication in namespace.variable_publications
    } == {
        (("api",), "home.values"),
        (("facade",), "home.values"),
    }


def test_two_python_names_one_folded_stem_get_separate_generated_symbols():
    """A generated symbol is shared with Fortran, which folds the two together."""
    module = parse_pyi_text(
        """
def left_value(x: Int32) -> Int32: ...
def right_value(x: Int32) -> Int32: ...
""",
        module_name="folded",
    )
    module.functions[0].metadata[PYTHON_EXPORTS_METADATA] = [{"namespace": (), "name": "Foo"}]
    module.functions[1].metadata[PYTHON_EXPORTS_METADATA] = [{"namespace": (), "name": "foo"}]
    complete_semantic_policies(module)

    plan = WrapperPlanner().build(module)

    functions = plan.namespaces[0].functions
    assert [function.binding.python_name for function in functions] == ["Foo", "foo"]
    stems = [function.symbol_name for function in functions]
    assert len({stem.casefold() for stem in stems}) == len(stems)


def test_planner_directly_projects_three_facets_and_distinct_call_orders():
    function = _hidden_result_plan().namespaces[0].functions[0]
    argument = function.arguments[0]
    result = function.results[0]

    assert function.entrypoint.symbol_name == "bind_c_scale"
    assert [(item.source_kind, item.owner_path) for item in function.entrypoint.parameters] == [
        ("projected_slot", function.entrypoint.projected_slots[0].owner_path),
        ("argument", argument.owner_path),
        ("projected_slot", function.entrypoint.projected_slots[2].owner_path),
        ("hidden_result", result.owner_path),
    ]
    assert function.entrypoint.results == (result.entrypoint,)
    assert argument.entrypoint.handoff_role == "hidden_values.scale.x:value"
    assert argument.projected_call_slot is function.entrypoint.projected_slots[1]
    assert [slot.source_kind for slot in function.entrypoint.projected_slots] == [
        "literal",
        "projection",
        "literal",
        "result",
    ]


def test_planner_fails_when_post_ir_policy_has_not_completed():
    module = parse_pyi_text(
        """
def add(x: Float64, y: Float64) -> Float64: ...
""",
        module_name="missing_policy",
    )

    with pytest.raises(ValueError, match="missing completed wrapper policy"):
        WrapperPlanner().build(module)


def test_planner_rejects_a_module_without_public_wrapper_exports():
    module = parse_pyi_text("", module_name="empty_api")
    complete_semantic_policies(module)

    with pytest.raises(ValueError, match="Semantic module 'empty_api' has no public wrapper exports"):
        WrapperPlanner().build(module)


def test_planner_reports_an_unsupported_completed_module_policy_at_its_owner_path():
    module = parse_pyi_text(
        """
label: String = "ready"
""",
        module_name="labels",
    )
    complete_semantic_policies(module)

    with pytest.raises(
        ValueError,
        match=r"Semantic variable 'labels\.label'.*module variable initializer requires a write-through native setter",
    ):
        WrapperPlanner().build(module)
