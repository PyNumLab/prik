"""Executable walkthroughs for maintainers reading `c_parser.parser`.

These tests intentionally expose the internal declaration gateway named in the
module-level parsing sketch. Behavioral coverage remains in the feature test
modules; this file keeps the parser's control flow easy to inspect.
"""


def test_tutorial_shared_declarator_backend_builds_layered_variable_type():
    from x2py.parsers.c import CArray, CConst, CInt, CParser, CPointer

    parser = CParser()
    specifiers, declarator = parser._split_declaration_specifiers("const int *values[4]")
    name, type_, storage, function_specifiers, direct_function = parser._build_declared_type(
        specifiers,
        declarator,
    )

    assert (specifiers, declarator) == ("const int", "*values[4]")
    assert name == "values"
    assert storage == []
    assert function_specifiers == []
    assert direct_function is None
    assert [type(component) for component in type_.components] == [CArray, CPointer, CInt]
    assert type_.components[-1].qualifiers == [CConst()]


def test_tutorial_parse_file_dispatches_declaration_roles_through_one_model():
    from x2py.parsers.c import CParser, CStruct

    parsed = CParser().parse_file(
        """
typedef int api_status;
struct request { int id; };
api_status submit(struct request *request);
extern int request_count;
""",
        filename="tutorial.h",
    )

    assert [typedef.name for typedef in parsed.typedefs] == ["api_status"]
    assert [struct.name for struct in parsed.structs] == ["request"]
    assert isinstance(parsed.functions[0].parameters[0].type.components[-1], CStruct)
    assert [function.name for function in parsed.functions] == ["submit"]
    assert [variable.name for variable in parsed.variables] == ["request_count"]
    assert parsed.diagnostics == []


def test_tutorial_preprocessed_input_reuses_parsing_and_remaps_locations():
    from x2py.parsers.c import CParser

    parsed = CParser().parse_file(
        '# 24 "include/api.h"\nint expanded_api(void);\n',
        filename="generated.i",
    )

    function = parsed.functions[0]
    assert parsed.preprocessing == "preprocessed"
    assert parsed.preprocessed_source_path == "generated.i"
    assert parsed.original_source_paths == ["include/api.h"]
    assert function.name == "expanded_api"
    assert function.origin == "preprocessed"
    assert function.source_location.filename == "include/api.h"
    assert function.source_location.line == 24
