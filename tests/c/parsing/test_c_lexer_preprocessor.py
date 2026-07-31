"""C lexer and lightweight preprocessing coverage."""

import pytest


def test_lexer_removes_comments_without_changing_string_or_char_literals():
    from x2py.parsers.c.lexer import lex_c_source

    tokens = lex_c_source(
        r"""
const char *url = "https://example.invalid/a//b";
char slash = '/';
/* removed block comment */
int value; // removed line comment
""",
        filename="comments.c",
    )

    spellings = [token.text for token in tokens]
    assert '"https://example.invalid/a//b"' in spellings
    assert "'/'" in spellings
    assert "comment" not in spellings


def test_lexer_removes_multiline_block_comments_but_preserves_following_line_numbers():
    from x2py.parsers.c.lexer import lex_c_source

    tokens = lex_c_source(
        "int first;\n/* removed\n   block */\nint second;\n",
        filename="block_comments.c",
    )

    identifiers = [token for token in tokens if token.kind == "identifier"]
    assert [token.text for token in identifiers] == ["int", "first", "int", "second"]
    assert identifiers[-2].line == 4
    assert identifiers[-1].column == 5


def test_line_continuations_preserve_original_line_numbers():
    from x2py.parsers.c.preprocessor import normalize_c_source

    normalized = normalize_c_source(
        "#define SUM(a, b) \\\n  ((a) + (b))\nint x;\n",
        filename="continuations.h",
    )

    assert normalized.records[0].original_start_line == 1
    assert normalized.records[0].original_end_line == 2
    assert normalized.records[1].original_start_line == 3


def test_top_level_split_helpers_ignore_nested_commas_and_function_bodies():
    from x2py.parsers.c.lexer import split_top_level_c_source, top_level_split

    assert top_level_split("int (*cmp)(int, int), int value") == [
        "int (*cmp)(int, int)",
        "int value",
    ]

    segments = split_top_level_c_source(
        'int add(int a, int b) { const char *s = "{;}"; return a + b; }\nint next(void);\n',
        filename="split.c",
    )

    assert [(segment.text, segment.terminator) for segment in segments] == [
        ("int add(int a, int b)", "block"),
        ("int next(void)", ";"),
    ]


def test_c_lexer_covers_linemarker_escapes_top_level_strings_and_eof_records():
    from x2py.parsers.c import parse_c_file
    from x2py.parsers.c.lexer import (
        CLogicalRecord,
        _unescape_linemarker_filename,
        lex_c_source,
        line_mappings_for_source,
        normalize_c_source,
        split_top_level_c_source,
    )
    from x2py.parsers.c.preprocessor import _record_location

    assert _unescape_linemarker_filename(r"a\nb\rc\td\\e\"f\x") == 'a\nb\rc\td\\e"fx'
    assert _unescape_linemarker_filename("tail\\") == "tail\\"

    mappings = line_mappings_for_source(
        '#line 7\nint local;\n# 3 "dir\\\\api\\".h"\nint named;\n',
        filename="generated.i",
        use_linemarkers=True,
    )
    assert mappings[1].filename == "generated.i"
    assert mappings[1].line == 7
    assert mappings[3].filename == 'dir\\api".h'
    assert mappings[3].line == 3

    segments = split_top_level_c_source('"literal";\nint unfinished', filename="odd.c")
    assert [(segment.text, segment.terminator) for segment in segments] == [
        ('"literal"', ";"),
        ("int unfinished", "eof"),
    ]

    normalized = normalize_c_source("#define API \\\n", filename="defs.h")
    assert normalized.records[0].text == "#define API"
    assert (
        _record_location(CLogicalRecord(text="#define API", filename="defs.h", original_source_lines=())).source_line
        is None
    )
    assert (
        _record_location(
            CLogicalRecord(text="define API", filename="defs.h", original_source_lines=("define API",))
        ).column
        == 1
    )

    token = lex_c_source(r'char *s = "unterminated\\', filename="bad.c")[-1]
    assert token.kind == "string"
    assert token.text == r'"unterminated\\'

    parsed = parse_c_file(
        '#line 11 "dir\\\\api\\".h"\nstruct __attribute__((annotate("tag\\"ged"))) named { int value; };\n',
        filename="generated.i",
        preprocessing="preprocessed",
    )
    assert parsed.structs[0].name == "named"
    assert parsed.structs[0].source_location.filename == 'dir\\api".h'


def test_c_lexer_mapping_helpers_cover_boundaries_ranges_and_position_updates():
    from x2py.parsers.c.lexer import (
        CLineMapping,
        _advance_position,
        _line_mapping,
        _mapped_filenames,
        _mapped_line_numbers,
        _mapped_source_lines,
        _source_line,
        _source_lines,
    )

    source_lines = ["first", "second", "third"]
    assert _source_line(source_lines, 1) == "first"
    assert _source_line(source_lines, 3) == "third"
    assert _source_line(source_lines, 0) is None
    assert _source_line(source_lines, 4) is None
    assert _source_lines(source_lines, 2, 3) == ("second", "third")

    mappings = [
        CLineMapping("first.h", 11, "first source"),
        CLineMapping("second.h", 22, None),
    ]
    assert _line_mapping(mappings, 1, "fallback.h") == mappings[0]
    assert _line_mapping(mappings, 2, "fallback.h") == mappings[1]
    assert _line_mapping(mappings, 0, "fallback.h") == CLineMapping("fallback.h", 0, None)
    assert _line_mapping(mappings, 3, "fallback.h") == CLineMapping("fallback.h", 3, None)
    assert _mapped_source_lines(mappings, 1, 2) == ("first source", "")
    assert _mapped_filenames(mappings, 1, 2) == ("first.h", "second.h")
    assert _mapped_line_numbers(mappings, 1, 2) == (11, 22)

    assert _advance_position("x", 4, 7) == (4, 8)
    assert _advance_position("\n", 4, 7) == (5, 1)


def test_c_lexer_linemarker_and_directive_helpers_cover_raw_and_preprocessed_modes():
    from x2py.parsers.c.lexer import (
        CLineMapping,
        _blank_preprocessor_directives,
        _parse_linemarker,
        line_mappings_for_source,
    )

    assert _parse_linemarker('# 12 "api.h" 1') == (12, "api.h")
    assert _parse_linemarker("#line 7 generated.h") == (7, "generated.h")
    assert _parse_linemarker("#line 9") == (9, None)
    assert _parse_linemarker("#pragma once") is None

    raw = line_mappings_for_source("int first;\nint second;", filename="raw.h")
    assert raw == [
        CLineMapping("raw.h", 1, "int first;"),
        CLineMapping("raw.h", 2, "int second;"),
    ]

    preprocessed = line_mappings_for_source(
        '# 40 "api.h"\nint first;\n#line 7\nint second;\n',
        filename="generated.i",
        use_linemarkers=True,
    )
    assert preprocessed == [
        CLineMapping("api.h", 40, '# 40 "api.h"'),
        CLineMapping("api.h", 40, "int first;"),
        CLineMapping("api.h", 7, "#line 7"),
        CLineMapping("api.h", 7, "int second;"),
    ]

    blanked = _blank_preprocessor_directives("#define VALUE \\\n  continued\nint kept;\n#pragma once")
    assert blanked.splitlines() == [
        " " * len("#define VALUE \\"),
        " " * len("  continued"),
        "int kept;",
        " " * len("#pragma once"),
    ]


def test_c_lexer_delimiter_helpers_cover_literals_nesting_offsets_and_validation():
    from x2py.parsers.c.lexer import (
        _scan_code_states,
        top_level_partition,
        top_level_split,
        top_level_split_with_offsets,
    )

    source = 'first("x,y", [a,b]), second'
    assert top_level_split_with_offsets(source) == [
        ('first("x,y", [a,b])', 0),
        ("second", source.index("second")),
    ]
    assert top_level_split(source) == ['first("x,y", [a,b])', "second"]
    assert top_level_partition('name = call("=", [x=y])') == ("name", 'call("=", [x=y])')
    assert top_level_partition("name") == ("name", None)

    states = list(_scan_code_states(source))
    quote_index = source.index('"')
    nested_comma_index = source.index(",", source.index("["))
    top_level_comma_index = source.index(",", source.index("]"))
    assert states[quote_index][3] == "normal"
    assert states[quote_index + 1][3] == "string"
    assert states[nested_comma_index][2] == ("(", "[")
    assert states[top_level_comma_index][2] == ()

    with pytest.raises(ValueError, match="single character"):
        top_level_split_with_offsets("a, b", "::")
    with pytest.raises(ValueError, match="single character"):
        top_level_partition("a=b", "==")


def test_c_lexer_aggregate_attribute_helpers_preserve_shape_and_classify_headers():
    from x2py.parsers.c.lexer import (
        _balanced_invocation_end,
        _is_aggregate_definition_header,
        _is_braced_declaration_header,
        _strip_aggregate_header_attributes,
    )

    invocation = '(outer(")") + nested(1))'
    assert _balanced_invocation_end(invocation, 0) == len(invocation)
    prefixed_invocation = "ignored) (nested(1))"
    assert _balanced_invocation_end(prefixed_invocation, prefixed_invocation.index("(")) == len(prefixed_invocation)
    single_quoted_invocation = "(outer(')') + nested(1))"
    assert _balanced_invocation_end(single_quoted_invocation, 0) == len(single_quoted_invocation)
    empty_quoted_invocation = '(outer("") + nested(1))'
    assert _balanced_invocation_end(empty_quoted_invocation, 0) == len(empty_quoted_invocation)
    assert _balanced_invocation_end("(unterminated", 0) is None

    header = "struct __attribute__((packed)) packet"
    stripped = _strip_aggregate_header_attributes(header)
    assert len(stripped) == len(header)
    assert stripped.split() == ["struct", "packet"]
    spaced_header = "struct __attribute__ ((packed)) packet"
    assert _strip_aggregate_header_attributes(spaced_header).split() == ["struct", "packet"]
    bare_header = "struct __attribute__"
    assert _strip_aggregate_header_attributes(bare_header).split() == ["struct"]
    multiline_header = "struct __attribute__((\npacked)) packet"
    assert _strip_aggregate_header_attributes(multiline_header).count("\n") == 1
    assert _is_aggregate_definition_header(header, tolerate_compiler_extensions=True)
    assert not _is_aggregate_definition_header(header)
    assert not _is_aggregate_definition_header("int factory(void)")
    assert not _is_aggregate_definition_header("struct packet(value)")
    assert not _is_aggregate_definition_header("struct packet = value")
    assert _is_braced_declaration_header("int values =")
    assert not _is_braced_declaration_header(header)
    assert not _is_braced_declaration_header("int function(void)")


def test_c_lexer_comment_normalization_and_tokens_preserve_source_accounting():
    from x2py.parsers.c.lexer import lex_c_source, normalize_c_source, strip_c_comments

    source = 'int first; // removed\nchar *text = "/* kept */"; /* block\n removed */ int second;\n'
    stripped = strip_c_comments(source)
    assert len(stripped) == len(source)
    assert stripped.count("\n") == source.count("\n")
    assert '"/* kept */"' in stripped
    assert "removed" not in stripped
    assert "int second;" in stripped

    normalized = normalize_c_source("int first = \\\n  1;\n\nint second;\n", filename="records.h")
    assert [(record.text, record.original_start_line, record.original_end_line) for record in normalized.records] == [
        ("int first = 1;", 1, 2),
        ("int second;", 4, 4),
    ]
    assert normalized.records[0].original_source_lines == ("int first = \\", "  1;")

    tokens = lex_c_source("int value = 12;\nvalue += 3;\nchar quote = '\\n';\n", filename="tokens.c")
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
    ]
    assert all(token.filename == "tokens.c" for token in tokens)
    assert tokens[5].source_line == "value += 3;"


def test_raw_mode_records_includes_without_expanding_them():
    from x2py.parsers.c import parse_c_file

    parsed = parse_c_file(
        '#include "api_types.h"\n#include <stddef.h>\nint run(void);\n',
        filename="includes.h",
        preprocessing="raw",
    )

    assert [include.target for include in parsed.includes] == ["api_types.h", "stddef.h"]
    assert [include.kind for include in parsed.includes] == ["local", "system"]


def test_raw_mode_resolves_local_includes_relative_to_path_input(tmp_path):
    from x2py.parsers.c import parse_c_file

    header = tmp_path / "api.h"
    types = tmp_path / "api_types.h"
    header.write_text('#include "api_types.h"\n', encoding="utf-8")
    types.write_text("typedef int api_int;\n", encoding="utf-8")

    parsed = parse_c_file(header)

    assert parsed.includes[0].resolved_path == str(types)
    assert parsed.diagnostics == []


def test_c_preprocessor_helpers_cover_include_dirs_and_filesystem_errors(tmp_path, monkeypatch):
    from pathlib import Path

    from x2py.parsers.c.lexer import CLogicalRecord
    from x2py.parsers.c.preprocessor import _record_location, _resolve_local_include

    include_dir = tmp_path / "include"
    include_dir.mkdir()
    types = include_dir / "api_types.h"
    types.write_text("typedef int api_int;\n", encoding="utf-8")

    assert _resolve_local_include("api_types.h", None, [include_dir]) == str(types)
    assert _resolve_local_include("missing.h", None, [include_dir]) is None

    unreadable_dir = tmp_path / "unreadable"
    unreadable_dir.mkdir()
    unreadable_candidate = unreadable_dir / "api_types.h"
    original_is_file = Path.is_file

    def raise_one_os_error(path):
        if path == unreadable_candidate:
            raise OSError("unreadable")
        return original_is_file(path)

    monkeypatch.setattr(Path, "is_file", raise_one_os_error)
    assert _resolve_local_include("api_types.h", str(unreadable_dir / "api.h"), [include_dir]) == str(types)

    location = _record_location(
        CLogicalRecord(
            text="  #pragma once",
            filename="api.h",
            original_start_line=7,
            original_source_lines=("  #pragma once",),
        )
    )
    assert (location.filename, location.line, location.column, location.source_line) == (
        "api.h",
        7,
        3,
        "  #pragma once",
    )
    assert (
        _record_location(CLogicalRecord(text="#pragma # once", original_source_lines=("#pragma # once",))).column == 1
    )


def test_collect_preprocessor_metadata_preserves_locations_and_diagnostics(tmp_path):
    from x2py.parsers.c.preprocessor import collect_preprocessor_metadata

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
    from x2py.parsers.c import CParseError, parse_c_file

    with pytest.raises(CParseError, match="require compiler preprocessing") as exc_info:
        parse_c_file(f"{directive}\nint run(void);\n", filename="raw_macro.h")

    assert exc_info.value.code == "CPARSE_PREPROCESSING_REQUIRED"
    assert exc_info.value.line_number == 1


def test_raw_mode_accepts_trivial_include_guards_without_preprocessing():
    from x2py.parsers.c import parse_c_file

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
    from x2py.parsers.c import parse_c_file

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
    from x2py.parsers.c import parse_c_file

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
    from x2py.parsers.c import parse_c_file

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
    from x2py.parsers.c import CComposedType, CFunctionType, CPointer, parse_c_file

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
    from x2py.parsers.c import CStruct, parse_c_file

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
    from x2py.parsers.c import CParseError, parse_c_file

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
