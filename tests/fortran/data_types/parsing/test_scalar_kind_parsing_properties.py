"""Generated Fortran intrinsic-kind parsing contracts."""

from tests.fortran._support.parser_properties import (
    _FORTRAN_SCALAR_TYPES,
    given,
    parse_fortran_file,
    pytest,
    st,
)


@pytest.mark.property
@given(base_type=_FORTRAN_SCALAR_TYPES, kind=st.integers(min_value=1, max_value=32), keyword=st.booleans())
def test_generated_fortran_intrinsic_kinds_are_preserved(base_type, kind, keyword):
    type_spec = f"{base_type}({'kind=' if keyword else ''}{kind})"
    source = f"subroutine generated_kind(value)\n  {type_spec}, intent(in) :: value\nend subroutine generated_kind\n"

    parsed = parse_fortran_file(source, filename="generated_kind.f90")

    assert parsed.diagnostics == []
    assert len(parsed.procedures) == 1
    assert parsed.procedures[0].arguments[0].base_type == base_type
    assert parsed.procedures[0].arguments[0].kind == str(kind)
