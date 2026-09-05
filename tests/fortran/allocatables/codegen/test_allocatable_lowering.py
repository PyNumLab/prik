"""Allocatable descriptor lowering from completed wrapper policy."""

import pytest

from tests.fortran._support.ownership_policy import parse_pyi_text
from prik.policy.completion import complete_semantic_policies
from prik.pipeline.wrapper import WrapperGenerator
from prik.planning import WrapperPlanner
from prik.policy.models import NativeArrayDescriptorKind, NativeDescriptorHandoffABI


def _allocatable_plan():
    module = parse_pyi_text(
        """
from prik.contracts import Addr, Allocatable, Annotated, Arg, Float64, Int32, MaybeUnallocated, native_call

@native_call([Addr(Arg(0))])
def make(n: Int32) -> Allocatable[Float64[:]]: ...

@native_call([Addr(Arg(0))])
def maybe_make(n: Int32) -> Annotated[Allocatable[Float64[:]], MaybeUnallocated]: ...
""",
        module_name="allocatable_handles",
    )
    complete_semantic_policies(module)
    return WrapperPlanner().build(module)


def _module_allocatable_plan():
    module = parse_pyi_text(
        """
from prik.contracts import Allocatable, Float64

plain_allocatable: Allocatable[Float64[:]]
""",
        module_name="allocatable_module_handles",
    )
    complete_semantic_policies(module)
    return WrapperPlanner().build(module)


def test_plain_module_allocatable_uses_standard_descriptor_callback_without_copy():
    artifacts = WrapperGenerator().generate(_module_allocatable_plan())
    c_source = next(source.text for source in artifacts.sources if source.path.suffix == ".c")
    bridge_source = next(source.text for source in artifacts.sources if source.path.suffix == ".f90")

    assert "void (*callback)(CFI_cdesc_t *, void *)" in c_source
    assert "prik_module_allocatable_module_handles_plain_allocatable_descriptor_callback" in c_source
    assert "descriptor->base_addr" in c_source
    assert "Py_BuildValue" in c_source
    assert "subroutine bind_c_plain_allocatable_descriptor(" in bridge_source
    assert 'bind(c, name="bind_c_plain_allocatable_descriptor")' in bridge_source
    assert "type(c_funptr), value :: callback_address" in bridge_source
    assert "procedure(prik_plain_allocatable_descriptor_consumer), pointer :: callback" in bridge_source
    assert "call callback(native_plain_allocatable, context)" in bridge_source


def test_allocated_direct_result_assigns_then_moves_into_owned_descriptor():
    bridge_source = next(
        source.text
        for source in WrapperGenerator().generate(_allocatable_plan()).sources
        if source.path.suffix == ".f90"
    )
    start = bridge_source.index("subroutine bind_c_make(")
    end = bridge_source.index("end subroutine", start)
    procedure = bridge_source[start:end]

    assert "real(c_double), allocatable, dimension(:), intent(out) :: result" in procedure
    assert "real(c_double), allocatable, dimension(:) :: result_value" in procedure
    assert "result_value = native_make(n)" in procedure
    assert "if (allocated(result_value)) then" in procedure
    assert "call move_alloc(result_value, result)" in procedure
    assert "if (allocated(result)) then" in procedure
    assert "deallocate(result)" in procedure
    assert "call prik_collect_allocatable_array_result(native_make(n), result)" not in procedure
    assert "result = result_value" not in procedure
    assert "function bind_c_owned_result_" in bridge_source
    assert "_allocated(" in bridge_source
    assert "real(c_double), allocatable, dimension(:), intent(in) :: result" in bridge_source
    assert "subroutine bind_c_owned_result_" in bridge_source
    assert "_deallocate(" in bridge_source
    assert "real(c_double), allocatable, dimension(:), intent(inout) :: result" in bridge_source
    assert "_destroy(" in bridge_source


def test_maybe_unallocated_direct_result_uses_collector_without_assignment():
    bridge_source = next(
        source.text
        for source in WrapperGenerator().generate(_allocatable_plan()).sources
        if source.path.suffix == ".f90"
    )
    start = bridge_source.index("subroutine bind_c_maybe_make(")
    end = bridge_source.index("end subroutine", start)
    procedure = bridge_source[start:end]

    assert "real(c_double), allocatable, dimension(:), intent(out) :: result" in procedure
    assert "call prik_collect_allocatable_array_result(native_maybe_make(n), result)" in procedure
    assert "real(c_double), allocatable, dimension(:) :: value" in procedure
    assert "if (allocated(value)) then" in procedure
    assert "call move_alloc(value, result)" in procedure
    assert "if (allocated(result)) then" in procedure
    assert "deallocate(result)" in procedure
    assert "result_value = native_make(n)" not in procedure
    assert "call move_alloc(result_value, result)" not in procedure
    assert "result = result_value" not in procedure
    assert "subroutine prik_collect_allocatable_array_result(" in procedure


def test_maybe_unallocated_is_only_valid_on_direct_allocatable_array_results():
    module = parse_pyi_text(
        """
from prik.contracts import Allocatable, Annotated, Float64, MaybeUnallocated

def invalid_argument(values: Annotated[Allocatable[Float64[:]], MaybeUnallocated]) -> Float64: ...
""",
        module_name="invalid_maybe_unallocated",
    )

    with pytest.raises(ValueError, match="MaybeUnallocated metadata"):
        complete_semantic_policies(module)


def _allocatable_argument_plan():
    module = parse_pyi_text(
        """
from prik.contracts import Allocatable, Float64, native_call

@native_call([])
def total(values: Allocatable[Float64[:]]) -> Float64: ...

plain_allocatable: Allocatable[Float64[:]]
""",
        module_name="allocatable_actuals",
    )
    complete_semantic_policies(module)
    return WrapperPlanner().build(module)


def test_no_generated_binding_establishes_an_allocated_allocatable_descriptor():
    """CFI_establish reserves the allocatable descriptor for the Fortran runtime.

    F2018 18.5.5.6 requires a null ``base_addr`` when the attribute is
    ``CFI_attribute_allocatable``: an allocatable established from C must start
    unallocated.  Pairing that attribute with a real address describes an
    already-allocated allocatable, which ifx rejects with
    ``CFI_ERROR_BASE_ADDR_NOT_NULL`` while gfortran silently accepts it.
    """
    artifacts = WrapperGenerator().generate(_allocatable_argument_plan())
    c_source = next(source.text for source in artifacts.sources if source.path.suffix == ".c")

    forged = [
        line.strip()
        for line in c_source.splitlines()
        if "CFI_establish(" in line and "CFI_attribute_allocatable" in line and ", NULL," not in line
    ]
    assert forged == []


def test_allocatable_argument_uses_the_descriptor_the_runtime_built():
    """The binding passes on the runtime's descriptor rather than a record of its own.

    A C descriptor is the Fortran runtime's to build, so the binding neither
    establishes one for an allocatable actual nor copies the one it is handed:
    the call is made inside the consumer holding it, and only that pointer
    crosses.
    """
    plan = _allocatable_argument_plan()
    functions = {function.binding.python_name: function for function in plan.namespaces[0].functions}
    argument = functions["total"].arguments[0]
    handle = argument.native_array_handle

    assert handle is not None
    assert handle.descriptor_kind is NativeArrayDescriptorKind.ALLOCATABLE
    assert handle.handoff.abi is NativeDescriptorHandoffABI.DIRECT_STANDARD_DESCRIPTOR

    artifacts = WrapperGenerator().generate(plan)
    c_source = next(source.text for source in artifacts.sources if source.path.suffix == ".c")
    assert "with_descriptor(" in c_source
    copied = [line.strip() for line in c_source.splitlines() if "memcpy(" in line and "CFI_CDESC_T" in line]
    assert copied == []
