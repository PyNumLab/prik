"""Tests split by stable ownership concept from `test_properties.py`."""

import pytest
from hypothesis import (
    given,
    strategies as st,
)
from prik import parse_fortran_file
from tests.fortran._support.parser_properties import (
    _FORTRAN_IDENTIFIER_STEMS,
    _FORTRAN_SCALAR_TYPES,
)


@pytest.mark.property
@given(
    module_stem=_FORTRAN_IDENTIFIER_STEMS,
    type_stem=_FORTRAN_IDENTIFIER_STEMS,
    field_types=st.lists(_FORTRAN_SCALAR_TYPES, min_size=1, max_size=5),
)
def test_generated_fortran_derived_types_preserve_fields(module_stem, type_stem, field_types):
    module_name = f"mod_{module_stem}"
    type_name = f"type_{type_stem}"
    fields = [f"field_{index}" for index in range(len(field_types))]
    field_lines = "".join(
        f"    {field_type} :: {field_name}\n" for field_name, field_type in zip(fields, field_types, strict=True)
    )
    source = (
        f"module {module_name}\n  type :: {type_name}\n{field_lines}  end type {type_name}\nend module {module_name}\n"
    )

    parsed = parse_fortran_file(source, filename=f"{module_name}.f90")

    assert parsed.diagnostics == []
    assert len(parsed.modules) == 1
    assert len(parsed.modules[0].derived_types) == 1
    derived_type = parsed.modules[0].derived_types[0]
    assert derived_type.name == type_name
    assert derived_type.module == module_name
    assert [(field.name, field.base_type) for field in derived_type.fields] == list(
        zip(fields, field_types, strict=True)
    )
