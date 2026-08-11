"""Tests split by stable ownership concept from `test_source_form_and_diagnostics_regressions.py`."""

import pytest
from pathlib import Path
from prik import (
    FortranParseError,
    parse_fortran_file,
)
from prik.parsers.fortran.models import (
    FortranArgument,
    FortranDerivedType,
    FortranModule,
    FortranProcedureSignature,
)
from prik.parsers.fortran.parser import (
    FortranParser,
    _ParserScope,
    _SourceUnitScanner,
)
from tests.fortran._support.parser_regressions import (
    _lines,
    _unit,
)


def test_source_unit_classification_preserves_child_regions_and_direct_ownership():
    scanner = _SourceUnitScanner()
    unit = scanner.scan_file_units(
        _lines(
            "module owner",
            "integer :: value",
            "interface callbacks",
            "  subroutine callback()",
            "  end subroutine callback",
            "end interface callbacks",
            "interface generic_work",
            "  module procedure work",
            "end interface generic_work",
            "contains",
            "# generated marker",
            "subroutine work()",
            "end subroutine work",
            "end module owner",
        ),
        filename="regions.f90",
    )[0]

    assert unit.header == unit.lines[0]
    assert unit.footer == unit.lines[-1]
    assert [line for line, _lineno, _source in unit.specification] == ["integer :: value"]
    assert unit.execution == []
    assert [line.strip() for line, _lineno, _source in unit.contains] == ["# generated marker"]
    assert [(child.kind, child.name, child.parent_region) for child in unit.children] == [
        ("interface", "callbacks", "specification"),
        ("interface", "generic_work", "specification"),
        ("procedure", "work", "contains"),
    ]
    assert [(child.kind, child.name, child.parent_region) for child in unit.children[0].children] == [
        ("procedure", "callback", "specification")
    ]
    assert [line.strip() for line, _lineno, _source in unit.children[1].specification] == ["module procedure work"]


def test_procedure_classification_keeps_local_interfaces_and_omits_internal_procedures():
    scanner = _SourceUnitScanner()
    unit = scanner.scan_file_units(
        _lines(
            "subroutine work(callback)",
            "integer :: value",
            "interface",
            "  subroutine callback()",
            "  end subroutine callback",
            "end interface",
            "value = 1",
            "contains",
            "subroutine inner()",
            "end subroutine inner",
            "end subroutine work",
        ),
        filename="regions.f90",
    )[0]

    assert [line for line, _lineno, _source in unit.specification] == ["integer :: value"]
    assert [line for line, _lineno, _source in unit.execution] == ["value = 1"]
    assert unit.contains == []
    assert [(child.kind, child.name, child.parent_region) for child in unit.children] == [
        ("interface", None, "specification")
    ]

    assert scanner.has_preferred_unit_end_ahead(unit.lines, 0, "procedure", "work") is True
    assert scanner.has_preferred_unit_end_ahead(unit.lines, 0, "procedure", "missing") is False
    assert scanner.has_preferred_unit_end_ahead(unit.lines[:-1], 0, "procedure", "work") is False
    immediate_type = _lines("type :: immediate", "end type immediate")
    assert scanner.has_preferred_unit_end_ahead(immediate_type, 0, "derived_type", "immediate") is True
    assert scanner.has_unit_end_ahead(immediate_type, 0, "derived_type") is True
    assert scanner.has_unit_end_ahead(unit.lines, 0, "procedure") is True


def test_unit_end_search_tracks_nested_specification_and_contains_units():
    scanner = _SourceUnitScanner()
    lines = _lines(
        "subroutine work()",
        "type :: local_state",
        "end type local_state",
        "contains",
        "subroutine inner()",
        "end subroutine inner",
        "end subroutine work",
    )

    assert scanner.find_unit_end(lines, 0, "procedure", filename="regions.f90") == 6
    assert scanner.has_unit_end_ahead(lines, 1, "derived_type") is True
    assert scanner.has_unit_end_ahead(lines, 4, "procedure") is True
    assert scanner.has_unit_end_ahead(lines[:-1], 0, "procedure") is True


def test_source_preparation_rejects_raw_cpp_and_preserves_root_units_and_source_form(tmp_path: Path):
    parser = FortranParser()
    lines, root_scope, units = parser._helper_prepare_source_units(
        """
module owner_mod
end module owner_mod
subroutine global_step()
end subroutine global_step
""",
        filename="prepare_contract.f90",
    )

    assert root_scope == _ParserScope(kind="file", name=None)
    assert [(unit.kind, unit.name, unit.start_line, unit.end_line) for unit in units] == [
        ("module", "owner_mod", 2, 3),
        ("procedure", "global_step", 4, 5),
    ]
    assert [line for line, _lineno, _source in lines if line.strip()] == [
        "module owner_mod",
        "end module owner_mod",
        "subroutine global_step()",
        "end subroutine global_step",
    ]
    assert parser._source_form("fixed.f") == "f77"
    assert parser._source_form("modern.f90") == "modern"
    assert parser._source_form(None) == "unknown"

    source_path = tmp_path / "path_input.f90"
    source_path.write_text("module from_path\nend module from_path\n", encoding="utf-8")
    assert parser._looks_like_existing_source_path(source_path) is True
    assert parser._looks_like_existing_source_path("module inline\nend module inline\n") is False
    assert parser._looks_like_existing_source_path(object()) is False

    with pytest.raises(FortranParseError) as error:
        parser._helper_prepare_source_units("#define VALUE 1\nmodule bad\nend module bad\n", filename="raw_cpp.f90")

    assert error.value.base_message == "Fortran CPP directives require compiler preprocessing before parsing."
    assert error.value.filename == "raw_cpp.f90"
    assert error.value.line_number == 1
    assert error.value.source_line == "#define VALUE 1"
    assert error.value.code == "PARSE_PREPROCESSING_REQUIRED"


def test_file_unit_scanning_skips_preprocessed_linemarkers_and_blank_unit_starts():
    scanner = _SourceUnitScanner()
    lines = _lines(
        '# 4 "generated.f90"',
        "",
        "module owner",
        "end module owner",
    )

    units = scanner.scan_file_units(
        lines,
        filename="generated.f90",
    )

    assert [(unit.kind, unit.name) for unit in units] == [("module", "owner")]
    assert scanner.classify_unit_start("   ") is None


def test_unit_end_and_header_validation_preserve_public_diagnostics():
    parser = FortranParser()
    scanner = _SourceUnitScanner()

    assert scanner.parse_unit_end("module", "end module owner_mod") == (True, "owner_mod")
    assert scanner.parse_unit_end("block_data", "end") == (True, None)
    assert scanner.parse_unit_end("procedure", "end function value") == (True, "value")
    assert scanner.unit_end_matches("enum", "end enum") is True
    assert scanner.unit_label("block_data") == "block data"
    assert parser._parse_submodule_header("submodule (ancestor_mod:parent_mod) child_mod", "headers.f90").parent == (
        "parent_mod"
    )
    assert parser._split_submodule_parent("ancestor_mod:parent_mod") == ("parent_mod", "ancestor_mod")
    assert parser._split_submodule_parent("parent_mod") == ("parent_mod", None)
    assert scanner.parse_interface_header("abstract interface") == (True, None)
    assert scanner.parse_interface_header("interface callbacks") == (True, "callbacks")

    with pytest.raises(FortranParseError) as module_error:
        parser._parse_module_header(
            "module bad-name",
            filename="headers.f90",
            lineno=3,
            source_line="module bad-name",
        )
    assert module_error.value.base_message == "Unsupported or malformed module header: module bad-name"
    assert module_error.value.filename == "headers.f90"
    assert module_error.value.line_number == 3
    assert module_error.value.source_line == "module bad-name"
    assert module_error.value.code == "PARSE_MALFORMED_HEADER"

    with pytest.raises(FortranParseError) as procedure_error:
        parser._helper_validate_possible_unit_header(
            "module procedure bad(x)",
            filename="headers.f90",
            lineno=4,
            source_line="module procedure bad(x)",
        )
    assert (
        procedure_error.value.base_message
        == "Unsupported or malformed module procedure header: module procedure bad(x)"
    )
    assert procedure_error.value.filename == "headers.f90"
    assert procedure_error.value.line_number == 4
    assert procedure_error.value.source_line == "module procedure bad(x)"
    assert procedure_error.value.code == "PARSE_MALFORMED_HEADER"


def test_classified_unit_regions_skip_nested_units_and_preserve_executable_boundary():
    unit = _unit(
        "procedure",
        "work",
        "subroutine work()",
        "integer :: counter",
        "",
        "interface",
        "  subroutine callback()",
        "  end subroutine callback",
        "end interface",
        "counter = counter + 1",
        "contains",
        "subroutine inner()",
        "end subroutine inner",
        "end subroutine work",
    )

    assert [line for line, _lineno, _source in unit.specification] == ["integer :: counter"]
    assert [line for line, _lineno, _source in unit.execution] == ["counter = counter + 1"]
    assert unit.contains == []
    assert unit.header == unit.lines[0]
    assert unit.footer == unit.lines[-1]


def test_sibling_unit_validation_ignores_unnamed_units_and_preserves_duplicate_diagnostics():
    parser = FortranParser()
    parser._helper_validate_sibling_units(
        [
            _unit("enum", None, "enum, bind(c)", "end enum"),
            _unit("enum", None, "enum, bind(c)", "end enum"),
        ],
        parent_scope=_ParserScope(kind="module", name="owner_mod"),
        filename="siblings.f90",
    )

    with pytest.raises(FortranParseError) as duplicate_module:
        parser._helper_validate_sibling_units(
            [
                _unit("module", "owner_mod", "module owner_mod", "end module owner_mod"),
                _unit("module", "Owner_Mod", "module Owner_Mod", "end module Owner_Mod"),
            ],
            parent_scope=_ParserScope(kind="file", name=None),
            filename="siblings.f90",
        )

    assert duplicate_module.value.base_message == "Duplicate module name 'Owner_Mod' in file scope."
    assert duplicate_module.value.filename == "siblings.f90"
    assert duplicate_module.value.line_number == 1
    assert duplicate_module.value.source_line == "module Owner_Mod"
    assert duplicate_module.value.code == "PARSE_DUPLICATE_UNIT"

    with pytest.raises(FortranParseError) as duplicate_procedure:
        parser._helper_validate_sibling_units(
            [
                _unit("procedure", "step", "subroutine step()", "end subroutine step"),
                _unit("procedure", "STEP", "subroutine STEP()", "end subroutine STEP"),
            ],
            parent_scope=_ParserScope(kind="module", name="owner_mod"),
            filename="siblings.f90",
        )

    assert duplicate_procedure.value.base_message == "Duplicate procedure name 'STEP' in module 'owner_mod'."
    assert duplicate_procedure.value.filename == "siblings.f90"
    assert duplicate_procedure.value.line_number == 1
    assert duplicate_procedure.value.source_line == "subroutine STEP()"
    assert duplicate_procedure.value.code == "PARSE_DUPLICATE_PROCEDURE"


def test_finalize_proc_duplicate_argument_diagnostic_preserves_header_metadata():
    parser = FortranParser()
    signature = FortranProcedureSignature(
        "step",
        "subroutine",
        arguments=[FortranArgument("value"), FortranArgument("VALUE")],
    )

    state = parser._new_procedure_scope_state(signature, symbols={})
    state.filename = "finalize_contract.f90"
    state.header_lineno = 12
    state.header_source_line = "subroutine step(value, VALUE)"

    with pytest.raises(FortranParseError) as error:
        parser._finalize_proc(state)

    assert error.value.base_message == "Duplicate argument name 'VALUE' in procedure 'step'."
    assert error.value.filename == "finalize_contract.f90"
    assert error.value.line_number == 12
    assert error.value.source_line == "subroutine step(value, VALUE)"
    assert error.value.code == "PARSE_DUPLICATE_ARGUMENT"


def test_declaration_push_preserves_type_field_metadata_and_duplicate_field_diagnostic():
    parser = FortranParser()
    dtype = FortranDerivedType("state_t")
    scope = _ParserScope(kind="derived_type", name=dtype.name, model=dtype)
    meta = parser._new_decl_meta("integer", "i4")
    meta.update({"pointer": True, "shape": [":"], "rank": 1})

    parser._helper_push_declaration_to_scope(
        scope,
        meta=meta,
        right="ids, IDs",
        role="type_field",
        filename="declarations.f90",
        lineno=7,
        source_line="integer(kind=i4), pointer, dimension(:) :: ids, IDs",
    )

    assert [(field.name, field.base_type, field.kind, field.pointer, field.shape) for field in dtype.fields] == [
        ("ids", "integer", "i4", True, [":"]),
        ("IDs", "integer", "i4", True, [":"]),
    ]
    with pytest.raises(FortranParseError) as error:
        parser._validate_derived_type_fields(dtype, filename="declarations.f90")

    assert error.value.base_message == "Duplicate field 'IDs' in derived type 'state_t'."
    assert error.value.filename == "declarations.f90"
    assert error.value.code == "PARSE_DUPLICATE_FIELD"


def test_unknown_procedure_declaration_diagnostic_preserves_public_metadata():
    parser = FortranParser()
    state = parser._new_procedure_scope_state(
        FortranProcedureSignature(name="work", kind="subroutine"),
        symbols={},
    )

    with pytest.raises(FortranParseError) as error:
        parser._handle_unknown_proc_declaration(
            "@@@",
            state,
            filename="procedure_contract.f90",
            lineno=8,
            source_line="@@@",
        )

    assert error.value.base_message == "Invalid Fortran syntax in procedure 'work' specification part: @@@"
    assert error.value.filename == "procedure_contract.f90"
    assert error.value.line_number == 8
    assert error.value.source_line == "@@@"
    assert error.value.code == "PARSE_INVALID_SYNTAX"


def test_contains_line_validation_accepts_spec_alternatives_without_mutating_scope_and_reports_invalid_lines():
    parser = FortranParser()
    module = FortranModule("owner_mod")
    scope = _ParserScope(kind="module", name=module.name, model=module, module_owner=module.name)

    parser._helper_validate_contains_lines(
        scope,
        _lines("", "# marker", "include 'shape.inc'", "integer :: macro_decl"),
        filename="contains_contract.f90",
    )

    assert module.variables == []

    with pytest.raises(FortranParseError) as error:
        parser._helper_validate_contains_lines(
            scope,
            _lines("@@@"),
            filename="contains_contract.f90",
        )

    assert error.value.base_message == "Invalid Fortran syntax in module 'owner_mod' contains part: @@@"
    assert error.value.filename == "contains_contract.f90"
    assert error.value.line_number == 1
    assert error.value.source_line == "@@@"
    assert error.value.code == "PARSE_INVALID_SYNTAX"


def test_interface_validation_keeps_scanning_after_valid_lines():
    parser = FortranParser()
    scope = _ParserScope(kind="interface", name="Callbacks")

    with pytest.raises(FortranParseError) as interface_error:
        parser._helper_validate_interface_lines(
            scope,
            _lines("", "# marker", "MODULE PROCEDURE :: First, Second", "PROCEDURE(Callback) :: Handler", "@@@"),
            filename="interface_contract.f90",
        )
    assert interface_error.value.base_message == "Invalid Fortran syntax in interface 'Callbacks': @@@"
    assert interface_error.value.filename == "interface_contract.f90"
    assert interface_error.value.line_number == 5
    assert interface_error.value.source_line == "@@@"
    assert interface_error.value.code == "PARSE_INVALID_SYNTAX"


@pytest.mark.parametrize(
    ("use_enum_validator", "unit", "expected_message"),
    [
        (
            False,
            _unit(
                "interface", "callbacks", "interface callbacks", "type :: nested", "end type nested", "end interface"
            ),
            "Invalid Fortran syntax in interface 'callbacks': type :: nested",
        ),
        (
            False,
            _unit("derived_type", "outer", "type :: outer", "type :: nested", "end type nested", "end type outer"),
            "Invalid Fortran syntax in derived type 'outer' specification part: type :: nested",
        ),
        (
            False,
            _unit(
                "block_data",
                "init_data",
                "block data init_data",
                "type :: nested",
                "end type nested",
                "end block data init_data",
            ),
            "Invalid Fortran syntax in block data 'init_data' specification part: type :: nested",
        ),
    ],
)
def test_nested_units_rejected_by_restricted_scopes_preserve_public_metadata(
    use_enum_validator, unit, expected_message
):
    parser = FortranParser()

    with pytest.raises(FortranParseError) as error:
        if use_enum_validator:
            parser._helper_validate_enum_unit(unit, filename="nested_contract.f90")
        else:
            parser._visit(
                unit,
                parent_scope=_ParserScope(kind="file", name=None),
                filename="nested_contract.f90",
            )

    assert error.value.base_message == expected_message
    assert error.value.filename == "nested_contract.f90"
    assert error.value.line_number == 2
    assert error.value.source_line == "type :: nested"
    assert error.value.code == "PARSE_INVALID_SYNTAX"


@pytest.mark.parametrize(
    ("line", "expected_message", "expected_code"),
    [
        (
            "!$omp threadprivate(counter)",
            "Unsupported OpenMP declarative directive in module 'owner_mod': !$omp threadprivate(counter)",
            "PARSE_UNSUPPORTED_OPENMP_DIRECTIVE",
        ),
        (
            "type :: missing_end",
            "Missing end derived type for derived type 'missing_end'.",
            "PARSE_MISSING_DERIVED_TYPE_END",
        ),
        (
            "call work()",
            "Executable statement is not allowed in module specification part 'owner_mod': call work()",
            "PARSE_EXECUTABLE_IN_SPECIFICATION",
        ),
        (
            "@@@",
            "Invalid Fortran syntax in module 'owner_mod' specification part: @@@",
            "PARSE_INVALID_SYNTAX",
        ),
        (
            "weirdtype value",
            "Unknown or unsupported datatype declaration in module 'owner_mod': weirdtype value",
            "PARSE_UNSUPPORTED_DECLARATION",
        ),
    ],
)
def test_module_like_spec_diagnostics_preserve_public_metadata(line, expected_message, expected_code):
    parser = FortranParser()
    module = FortranModule("owner_mod")
    scope = _ParserScope(kind="module", name=module.name, model=module, module_owner=module.name)

    with pytest.raises(FortranParseError) as error:
        parser._parse_module_like_spec_line(
            scope,
            line,
            filename="module_contract.f90",
            lineno=7,
            source_line=line,
        )

    assert error.value.base_message == expected_message
    assert error.value.filename == "module_contract.f90"
    assert error.value.line_number == 7
    assert error.value.source_line == line
    assert error.value.code == expected_code


@pytest.mark.parametrize(
    ("line", "expected_message", "expected_code"),
    [
        (
            "type :: missing_end",
            "Missing end derived type for derived type 'missing_end'.",
            "PARSE_MISSING_DERIVED_TYPE_END",
        ),
        (
            "!$omp threadprivate(counter)",
            "Unsupported OpenMP declarative directive in type 'state_t': !$omp threadprivate(counter)",
            "PARSE_UNSUPPORTED_OPENMP_DIRECTIVE",
        ),
        (
            "@@@",
            "Invalid Fortran syntax in type 'state_t' specification part: @@@",
            "PARSE_INVALID_SYNTAX",
        ),
        (
            "weirdtype value",
            "Unknown or unsupported datatype declaration in type 'state_t': weirdtype value",
            "PARSE_UNSUPPORTED_DECLARATION",
        ),
    ],
)
def test_type_spec_diagnostics_preserve_public_metadata(line, expected_message, expected_code):
    parser = FortranParser()
    dtype = FortranDerivedType("state_t")
    scope = _ParserScope(kind="derived_type", name=dtype.name, model=dtype)

    with pytest.raises(FortranParseError) as error:
        parser._parse_type_spec_line(
            line,
            scope,
            filename="type_contract.f90",
            lineno=7,
            source_line=line,
        )

    assert error.value.base_message == expected_message
    assert error.value.filename == "type_contract.f90"
    assert error.value.line_number == 7
    assert error.value.source_line == line
    assert error.value.code == expected_code


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


@pytest.mark.parametrize(
    ("header_parser", "header_result", "unit_kind", "entity_name"),
    [
        ("_parse_module_header", None, "module", "module"),
        ("_parse_submodule_header", None, "submodule", "submodule"),
        ("_parse_program_header", None, "program", "program"),
        ("_parse_block_data_header", None, "block_data", "block data"),
        ("_init_derived_type", None, "derived_type", "derived-type"),
    ],
)
def test_source_unit_visitor_defensive_diagnostics_preserve_public_metadata(
    monkeypatch,
    header_parser,
    header_result,
    unit_kind,
    entity_name,
):
    parser = FortranParser()
    monkeypatch.setattr(parser, header_parser, lambda *args, **kwargs: header_result)

    with pytest.raises(FortranParseError) as error:
        parser._visit(
            _unit(unit_kind, "broken", "broken header", "broken footer"),
            parent_scope=_ParserScope(kind="file", name=None),
            filename="visitor_contract.f90",
        )

    assert error.value.base_message == f"Expected {entity_name} unit."
    assert error.value.filename == "visitor_contract.f90"
    assert error.value.line_number == 1
    assert error.value.source_line == "broken header"
    assert error.value.code == "PARSE_EXPECTED_UNIT"


def test_interface_unit_defensive_diagnostic_uses_scanner_header_recognition(monkeypatch):
    parser = FortranParser()
    monkeypatch.setattr(parser._source_unit_scanner, "parse_interface_header", lambda _line: (False, None))

    with pytest.raises(FortranParseError) as error:
        parser._visit(
            _unit("interface", "broken", "broken header", "broken footer"),
            parent_scope=_ParserScope(kind="file", name=None),
            filename="visitor_contract.f90",
        )

    assert error.value.base_message == "Expected interface unit."
    assert error.value.filename == "visitor_contract.f90"
    assert error.value.line_number == 1
    assert error.value.source_line == "broken header"
    assert error.value.code == "PARSE_EXPECTED_UNIT"


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
