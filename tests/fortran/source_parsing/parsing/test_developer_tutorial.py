"""Executable developer tutorial for the grammar-style parser internals.

This test is intentionally written as a small walkthrough rather than as a
black-box public API test. It shows the private visitor/scanner sequence that
maintainers should follow when changing `prik/parsers/fortran/parser.py`:

1. preprocess, then scan fully classified file-level source units,
2. inspect the scanner-owned grammar regions and direct children,
3. visit the unit with a scope,
4. inspect a retained child without rescanning its parent's source.
"""

from prik.parsers.fortran.parser import FortranParser, _SourceUnitScanner


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
    scanner = _SourceUnitScanner()

    lines, root_scope, top_units = parser._helper_prepare_source_units(
        source,
        filename="developer_tutorial.f90",
    )
    assert [line[1] for line in lines[:3]] == [1, 2, 3]
    assert [(unit.kind, unit.name, unit.start_line, unit.end_line) for unit in top_units] == [
        ("module", "dims_mod", 1, 10)
    ]

    module_unit = top_units[0]
    module_grammar = scanner.grammar("module")
    assert module_grammar.has_contains_part is True
    assert module_unit.header == module_unit.lines[0]
    assert [line[0].strip() for line in module_unit.specification] == [
        "implicit none",
        "integer, parameter :: n = 8",
    ]
    assert module_unit.contains == []

    module = parser._visit(
        module_unit,
        parent_scope=root_scope,
        filename="developer_tutorial.f90",
    )
    assert module.name == "dims_mod"
    assert module.variables[0].name == "n"
    assert module.variables[0].value == "8"
    assert module.variables[0].symbolic_value == "8"

    child_units = module_unit.children
    assert [(unit.kind, unit.name, unit.start_line, unit.end_line) for unit in child_units] == [
        ("procedure", "total", 5, 9)
    ]
    assert child_units[0].parent_region == "contains"

    procedure_unit = child_units[0]
    assert [line[0].strip() for line in procedure_unit.specification] == [
        "implicit none",
        "real, intent(in) :: values(n)",
        "real :: out",
    ]
    assert procedure_unit.execution == []
    assert procedure_unit.contains == []

    proc = module.procedures[0]
    assert proc.name == "total"
    assert proc.arguments[0].name == "values"
    assert proc.arguments[0].shape == ["n"]
    assert proc.arguments[0].base_type == "real"
    assert proc.result.name == "out"
    assert proc.result.base_type == "real"
