"""Tests split by stable ownership concept from `test_procedures_and_interfaces.py`."""

from tests.fortran._support.parser_procedures import (
    COMPILE_TIME_EXPRESSION_SOURCE,
    parse_fortran_file,
)


def test_parameterized_derived_type_declarations_preserve_and_resolve_arguments():
    parsed = parse_fortran_file(COMPILE_TIME_EXPRESSION_SOURCE)
    module = parsed.modules[0]
    variables = {var.name: var for var in module.variables}
    buffer_type = next(dtype for dtype in module.derived_types if dtype.name == "buffer_type")
    fields = {field.name: field for field in buffer_type.fields}

    assert variables["compile_time_buffer"].base_type == "derived"
    assert variables["compile_time_buffer"].kind == "buffer_type(real64, 4)"
    assert fields["values"].kind == "k"
    assert fields["values"].shape == ["n"]
