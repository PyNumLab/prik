from pathlib import Path

import pytest

from tests.fortran._support.ownership_policy import parse_pyi_text
from prik.parsers.fortran.parser import parse_fortran_project
from prik.pipeline.build import _apply_source_python_exports, _fortran_source_for_pipeline, _merge_wrapper_modules
from prik.preprocessing import PreprocessingConfig
from prik.semantics.fortran2ir import fortran_project_to_semantic_modules
from prik.semantics.models import (
    RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA,
)
from prik.policy.completion import complete_semantic_policies
from prik.policy.ownership import PythonBarrierAction
from prik.policy.models import (
    CallbackABIKind,
    CallbackTransferAction,
    FunctionWrapperPolicy,
)
from prik.policy.construction import completed_function_wrapper_policy

FIXTURES = Path(__file__).parents[1] / "end_to_end" / "fixtures"


def _source_semantic_module(filename: str, *, module_name: str, assume_intent_in_scalars: bool = False):
    source = FIXTURES / "native" / filename
    parsed = parse_fortran_project({str(source): _fortran_source_for_pipeline(source, PreprocessingConfig())})
    modules = fortran_project_to_semantic_modules(parsed, assume_intent_in_scalars=assume_intent_in_scalars)
    _apply_source_python_exports(modules)
    module = _merge_wrapper_modules(modules, name=module_name)
    complete_semantic_policies(module)
    return module


def test_source_callback_value_default_and_explicit_reference_are_completed():
    module = _source_semantic_module("fcallback_all_f90.f90", module_name="fcallback_all_f90")
    function = next(item for item in module.functions if item.name == "apply_value_callback")
    policy = completed_function_wrapper_policy(function)
    transfer = policy.arguments[0].callback.arguments[0]

    assert transfer.abi is CallbackABIKind.VALUE
    assert transfer.passed_by_value is True
    assert transfer.adapter_action is CallbackTransferAction.COPY_IN

    array_function = next(item for item in module.functions if item.name == "apply_array_storage_callback")
    array_policy = completed_function_wrapper_policy(array_function)
    extent = array_policy.arguments[0].callback.arguments[0]
    assert extent.abi is CallbackABIKind.REFERENCE
    assert extent.passed_by_value is False
    assert extent.adapter_action is CallbackTransferAction.COPY_IN


@pytest.mark.parametrize(
    ("prototype", "blocker"),
    [
        (
            "def callback_shape(value: Allocatable[Float64]) -> None: ...",
            "callback argument 'value' uses unsupported allocatable, pointer, polymorphic, or assumed-type storage",
        ),
        (
            "def callback_shape(value: Float64 = ...) -> None: ...",
            "callback argument 'value' cannot be optional",
        ),
        (
            "def callback_shape() -> Pointer[Float64]: ...",
            "callback result uses unsupported allocatable, pointer, polymorphic, or assumed-type storage",
        ),
    ],
)
def test_callback_descriptor_and_optional_forms_are_blocked_before_codegen(prototype: str, blocker: str):
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


def test_writable_callback_scalars_use_rank_zero_storage_without_synthesizing_intent():
    """Every dummy the callee may write is projected as writable storage.

    Python has no writable scalar, so a dummy the native caller reads back must
    reach the callable as rank-zero storage.  An undeclared ``intent`` is
    conservatively writable because Fortran permits the callee to modify it,
    and the declaration keeps no intent of its own either way.
    """
    module = _source_semantic_module("fcallback_all_f90.f90", module_name="fcallback_all_f90")
    function = next(item for item in module.functions if item.name == "apply_scalar_storage_callback")
    policy = completed_function_wrapper_policy(function)
    transfers = policy.arguments[0].callback.arguments

    assert [transfer.intent for transfer in transfers] == ["inout", "out", None]
    assert [transfer.python_action for transfer in transfers] == [PythonBarrierAction.SCALAR_STORAGE] * 3
    assert [transfer.adapter_action for transfer in transfers] == [
        CallbackTransferAction.COPY_IN_OUT,
        CallbackTransferAction.COPY_OUT,
        CallbackTransferAction.COPY_IN_OUT,
    ]
    assert policy.supported is True


def test_assume_intent_in_scalars_elects_the_input_only_default_for_an_undeclared_intent():
    """The flag chooses which default an undeclared ``intent`` receives.

    It narrows the conservative read/write default to input-only; it does not
    give the dummy a declared direction, so the contract still carries none.
    """
    module = _source_semantic_module(
        "fcallback_all_f90.f90",
        module_name="fcallback_all_f90",
        assume_intent_in_scalars=True,
    )
    function = next(item for item in module.functions if item.name == "apply_scalar_storage_callback")
    transfers = completed_function_wrapper_policy(function).arguments[0].callback.arguments

    undeclared = transfers[2]
    assert undeclared.intent is None
    assert undeclared.python_action is PythonBarrierAction.SCALAR_VALUE
    assert undeclared.adapter_action is CallbackTransferAction.COPY_IN


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


def test_imported_interface_keeps_its_declaring_module_in_the_completed_identity():
    """A type an imported interface owns must not be attributed to the consumer.

    The consuming module never imports ``point_t``, so an identity taken from
    the consuming scope names a type that module does not define and no wrapper
    definition can satisfy it.
    """
    sources = {
        "callback_types.f90": """
module callback_types
  implicit none
  type :: point_t
    real(8) :: x
  end type point_t

  abstract interface
    subroutine move_point(p)
      import :: point_t
      implicit none
      type(point_t), intent(inout) :: p
    end subroutine move_point
  end interface
end module callback_types
""",
        "consumer.f90": """
module consumer
  use callback_types, only : move_point
  implicit none
contains
  subroutine run(f)
    procedure(move_point) :: f
  end subroutine run
end module consumer
""",
    }
    parsed = parse_fortran_project(sources)
    modules = fortran_project_to_semantic_modules(parsed)
    _apply_source_python_exports(modules)
    module = _merge_wrapper_modules(modules, name="merged")
    complete_semantic_policies(module)

    function = next(item for item in module.functions if item.name == "run")
    policy = completed_function_wrapper_policy(function)

    assert policy.supported is True
    assert policy.arguments[0].callback.arguments[0].derived_type_identity == ("callback_types", "point_t")


def test_imported_interface_result_keeps_its_declaring_module_in_the_completed_identity():
    """A callback result's type identity must name the module that declares it."""
    sources = {
        "callback_types.f90": """
module callback_types
  implicit none
  type :: point_t
    real(8) :: x
  end type point_t

  abstract interface
    function make_point(x) result(p)
      import :: point_t
      implicit none
      real(8), intent(in) :: x
      type(point_t) :: p
    end function make_point
  end interface
end module callback_types
""",
        "consumer.f90": """
module consumer
  use callback_types, only : make_point
  implicit none
contains
  subroutine run(f)
    procedure(make_point) :: f
  end subroutine run
end module consumer
""",
    }
    parsed = parse_fortran_project(sources)
    modules = fortran_project_to_semantic_modules(parsed)
    _apply_source_python_exports(modules)
    module = _merge_wrapper_modules(modules, name="merged")
    complete_semantic_policies(module)

    policy = completed_function_wrapper_policy(next(item for item in module.functions if item.name == "run"))

    assert policy.supported is True
    assert policy.arguments[0].callback.result.transfer.derived_type_identity == ("callback_types", "point_t")
