"""Scalar module-variable planning and lowering tests."""

from __future__ import annotations

from dataclasses import replace
from unittest.mock import Mock

import pytest

from tests.fortran._support.ownership_policy import parse_pyi_text
from prik.parsers.fortran.parser import parse_fortran_project
from prik.pipeline.build import _apply_source_python_exports, _merge_wrapper_modules
from prik.semantics.fortran2ir import fortran_project_to_semantic_modules
from prik.semantics.ownership import AssignmentMode, SetterAction
from prik.semantics.policy_completion import complete_semantic_policies
from prik.semantics.wrapper_policy import ModuleGetterAction
from prik.wrapper_codegen import WrapperCodeGenerator, WrapperPlanner
from prik.wrapper_codegen.c.binding import CBindingGenerator
from prik.wrapper_codegen.fortran.bridge import FortranBridgeGenerator


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


def _computed_constant_plan():
    parsed = parse_fortran_project(
        {
            "computed_constants.f90": """
module computed_constants
  integer, parameter :: computed = kind(1.0) * 2
  character*1, parameter :: prefix = 'D'
end module computed_constants
"""
        }
    )
    modules = fortran_project_to_semantic_modules(parsed)
    _apply_source_python_exports(modules)
    module = _merge_wrapper_modules(modules, name="computed_constants_wrapper")
    complete_semantic_policies(module)
    return WrapperPlanner().build(module)


def _source(artifacts, suffix: str) -> str:
    return next(item.text for item in artifacts.sources if item.path.name.endswith(suffix))


def _replace_variable(plan, python_name: str, edit):
    root = plan.namespaces[0]
    variables = tuple(
        edit(variable) if variable.binding.python_names == (python_name,) else variable for variable in root.variables
    )
    return replace(plan, namespaces=(replace(root, variables=variables), *plan.namespaces[1:]))


def test_module_variable_plan_contains_only_completed_dispatch_facts():
    plan = _plan()
    variables = {variable.binding.python_names[0]: variable for variable in plan.namespaces[0].variables}

    assert variables["limit"].binding.getter_action is ModuleGetterAction.CONSTANT_VALUE
    assert variables["limit"].binding.setter_action is SetterAction.OMIT
    assert variables["limit"].bridge.native_assignment is AssignmentMode.NONE
    assert variables["limit"].binding.constant_value == 12
    assert variables["counter"].binding.getter_action is ModuleGetterAction.DIRECT_VALUE
    assert variables["counter"].binding.setter_action is SetterAction.WRITE_THROUGH
    assert variables["counter"].bridge.native_assignment is AssignmentMode.VALUE_COPY
    assert variables["counter"].binding.initializer == 3
    assert variables["target_scale"].bridge.native_assignment is AssignmentMode.VALUE_COPY
    assert variables["optional_scale"].binding.getter_action is ModuleGetterAction.NULLABLE_SNAPSHOT
    assert variables["optional_scale"].bridge.descriptor_kind == "allocatable"
    assert variables["optional_scale"].binding.setter_action is SetterAction.REJECT_REPLACEMENT
    assert variables["optional_scale"].bridge.native_assignment is AssignmentMode.NONE
    assert variables["selected_scale"].bridge.descriptor_kind == "pointer"
    assert variables["selected_scale"].bridge.native_assignment is AssignmentMode.NONE


def test_symbolic_source_parameter_reuses_scalar_bridge_getter_for_module_initialization():
    plan = _computed_constant_plan()
    variables = {variable.binding.python_names[0]: variable for variable in plan.namespaces[1].variables}
    computed = variables["computed"]
    assert computed.binding.getter_action is ModuleGetterAction.NATIVE_CONSTANT_VALUE
    assert computed.binding.constant_value is None
    assert computed.bridge.getter_role == "computed_constants.computed:getter"
    assert computed.binding.setter_action is SetterAction.OMIT

    artifacts = WrapperCodeGenerator().generate(plan)
    c_source = _source(artifacts, ".c")
    fortran_source = _source(artifacts, ".f90")
    assert "int32_t bind_c_get_computed(void);" in c_source
    assert "int32_t constant_computed_value_0 = bind_c_get_computed();" in c_source
    assert 'PyUnicode_FromString("D")' in c_source
    assert "native_computed => computed" in fortran_source
    assert "function bind_c_get_computed()" in fortran_source
    assert "result = native_computed" in fortran_source
    assert "bind_c_set_computed" not in c_source
    assert "bind_c_set_computed" not in fortran_source


def test_module_variable_visitors_consume_their_backend_owned_actions():
    plan = _plan()
    counter = next(
        variable for variable in plan.namespaces[0].variables if variable.binding.python_names == ("counter",)
    )
    split_actions = replace(
        counter,
        binding=replace(
            counter.binding,
            getter_action=ModuleGetterAction.CONSTANT_VALUE,
            setter_action=SetterAction.OMIT,
        ),
        bridge=replace(
            counter.bridge,
            getter_action=ModuleGetterAction.DIRECT_VALUE,
            native_assignment=AssignmentMode.VALUE_COPY,
        ),
    )

    assert CBindingGenerator().visit(split_actions) == ()
    assert [procedure.name for procedure in FortranBridgeGenerator().visit(split_actions)] == [
        "bind_c_get_counter",
        "bind_c_set_counter",
    ]


def test_fortran_module_setter_rejects_unsupported_bridge_assignment():
    plan = _plan()
    counter = next(
        variable for variable in plan.namespaces[0].variables if variable.binding.python_names == ("counter",)
    )
    invalid = replace(counter, bridge=replace(counter.bridge, native_assignment=AssignmentMode.ALIAS))

    with pytest.raises(ValueError, match="Unsupported Fortran module setter assignment"):
        FortranBridgeGenerator().visit(invalid)


@pytest.mark.parametrize(
    ("python_name", "assignment"),
    [
        ("counter", AssignmentMode.NONE),
        ("counter", AssignmentMode.ALIAS),
        ("optional_scale", AssignmentMode.VALUE_COPY),
        ("optional_scale", AssignmentMode.ALIAS),
        ("limit", AssignmentMode.VALUE_COPY),
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
    generator = WrapperCodeGenerator(
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


def test_module_variable_generators_dispatch_get_set_and_rejection_from_plan():
    artifacts = WrapperCodeGenerator().generate(_plan())
    c_source = _source(artifacts, ".c")
    fortran_source = _source(artifacts, ".f90")

    assert "scalar_state_root_module_property_setup_getattro" in c_source
    assert "scalar_state_root_module_property_setup_setattro" in c_source
    assert 'PyModule_AddObject(mod, "limit"' in c_source
    assert "bind_c_set_counter(3);" in c_source
    assert "return bind_c_get_counter();" not in c_source
    assert "bind_c_get_counter()" in c_source
    assert "bind_c_set_counter(value)" in c_source
    assert "module variable optional_scale is read-only" in c_source
    assert "module variable selected_scale is read-only" in c_source
    assert 'getenv("PRIK_WRAPPER_FAIL_ALLOC")' in c_source
    assert "result = native_counter" in fortran_source
    assert "native_counter = value" in fortran_source
    assert "allocated(native_optional_scale)" in fortran_source
    assert "associated(native_selected_scale)" in fortran_source
    assert "optional_scale = value" not in fortran_source
    assert "selected_scale = value" not in fortran_source


def test_generator_rejects_python_module_setter_without_bridge_handoff():
    plan = _plan()
    counter = next(
        variable for variable in plan.namespaces[0].variables if variable.binding.python_names == ("counter",)
    )
    invalid_counter = replace(counter, bridge=replace(counter.bridge, setter_role=None))
    invalid = replace(
        plan,
        namespaces=(
            replace(
                plan.namespaces[0],
                variables=tuple(
                    invalid_counter if variable is counter else variable for variable in plan.namespaces[0].variables
                ),
            ),
        ),
    )

    with pytest.raises(ValueError, match="missing-module-setter-role"):
        WrapperCodeGenerator().generate(invalid)


def test_generator_rejects_binding_bridge_module_getter_disagreement():
    plan = _plan()
    counter = next(
        variable for variable in plan.namespaces[0].variables if variable.binding.python_names == ("counter",)
    )
    invalid_counter = replace(
        counter,
        bridge=replace(counter.bridge, getter_action=ModuleGetterAction.NULLABLE_SNAPSHOT),
    )
    invalid = replace(
        plan,
        namespaces=(
            replace(
                plan.namespaces[0],
                variables=tuple(
                    invalid_counter if variable is counter else variable for variable in plan.namespaces[0].variables
                ),
            ),
        ),
    )

    with pytest.raises(ValueError, match="inconsistent-module-getter-action"):
        WrapperCodeGenerator().generate(invalid)
