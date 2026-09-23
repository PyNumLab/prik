"""The dummy declaration owns the assumed-type C ABI."""

from prik.parsers.fortran import parse_fortran_file
from prik.pipeline.wrapper import WrapperGenerator
from prik.planning import WrapperPlanner
from prik.policy import complete_semantic_policies
from prik.policy.models import ArrayEntrypointABI, EntrypointPassingConvention, NativeEntrypointAction
from prik.semantics.fortran2ir import fortran_module_to_semantic_module


SOURCE = """
module assumed_type_entrypoints
  use iso_c_binding
contains
  subroutine direct_scalar(x) bind(C)
    type(*), intent(in) :: x
  end subroutine
  subroutine direct_size(x) bind(C)
    type(*), dimension(*), intent(in) :: x
  end subroutine
  subroutine direct_shape(x) bind(C)
    type(*), dimension(:), intent(in) :: x
  end subroutine
  subroutine direct_rank(x) bind(C)
    type(*), dimension(..), intent(in) :: x
  end subroutine
end module
"""


def test_direct_assumed_type_plan_and_c_signatures_follow_dummy_abi():
    module = fortran_module_to_semantic_module(parse_fortran_file(SOURCE).modules[0])
    complete_semantic_policies(module)
    plan = WrapperPlanner().build(module)
    assert plan.bridge is None
    expected = {
        "direct_scalar": (EntrypointPassingConvention.POINTER_REFERENCE, None, "void *"),
        "direct_size": (EntrypointPassingConvention.POINTER_REFERENCE, ArrayEntrypointABI.RAW_ADDRESS, "void *"),
        "direct_shape": (
            EntrypointPassingConvention.C_DESCRIPTOR_POINTER,
            ArrayEntrypointABI.C_DESCRIPTOR,
            "CFI_cdesc_t *",
        ),
        "direct_rank": (
            EntrypointPassingConvention.C_DESCRIPTOR_POINTER,
            ArrayEntrypointABI.C_DESCRIPTOR,
            "CFI_cdesc_t *",
        ),
    }
    generated = WrapperGenerator().generate(plan)
    binding = next(source.text for source in generated.sources if source.path.suffix == ".c")
    for function in plan.namespaces[0].functions:
        name = function.binding.python_name
        passing, array_abi, c_type = expected[name]
        assert function.entrypoint.action is NativeEntrypointAction.DIRECT_C_ABI
        assert function.bridge is None
        assert function.arguments[0].entrypoint.passing is passing
        if array_abi is not None:
            assert function.arguments[0].array.entrypoint_abi is array_abi
        assert f"void {name}({c_type} x);" in binding
