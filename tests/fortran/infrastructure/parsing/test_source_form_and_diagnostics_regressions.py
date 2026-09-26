"""Singular-unit entrypoint diagnostics, unit filenames, and line numbers after compiler preprocessing."""

import pytest

from prik.parsers.fortran import FortranParseError, FortranParser, parse_fortran_file


@pytest.mark.parametrize(
    ("visitor_name", "entity_name"),
    [
        ("parse_module", "module"),
        ("parse_submodule", "submodule"),
        ("parse_interface", "interface"),
        ("parse_derived_type", "derived type"),
        ("parse_program", "program"),
        ("parse_block_data", "block data unit"),
    ],
)
def test_singular_parser_entrypoint_diagnostics_preserve_names_entities_and_filename(visitor_name, entity_name):
    parser = FortranParser()

    with pytest.raises(FortranParseError) as error:
        getattr(parser, visitor_name)("", filename="empty_contract.f90")

    assert error.value.base_message == f"{visitor_name}() expected exactly one {entity_name}, but none were found"
    assert error.value.filename == "empty_contract.f90"
    assert error.value.code == "PARSE_WRONG_ENTRYPOINT"


def test_unit_models_preserve_filename_propagation():
    parsed = parse_fortran_file(
        """
module owner_mod
end module owner_mod
submodule (owner_mod) child_mod
end submodule child_mod
program driver
end program driver
block data init_data
end block data init_data
""",
        filename="unit_models.f90",
    )

    assert parsed.modules[0].filename == "unit_models.f90"
    assert parsed.submodules[0].filename == "unit_models.f90"
    assert parsed.programs[0].filename == "unit_models.f90"
    assert parsed.block_data_units[0].filename == "unit_models.f90"


@pytest.mark.parametrize(
    ("preprocessed", "line_number"),
    [
        pytest.param(
            '# 1 "bad.F90"\n# 1 "<built-in>"\n# 1 "<command-line>"\n# 1 "bad.F90"\n'
            'module bad\n  implicit none\n\n# 1 "consts.h" 1\n  integer :: from_header\n'
            '# 4 "bad.F90" 2\n\n\n\n  x = 3\nend module bad\n',
            7,
            id="main-source-after-include-and-conditional",
        ),
        pytest.param(
            '# 1 "bad.F90"\n# 1 "<built-in>"\n# 1 "<command-line>"\n# 1 "bad.F90"\n'
            'module bad\n  implicit none\n\n# 1 "bad_inc.h" 1\n  x = 3\n# 4 "bad.F90" 2\nend module bad\n',
            3,
            id="included-line-reports-the-include",
        ),
    ],
)
def test_diagnostics_on_compiler_output_report_main_source_lines(preprocessed: str, line_number: int):
    """Compiler line markers renumber diagnostics to the source the user wrote."""
    with pytest.raises(FortranParseError) as error:
        parse_fortran_file(preprocessed, filename="bad.F90")

    assert error.value.code == "PARSE_EXECUTABLE_IN_SPECIFICATION"
    assert error.value.line_number == line_number
