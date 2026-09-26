"""Scalar module-variable planning and lowering tests."""

from __future__ import annotations

from dataclasses import replace
from unittest.mock import Mock

import pytest

from tests.fortran._support.ownership_policy import parse_pyi_text
from prik.policy.ownership import AssignmentMode, SetterAction
from prik.policy.completion import complete_semantic_policies
from prik.policy.models import ModuleGetterAction
from prik.pipeline.wrapper import WrapperGenerator
from prik.planning import WrapperPlanner
from prik.codegen.c.binding import CBindingGenerator
from prik.codegen.fortran.bridge import FortranBridgeGenerator


SCALAR_MODULE_CONTRACT = """
limit: Final[Int32] = 12
counter: Int32 = 3
target_scale: Annotated[Float64, Aliased]
optional_scale: Allocatable[Float64]
selected_scale: Pointer[Float64]

def summarize() -> Int32: ...
"""


def _plan():
    module = parse_pyi_text(SCALAR_MODULE_CONTRACT, module_name="scalar_state")
    complete_semantic_policies(module)
    return WrapperPlanner().build(module)


def _source(artifacts, suffix: str) -> str:
    return next(item.text for item in artifacts.sources if item.path.name.endswith(suffix))


def _replace_variable(plan, python_name: str, edit):
    current = next(variable for variable in plan.variables if variable.bridge.native_name == python_name)
    replacement = edit(current)
    variables = tuple(replacement if variable is current else variable for variable in plan.variables)
    namespaces = tuple(
        replace(
            namespace,
            variable_publications=tuple(
                replace(publication, variable=replacement) if publication.variable is current else publication
                for publication in namespace.variable_publications
            ),
        )
        for namespace in plan.namespaces
    )
    return replace(plan, variables=variables, namespaces=namespaces)


def test_module_variable_visitors_consume_their_backend_owned_actions():
    plan = _plan()
    counter = next(variable for variable in plan.variables if variable.bridge.native_name == "counter")
    split_actions = replace(
        counter,
        binding=replace(
            counter.binding,
            getter_action=ModuleGetterAction.CONSTANT_VALUE,
            setter_action=SetterAction.OMIT,
        ),
        bridge=replace(
            counter.bridge,
            native_getter_action=ModuleGetterAction.DIRECT_VALUE,
            native_assignment=AssignmentMode.VALUE_COPY,
        ),
    )

    assert CBindingGenerator().visit(split_actions) == ()
    bridge = FortranBridgeGenerator()
    bridge.visit(plan)
    assert [procedure.name for procedure in bridge.visit(split_actions)] == [
        "bind_c_get_counter",
        "bind_c_set_counter",
    ]


def test_fortran_module_setter_rejects_unsupported_bridge_assignment():
    plan = _plan()
    counter = next(variable for variable in plan.variables if variable.bridge.native_name == "counter")
    invalid = replace(counter, bridge=replace(counter.bridge, native_assignment=AssignmentMode.ALIAS))

    bridge = FortranBridgeGenerator()
    bridge.visit(plan)
    with pytest.raises(ValueError, match="Unsupported Fortran module setter assignment"):
        bridge.visit(invalid)


@pytest.mark.parametrize(
    ("python_name", "assignment"),
    [
        pytest.param("counter", AssignmentMode.ALIAS, id="direct-value-with-alias"),
        pytest.param("optional_scale", AssignmentMode.NONE, id="descriptor-without-assignment"),
        pytest.param("limit", AssignmentMode.VALUE_COPY, id="constant-with-assignment"),
    ],
)
def test_module_setter_assignment_mismatch_fails_before_backend_preflight_or_lowering(
    python_name,
    assignment,
):
    invalid = _replace_variable(
        _plan(),
        python_name,
        lambda variable: replace(
            variable,
            bridge=replace(variable.bridge, native_assignment=assignment),
        ),
    )
    c_generator = Mock(spec=CBindingGenerator)
    fortran_generator = Mock(spec=FortranBridgeGenerator)
    c_printer = Mock()
    fortran_printer = Mock()
    generator = WrapperGenerator(
        c_generator=c_generator,
        fortran_generator=fortran_generator,
        c_printer=c_printer,
        fortran_printer=fortran_printer,
    )

    with pytest.raises(ValueError, match="invalid-module-native-assignment") as error:
        generator.generate(invalid)

    assert "Unsupported Fortran module setter assignment" not in str(error.value)
    c_generator.require_supported.assert_not_called()
    fortran_generator.require_supported.assert_not_called()
    c_generator.visit.assert_not_called()
    fortran_generator.visit.assert_not_called()
    c_generator.requires_native_support.assert_not_called()
    c_printer.doprint.assert_not_called()
    fortran_printer.doprint.assert_not_called()


def test_generated_support_procedure_symbol_is_shared_by_both_boundary_lowerers():
    plan = _plan()
    procedure = next(
        item
        for item in plan.entrypoint.support_procedures
        if item.owner_path == "scalar_state.counter" and item.role == "module:set"
    )
    renamed = replace(procedure, symbol_name="planned_counter_assignment")
    edited = replace(
        plan,
        entrypoint=replace(
            plan.entrypoint,
            support_procedures=tuple(
                renamed if item is procedure else item for item in plan.entrypoint.support_procedures
            ),
        ),
    )

    artifacts = WrapperGenerator().generate(edited)
    c_source = _source(artifacts, ".c")
    fortran_source = _source(artifacts, ".f90")

    assert "void planned_counter_assignment(int32_t value);" in c_source
    assert "planned_counter_assignment(value);" in c_source
    assert "subroutine planned_counter_assignment(value)" in fortran_source
    assert 'bind(c, name="planned_counter_assignment")' in fortran_source


def test_missing_generated_support_procedure_fails_before_lowering():
    plan = _plan()
    edited = replace(
        plan,
        entrypoint=replace(
            plan.entrypoint,
            support_procedures=tuple(
                item
                for item in plan.entrypoint.support_procedures
                if not (item.owner_path == "scalar_state.counter" and item.role == "module:set")
            ),
        ),
    )

    with pytest.raises(ValueError, match="incomplete-auxiliary-entrypoint-inventory"):
        WrapperGenerator().generate(edited)


def test_bridge_local_module_target_edit_does_not_change_the_c_boundary():
    plan = _plan()
    baseline = _source(WrapperGenerator().generate(plan), ".c")
    edited = _replace_variable(
        plan,
        "counter",
        lambda variable: replace(
            variable,
            bridge=replace(variable.bridge, native_name="counter_alternate"),
        ),
    )

    artifacts = WrapperGenerator().generate(edited)

    assert _source(artifacts, ".c") == baseline
    assert "native_counter => counter_alternate" in _source(artifacts, ".f90")


def test_generator_rejects_python_module_setter_without_bridge_handoff():
    invalid = _replace_variable(
        _plan(),
        "counter",
        lambda variable: replace(
            variable,
            entrypoint=replace(variable.entrypoint, setter_role=None),
        ),
    )

    with pytest.raises(ValueError, match="missing-module-setter-role"):
        WrapperGenerator().generate(invalid)
