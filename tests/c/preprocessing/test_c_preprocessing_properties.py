"""Property-based preprocessing invariants for generated C sources."""

from tests.c._support.parser_properties import (
    CParseError,
    _C_IDENTIFIERS,
    given,
    parse_c_file,
    pytest,
    st,
)


@pytest.mark.property
@given(
    feature=_C_IDENTIFIERS,
    function_names=st.lists(_C_IDENTIFIERS, min_size=2, max_size=2, unique=True),
)
def test_generated_c_raw_conditionals_require_preprocessing(feature, function_names):
    source = f"#ifdef {feature}\nint {function_names[0]}(void);\n#else\nint {function_names[1]}(void);\n#endif\n"

    with pytest.raises(CParseError, match="require compiler preprocessing") as exc_info:
        parse_c_file(source, filename="conditional.h", preprocessing="raw")

    assert exc_info.value.code == "CPARSE_PREPROCESSING_REQUIRED"


@pytest.mark.property
@given(line_number=st.integers(min_value=1, max_value=100_000), stem=_C_IDENTIFIERS)
def test_generated_c_linemarkers_map_function_origin(line_number, stem):
    mapped_filename = f"{stem}.h"
    source = f'#line {line_number} "{mapped_filename}"\nint exported(void);\n'

    parsed = parse_c_file(source, filename="generated.i", preprocessing="preprocessed")

    assert parsed.diagnostics == []
    assert len(parsed.functions) == 1
    assert parsed.functions[0].source_location is not None
    assert parsed.functions[0].source_location.filename == mapped_filename
    assert parsed.functions[0].source_location.line == line_number


@pytest.mark.property
@given(local_stem=_C_IDENTIFIERS, system_stem=_C_IDENTIFIERS)
def test_generated_c_raw_includes_record_local_and_system_targets(local_stem, system_stem):
    local_target = f"hypothesis_missing_{local_stem}.h"
    system_target = f"{system_stem}.h"
    source = f'#include "{local_target}"\n#include <{system_target}>\nint exported(void);\n'

    parsed = parse_c_file(source, filename="generated_api.h", preprocessing="raw")

    assert [(include.target, include.kind) for include in parsed.includes] == [
        (local_target, "local"),
        (system_target, "system"),
    ]
    assert [diagnostic.code for diagnostic in parsed.diagnostics] == ["C_UNRESOLVED_INCLUDE"]
