"""Tests split by stable ownership concept from `test_source_form_and_diagnostics_regressions.py`."""

from prik import parse_fortran_file
from prik.parsers.fortran.models import (
    FortranArgument,
    FortranProcedureSignature,
)
from prik.parsers.fortran.parser import (
    FortranParser,
    _ParserScope,
)
from tests.fortran._support.parser_regressions import _unit


def test_function_result_assignment_name_with_intrinsic_prefix_starts_execution_part():
    parsed = parse_fortran_file(
        """
        real function real_c4(z)
        complex z
        real_c4 = real(z)
        return
        end
        """
    )

    proc = parsed.procedures[0]
    assert proc.name == "real_c4"
    assert proc.result is not None
    assert proc.result.base_type == "real"


def test_procedure_bind_c_name_and_value_argument_are_preserved():
    parsed = parse_fortran_file(
        """
module c_api
  use iso_c_binding
contains
  integer(c_int) function renamed(n) bind(C, name="prik_renamed") result(res)
    integer(c_int), value, intent(in) :: n
    res = n
  end function renamed
end module c_api
"""
    )

    proc = parsed.modules[0].procedures[0]
    assert proc.attributes == ["bind(c)"]
    assert proc.bind_name == "prik_renamed"
    assert proc.arguments[0].pass_by_value is True


def test_nonexecution_child_units_keep_specification_and_contains_children_only():
    parser = FortranParser()
    unit = _unit(
        "procedure",
        "work",
        "subroutine work()",
        "type :: local_state",
        "end type local_state",
        "call setup()",
        "interface",
        "  subroutine hidden()",
        "  end subroutine hidden",
        "end interface",
        "contains",
        "subroutine inner()",
        "end subroutine inner",
        "end subroutine work",
    )

    children = parser._helper_nonexecution_child_units(
        unit,
        parent_scope=_ParserScope(kind="procedure", name="work"),
        filename="children.f90",
    )

    assert [(child.kind, child.name, child.start_line, child.end_line) for child in children] == [
        ("derived_type", "local_state", 2, 3),
        ("procedure", "inner", 10, 11),
    ]


def test_finalize_proc_resolves_signature_arguments_imports_and_uses_without_exposing_resolved_params():
    parser = FortranParser()
    signature = FortranProcedureSignature(
        "scale",
        "subroutine",
        arguments=[
            FortranArgument("count", base_type="integer"),
            FortranArgument("values", base_type="real", kind="rk", shape=["count"]),
        ],
    )

    state = parser._new_procedure_scope_state(
        signature,
        symbols={argument.name.lower(): argument for argument in signature.arguments},
    )
    state.uses = {"precision_mod": []}
    state.local_params = {"rk": "8", "count": "4"}
    state.imports = {"state_t", "callback"}
    state.filename = "finalize_contract.f90"

    finalized = parser._finalize_proc(state)

    assert finalized is not signature
    assert [(argument.name, argument.base_type, argument.kind, argument.shape) for argument in finalized.arguments] == [
        ("count", "integer", "", []),
        ("values", "real", "8", ["4"]),
    ]
    assert finalized.attributes == ["import(callback)", "import(state_t)"]
    assert finalized.uses == {"precision_mod": []}
    assert finalized.variables == {}
