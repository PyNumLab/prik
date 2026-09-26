"""Allocatable descriptor-handle routing decisions completed before lowering."""

from prik.parsers.fortran import parse_fortran_file
from prik.planning import WrapperPlanner
from prik.policy.completion import complete_semantic_policies
from prik.policy.models import NativeArrayOwnerStorage, NativeDescriptorHandoffABI, NativeEntrypointAction
from prik.semantics.fortran2ir import fortran_module_to_semantic_module


def test_deferred_character_owner_storage_keeps_the_direct_descriptor_abi():
    """Storage ownership does not replace a bind(C) procedure's declared ABI."""
    parsed = parse_fortran_file(
        """
module direct_character_owner
  use iso_c_binding
contains
  subroutine rewrite(values) bind(c)
    character(kind=c_char, len=:), allocatable, intent(inout) :: values(:, :)
  end subroutine
end module
"""
    )
    module = fortran_module_to_semantic_module(parsed.modules[0])
    complete_semantic_policies(module)
    function = WrapperPlanner().build(module).namespaces[0].functions[0]
    handle = function.arguments[0].native_array_handle
    assert handle.owner_storage is NativeArrayOwnerStorage.FORTRAN_OWNER
    assert handle.handoff.abi is NativeDescriptorHandoffABI.DIRECT_STANDARD_DESCRIPTOR
    assert function.entrypoint.action is NativeEntrypointAction.DIRECT_C_ABI
    assert function.entrypoint.symbol_name == "rewrite"
