"""Internal semantic-policy to wrapper-plan projection contracts."""

from __future__ import annotations


from dataclasses import replace

import pytest

from tests.fortran._support.ownership_policy import parse_pyi_text
from prik.semantics.models import PYTHON_EXPORTS_METADATA
from prik.policy.completion import complete_semantic_policies
from prik.planning.planner import _ClassPolicyCatalog
from prik.pipeline.wrapper import WrapperGenerator
from prik.planning import WrapperPlanner


def _plan(source: str, *, module_name: str = "fmath"):
    module = parse_pyi_text(source, module_name=module_name)
    complete_semantic_policies(module)
    return WrapperPlanner().build(module)


def _scalar_plan():
    return _plan(
        """
@nogil
@bind("SWAP_ARGS")
@standalone
@native_call([Addr(Arg(1)), Addr(Arg(0))])
def swap_args(x: Float64, y: Float64) -> Float64: ...
""",
        module_name="runtime_policy",
    )


def _hidden_result_plan():
    return _plan(
        """
@native_call([Int32(1), Arg(0), Bool(False), Return("result", 0)])
def scale(x: Float64) -> Float64: ...
""",
        module_name="hidden_values",
    )


def _edit_first_function(plan, edit):
    root = plan.namespaces[0]
    functions = (edit(root.functions[0]), *root.functions[1:])
    return replace(plan, namespaces=(replace(root, functions=functions), *plan.namespaces[1:]))


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


def test_planner_keeps_one_module_variable_plan_for_multiple_publications():
    """Namespace publications reference one plan that owns native access."""
    module = parse_pyi_text("counter: Int32\n", module_name="state")
    module.variables[0].metadata[PYTHON_EXPORTS_METADATA] = [
        {"namespace": (), "name": "counter"},
        {"namespace": ("facade",), "name": "counter"},
    ]
    complete_semantic_policies(module)

    plan = WrapperPlanner().build(module)

    variables = list(plan.variables)
    publications = [
        (namespace.python_path, publication.variable_owner_path, publication.python_names)
        for namespace in plan.namespaces
        for publication in namespace.variable_publications
    ]
    assert len(variables) == 1
    assert publications == [
        ((), variables[0].owner_path, ("counter",)),
        (("facade",), variables[0].owner_path, ("counter",)),
    ]


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
        (namespace.python_path, publication.variable_owner_path)
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


def test_binding_registers_child_namespaces_as_importable_submodules():
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
    artifacts = WrapperGenerator().generate(WrapperPlanner().build(module))
    c_source = next(source.text for source in artifacts.sources if source.path.name.endswith(".c"))

    assert "PyModule_Create(&namespaced_left_module)" in c_source
    assert "PyModule_Create(&namespaced_right_module)" in c_source
    left_registration = 'PyDict_SetItemString(PyImport_GetModuleDict(), "namespaced.left", namespace_left) < 0'
    assert left_registration in c_source
    assert 'PyDict_SetItemString(PyImport_GetModuleDict(), "namespaced.right", namespace_right) < 0' in c_source
    assert c_source.index(left_registration) > c_source.index("PyModule_Create(&namespaced_left_module)")


def test_post_ir_export_policy_fixes_names_within_each_namespace():
    module = parse_pyi_text(
        """
def first(x: Int32) -> Int32: ...
def second(x: Int32) -> Int32: ...
""",
        module_name="namespaced_fixes",
    )
    module.functions[0].name = "lambda"
    module.functions[0].native_name = "first"
    module.functions[0].metadata[PYTHON_EXPORTS_METADATA] = [{"namespace": ("child",), "name": None}]
    module.functions[1].name = "lambda_"
    module.functions[1].native_name = "second"
    module.functions[1].metadata[PYTHON_EXPORTS_METADATA] = [{"namespace": ("child",), "name": None}]

    complete_semantic_policies(module)
    plan = WrapperPlanner().build(module)
    child = next(namespace for namespace in plan.namespaces if namespace.python_path == ("child",))

    assert [function.binding.python_name for function in child.functions] == ["lambda_", "lambda__2"]


def test_planner_omits_private_functions_from_public_namespaces():
    module = parse_pyi_text(
        """
def visible(x: Int32) -> Int32: ...
def hidden(x: Int32) -> Int32: ...
""",
        module_name="visibility",
    )
    module.functions[1].visibility = "private"
    complete_semantic_policies(module)

    plan = WrapperPlanner().build(module)

    assert [function.binding.python_name for function in plan.namespaces[0].functions] == ["visible"]


def test_class_policy_catalog_organizes_nested_classes_and_callable_owner_paths():
    module = parse_pyi_text(
        """
class outer:
    class inner:
        @native_call([Pass(), Addr(Arg(0))])
        def shift(self, dx: Float64) -> None: ...

        @overload("shift")
        def move(self, dx: Float64) -> None: ...
""",
        module_name="nested_catalog",
    )
    complete_semantic_policies(module)

    catalog = _ClassPolicyCatalog.from_module(module)
    outer, inner = catalog.entries

    assert tuple(entry.semantic_class.name for entry in catalog.entries) == ("outer", "inner")
    assert inner.methods_by_owner_path["nested_catalog.outer.inner.shift"].name == "shift"
    assert inner.method_policies_by_owner_path["nested_catalog.outer.inner.shift"].python_name == "shift"
    assert inner.overload_functions_by_owner_path["nested_catalog.outer.inner.move.shift"].name == "shift"

    with pytest.raises(TypeError):
        inner.methods_by_owner_path["nested_catalog.outer.inner.shift"] = outer.semantic_class

    plan = WrapperPlanner().build(module)
    generated = WrapperGenerator().generate(plan)

    planned_outer, planned_inner = plan.namespaces[0].derived_types
    assert (planned_outer.native_type_name, planned_inner.native_type_name) == ("outer", "inner")
    # The nested type is defined beside its parent and bound on it, not here.
    assert planned_outer.python_names == ("outer",)
    assert planned_inner.python_names == ()
    assert planned_inner.nested_in == planned_outer.type_identity
    assert planned_inner.contract_name == "inner"
    assert {source.path.suffix for source in generated.sources} == {".c", ".h", ".f90"}


def test_planner_projects_required_array_buffer_policy():
    module = parse_pyi_text(
        """
def sum_values(values: Float64[:]) -> Float64: ...
""",
        module_name="array_argument",
    )
    complete_semantic_policies(module)

    assert WrapperPlanner().build(module).namespaces[0].functions[0].arguments[0].array is not None


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
