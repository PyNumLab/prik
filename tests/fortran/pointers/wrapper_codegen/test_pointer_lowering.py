"""Pointer descriptor lowering from completed wrapper policy."""

from tests.fortran._support.ownership_policy import parse_pyi_text
from x2py.semantics.policy_completion import complete_semantic_policies
from x2py.semantics.wrapper_policy import (
    NativeArrayDescriptorKind,
    NativeArrayDescriptorOwnership,
    NativeArrayOperation,
    NativeArrayResultAllocation,
    NativeDescriptorHandoffABI,
)
from x2py.wrapper_codegen import WrapperCodeGenerator, WrapperPlanner


def _pointer_plan():
    module = parse_pyi_text(
        """
from x2py.contracts import Annotated, Arg, Float64, Int32, Pointer, PointerAssociation, PointerPolicy, Return, native_call

module_pointer: Annotated[
    Pointer[Float64[:]],
    PointerAssociation("runtime"),
    PointerPolicy(
        nullable=True,
        transfer="call_local",
        target_owner="module",
        lifetime="module",
        deallocation="never",
        shape_source="pointer_bounds",
        contiguity="strided",
        reassociation="never",
        aliasing="borrowed",
        mutability="view",
    ),
]

def make_pointer(n: Int32) -> Annotated[
    Pointer[Float64[:]],
    PointerPolicy(
        nullable=True,
        transfer="call_local",
        target_owner="module",
        lifetime="module",
        deallocation="never",
        shape_source="pointer_bounds",
        contiguity="strided",
        reassociation="never",
        aliasing="borrowed",
        mutability="view",
    ),
]: ...

@native_call([Arg(0), Return("selected", 0)])
def select_pointer(n: Int32) -> Annotated[
    Pointer[Float64[:]],
    PointerPolicy(
        nullable=True,
        transfer="call_local",
        target_owner="module",
        lifetime="module",
        deallocation="never",
        shape_source="pointer_bounds",
        contiguity="strided",
        reassociation="never",
        aliasing="borrowed",
        mutability="view",
    ),
]: ...
""",
        module_name="pointer_lowering",
    )
    complete_semantic_policies(module)
    return WrapperPlanner().build(module)


def test_pointer_plans_complete_descriptor_ownership_and_operations_before_lowering():
    plan = _pointer_plan()
    namespace = plan.namespaces[0]
    module_pointer = namespace.variables[0].native_array_handle
    functions = {function.binding.python_name: function for function in namespace.functions}
    pointer_result = functions["make_pointer"].results[0].native_array_handle
    pointer_output = functions["select_pointer"].results[0]

    assert module_pointer is not None
    assert module_pointer.descriptor_kind is NativeArrayDescriptorKind.POINTER
    assert module_pointer.borrowed is True
    assert module_pointer.required_headers == ("ISO_Fortran_binding.h",)
    assert NativeArrayOperation.ASSOCIATE in module_pointer.operations
    assert NativeArrayOperation.NULLIFY in module_pointer.operations
    assert NativeArrayOperation.DESTROY not in module_pointer.operations

    assert pointer_result is not None
    assert pointer_result.handoff.abi is NativeDescriptorHandoffABI.OWNED_RESULT_STORAGE
    assert pointer_result.descriptor_ownership is NativeArrayDescriptorOwnership.OWNED
    assert pointer_result.result_allocation is NativeArrayResultAllocation.NOT_APPLICABLE
    assert pointer_result.target_lifetime == "module"
    assert NativeArrayOperation.DESTROY in pointer_result.operations

    assert pointer_output.source_kind == "hidden_output"
    assert pointer_output.native_array_handle is not None
    assert pointer_output.native_array_handle.handoff.abi is NativeDescriptorHandoffABI.OWNED_RESULT_STORAGE


def test_pointer_lowering_assigns_descriptors_without_target_deallocation():
    artifacts = WrapperCodeGenerator().generate(_pointer_plan())
    c_source = next(source.text for source in artifacts.sources if source.path.suffix == ".c")
    bridge_source = next(source.text for source in artifacts.sources if source.path.suffix == ".f90")

    assert "void bind_c_module_pointer_associate(CFI_cdesc_t * source);" in c_source
    assert "bind_c_module_pointer_associate(source_descriptor);" in c_source
    assert "native_module_pointer => source" in bridge_source

    result_start = bridge_source.index("subroutine bind_c_make_pointer(")
    result_end = bridge_source.index("end subroutine", result_start)
    result_procedure = bridge_source[result_start:result_end]
    assert "real(c_double), pointer, dimension(:), intent(out) :: result" in result_procedure
    assert "result_value => native_make_pointer(n)" in result_procedure
    assert "result => result_value" in result_procedure
    assert "move_alloc" not in result_procedure

    output_start = bridge_source.index("subroutine bind_c_select_pointer(")
    output_end = bridge_source.index("end subroutine", output_start)
    output_procedure = bridge_source[output_start:output_end]
    assert "real(c_double), pointer, dimension(:), intent(out) :: selected" in output_procedure
    assert "call native_select_pointer(n, selected_value)" in output_procedure
    assert "selected => selected_value" in output_procedure

    operations_start = bridge_source.index("end subroutine bind_c_make_pointer")
    operations_end = bridge_source.index("subroutine bind_c_select_pointer(", operations_start)
    pointer_operations = bridge_source[operations_start:operations_end]
    assert "result => source" in pointer_operations
    assert "nullify(result)" in pointer_operations
    assert "deallocate(result)" not in pointer_operations
