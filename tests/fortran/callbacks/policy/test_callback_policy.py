import pytest

from tests.fortran._support.ownership_policy import parse_pyi_text
from prik.parsers.fortran.parser import parse_fortran_project
from prik.pipeline.build import _apply_source_python_exports, _merge_wrapper_modules
from prik.semantics.fortran2ir import fortran_project_to_semantic_modules
from prik.semantics.models import (
    RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA,
)
from prik.policy.completion import complete_semantic_policies
from prik.policy.ownership import PythonBarrierAction
from prik.policy.models import (
    FunctionWrapperPolicy,
)


@pytest.mark.parametrize(
    ("prototype", "blocker"),
    [
        (
            "def callback_shape(value: Allocatable[Float64]) -> None: ...",
            "callback argument 'value' uses unsupported allocatable, pointer, polymorphic, or assumed-type storage",
        ),
        (
            "def callback_shape(value: Float64 = ...) -> None: ...",
            "callback argument 'value' cannot be both optional and passed by value; "
            "use a reference dummy so absence has a null-pointer ABI",
        ),
        (
            "def callback_shape() -> Pointer[Float64]: ...",
            "callback result uses unsupported allocatable, pointer, polymorphic, or assumed-type storage",
        ),
    ],
)
def test_unsupported_callback_forms_are_blocked_before_codegen(prototype: str, blocker: str):
    module = parse_pyi_text(
        f"""
@prototype
{prototype}

def apply(callback: callback_shape) -> None: ...
""",
        module_name="unsupported_callback_shape",
    )

    complete_semantic_policies(module)

    policy = module.functions[0].metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]
    assert isinstance(policy, FunctionWrapperPolicy)
    assert policy.supported is False
    assert blocker in policy.blockers


def test_procedure_interface_from_an_unsupplied_module_is_blocked_by_name():
    """A named interface no input declares is reported against that name.

    Without the module that declares it the dummy has no signature, so the
    diagnostic must name the interface the declaration asked for rather than
    the opaque placeholder type it fell back to.
    """
    source = """
module solver_mod
  use, non_intrinsic :: pintrf_mod, only : OBJ
  implicit none
contains
  subroutine minimize(calfun, x)
    procedure(OBJ) :: calfun
    real(8), intent(in) :: x
  end subroutine minimize
end module solver_mod
"""
    parsed = parse_fortran_project({"solver.f90": source})
    modules = fortran_project_to_semantic_modules(parsed)
    _apply_source_python_exports(modules)
    module = _merge_wrapper_modules(modules, name="solver_mod")
    complete_semantic_policies(module)

    policy = module.functions[0].metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]
    assert policy.supported is False
    assert (
        "argument 'calfun' declares procedure interface 'OBJ', which no supplied source declares; "
        "add the module that declares it to the build inputs" in policy.blockers
    )


@pytest.mark.parametrize(
    ("prototype", "blocker"),
    [
        (
            "def callback_shape(value: Out(Addr(Float64))) -> None: ...",
            "callback argument 'value' is intent(out) and cannot use the value spelling "
            "Addr(Float64); use Float64[()] for writable storage",
        ),
        (
            "def callback_shape(value: InOut(Addr(Int32))) -> None: ...",
            "callback argument 'value' is intent(inout) and cannot use the value spelling "
            "Addr(Int32); use Int32[()] for writable storage",
        ),
    ],
)
def test_value_spelling_is_blocked_for_written_back_callback_scalars(prototype: str, blocker: str):
    """An out or inout dummy spelled as a value would silently discard the write."""
    module = parse_pyi_text(
        f"""
@prototype
{prototype}

def apply(callback: callback_shape) -> None: ...
""",
        module_name="discarded_callback_writeback",
    )

    complete_semantic_policies(module)

    policy = module.functions[0].metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]
    assert policy.supported is False
    assert blocker in policy.blockers


def test_read_only_callback_scalars_keep_the_value_spelling():
    """An in dummy is never read back, so the value projection stays valid."""
    module = parse_pyi_text(
        """
@prototype
def callback_shape(value: In(Addr(Float64))) -> None: ...

def apply(callback: callback_shape) -> None: ...
""",
        module_name="read_only_callback_scalar",
    )

    complete_semantic_policies(module)

    policy = module.functions[0].metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]
    assert policy.supported is True
    assert policy.arguments[0].callback.arguments[0].python_action is PythonBarrierAction.SCALAR_VALUE
