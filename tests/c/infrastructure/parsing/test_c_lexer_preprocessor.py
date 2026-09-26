"""C lexer and lightweight preprocessing coverage."""

import pytest


def test_c_lexer_strips_comments_and_joins_continuations_without_losing_source_accounting():
    from prik.parsers.c.lexer import lex_c_source, normalize_c_source, strip_c_comments

    source = (
        'int first; // removed\nchar *text = "/* kept */ a//b"; /* block\n removed */ int second;\n'
        "char slash = '/';\n"
    )
    stripped = strip_c_comments(source)
    assert len(stripped) == len(source)
    assert stripped.count("\n") == source.count("\n")
    assert '"/* kept */ a//b"' in stripped
    assert "'/'" in stripped
    assert "removed" not in stripped
    assert "int second;" in stripped

    normalized = normalize_c_source("int first = \\\n  1;\n\nint second;\n#define API \\\n", filename="records.h")
    assert [(record.text, record.original_start_line, record.original_end_line) for record in normalized.records] == [
        ("int first = 1;", 1, 2),
        ("int second;", 4, 4),
        ("#define API", 5, 5),
    ]
    assert normalized.records[0].original_source_lines == ("int first = \\", "  1;")

    tokens = lex_c_source(
        "int value = 12;\nvalue += 3;\nchar quote = '\\n';\n/* removed\n   block */ int after;\n",
        filename="tokens.c",
    )
    assert [(token.text, token.kind, token.line, token.column) for token in tokens] == [
        ("int", "identifier", 1, 1),
        ("value", "identifier", 1, 5),
        ("=", "punctuation", 1, 11),
        ("12", "number", 1, 13),
        (";", "punctuation", 1, 15),
        ("value", "identifier", 2, 1),
        ("+=", "punctuation", 2, 7),
        ("3", "number", 2, 10),
        (";", "punctuation", 2, 11),
        ("char", "identifier", 3, 1),
        ("quote", "identifier", 3, 6),
        ("=", "punctuation", 3, 12),
        ("'\\n'", "char", 3, 14),
        (";", "punctuation", 3, 18),
        ("int", "identifier", 5, 13),
        ("after", "identifier", 5, 17),
        (";", "punctuation", 5, 22),
    ]
    assert all(token.filename == "tokens.c" for token in tokens)
    assert tokens[5].source_line == "value += 3;"

    unterminated = lex_c_source(r'char *s = "unterminated\\', filename="bad.c")[-1]
    assert (unterminated.kind, unterminated.text) == ("string", r'"unterminated\\')


def test_top_level_split_keeps_literal_statements_and_reports_an_unterminated_tail():
    from prik.parsers.c.lexer import split_top_level_c_source

    segments = split_top_level_c_source('"literal";\nint unfinished', filename="odd.c")

    assert [(segment.text, segment.terminator) for segment in segments] == [
        ('"literal"', ";"),
        ("int unfinished", "eof"),
    ]


def test_linemarkers_map_escaped_filenames_and_bare_line_directives():
    from prik.parsers.c import parse_c_file
    from prik.parsers.c.lexer import CLineMapping, line_mappings_for_source

    assert line_mappings_for_source("int first;\nint second;", filename="raw.h") == [
        CLineMapping("raw.h", 1, "int first;"),
        CLineMapping("raw.h", 2, "int second;"),
    ]
    mappings = line_mappings_for_source(
        '#line 7\nint local;\n# 3 "dir\\\\api\\".h"\nint named;\n#line 40\nint kept_file;\n',
        filename="generated.i",
        use_linemarkers=True,
    )
    # A bare #line keeps the current file; an escaped filename is unescaped.
    assert [(mapping.filename, mapping.line) for mapping in mappings[1::2]] == [
        ("generated.i", 7),
        ('dir\\api".h', 3),
        ('dir\\api".h', 40),
    ]

    parsed = parse_c_file(
        '#line 11 "dir\\\\api\\".h"\nstruct __attribute__((annotate("tag\\"ged"))) named { int value; };\n',
        filename="generated.i",
        preprocessing="preprocessed",
    )
    assert parsed.structs[0].name == "named"
    assert parsed.structs[0].source_location.filename == 'dir\\api".h'
    assert parsed.structs[0].source_location.line == 11


def test_raw_mode_resolves_local_includes_relative_to_path_input(tmp_path):
    from prik.parsers.c import parse_c_file

    header = tmp_path / "api.h"
    types = tmp_path / "api_types.h"
    header.write_text('#include "api_types.h"\n', encoding="utf-8")
    types.write_text("typedef int api_int;\n", encoding="utf-8")

    parsed = parse_c_file(header)

    assert parsed.includes[0].resolved_path == str(types)
    assert parsed.diagnostics == []


def test_collect_preprocessor_metadata_preserves_locations_and_diagnostics(tmp_path):
    from prik.preprocessing.c import collect_preprocessor_metadata

    include_dir = tmp_path / "include"
    include_dir.mkdir()
    types = include_dir / "api_types.h"
    types.write_text("typedef int api_int;\n", encoding="utf-8")

    metadata = collect_preprocessor_metadata(
        '#pragma once\n#include "api_types.h"\n#include "missing.h"\n#include <stddef.h>\n',
        filename=str(tmp_path / "api.h"),
        include_dirs=[include_dir],
    )
    assert [(item.directive, item.argument, item.source_location.filename) for item in metadata.raw_directives] == [
        ("pragma", "once", str(tmp_path / "api.h")),
    ]
    assert [
        (item.target, item.kind, item.resolved_path, item.source_location.filename, item.source_location.line)
        for item in metadata.includes
    ] == [
        ("api_types.h", "local", str(types), str(tmp_path / "api.h"), 2),
        ("missing.h", "local", None, str(tmp_path / "api.h"), 3),
        ("stddef.h", "system", None, str(tmp_path / "api.h"), 4),
    ]
    diagnostic = metadata.diagnostics[0]
    assert (
        diagnostic.code,
        diagnostic.message,
        diagnostic.severity,
        diagnostic.location.filename,
        diagnostic.location.line,
        diagnostic.unit_kind,
        diagnostic.unit_name,
    ) == (
        "C_UNRESOLVED_INCLUDE",
        'Could not resolve local include "missing.h".',
        "warning",
        str(tmp_path / "api.h"),
        3,
        "include",
        "missing.h",
    )

    relative_dir = tmp_path / "relative"
    relative_dir.mkdir()
    relative_types = relative_dir / "relative_types.h"
    relative_types.write_text("typedef int relative_int;\n", encoding="utf-8")
    relative_metadata = collect_preprocessor_metadata(
        '#include "relative_types.h"\n',
        filename=str(relative_dir / "api.h"),
    )
    assert relative_metadata.includes[0].resolved_path == str(relative_types)


@pytest.mark.parametrize(
    "directive",
    [
        "#define API_VERSION 3",
        "#undef API_VERSION",
        "#ifdef API_VERSION",
        "#include API_HEADER",
        "#error configure preprocessing",
    ],
)
def test_raw_mode_rejects_directives_that_require_preprocessing(directive):
    from prik.parsers.c import CParseError, parse_c_file

    with pytest.raises(CParseError, match="require compiler preprocessing") as exc_info:
        parse_c_file(f"{directive}\nint run(void);\n", filename="raw_macro.h")

    assert exc_info.value.code == "CPARSE_PREPROCESSING_REQUIRED"
    assert exc_info.value.line_number == 1


def test_raw_mode_accepts_trivial_include_guards_without_preprocessing():
    from prik.parsers.c import parse_c_file

    parsed = parse_c_file(
        """
#ifndef API_H
#define API_H

int run(void);

#endif
""",
        filename="api.h",
    )

    assert parsed.preprocessing == "raw"
    assert [function.name for function in parsed.functions] == ["run"]
    assert parsed.macros == []
    assert parsed.raw_directives == []


def test_raw_mode_records_pragmas_as_metadata_without_hiding_declarations():
    from prik.parsers.c import parse_c_file

    parsed = parse_c_file(
        """
#pragma once
#pragma GCC diagnostic push
int configured(void);
""",
        filename="pragmas.h",
        preprocessing="raw",
    )

    assert [fn.name for fn in parsed.functions] == ["configured"]
    assert [(item.directive, item.argument) for item in parsed.raw_directives] == [
        ("pragma", "once"),
        ("pragma", "GCC diagnostic push"),
    ]
    assert parsed.raw_directives[0].source_location.line == 2


def test_raw_mode_openmp_declaration_pragmas_do_not_hide_declarations():
    from prik.parsers.c import parse_c_file

    parsed = parse_c_file(
        """
#pragma omp declare simd
int saxpy(int n, const float *x, float *y);

#pragma omp declare target
extern int omp_global;
int omp_helper(void);
#pragma omp end declare target
""",
        filename="openmp_pragmas.h",
        preprocessing="raw",
    )

    assert [fn.name for fn in parsed.functions] == ["saxpy", "omp_helper"]
    assert [variable.name for variable in parsed.variables] == ["omp_global"]
    assert [(item.directive, item.argument) for item in parsed.raw_directives] == [
        ("pragma", "omp declare simd"),
        ("pragma", "omp declare target"),
        ("pragma", "omp end declare target"),
    ]


def test_compiler_preprocessed_mode_accepts_line_markers_and_expanded_declarations():
    from prik.parsers.c import parse_c_file

    parsed = parse_c_file(
        """
# 1 "api.h"
int exported(void);
# line 20 "api.h"
double scale(double x);
""",
        filename="api.i",
        preprocessing="preprocessed",
    )

    assert [fn.name for fn in parsed.functions] == ["exported", "scale"]
    assert [fn.origin for fn in parsed.functions] == ["preprocessed", "preprocessed"]
    assert parsed.preprocessed_source_path == "api.i"
    assert parsed.original_source_paths == ["api.h"]
    assert parsed.functions[0].source_location.filename == "api.h"
    assert parsed.functions[0].source_location.line == 1
    assert parsed.functions[1].source_location.line == 20
    payload = parsed.to_dict()
    assert "origin" not in payload["functions"][0]
    assert payload["preprocessed_source_path"] == "api.i"
    assert payload["original_source_paths"] == ["api.h"]


def test_compiler_preprocessed_mode_maps_gcc_linemarkers_across_includes_and_line_jumps():
    from prik.parsers.c import CComposedType, CFunctionType, CPointer, parse_c_file

    parsed = parse_c_file(
        """
# 10 "include/api.h" 1
typedef struct api_state api_state;
# 42 "include/api.h" 2
typedef int (*api_callback)(const char *name, int values[static 4]);
# 90 "generated/detail.h" 1
struct generated_detail {
    int id;
    double (*ops[2])(double);
};
# 120 "include/api.h" 2
int api_register(api_state *state, api_callback cb, int (*factory)(api_state *, const char *));
""",
        filename="api.i",
        preprocessing="compiler",
    )

    assert [typedef.name for typedef in parsed.typedefs] == ["api_state", "api_callback"]
    assert [typedef.origin for typedef in parsed.typedefs] == ["preprocessed", "preprocessed"]
    assert parsed.typedefs[0].source_location.filename == "include/api.h"
    assert parsed.typedefs[0].source_location.line == 10
    assert parsed.typedefs[1].source_location.filename == "include/api.h"
    assert parsed.typedefs[1].source_location.line == 42
    assert isinstance(parsed.typedefs[1].type, CComposedType)
    assert any(isinstance(component, CFunctionType) for component in parsed.typedefs[1].type.components)

    detail = parsed.structs[0]
    assert detail.origin == "preprocessed"
    assert detail.name == "generated_detail"
    assert detail.source_location.filename == "generated/detail.h"
    assert detail.source_location.line == 90
    assert [member.name for member in detail.members] == ["id", "ops"]
    assert [member.origin for member in detail.members] == ["preprocessed", "preprocessed"]
    assert detail.members[1].source_location.filename == "generated/detail.h"
    assert detail.members[1].source_location.line == 92
    assert isinstance(detail.members[1].type, CComposedType)
    assert any(isinstance(component, CPointer) for component in detail.members[1].type.components)

    function = parsed.functions[0]
    assert function.origin == "preprocessed"
    assert function.name == "api_register"
    assert function.source_location.filename == "include/api.h"
    assert function.source_location.line == 120
    assert [parameter.name for parameter in function.parameters] == ["state", "cb", "factory"]
    assert [parameter.origin for parameter in function.parameters] == ["preprocessed"] * 3
    assert parsed.original_source_paths == ["include/api.h", "generated/detail.h"]


def test_compiler_preprocessed_mode_maps_nested_aggregate_members_to_original_file():
    from prik.parsers.c import CStruct, parse_c_file

    parsed = parse_c_file(
        """
#line 33 "include/api.h"
struct outer {
    int first;
    struct { int nested; } inner;
};
""",
        filename="api.i",
        preprocessing="preprocessed",
    )

    outer = parsed.structs[0]
    inner = outer.members[1]
    assert isinstance(inner.type, CStruct)
    assert outer.origin == "preprocessed"
    assert inner.origin == "preprocessed"
    assert inner.type.origin == "preprocessed"
    assert inner.type.members[0].origin == "preprocessed"
    assert inner.source_location.filename == "include/api.h"
    assert inner.source_location.line == 35
    assert inner.type.members[0].source_location.filename == "include/api.h"
    assert inner.type.members[0].source_location.line == 35
    assert parsed.diagnostics == []


def test_compiler_preprocessed_mode_maps_fatal_parse_errors_to_original_file():
    from prik.parsers.c import CParseError, parse_c_file

    with pytest.raises(CParseError) as exc_info:
        parse_c_file(
            """
# 77 "include/bad_api.h"
unsigned float value;
""",
            filename="bad.i",
            preprocessing="compiler",
        )

    exc = exc_info.value
    assert exc.filename == "include/bad_api.h"
    assert exc.line_number == 77
    assert exc.source_line == "unsigned float value;"
