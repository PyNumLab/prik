"""Executable developer tutorial for the grammar-style parser internals.

This test is intentionally written as a small walkthrough rather than as a
black-box public API test. It shows the private visitor/helper sequence that
maintainers should follow when changing `x2py/parsers/fortran/parser.py`:

1. preprocess and slice file-level source units,
2. split one unit into grammar parts,
3. visit the unit with a scope,
4. recursively slice and inspect its direct children.
"""

from x2py.parsers.fortran.parser import FortranParser


def test_developer_tutorial_recursive_unit_visitors_and_helpers():
    source = "\n".join(
        [
            "module dims_mod",
            "  implicit none",
            "  integer, parameter :: n = 8",
            "contains",
            "  function total(values) result(out)",
            "    implicit none",
            "    real, intent(in) :: values(n)",
            "    real :: out",
            "  end function total",
            "end module dims_mod",
            "",
        ]
    )

    parser = FortranParser()

    lines, root_scope, top_units = parser._helper_prepare_source_units(
        source,
        filename="developer_tutorial.f90",
    )
    assert [line[1] for line in lines[:3]] == [1, 2, 3]
    assert [(unit.kind, unit.name, unit.start_line, unit.end_line) for unit in top_units] == [
        ("module", "dims_mod", 1, 10)
    ]

    module_unit = top_units[0]
    module_grammar = parser._helper_unit_grammar("module")
    module_parts = parser._helper_split_unit_parts(
        module_unit,
        module_grammar,
        filename="developer_tutorial.f90",
    )
    assert module_parts.header == module_unit.lines[0]
    assert [line[0].strip() for line in module_parts.specification] == [
        "implicit none",
        "integer, parameter :: n = 8",
    ]
    assert module_parts.contains == []

    module = parser._visit(
        module_unit,
        parent_scope=root_scope,
        filename="developer_tutorial.f90",
    )
    assert module.name == "dims_mod"
    assert module.variables[0].name == "n"
    assert module.variables[0].value == "8"
    assert module.variables[0].symbolic_value == "8"

    module_scope = parser._helper_scope_for_model("module", module, parent=root_scope)
    child_units = parser._helper_slice_child_units(
        module_unit.lines[1:-1],
        parent_scope=module_scope,
        filename="developer_tutorial.f90",
    )
    assert [(unit.kind, unit.name, unit.start_line, unit.end_line) for unit in child_units] == [
        ("procedure", "total", 5, 9)
    ]

    procedure_unit = child_units[0]
    procedure_parts = parser._helper_split_unit_parts(
        procedure_unit,
        parser._helper_unit_grammar("procedure"),
        filename="developer_tutorial.f90",
    )
    assert [line[0].strip() for line in procedure_parts.specification] == [
        "implicit none",
        "real, intent(in) :: values(n)",
        "real :: out",
    ]
    assert procedure_parts.execution == []
    assert procedure_parts.contains == []

    proc = module.procedures[0]
    assert proc.name == "total"
    assert proc.arguments[0].name == "values"
    assert proc.arguments[0].shape == ["n"]
    assert proc.arguments[0].base_type == "real"
    assert proc.result.name == "out"
    assert proc.result.base_type == "real"
