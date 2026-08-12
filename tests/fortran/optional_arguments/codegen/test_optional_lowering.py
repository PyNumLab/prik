"""Optional scalar, descriptor, and writeback lowering tests."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from tests.fortran._support.ownership_policy import parse_pyi_text
from prik.pipeline.pyi import pyi_file_to_semantic_module
from prik.policy.completion import complete_semantic_policies
from prik.policy.models import BridgeDataAction, OptionalMode
from prik.pipeline.wrapper import WrapperGenerator
from prik.planning import WrapperPlanner


OPTIONAL_FIXED_CONTRACT = (
    Path(__file__).parents[1] / "end_to_end" / "fixtures" / "contracts" / "foptional_fixed" / "__init__.pyi"
)


def _artifacts(module):
    complete_semantic_policies(module)
    return WrapperGenerator().generate(WrapperPlanner().build(module))


def _source(artifacts, suffix: str) -> str:
    return next(item.text for item in artifacts.sources if item.path.name.endswith(suffix))


def _replace_root_function(plan, function):
    root = plan.namespaces[0]
    return replace(plan, namespaces=(replace(root, functions=(function,)), *plan.namespaces[1:]))


def test_optional_scalar_lowering_distinguishes_absent_or_none_from_value():
    module = pyi_file_to_semantic_module(OPTIONAL_FIXED_CONTRACT, module_name="foptional_fixed")
    complete_semantic_policies(module)
    plan = WrapperPlanner().build(module)
    factor = plan.namespaces[0].functions[0].arguments[1]

    assert factor.binding.optional_mode is OptionalMode.NULLABLE_VALUE
    assert factor.bridge.optional_mode is OptionalMode.NULLABLE_VALUE
    artifacts = WrapperGenerator().generate(plan)
    c_source = _source(artifacts, ".c")
    fortran_source = _source(artifacts, ".f90")

    assert 'PyArg_ParseTupleAndKeywords(args, kwargs, "O|O"' in c_source
    assert "PyObject * bound_factor_obj = Py_None;" in c_source
    assert "if (bound_factor_obj != Py_None)" in c_source
    assert "bound_factor_nullable = &bound_factor;" in c_source
    assert "bind_c_optional_scale(base, bound_factor)" in fortran_source
    assert "if (c_associated(bound_factor)) then" in fortran_source
    assert "result = optional_scale(base=base, factor=factor)" in fortran_source
    assert "result = optional_scale(base=base)" in fortran_source


def test_optional_descriptor_lowering_records_presence_and_nullable_value_handoffs():
    module = parse_pyi_text(
        """
@native_call([Allocatable(Arg(0))])
def alloc_state(value: Annotated[Float64, Immutable] | None = ...) -> Int32: ...
""",
        module_name="scalar_optional_descriptors",
    )
    complete_semantic_policies(module)
    plan = WrapperPlanner().build(module)
    value = plan.namespaces[0].functions[0].arguments[0]

    assert value.binding.optional_mode is OptionalMode.DESCRIPTOR
    assert value.bridge.presence_role == "scalar_optional_descriptors.alloc_state.value:present"
    assert value.bridge.data_action is BridgeDataAction.COPY_REPRESENTATION
    assert value.bridge.copy_reason == "materialize owned Fortran allocatable scalar storage from the binding value"
    artifacts = WrapperGenerator().generate(plan)
    c_source = _source(artifacts, ".c")
    fortran_source = _source(artifacts, ".f90")

    assert "PyObject * bound_value_obj = NULL;" in c_source
    assert "if (bound_value_obj != NULL)" in c_source
    assert "bound_value_present = &bound_value;" in c_source
    assert "(bound_value_obj != NULL) && (bound_value_obj != Py_None)" in c_source
    assert "bind_c_alloc_state(bound_value_nullable, bound_value_present)" in c_source
    assert "type(c_ptr), value :: bound_value_present" in fortran_source
    assert "if (c_associated(bound_value_present)) then" in fortran_source
    assert "result = native_alloc_state(value=value_descriptor)" in fortran_source
    assert "result = native_alloc_state()" in fortran_source


def test_optional_arguments_with_hidden_literals_fail_during_shared_plan_validation():
    module = parse_pyi_text(
        """
@native_call([Int32(1), Arg(0)])
def optional_literal(value: Annotated[Float64, Immutable] | None = ...) -> Float64: ...
""",
        module_name="optional_literal",
    )
    complete_semantic_policies(module)

    with pytest.raises(ValueError, match="optional-native-literal-combination"):
        WrapperGenerator().generate(WrapperPlanner().build(module))


def test_required_descriptor_keeps_python_presence_separate_from_native_state_and_copyout():
    module = parse_pyi_text(
        """
@native_call([Allocatable(Arg(0))])
def update(value: Float64 | None) -> Returns["value", Float64] | None: ...
""",
        module_name="scalar_required_descriptors",
    )
    complete_semantic_policies(module)
    plan = WrapperPlanner().build(module)
    value = plan.namespaces[0].functions[0].arguments[0]

    assert value.binding.optional_mode is OptionalMode.REQUIRED_DESCRIPTOR
    assert value.bridge.presence_role is None
    assert value.bridge.descriptor_output_role == f"{value.owner_path}:descriptor-output"
    assert value.bridge.descriptor_output_presence_role == f"{value.owner_path}:descriptor-output-present"

    artifacts = WrapperGenerator().generate(plan)
    c_source = _source(artifacts, ".c")
    fortran_source = _source(artifacts, ".f90")

    assert 'PyArg_ParseTupleAndKeywords(args, kwargs, "O"' in c_source
    assert "bind_c_update(bound_value_nullable, &bound_value, &bound_value_descriptor_output_present)" in c_source
    assert "void * value_output" in c_source
    assert "int * value_output_present" in c_source
    assert "type(c_ptr), value :: bound_value_output" in fortran_source
    assert "integer(c_int), intent(out) :: bound_value_output_present" in fortran_source
    assert "call native_update(value_descriptor)" in fortran_source
    assert "if (allocated(value_descriptor)) then" in fortran_source
    assert "call c_f_pointer(bound_value_output, value_output)" in fortran_source


def test_generator_rejects_descriptor_plan_without_presence_role():
    module = parse_pyi_text(
        """
@native_call([Allocatable(Arg(0))])
def alloc_state(value: Annotated[Float64, Immutable] | None = ...) -> Int32: ...
""",
        module_name="invalid_descriptor",
    )
    complete_semantic_policies(module)
    plan = WrapperPlanner().build(module)
    function = plan.namespaces[0].functions[0]
    argument = function.arguments[0]
    invalid_argument = replace(argument, bridge=replace(argument.bridge, presence_role=None))
    invalid = _replace_root_function(plan, replace(function, arguments=(invalid_argument,)))

    with pytest.raises(ValueError, match="missing-descriptor-presence-role"):
        WrapperGenerator().generate(invalid)
