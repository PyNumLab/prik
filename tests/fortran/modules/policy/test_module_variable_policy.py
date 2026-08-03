"""Completed policy for editable module-variable initialization."""

from tests.fortran._support.ownership_policy import (
    SetterAction,
    complete_semantic_policies,
    parse_pyi_text,
)
from prik.parsers.fortran.parser import parse_fortran_project
from prik.pipeline.build import _apply_source_python_exports, _merge_wrapper_modules
from prik.semantics.fortran2ir import fortran_project_to_semantic_modules
from prik.semantics.models import RESOLVED_MODULE_VARIABLE_POLICY_METADATA
from prik.semantics.ownership import AssignmentMode
from prik.semantics.wrapper_policy import ModuleGetterAction, ModuleVariablePolicy


def test_scalar_module_variable_policy_completes_access_and_storage_before_planning():
    module = parse_pyi_text(
        """
limit: Final[Int32] = 12
counter: Int32 = 3
target_scale: Annotated[Float64, Aliased]
optional_scale: Allocatable[Float64]
selected_scale: Pointer[Float64]
""",
        module_name="scalar_state",
    )
    complete_semantic_policies(module)

    policies = {
        variable.name: variable.metadata[RESOLVED_MODULE_VARIABLE_POLICY_METADATA] for variable in module.variables
    }

    assert all(isinstance(policy, ModuleVariablePolicy) for policy in policies.values())
    assert all(policy.supported for policy in policies.values())
    assert policies["limit"].getter_action is ModuleGetterAction.CONSTANT_VALUE
    assert policies["limit"].setter_action is SetterAction.OMIT
    assert policies["limit"].native_assignment is AssignmentMode.NONE
    assert policies["limit"].constant_value == 12
    assert policies["counter"].getter_action is ModuleGetterAction.DIRECT_VALUE
    assert policies["counter"].setter_action is SetterAction.WRITE_THROUGH
    assert policies["counter"].native_assignment is AssignmentMode.VALUE_COPY
    assert policies["counter"].initializer == 3
    assert policies["target_scale"].getter_action is ModuleGetterAction.DIRECT_VALUE
    assert policies["target_scale"].setter_action is SetterAction.WRITE_THROUGH
    assert policies["target_scale"].native_assignment is AssignmentMode.VALUE_COPY
    assert policies["optional_scale"].getter_action is ModuleGetterAction.NULLABLE_SNAPSHOT
    assert policies["optional_scale"].descriptor_kind == "allocatable"
    assert policies["optional_scale"].setter_action is SetterAction.REJECT_REPLACEMENT
    assert policies["optional_scale"].native_assignment is AssignmentMode.NONE
    assert policies["selected_scale"].getter_action is ModuleGetterAction.NULLABLE_SNAPSHOT
    assert policies["selected_scale"].descriptor_kind == "pointer"
    assert policies["selected_scale"].setter_action is SetterAction.REJECT_REPLACEMENT
    assert policies["selected_scale"].native_assignment is AssignmentMode.NONE


def test_symbolic_source_parameters_use_native_getters_while_literals_stay_in_binding():
    parsed = parse_fortran_project(
        {
            "computed_constants.f90": """
module computed_constants
  integer, parameter :: computed = kind(1.0) * 2
  real, parameter :: tolerance = epsilon(0.0)
  integer, parameter :: literal = 12
  character*1, parameter :: prefix = 'D'
end module computed_constants
"""
        }
    )
    modules = fortran_project_to_semantic_modules(parsed)
    _apply_source_python_exports(modules)
    module = _merge_wrapper_modules(modules, name="computed_constants_wrapper")

    complete_semantic_policies(module)

    policies = {
        variable.name: variable.metadata[RESOLVED_MODULE_VARIABLE_POLICY_METADATA] for variable in module.variables
    }
    assert policies["computed"].getter_action is ModuleGetterAction.NATIVE_CONSTANT_VALUE
    assert policies["computed"].constant_value is None
    assert policies["computed"].setter_action is SetterAction.OMIT
    assert policies["tolerance"].getter_action is ModuleGetterAction.NATIVE_CONSTANT_VALUE
    assert policies["tolerance"].constant_value is None
    assert policies["literal"].getter_action is ModuleGetterAction.CONSTANT_VALUE
    assert policies["literal"].constant_value == 12
    assert policies["prefix"].getter_action is ModuleGetterAction.CONSTANT_VALUE
    assert policies["prefix"].constant_value == "D"
    assert all(policy.supported for policy in policies.values())


def test_fixed_module_array_requires_explicit_addressable_alias_storage():
    module = parse_pyi_text(
        """
from prik.contracts import Float64

values: Float64[4]
""",
        module_name="plain_array_state",
    )
    complete_semantic_policies(module)

    policy = module.variables[0].metadata[RESOLVED_MODULE_VARIABLE_POLICY_METADATA]
    assert policy.supported is False
    assert "ordinary module array requires addressable Aliased target storage" in policy.blockers
