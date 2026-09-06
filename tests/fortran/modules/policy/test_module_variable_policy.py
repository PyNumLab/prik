"""Completed policy for editable module-variable initialization."""

from prik.policy.ownership import SetterAction
from prik.policy.completion import complete_semantic_policies
from tests.fortran._support.ownership_policy import parse_pyi_text
from prik.parsers.fortran.parser import parse_fortran_project
from prik.pipeline.build import _apply_source_python_exports, _merge_wrapper_modules
from prik.printers.pyi import PyiPrinter
from prik.semantics.fortran2ir import fortran_project_to_semantic_modules
from prik.semantics.models import RESOLVED_MODULE_VARIABLE_POLICY_METADATA
from prik.policy.ownership import AssignmentMode
from prik.policy.models import (
    ModuleArrayAddressMechanism,
    ModuleGetterAction,
    ModuleVariablePolicy,
    NativeArrayDescriptorAttribute,
)


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


def test_fixed_character_handles_publish_only_the_descriptor_attribute_their_callback_can_supply():
    parsed = parse_fortran_project(
        {
            "character_arrays.f90": """
module character_arrays
  character(len=5), allocatable :: fixed_alloc(:)
  character(len=5), pointer :: fixed_pointer(:) => null()
  character(len=:), allocatable :: deferred_alloc(:)
  real(8), allocatable :: numbers(:)
end module character_arrays
"""
        }
    )
    modules = fortran_project_to_semantic_modules(parsed)
    _apply_source_python_exports(modules)
    module = _merge_wrapper_modules(modules, name="character_arrays")
    complete_semantic_policies(module)

    handles = {
        variable.name: variable.metadata[RESOLVED_MODULE_VARIABLE_POLICY_METADATA].native_array_handle
        for variable in module.variables
    }

    assert handles["fixed_alloc"].descriptor_attribute is NativeArrayDescriptorAttribute.OTHER
    assert handles["fixed_pointer"].descriptor_attribute is NativeArrayDescriptorAttribute.OTHER
    assert handles["deferred_alloc"].descriptor_attribute is NativeArrayDescriptorAttribute.ALLOCATABLE
    assert handles["numbers"].descriptor_attribute is NativeArrayDescriptorAttribute.ALLOCATABLE


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


def test_parameter_arrays_complete_as_immutable_native_snapshots():
    parsed = parse_fortran_project(
        {
            "parameter_array.f90": """
module parameter_array
  use iso_fortran_env, only: real64
  real(real64), parameter :: dpmpar(3) = [epsilon(1.0_real64), tiny(1.0_real64), huge(1.0_real64)]
end module parameter_array
"""
        }
    )
    modules = fortran_project_to_semantic_modules(parsed)
    _apply_source_python_exports(modules)
    module = _merge_wrapper_modules(modules, name="parameter_array_wrapper")

    complete_semantic_policies(module)

    policy = next(
        variable.metadata[RESOLVED_MODULE_VARIABLE_POLICY_METADATA]
        for variable in module.variables
        if variable.name == "dpmpar"
    )
    assert policy.supported is True
    assert policy.getter_action is ModuleGetterAction.NATIVE_CONSTANT_ARRAY_VALUE
    assert policy.getter is not None
    assert policy.getter.owner.value == "python"
    assert policy.setter_action is SetterAction.OMIT
    assert policy.native_assignment is AssignmentMode.NONE
    assert policy.constant_value is None
    assert policy.array is not None
    assert policy.array.shape == ("3",)
    assert "dpmpar: Final[Float64[3]]" in PyiPrinter().emit(module)


def test_fixed_module_array_address_mechanism_follows_declared_addressability():
    """A fixed module array is borrowed either way; only its address route differs."""
    module = parse_pyi_text(
        """
from prik.contracts import Aliased, Annotated, Float64

values: Float64[4]
addressable: Annotated[Float64[4], Aliased]
""",
        module_name="plain_array_state",
    )
    complete_semantic_policies(module)

    policies = {
        variable.name: variable.metadata[RESOLVED_MODULE_VARIABLE_POLICY_METADATA] for variable in module.variables
    }
    assert [policy.supported for policy in policies.values()] == [True, True]
    assert policies["values"].getter_action is ModuleGetterAction.BORROWED_ARRAY_VIEW
    assert policies["values"].array_address is ModuleArrayAddressMechanism.CAPTURED_ADDRESS
    assert policies["addressable"].array_address is ModuleArrayAddressMechanism.TARGET_ADDRESS
    # Neither route hands Python the whole variable back to reassign.
    assert policies["values"].setter_action is SetterAction.REJECT_REPLACEMENT
    assert policies["addressable"].setter_action is SetterAction.REJECT_REPLACEMENT


def test_logical_module_arrays_are_borrowed_at_every_width():
    """A live view aliases element for element, so the dtype reports the width.

    NumPy has no Boolean wider than one byte, so a logical array is described by
    the integer of matching width rather than narrowed to `bool`. The widths
    then agree for every Fortran kind and each is borrowed as a live view.
    """
    module = parse_pyi_text(
        """
from prik.contracts import Bool, Bool32

narrow: Bool[3]
wide: Bool32[3]
""",
        module_name="logical_state",
    )
    complete_semantic_policies(module)

    policies = {
        variable.name: variable.metadata[RESOLVED_MODULE_VARIABLE_POLICY_METADATA] for variable in module.variables
    }
    for name in ("narrow", "wide"):
        assert policies[name].supported is True, name
        assert policies[name].getter_action is ModuleGetterAction.BORROWED_ARRAY_VIEW, name
        assert policies[name].blockers == (), name
