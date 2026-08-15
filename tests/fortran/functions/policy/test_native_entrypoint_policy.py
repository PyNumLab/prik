from prik.parsers.fortran import parse_fortran_file
from prik.policy import complete_semantic_policies
from prik.policy.construction import completed_function_wrapper_policy
from prik.policy.models import (
    EntrypointOptionalityAction,
    EntrypointPassingConvention,
    EntrypointProjectionAction,
    NativeEntrypointAction,
    ScalarLogicalABI,
)
from prik.semantics.fortran2ir import fortran_module_to_semantic_module


def _completed_policies(source: str):
    parsed = parse_fortran_file(source)
    module = fortran_module_to_semantic_module(parsed.modules[0])
    complete_semantic_policies(module)
    return {function.name: completed_function_wrapper_policy(function) for function in module.functions}


def test_entrypoint_policy_selects_direct_per_operation_and_keeps_ordinary_adapter():
    policies = _completed_policies(
        """
module entrypoints
  use iso_c_binding
contains
  real(c_double) function direct_value(value) bind(C, name="direct_value_label") result(output)
    real(c_double), value, intent(in) :: value
    output = value
  end function direct_value

  subroutine direct_reference(value) bind(C)
    real(c_double), intent(inout) :: value
  end subroutine direct_reference

  subroutine ordinary(value)
    real(c_double), intent(inout) :: value
  end subroutine ordinary
end module entrypoints
"""
    )

    direct_value = policies["direct_value"]
    assert direct_value.entrypoint_action is NativeEntrypointAction.DIRECT_C_ABI
    assert direct_value.entrypoint_symbol == "direct_value_label"
    assert direct_value.arguments[0].entrypoint_passing is EntrypointPassingConvention.C_VALUE
    assert direct_value.native_call_slots[0].projection_action is EntrypointProjectionAction.ARGUMENT_DEFAULT

    direct_reference = policies["direct_reference"]
    assert direct_reference.entrypoint_action is NativeEntrypointAction.DIRECT_C_ABI
    assert direct_reference.arguments[0].entrypoint_passing is EntrypointPassingConvention.POINTER_REFERENCE

    ordinary = policies["ordinary"]
    assert ordinary.entrypoint_action is NativeEntrypointAction.GENERATED_FORTRAN_ADAPTER
    assert ordinary.entrypoint_symbol == ""
    assert ordinary.entrypoint_diagnostics == ("original procedure has no Fortran C ABI fact",)


def test_entrypoint_policy_directs_nonvalue_optional_and_adapts_optional_value():
    policies = _completed_policies(
        """
module optional_entrypoints
  use iso_c_binding
contains
  subroutine optional_reference(value) bind(C)
    real(c_double), optional, intent(in) :: value
  end subroutine optional_reference

  subroutine optional_value(value) bind(C)
    real(c_double), value, optional, intent(in) :: value
  end subroutine optional_value
end module optional_entrypoints
"""
    )

    reference = policies["optional_reference"]
    assert reference.entrypoint_action is NativeEntrypointAction.DIRECT_C_ABI
    assert reference.arguments[0].entrypoint_passing is EntrypointPassingConvention.NULLABLE_POINTER
    assert reference.arguments[0].entrypoint_optionality is EntrypointOptionalityAction.NULL_POINTER

    value = policies["optional_value"]
    assert value.entrypoint_action is NativeEntrypointAction.GENERATED_FORTRAN_ADAPTER
    assert value.arguments[0].entrypoint_optionality is EntrypointOptionalityAction.ADAPTER_SIDE_FORTRAN_OMISSION
    assert "adapter-side Fortran omission" in value.entrypoint_diagnostics[0]


def test_entrypoint_policy_distinguishes_c_bool_from_ordinary_logical_storage():
    policies = _completed_policies(
        """
module logical_entrypoints
  use iso_c_binding
contains
  logical(c_bool) function direct_bool(value) bind(C) result(output)
    logical(c_bool), value, intent(in) :: value
    output = value
  end function direct_bool

  logical function ordinary_bool(value) result(output)
    logical, intent(in) :: value
    output = value
  end function ordinary_bool
end module logical_entrypoints
"""
    )

    direct = policies["direct_bool"]
    assert direct.entrypoint_action is NativeEntrypointAction.DIRECT_C_ABI
    assert direct.arguments[0].scalar_logical_abi is ScalarLogicalABI.C_BOOL

    ordinary = policies["ordinary_bool"]
    assert ordinary.entrypoint_action is NativeEntrypointAction.GENERATED_FORTRAN_ADAPTER
    assert ordinary.arguments[0].scalar_logical_abi is ScalarLogicalABI.NATIVE_KIND_COPY
