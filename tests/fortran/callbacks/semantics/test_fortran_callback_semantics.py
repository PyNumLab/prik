"""Tests split by stable ownership concept from `test_compile_time_values.py`."""

from prik.parsers.fortran import parse_fortran_project
from prik.printers import emit_module
from prik.semantics.fortran2ir import FortranToIRConverter
from prik.semantics.models import (
    EXTERNAL_TYPE_REF_METADATA,
    PROTOTYPE_REF_METADATA,
    UNRESOLVED_PROCEDURE_INTERFACE_METADATA,
)
from prik.semantics.native_contract import native_contract_issues
from tests.fortran._support.semantic_conversion import get_function
from prik.parsers.fortran import parse_fortran_file as parse_fortran_source
from prik.pipeline.pyi import pyi_text_to_semantic_module as parse_pyi_text


def test_dummy_procedure_interfaces_become_complete_callable_contracts():
    source = """
module callbacks
  type :: point_t
    real(8) :: x
  end type point_t
    abstract interface
      function transform_iface(count, values, point) result(output)
        import :: point_t
        integer, intent(in) :: count
        real(8), intent(in) :: values(count)
        type(point_t), intent(in) :: point
        real(8) :: output(count)
      end function transform_iface
      subroutine no_intent_iface(count, values)
        integer :: count
        real(8) :: values(count)
      end subroutine no_intent_iface
      subroutine value_iface(value, ref)
        integer, value, intent(in) :: value
        real(8) :: ref
      end subroutine value_iface
      subroutine notify_iface(value)
        integer, intent(in) :: value
      end subroutine notify_iface
      subroutine string_iface(read_label, write_label, update_label)
        character(len=8), intent(in) :: read_label
        character(len=8), intent(out) :: write_label
        character(len=8), intent(inout) :: update_label
      end subroutine string_iface
  end interface
contains
  subroutine abstract_case(callback)
    procedure(transform_iface) :: callback
  end subroutine abstract_case
  subroutine explicit_case(callback)
    interface
      integer function callback(value) result(output)
        integer, intent(in) :: value
      end function callback
    end interface
  end subroutine explicit_case
  subroutine notify_case(callback)
    procedure(notify_iface) :: callback
  end subroutine notify_case
  subroutine no_intent_case(callback)
    procedure(no_intent_iface) :: callback
  end subroutine no_intent_case
  subroutine value_case(callback)
    procedure(value_iface) :: callback
  end subroutine value_case
  subroutine string_case(callback)
    procedure(string_iface) :: callback
  end subroutine string_case
end module callbacks
"""
    module = FortranToIRConverter().visit(parse_fortran_source(source).modules[0])

    abstract_callback = get_function(module, "abstract_case").arguments[0].semantic_type
    assert abstract_callback.name == "transform_iface"
    assert [argument.name for argument in abstract_callback.metadata["callback_arguments"]] == [
        "count",
        "values",
        "point",
    ]
    assert [argument.name for argument in abstract_callback.metadata["arguments"]] == [
        "Int32",
        "Float64",
        "point_t",
    ]
    assert abstract_callback.metadata["arguments"][1].shape == ["count"]
    assert abstract_callback.metadata["return"].name == "Float64"
    assert abstract_callback.metadata["return"].shape == ["count"]
    assert abstract_callback.metadata["callback_lifetime"] == "call"
    assert abstract_callback.metadata["callback_thread"] == "entering_thread"
    assert abstract_callback.metadata["callback_exception"] == "print_traceback_and_abort"
    assert all(
        argument.semantic_type.storage is not None for argument in abstract_callback.metadata["callback_arguments"]
    )

    explicit_callback = get_function(module, "explicit_case").arguments[0].semantic_type
    assert explicit_callback.name == "callback"
    assert [argument.name for argument in explicit_callback.metadata["arguments"]] == ["Int32"]
    assert explicit_callback.metadata["return"].name == "Int32"

    notify_callback = get_function(module, "notify_case").arguments[0].semantic_type
    assert notify_callback.metadata["return"].name == "None"

    no_intent_callback = get_function(module, "no_intent_case").arguments[0].semantic_type
    assert all(argument.semantic_type.storage.mutable for argument in no_intent_callback.metadata["callback_arguments"])

    value_callback = get_function(module, "value_case").arguments[0].semantic_type
    assert [argument.name for argument in value_callback.metadata["callback_arguments"]] == ["value", "ref"]
    assert [argument.origin.metadata["value"] for argument in value_callback.metadata["callback_arguments"]] == [
        True,
        False,
    ]

    string_callback = get_function(module, "string_case").arguments[0].semantic_type
    assert all(
        argument.semantic_type.storage.array.category == "scalar_storage"
        for argument in string_callback.metadata["callback_arguments"]
    )

    emitted = emit_module(module)
    assert "@prototype\ndef transform_iface(" in emitted
    assert "callback: transform_iface" in emitted
    assert "@prototype\ndef value_iface(" in emitted
    assert "value: In(Int32)" in emitted
    # A dummy with no declared intent keeps that absence in the contract while
    # carrying storage the callee may write through.
    assert "ref: Float64[()]" in emitted
    assert "@prototype\ndef string_iface(" in emitted
    assert "read_label: In(String[8])" in emitted
    assert native_contract_issues(parse_pyi_text(emitted, module_name=module.name)) == []

    project = parse_fortran_project(
        {
            "callback_types.f90": """
module callback_types
  abstract interface
    integer function unary(value) result(output)
      integer, intent(in) :: value
    end function unary
  end interface
end module callback_types
""",
            "callback_user.f90": """
module callback_user
  use callback_types, only: renamed => unary
contains
  integer function apply(callback, value) result(output)
    procedure(renamed) :: callback
    integer, intent(in) :: value
    output = callback(value)
  end function apply
end module callback_user
""",
        }
    )
    modules = {item.name: item for item in FortranToIRConverter().visit(project)}
    imported_callback = get_function(modules["callback_user"], "apply").arguments[0].semantic_type
    assert imported_callback.name == "renamed"
    assert [argument.name for argument in imported_callback.metadata["arguments"]] == ["Int32"]
    assert imported_callback.metadata["return"].name == "Int32"

    standalone = parse_fortran_source(
        """
subroutine standalone_case(callback)
  interface
    integer function callback(value) result(output)
      integer, intent(in) :: value
    end function callback
  end interface
end subroutine standalone_case
"""
    )
    standalone_module = FortranToIRConverter().visit(standalone)[0]
    standalone_callback = get_function(standalone_module, "standalone_case").arguments[0].semantic_type
    assert standalone_callback.name == "callback"
    assert [argument.name for argument in standalone_callback.metadata["arguments"]] == ["Int32"]
    assert standalone_callback.metadata["return"].name == "Int32"


def test_duplicate_interface_signatures_emit_one_named_callback_prototype():
    source = """
module duplicate_prototypes
  abstract interface
    subroutine callback(value)
      integer :: value
    end subroutine callback
  end interface
  interface
    subroutine callback(value)
      integer :: value
    end subroutine callback
  end interface
contains
  subroutine apply(callback)
    procedure(callback) :: callback
  end subroutine apply
end module duplicate_prototypes
"""

    module = FortranToIRConverter().visit(parse_fortran_source(source).modules[0])

    assert [prototype.name for prototype in module.prototypes] == ["callback"]


def test_imported_abstract_interface_resolves_across_files_and_keeps_its_declared_name():
    """A `procedure(OBJ)` dummy resolves against the module that declares OBJ.

    The interface name reaches the generated contract as a public symbol, so
    the declaration keeps the spelling the interface was declared with rather
    than the casefolded key used to match it.
    """
    interface_source = """
module pintrf_mod
  implicit none
  private
  public :: OBJ

  abstract interface
    subroutine OBJ(x, f)
      implicit none
      real(8), intent(in) :: x(:)
      real(8), intent(out) :: f
    end subroutine OBJ
  end interface
end module pintrf_mod
"""
    solver_source = """
module solver_mod
  use, non_intrinsic :: pintrf_mod, only : OBJ
  implicit none
contains
  subroutine minimize(calfun, x, f)
    procedure(OBJ) :: calfun
    real(8), intent(in) :: x(:)
    real(8), intent(out) :: f
    call calfun(x, f)
  end subroutine minimize
end module solver_mod
"""
    project = parse_fortran_project({"pintrf.f90": interface_source, "solver.f90": solver_source})
    modules = {module.name: module for module in FortranToIRConverter().visit(project)}

    callback = get_function(modules["solver_mod"], "minimize").arguments[0].semantic_type
    assert callback.name == "OBJ"
    assert callback.storage is not None and callback.storage.kind == "callback"
    assert [argument.name for argument in callback.metadata["callback_arguments"]] == ["x", "f"]
    assert callback.metadata["arguments"][0].shape == ["::"]
    assert callback.metadata["return"].name == "None"


def test_named_but_undeclared_procedure_interface_is_recorded_for_diagnosis():
    """An unresolved `procedure(OBJ)` keeps the name so later stages can report it."""
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

    module = FortranToIRConverter().visit(parse_fortran_source(source).modules[0])

    callback = get_function(module, "minimize").arguments[0].semantic_type
    assert callback.metadata[UNRESOLVED_PROCEDURE_INTERFACE_METADATA] == "OBJ"


CALLBACK_TYPES_SOURCE = """
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
"""


def test_imported_interface_resolves_its_types_in_the_declaring_module():
    """An interface body is written in the scope of the module that declares it.

    The consuming module need not import the types the interface names, so
    those types must keep the declaring module's identity rather than being
    attributed to whichever module imported the interface.
    """
    consumer_source = """
module consumer
  use callback_types, only : move_point
  implicit none
contains
  subroutine run(f)
    procedure(move_point) :: f
  end subroutine run
end module consumer
"""
    project = parse_fortran_project({"callback_types.f90": CALLBACK_TYPES_SOURCE, "consumer.f90": consumer_source})
    modules = {module.name: module for module in FortranToIRConverter().visit(project)}

    callback = get_function(modules["consumer"], "run").arguments[0].semantic_type
    point = callback.metadata["callback_arguments"][0].semantic_type
    assert point.name == "point_t"
    assert point.metadata[EXTERNAL_TYPE_REF_METADATA]["origin_module"] == "callback_types"


def test_procedure_local_use_resolves_an_imported_interface():
    """A ``use`` inside one procedure names the interface only in that scope."""
    source = """
module proclocal_mod
  implicit none
contains
  subroutine run_local(callback)
    use callback_types, only : move_point
    implicit none
    procedure(move_point) :: callback
  end subroutine run_local
end module proclocal_mod
"""
    project = parse_fortran_project({"callback_types.f90": CALLBACK_TYPES_SOURCE, "users.f90": source})
    modules = {module.name: module for module in FortranToIRConverter().visit(project)}

    callback = get_function(modules["proclocal_mod"], "run_local").arguments[0].semantic_type
    assert callback.name == "move_point"
    assert callback.storage is not None and callback.storage.kind == "callback"


def test_reexported_interface_resolves_through_every_import_hop():
    """An interface published by a re-exporting module resolves to its declarer."""
    reexport_source = """
module reexport_mod
  use callback_types, only : move_point
  implicit none
  public :: move_point
end module reexport_mod
"""
    chain_source = """
module chain_mod
  use reexport_mod, only : move_point
  implicit none
contains
  subroutine run_chain(callback)
    procedure(move_point) :: callback
  end subroutine run_chain
end module chain_mod
"""
    project = parse_fortran_project(
        {
            "callback_types.f90": CALLBACK_TYPES_SOURCE,
            "reexport.f90": reexport_source,
            "chain.f90": chain_source,
        }
    )
    modules = {module.name: module for module in FortranToIRConverter().visit(project)}

    callback = get_function(modules["chain_mod"], "run_chain").arguments[0].semantic_type
    assert callback.name == "move_point"
    assert callback.storage is not None and callback.storage.kind == "callback"
    point = callback.metadata["callback_arguments"][0].semantic_type
    assert point.metadata[EXTERNAL_TYPE_REF_METADATA]["origin_module"] == "callback_types"


MAKE_POINT_SOURCE = """
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
"""


def test_imported_interface_result_keeps_the_declaring_module():
    """A callback result carries the declaring module's types like a dummy does.

    Ownership was recorded only while iterating dummies, so a function
    interface returning a module-owned type attributed it to the consumer.
    """
    consumer_source = """
module consumer
  use callback_types, only : make_point
  implicit none
contains
  subroutine run(f)
    procedure(make_point) :: f
  end subroutine run
end module consumer
"""
    project = parse_fortran_project({"callback_types.f90": MAKE_POINT_SOURCE, "consumer.f90": consumer_source})
    modules = {module.name: module for module in FortranToIRConverter().visit(project)}

    callback = get_function(modules["consumer"], "run").arguments[0].semantic_type
    result = callback.metadata["return"]
    assert result.name == "point_t"
    assert result.metadata[EXTERNAL_TYPE_REF_METADATA]["origin_module"] == "callback_types"


def test_procedure_local_rename_keeps_both_the_declared_and_local_names():
    """A renamed import binds a new name without changing the declared one.

    The contract must import the declaring name under the local alias, which
    requires keeping the two spellings apart as separate source facts.
    """
    source = """
module ren_types
  implicit none
  abstract interface
    subroutine OBJ(x)
      implicit none
      real(8), intent(in) :: x
    end subroutine OBJ
  end interface
end module ren_types

module ren_consumer
  implicit none
contains
  subroutine run_ren(callback)
    use ren_types, only : LOCAL_OBJ => OBJ
    implicit none
    procedure(LOCAL_OBJ) :: callback
  end subroutine run_ren
end module ren_consumer
"""

    module = FortranToIRConverter().visit(parse_fortran_source(source))[1]

    callback = get_function(module, "run_ren").arguments[0].semantic_type
    assert callback.name == "LOCAL_OBJ"
    assert callback.metadata[PROTOTYPE_REF_METADATA] == {
        "name": "OBJ",
        "local_name": "LOCAL_OBJ",
        "origin_module": "ren_types",
    }


def test_interface_reference_uses_the_declared_spelling():
    """Fortran matches names case-insensitively; Python contracts do not.

    A reference spelled in another case is the same interface, so the contract
    keeps the declared spelling instead of binding a second name.
    """
    source = """
module cas_mod
  implicit none
  abstract interface
    subroutine OBJ(x)
      implicit none
      real(8), intent(in) :: x
    end subroutine OBJ
  end interface
contains
  subroutine run_cas(callback)
    procedure(obj) :: callback
  end subroutine run_cas
end module cas_mod
"""

    module = FortranToIRConverter().visit(parse_fortran_source(source).modules[0])

    assert get_function(module, "run_cas").arguments[0].semantic_type.name == "OBJ"


ACCESSIBILITY_SOURCE = """
module acc_a
  implicit none
  abstract interface
    subroutine OBJ(x)
      implicit none
      real(8), intent(in) :: x
    end subroutine OBJ
  end interface
end module acc_a

module acc_b_public
  use acc_a, only : OBJ
  implicit none
  private
  public :: OBJ
end module acc_b_public

module acc_b_private
  use acc_a, only : OBJ
  implicit none
  private
end module acc_b_private

module acc_ok
  use acc_b_public, only : OBJ
  implicit none
contains
  subroutine run_ok(callback)
    procedure(OBJ) :: callback
  end subroutine run_ok
end module acc_ok

module acc_bad
  use acc_b_private, only : OBJ
  implicit none
contains
  subroutine run_bad(callback)
    procedure(OBJ) :: callback
  end subroutine run_bad
end module acc_bad
"""


def _is_resolved_callback(module, function_name: str) -> bool:
    semantic_type = get_function(module, function_name).arguments[0].semantic_type
    return semantic_type.storage is not None and semantic_type.storage.kind == "callback"


def test_reexported_interface_resolves_only_when_the_module_publishes_it():
    """Following a re-export must respect the module's own accessibility.

    A name a module imports privately is not part of its interface, so reaching
    it through ``use`` must not resolve even though the chain exists.
    """
    modules = {
        module.name: module for module in FortranToIRConverter().visit(parse_fortran_source(ACCESSIBILITY_SOURCE))
    }

    assert _is_resolved_callback(modules["acc_ok"], "run_ok")
    assert not _is_resolved_callback(modules["acc_bad"], "run_bad")


def test_accessibility_is_enforced_at_every_re_export_hop():
    """A private hop anywhere in the chain stops the name from travelling."""
    source = (
        ACCESSIBILITY_SOURCE
        + """
module acc_mid
  use acc_b_public, only : OBJ
  implicit none
  private
end module acc_mid

module acc_far
  use acc_mid, only : OBJ
  implicit none
contains
  subroutine run_far(callback)
    procedure(OBJ) :: callback
  end subroutine run_far
end module acc_far
"""
    )
    modules = {module.name: module for module in FortranToIRConverter().visit(parse_fortran_source(source))}

    assert not _is_resolved_callback(modules["acc_far"], "run_far")
