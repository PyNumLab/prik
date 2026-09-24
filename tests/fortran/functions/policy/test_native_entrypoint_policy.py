import ast

from prik.parsers.fortran import parse_fortran_file
from prik.policy import complete_semantic_policies
from prik.policy.construction import completed_function_wrapper_policy
from prik.policy.models import (
    EntrypointOptionalityAction,
    EntrypointPassingConvention,
    EntrypointProjectionAction,
    NativeEntrypointAction,
    ScalarActualMode,
    ScalarLogicalABI,
)
from prik.semantics.fortran2ir import fortran_module_to_semantic_module
from prik.semantics.pyi2ir import convert_pyi_to_ir


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


def test_rank_zero_actual_transport_follows_the_dummy_on_direct_and_adapted_routes():
    """A VALUE dummy copies a rank-zero actual whether or not a bridge adapts it."""
    policies = _completed_policies(
        """
module actual_routes
  use iso_c_binding
contains
  subroutine direct_value(n) bind(C)
    integer(c_int), value :: n
  end subroutine direct_value

  subroutine adapted_value(n)
    integer, value :: n
  end subroutine adapted_value

  subroutine adapted_reference(n)
    integer, intent(inout) :: n
  end subroutine adapted_reference

  subroutine c_bool_logical(flag)
    logical(c_bool), intent(inout) :: flag
  end subroutine c_bool_logical
end module actual_routes
"""
    )

    assert {name: policy.arguments[0].scalar_actual_mode for name, policy in policies.items()} == {
        "direct_value": ScalarActualMode.NUMERIC_VALUE,
        "adapted_value": ScalarActualMode.NUMERIC_VALUE,
        "adapted_reference": ScalarActualMode.NUMERIC_REFERENCE,
        "c_bool_logical": ScalarActualMode.NUMERIC_REFERENCE,
    }


def test_wider_logical_dummies_borrow_integer_storage_of_their_own_width():
    """A logical wider than c_bool crosses as its own integer width, as its arrays do."""
    source = """
from prik.contracts import Bool, Bool16, Bool32, Bool64

def flags(narrow: Bool, short: Bool16, default: Bool32, wide: Bool64) -> None: ...
"""
    module = convert_pyi_to_ir(ast.parse(source), module_name="logical_storage", source=source)
    complete_semantic_policies(module)
    arguments = completed_function_wrapper_policy(module.functions[0]).arguments

    assert [(argument.scalar_logical_abi, argument.native_storage_c_type) for argument in arguments] == [
        (ScalarLogicalABI.C_BOOL, None),
        (ScalarLogicalABI.NATIVE_KIND_STORAGE, "int16_t"),
        (ScalarLogicalABI.NATIVE_KIND_STORAGE, "int32_t"),
        (ScalarLogicalABI.NATIVE_KIND_STORAGE, "int64_t"),
    ]
    assert all(argument.scalar_actual_mode is not None for argument in arguments)


def test_immutable_values_copy_rank_zero_actuals_instead_of_lending_storage():
    """Immutable storage is only read; a plain update lends the actual's storage."""
    source = """
from prik.contracts import Annotated, Immutable, Int32, Returns, String

def bump(value: Annotated[Int32, Immutable]) -> Returns["value", Int32]: ...
def bump_in_place(value: Int32) -> Returns["value", Int32]: ...
def label(text: Annotated[String[8], Immutable]) -> Returns["text", String[8]]: ...
def label_in_place(text: String[8]) -> Returns["text", String[8]]: ...
"""
    module = convert_pyi_to_ir(ast.parse(source), module_name="immutable_actuals", source=source)
    complete_semantic_policies(module)

    assert {
        function.name: completed_function_wrapper_policy(function).arguments[0].scalar_actual_mode
        for function in module.functions
    } == {
        "bump": ScalarActualMode.NUMERIC_VALUE,
        "bump_in_place": ScalarActualMode.NUMERIC_REFERENCE,
        "label": ScalarActualMode.CHARACTER_VALUE,
        "label_in_place": ScalarActualMode.CHARACTER_REFERENCE,
    }
