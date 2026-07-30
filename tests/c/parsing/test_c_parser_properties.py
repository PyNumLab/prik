"""Tests split by stable ownership concept from `test_properties.py`."""

from tests.c._support.parser_properties import (
    CParseError,
    _C_IDENTIFIERS,
    _FUZZ_TEXT,
    c_nested_variable_declarations,
    c_prototypes,
    given,
    json,
    parse_c_file,
    pytest,
    split_top_level_c_source,
    st,
    suppress,
    top_level_split,
)


@pytest.mark.property
@given(c_prototypes())
def test_generated_c_prototypes_are_json_stable(case):
    function_name, parameter_names, source = case

    parsed = parse_c_file(source, filename=f"{function_name}.h")
    reparsed = parse_c_file(source, filename=f"{function_name}.h")

    assert parsed.diagnostics == []
    assert len(parsed.functions) == 1
    assert parsed.functions[0].name == function_name
    assert [param.name for param in parsed.functions[0].parameters] == parameter_names
    assert json.loads(json.dumps(parsed.to_dict(), sort_keys=True)) == reparsed.to_dict()


@pytest.mark.property
@given(c_prototypes(), st.sampled_from([" ", "\t", "\n  "]))
def test_generated_c_prototype_whitespace_preserves_signature(case, whitespace):
    function_name, parameter_names, source = case
    variant = source.replace("(", f"{whitespace}(").replace(", ", f",{whitespace}").replace(");", f"){whitespace};")

    parsed = parse_c_file(variant, filename=f"{function_name}.h")

    assert parsed.diagnostics == []
    assert len(parsed.functions) == 1
    assert parsed.functions[0].name == function_name
    assert [param.name for param in parsed.functions[0].parameters] == parameter_names


@pytest.mark.property
@given(c_nested_variable_declarations())
def test_generated_c_nested_declarators_preserve_component_order(case):
    source, expected_components = case

    parsed = parse_c_file(source, filename="nested.h")
    reparsed = parse_c_file(source, filename="nested.h")

    assert parsed.diagnostics == []
    assert len(parsed.variables) == 1
    variable = parsed.variables[0]
    assert variable.name == "value"
    assert type(variable.type).__name__ == "CComposedType"
    assert [type(component).__name__ for component in variable.type.components] == expected_components
    assert parsed.to_dict() == reparsed.to_dict()


@pytest.mark.property
@given(st.lists(_C_IDENTIFIERS, min_size=1, max_size=6, unique=True))
def test_top_level_c_split_ignores_nested_commas_and_literal_commas(names):
    parts = [f'call_{index}({name}, nested({name}, "{name},literal"))' for index, name in enumerate(names)]

    assert top_level_split(", ".join(parts)) == parts


@pytest.mark.property
@given(st.lists(_C_IDENTIFIERS, min_size=1, max_size=6, unique=True))
def test_top_level_c_source_split_ignores_function_body_delimiters(names):
    source = "".join(f'int {name}(void) {{ const char *text = "{{;}}"; return 0; }}\n' for name in names)

    segments = split_top_level_c_source(source, filename="generated.c")

    assert [(segment.text, segment.terminator) for segment in segments] == [
        (f"int {name}(void)", "block") for name in names
    ]


@pytest.mark.property
@given(function_name=_C_IDENTIFIERS)
def test_generated_c_visibility_attributes_are_tolerated(function_name):
    source = f'int {function_name}(void) __attribute__((visibility("default")));\n'

    parsed = parse_c_file(source, filename="compiler.h", preprocessing="compiler")

    assert parsed.diagnostics == []
    assert [function.name for function in parsed.functions] == [function_name]


@pytest.mark.fuzz
@given(_FUZZ_TEXT)
def test_c_parser_fuzz_fragments_only_raise_owned_errors(source):
    with suppress(CParseError):
        parse_c_file(source, filename="fuzz.h")
