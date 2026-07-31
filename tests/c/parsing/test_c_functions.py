"""C function prototype and definition parser tests."""

import pytest


def test_named_function_exposes_result_type_named_parameters_and_derived_type():
    from x2py.parsers.c import CDouble, CFunctionType, CTypedef, parse_c_file

    parsed = parse_c_file(
        "double dot(size_t n, const double *x, const double *y);\n",
        filename="functions.h",
    )

    function = parsed.functions[0]
    assert function.name == "dot"
    assert isinstance(function.result_type, CDouble)
    assert [parameter.name for parameter in function.parameters] == ["n", "x", "y"]
    assert isinstance(function.parameters[0].type, CTypedef)
    assert isinstance(function.type, CFunctionType)
    assert function.type.parameter_types == [parameter.type for parameter in function.parameters]


def test_function_definitions_skip_bodies_but_preserve_start_and_end_locations():
    from x2py.parsers.c import parse_c_file

    parsed = parse_c_file(
        """
int add(int a, int b)
{
    return a + b;
}
""",
        filename="definitions.c",
    )

    function = parsed.functions[0]
    assert function.name == "add"
    assert function.start is not None
    assert function.end is not None
    assert function.start.line == 2
    assert function.end.line == 5


def test_void_parameter_list_and_empty_parameter_list_are_distinguished():
    from x2py.parsers.c import parse_c_file

    parsed = parse_c_file("int explicit_void(void);\nint unspecified();\n", filename="void_params.h")

    functions = {function.name: function for function in parsed.functions}
    assert functions["explicit_void"].parameters == []
    assert functions["explicit_void"].prototype_style == "prototype"
    assert functions["unspecified"].prototype_style == "unspecified"


def test_variadic_functions_are_parsed_as_source_facts():
    from x2py.parsers.c import parse_c_file

    parsed = parse_c_file("int log_msg(const char *fmt, ...);\n", filename="variadic.h")

    assert parsed.functions[0].is_variadic is True
    assert parsed.functions[0].type.is_variadic is True


def test_old_style_knr_function_definition_raises_unsupported_diagnostic():
    from x2py.parsers.c import CParseError, parse_c_file

    source = """
int add(a, b)
int a;
int b;
{
    return a + b;
}
"""

    with pytest.raises(CParseError, match="K&R") as exc_info:
        parse_c_file(source, filename="knr.c")

    error = exc_info.value
    assert error.code == "CPARSE_UNSUPPORTED_KNR_DEFINITION"
    assert error.filename == "knr.c"
    assert error.line_number == 2
    assert error.column == 5
    assert error.source_line == "int add(a, b)"


def test_old_style_knr_detection_uses_linemarkers_and_normalized_headers():
    from x2py.parsers.c import CParseError, parse_c_file

    source = """# 40 "generated_api.c"
__extension__ int exported(a)
int a;
{
    return a;
}
"""

    with pytest.raises(CParseError) as exc_info:
        parse_c_file(source, filename="generated.i", preprocessing="preprocessed")

    error = exc_info.value
    assert error.code == "CPARSE_UNSUPPORTED_KNR_DEFINITION"
    assert error.filename == "generated_api.c"
    assert error.line_number == 40
    assert error.column == 19
    assert error.source_line == "__extension__ int exported(a)"


def test_modern_prototype_before_old_style_definition_does_not_stop_knr_detection():
    from x2py.parsers.c import CParseError, CParser, parse_c_file

    source = """
int modern(int value)
{
    return value;
}
int legacy(a)
int a;
{
    return a;
}
"""

    with pytest.raises(CParseError) as exc_info:
        parse_c_file(source, filename="mixed_knr.c")

    error = exc_info.value
    assert error.code == "CPARSE_UNSUPPORTED_KNR_DEFINITION"
    assert error.filename == "mixed_knr.c"
    assert error.line_number == 6
    assert error.column == 5
    assert error.source_line == "int legacy(a)"

    with pytest.raises(CParseError):
        CParser()._raise_for_unsupported_old_style_definitions(
            source,
            "mixed_knr.c",
            use_linemarkers=False,
            normalize_compiler_extensions=False,
        )


def test_old_style_knr_scan_skips_directives_and_keeps_scanning():
    from x2py.parsers.c import CParseError, CParser

    parser = CParser()
    parser._raise_for_unsupported_old_style_definitions(
        "#if defined(FEATURE)\nint value;\n",
        "feature_guard.c",
        use_linemarkers=False,
        normalize_compiler_extensions=False,
    )

    with pytest.raises(CParseError):
        parser._raise_for_unsupported_old_style_definitions(
            "(not_a_declaration)\nint legacy(a)\nint a;\n",
            "scan_through.c",
            use_linemarkers=False,
            normalize_compiler_extensions=False,
        )


def test_find_parameter_list_returns_outer_function_signature_bounds():
    from x2py.parsers.c import CParser

    parser = CParser()
    text = "int run(int (*callback)(char ch), const char *label)   "

    assert parser._find_parameter_list(text) == (text.index("("), text.rstrip().rindex(")"))
    assert parser._find_parameter_list("int value") is None


def test_control_statement_parameter_lists_inside_function_bodies_are_not_knr_definitions():
    from x2py.parsers.c import parse_c_file

    parsed = parse_c_file(
        """
int run(int value)
{
    if (value)
    {
        return value;
    }
    while (value)
    {
        value--;
    }
loop: for (value)
    {
        value--;
    }
branch: switch (value)
    {
    default:
        return value;
    }
    return 0;
}
""",
        filename="body_control.c",
    )

    assert [function.name for function in parsed.functions] == ["run"]


@pytest.mark.parametrize(
    "source",
    [
        "def solve():\n    return 0\n",
        "lambda x: x\n",
        "int add(int a, int b);\ninteger :: state;\n",
        "int add(int a, int b);\ntype(c_ptr) :: handle;\n",
    ],
)
def test_c_parser_rejects_non_c_top_level_syntax(source):
    from x2py.parsers.c import CParseError, parse_c_file

    with pytest.raises(CParseError, match="Invalid C syntax") as exc_info:
        parse_c_file(source, filename="mixed.h")

    assert exc_info.value.code == "CPARSE_INVALID_SYNTAX"


def test_c_parser_invalid_syntax_error_maps_preprocessed_source_location():
    from x2py.parsers.c import CParseError, parse_c_file

    with pytest.raises(CParseError) as exc_info:
        parse_c_file(
            '# 80 "generated.input"\nvalue_type :: state;\n',
            filename="translation.i",
            preprocessing="preprocessed",
        )

    assert exc_info.value.code == "CPARSE_INVALID_SYNTAX"
    assert exc_info.value.filename == "generated.input"
    assert exc_info.value.line_number == 80


def test_c_parser_skips_non_c_tokens_inside_function_body():
    from x2py.parsers.c import parse_c_file

    parsed = parse_c_file(
        """
int run(void)
{
    value_type :: state;
    return 0;
}
""",
        filename="mixed_body.c",
    )

    assert [function.name for function in parsed.functions] == ["run"]


def test_c_parser_does_not_classify_valid_c_from_typedef_identifier_spelling():
    from x2py.parsers.c import CTypedef, parse_c_file

    parsed = parse_c_file("subroutine solve(void);\n", filename="identifier_spelling.h")

    assert [function.name for function in parsed.functions] == ["solve"]
    assert isinstance(parsed.functions[0].result_type, CTypedef)
    assert parsed.functions[0].result_type.name == "subroutine"


@pytest.mark.parametrize("source", ["@@@\n", "int run(void);\n@@@;\n"])
def test_c_parser_rejects_invalid_top_level_syntax(source):
    from x2py.parsers.c import CParseError, parse_c_file

    with pytest.raises(CParseError, match="Invalid C syntax") as exc_info:
        parse_c_file(source, filename="invalid.c")

    assert exc_info.value.code == "CPARSE_INVALID_SYNTAX"


def test_c_parser_ignores_invalid_syntax_inside_function_body():
    from x2py.parsers.c import parse_c_file

    parsed = parse_c_file(
        """
int run(void)
{
    @@@
    return 0;
}
""",
        filename="invalid_body.c",
    )

    assert [function.name for function in parsed.functions] == ["run"]


@pytest.mark.parametrize(
    "source",
    [
        "struct bad { @@@; };\n",
        "enum bad { OK, @@@ };\n",
        "int run(@@@);\n",
        "int run(int first, ..., int last);\n",
    ],
)
def test_c_parser_rejects_invalid_nested_grammar_units(source):
    from x2py.parsers.c import CParseError, parse_c_file

    with pytest.raises(CParseError, match="Invalid C syntax") as exc_info:
        parse_c_file(source, filename="invalid_nested.h")

    assert exc_info.value.code == "CPARSE_INVALID_SYNTAX"


def test_control_flow_conditions_inside_function_body_do_not_look_like_knr_definitions():
    from x2py.parsers.c import parse_c_file

    parsed = parse_c_file(
        """
int evaluate(int value)
{
    if (value)
        value = 1;
    else if (value)
        value = 2;
    return value;
}
""",
        filename="control_flow.c",
    )

    assert [function.name for function in parsed.functions] == ["evaluate"]


def test_function_pointer_parameter_is_a_callback_candidate_with_nameless_signature():
    from x2py.parsers.c import CFunctionType, CInt, CPointer, parse_c_file

    parsed = parse_c_file(
        "void sort_items(void *items, int (*compare)(const void *, const void *));\n",
        filename="callbacks.h",
    )

    compare = parsed.functions[0].parameters[1]
    assert compare.callback_candidate is True
    assert compare.callback_policy is None
    assert [type(component) for component in compare.type.components] == [CPointer, CFunctionType]
    signature = compare.type.components[1]
    assert isinstance(signature.result_type, CInt)
    assert len(signature.parameter_types) == 2


def test_function_parameter_preserves_declaration_and_adjusts_to_callback_pointer():
    from x2py.parsers.c import CComposedType, CFunctionType, CPointer, parse_c_file

    parsed = parse_c_file("void apply(int callback(int));\n", filename="adjusted_callback.h")

    callback = parsed.functions[0].parameters[0]
    assert isinstance(callback.declared_type, CFunctionType)
    assert isinstance(callback.type, CComposedType)
    assert [type(component) for component in callback.type.components] == [CPointer, CFunctionType]
    assert callback.type.components[1] is callback.declared_type
    assert callback.callback_candidate is True
    assert parsed.functions[0].type.parameter_types[0] is callback.type


def test_project_resolves_callback_typedef_parameter_to_typedef_signature():
    from x2py.parsers.c import CFunctionType, CTypedef, parse_c_project

    project = parse_c_project(
        {
            "callback_typedef.h": """
typedef int (*compare_fn)(const void *a, const void *b);
void sort_items(void *items, compare_fn compare);
"""
        }
    )

    referenced = project.functions["sort_items"].parameters[1].type
    assert isinstance(referenced, CTypedef)
    assert isinstance(referenced.type.components[1], CFunctionType)


def test_function_returning_pointer_to_const_struct_is_preserved():
    from x2py.parsers.c import CComposedType, CConst, CPointer, CStruct, parse_c_file

    parsed = parse_c_file(
        "struct state;\nconst struct state *current_state(void);\n",
        filename="return_pointer.h",
    )

    result = parsed.functions[0].result_type
    assert isinstance(result, CComposedType)
    assert isinstance(result.components[0], CPointer)
    assert isinstance(result.components[1], CStruct)
    assert result.components[1].qualifiers == [CConst()]


def test_matching_prototype_and_definition_merge_and_prefer_definition():
    from x2py.parsers.c import parse_c_file

    parsed = parse_c_file(
        """
int solve(int value);
int solve(int value)
{
    return value;
}
""",
        filename="redeclarations.c",
    )

    assert [function.name for function in parsed.functions] == ["solve"]
    function = parsed.functions[0]
    assert function.is_definition is True
    assert function.source_location.line == 3
    assert [location.line for location in function.declaration_locations] == [2]
    assert parsed.diagnostics == []


def test_inline_function_body_in_header_is_recorded_as_definition():
    from x2py.parsers.c import parse_c_file

    parsed = parse_c_file(
        "static inline int add_one(int value) { return value + 1; }\n",
        filename="inline_api.h",
    )

    function = parsed.functions[0]
    assert function.name == "add_one"
    assert function.storage == ["static"]
    assert function.specifiers == ["inline"]
    assert function.is_definition is True
    assert function.start.line == 1
    assert function.end.line == 1


def test_function_declaration_attributes_are_tolerated_when_type_shape_is_unchanged():
    from x2py.parsers.c import parse_c_file

    parsed = parse_c_file(
        'int exported(void) __attribute__((visibility("default")));\nint deprecated(void) [[deprecated]];\n',
        filename="function_attributes.h",
        preprocessing="compiler",
    )

    assert [function.name for function in parsed.functions] == ["exported", "deprecated"]
    assert parsed.diagnostics == []


def test_unsupported_function_declarator_is_reported_and_later_declarations_continue():
    from x2py.parsers.c import parse_c_file

    parsed = parse_c_file(
        "int broken @@ { return 0; }\nint kept;\n",
        filename="bad_function_declarator.c",
    )

    assert parsed.functions == []
    assert [variable.name for variable in parsed.variables] == ["kept"]
    assert len(parsed.diagnostics) == 1
    diagnostic = parsed.diagnostics[0]
    assert diagnostic.code == "C_UNSUPPORTED_DECLARATOR"
    assert diagnostic.unit_kind == "declarator"
    assert diagnostic.message == "Unsupported declarator syntax after parsed type layers: '@@'."
    assert diagnostic.location is not None
    assert diagnostic.location.line == 1
    assert diagnostic.location.column == 1


def test_conflicting_function_prototypes_report_diagnostic():
    from x2py.parsers.c import parse_c_file

    parsed = parse_c_file(
        "int work(int value);\ndouble work(double value);\n",
        filename="conflicting_functions.h",
    )

    assert [function.name for function in parsed.functions] == ["work"]
    assert any(diag.code == "C_CONFLICTING_FUNCTION_DECLARATION" for diag in parsed.diagnostics)


def test_function_conflicts_consider_parameters_and_variadic_marker():
    from x2py.parsers.c import parse_c_file

    parsed = parse_c_file(
        """
int same_return(int value);
int same_return(double value);
int log_msg(const char *fmt);
int log_msg(const char *fmt, ...);
""",
        filename="function_shape_conflicts.h",
    )

    conflicts = [
        diagnostic.unit_name
        for diagnostic in parsed.diagnostics
        if diagnostic.code == "C_CONFLICTING_FUNCTION_DECLARATION"
    ]
    assert conflicts == ["same_return", "log_msg"]


def test_duplicate_function_definitions_report_diagnostic():
    from x2py.parsers.c import parse_c_file

    parsed = parse_c_file(
        """
int value(void) { return 1; }
int value(void) { return 2; }
""",
        filename="duplicate_functions.c",
    )

    assert [function.name for function in parsed.functions] == ["value"]
    assert parsed.functions[0].is_definition is True
    assert any(diag.code == "C_DUPLICATE_FUNCTION_DEFINITION" for diag in parsed.diagnostics)
