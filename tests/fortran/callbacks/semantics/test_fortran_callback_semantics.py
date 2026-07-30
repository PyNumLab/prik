"""Tests split by stable ownership concept from `test_compile_time_values.py`."""

from tests.fortran._support.semantic_conversion import (
    FortranToIRConverter,
    emit_module,
    get_function,
    native_contract_issues,
    parse_fortran_project,
    parse_fortran_source,
    parse_pyi_text,
)


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
    assert "value: Int32" in emitted
    assert "ref: Addr(Float64)" in emitted
    assert "@prototype\ndef string_iface(" in emitted
    assert "read_label: String[8]" in emitted
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
