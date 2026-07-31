"""C parser public API coverage for the current partial subset."""

from pathlib import Path


def test_c_parser_path_and_include_key_helpers_preserve_boundary_contracts(monkeypatch):
    from x2py.parsers.c.parser import _include_key_from_current, _looks_like_existing_source_path

    monkeypatch.setattr(Path, "is_file", lambda self: True)

    assert _looks_like_existing_source_path(Path("api.h")) is True
    assert _looks_like_existing_source_path("api.h") is True
    assert _looks_like_existing_source_path("") is False
    assert _looks_like_existing_source_path("int answer(void);\n") is False
    assert _looks_like_existing_source_path(object()) is False
    assert _include_key_from_current("api.h", "types.h") == "types.h"
    assert _include_key_from_current("src/api.h", "types.h") == "src/types.h"

    def raise_os_error(path):
        raise OSError

    monkeypatch.setattr(Path, "is_file", raise_os_error)

    assert _looks_like_existing_source_path("api.h") is False


def test_c_parser_public_wrappers_forward_explicit_options(monkeypatch):
    from x2py.parsers.c import parse_c_file, parse_c_project

    calls = []

    class RecordingParser:
        def parse_file(self, *args, **kwargs):
            calls.append(("file", args, kwargs))
            return "file-result"

        def parse_project(self, *args, **kwargs):
            calls.append(("project", args, kwargs))
            return "project-result"

    monkeypatch.setattr("x2py.parsers.c.parser._DEFAULT_PARSER", RecordingParser())

    include_dirs = [Path("include")]
    assert (
        parse_c_file(
            "api source",
            filename="api.h",
            include_dirs=include_dirs,
            preprocessing="preprocessed",
            encoding="latin-1",
        )
        == "file-result"
    )
    assert (
        parse_c_project(
            {"api.h": "api source"},
            include_dirs=include_dirs,
            preprocessing="preprocessed",
            encoding="latin-1",
        )
        == "project-result"
    )
    assert calls == [
        (
            "file",
            ("api source",),
            {
                "filename": "api.h",
                "include_dirs": include_dirs,
                "preprocessing": "preprocessed",
                "encoding": "latin-1",
            },
        ),
        (
            "project",
            ({"api.h": "api source"},),
            {
                "include_dirs": include_dirs,
                "preprocessing": "preprocessed",
                "encoding": "latin-1",
            },
        ),
    ]


def test_parse_c_file_accepts_inline_source_and_returns_typed_model():
    from x2py.parsers.c import CFile, parse_c_file

    parsed = parse_c_file("int add(int a, int b);\n", filename="inline.h")

    assert isinstance(parsed, CFile)
    assert parsed.filename == "inline.h"
    assert parsed.language == "c"
    assert [fn.name for fn in parsed.functions] == ["add"]


def test_x2py_exports_c_file_and_project_entrypoints_like_fortran():
    from x2py import CFile, CProject, parse_c_file, parse_c_project

    parsed = parse_c_file("int add(int left, int right);\n", filename="api.h")
    project = parse_c_project({"api.h": "int add(int left, int right);\n"})

    assert isinstance(parsed, CFile)
    assert isinstance(project, CProject)
    assert "add" in project.functions


def test_parse_c_file_accepts_path_input_and_preserves_filename(tmp_path: Path):
    from x2py.parsers.c import parse_c_file

    header = tmp_path / "api.h"
    header.write_text("double scale(double x);\n", encoding="utf-8")

    parsed = parse_c_file(header)

    assert parsed.filename == str(header)
    assert [fn.name for fn in parsed.functions] == ["scale"]


def test_parse_c_file_accepts_empty_source_and_unknown_suffix():
    from x2py.parsers.c import parse_c_file

    parsed = parse_c_file("", filename="empty.src")

    assert parsed.filename == "empty.src"
    assert parsed.functions == []
    assert parsed.diagnostics == []


def test_parse_c_file_rejects_unknown_preprocessing_mode():
    import pytest

    from x2py.parsers.c import parse_c_file

    with pytest.raises(ValueError, match="preprocessing mode"):
        parse_c_file("int answer(void);\n", filename="api.h", preprocessing="unknown")


def test_parse_c_project_accepts_mapping_sources():
    from x2py.parsers.c import CProject, parse_c_project

    project = parse_c_project(
        {
            "types.h": "typedef int api_int;\n",
            "api.h": '#include "types.h"\napi_int answer(void);\n',
        }
    )

    assert isinstance(project, CProject)
    assert set(project.files) == {"types.h", "api.h"}
    assert project.files["api.h"].language == "c"
    assert set(project.functions) == {"answer"}


def test_parse_c_project_accepts_single_file_path(tmp_path: Path):
    from x2py.parsers.c import parse_c_project

    source = tmp_path / "api.c"
    source.write_text("int answer(void);\n", encoding="utf-8")

    project = parse_c_project(source)

    assert set(project.files) == {str(source)}
    assert set(project.functions) == {"answer"}


def test_parse_c_project_indexes_forward_structs_by_tag_name():
    from x2py.parsers.c import parse_c_project

    project = parse_c_project(
        {
            "types.h": "struct handle;\n",
            "api.h": "struct handle *open_handle(void);\n",
        }
    )

    assert set(project.structs) == {"handle"}
    assert project.structs["handle"].is_incomplete is True
    assert project.files["types.h"].structs[0].name == "handle"


def test_parse_c_project_indexes_named_union_and_enum_tags():
    from x2py.parsers.c import parse_c_project

    project = parse_c_project(
        {
            "types.h": "union value { int i; }; enum status { STATUS_OK = 0 };",
        }
    )

    assert set(project.unions) == {"value"}
    assert set(project.enums) == {"status"}


def test_parse_c_project_accepts_directory_input_with_c_and_h_files(tmp_path: Path):
    from x2py.parsers.c import parse_c_project

    (tmp_path / "api.h").write_text("int add(int a, int b);\n", encoding="utf-8")
    (tmp_path / "api.c").write_text('#include "api.h"\n', encoding="utf-8")
    (tmp_path / "notes.txt").write_text("ignored\n", encoding="utf-8")

    project = parse_c_project(tmp_path)

    assert set(project.files) == {"api.h", "api.c"}


def test_c_file_serialization_is_json_stable():
    from x2py.parsers.c import parse_c_file

    parsed = parse_c_file("", filename="empty.c")

    assert parsed.to_dict() == {
        "filename": "empty.c",
        "language": "c",
        "preprocessing": "raw",
        "functions": [],
        "structs": [],
        "unions": [],
        "enums": [],
        "typedefs": [],
        "variables": [],
        "macros": [],
        "includes": [],
        "raw_directives": [],
        "macro_dependencies": [],
        "diagnostics": [],
    }
    assert "preprocessing_recipe" not in parsed.to_dict()


def test_concrete_type_serialization_preserves_semantic_type_fields_and_locations():
    from x2py.parsers.c import parse_c_file

    parsed = parse_c_file(
        "typedef int (*compare_fn)(const void *, const void *);\ncompare_fn select_compare(void);\n",
        filename="types.h",
    )
    payload = parsed.to_dict()

    typedef = payload["typedefs"][0]
    assert typedef["model"] == "CTypedef"
    assert typedef["type"]["model"] == "CComposedType"
    assert typedef["type"]["components"][0]["model"] == "CPointer"
    assert typedef["type"]["components"][1]["model"] == "CFunctionType"
    assert typedef["type"]["components"][1]["result_type"]["model"] == "CInt"
    first_parameter = typedef["type"]["components"][1]["parameter_types"][0]
    assert first_parameter["components"][-1]["qualifiers"] == ["const"]
    assert typedef["source_location"]["filename"] == "types.h"
    assert typedef["source_location"]["line"] == 1

    function = payload["functions"][0]
    assert function["result_type"]["model"] == "CTypedef"
    assert function["result_type"]["name"] == "compare_fn"
    assert function["source_location"]["line"] == 2


def test_parameter_adjustment_serialization_preserves_declared_and_effective_types():
    from x2py.parsers.c import parse_c_file

    payload = parse_c_file(
        "void process(int values[4], int callback(int));\n",
        filename="adjustment.h",
    ).to_dict()
    values, callback = payload["functions"][0]["parameters"]

    assert values["declared_type"]["components"][0]["model"] == "CArray"
    assert values["declared_type"]["components"][0]["bound"] == "4"
    assert values["type"]["components"][0]["model"] == "CPointer"
    assert callback["declared_type"]["model"] == "CFunctionType"
    assert callback["type"]["components"][0]["model"] == "CPointer"
    assert callback["type"]["components"][1]["model"] == "CFunctionType"


def test_inline_aggregate_typedef_serialization_uses_references_without_cycles():
    from x2py.parsers.c import parse_c_file

    payload = parse_c_file(
        "typedef struct node { struct node *next; } node_t;\n",
        filename="node.h",
    ).to_dict()

    assert payload["structs"][0]["model"] == "CStruct"
    assert payload["structs"][0]["members"][0]["type"]["components"][-1]["model"] == "CStruct"
    assert payload["typedefs"][0]["model"] == "CTypedef"
    assert payload["typedefs"][0]["type"] == {"reference": "struct node"}


def test_unresolved_typedef_reference_metadata_is_preserved_in_json():
    from x2py.parsers.c import parse_c_file

    payload = parse_c_file("api_size count(void);\n", filename="unresolved.h").to_dict()

    result_type = payload["functions"][0]["result_type"]
    assert result_type["model"] == "CTypedef"
    assert result_type["name"] == "api_size"
    assert result_type["type"] is None


def test_c_parser_instance_entrypoints_match_public_functions():
    from x2py.parsers.c import CParser, parse_c_file, parse_c_project

    source = "int answer(void);\n"
    parser = CParser()

    assert parser.parse_file(source, filename="api.h") == parse_c_file(source, filename="api.h")
    assert parser.parse_project({"api.h": source}) == parse_c_project({"api.h": source})
    assert parser._assemble_project({"api.h": parser.parse_file(source, filename="api.h")}) == parse_c_project(
        {"api.h": source}
    )


def test_c_parse_error_attributes_and_diagnostic_formatting():
    from x2py.parsers.c import CArray, CComposedType, CInt, CParseError, CPointer, CSourceLocation

    err = CParseError(
        "unexpected token",
        filename="bad.h",
        line_number=2,
        column=5,
        source_line="int broken(;",
    )

    assert err.filename == "bad.h"
    assert err.line_number == 2
    assert err.column == 5
    assert err.base_message == "unexpected token"
    assert err.code == "CPARSE_ERROR"

    diagnostic = err.format_diagnostic(color=False, debug=True)
    assert "bad.h:2:5: error[CPARSE_ERROR]: unexpected token" in diagnostic
    assert "2 | int broken(;" in diagnostic
    assert "note: parser raised at" in diagnostic

    assert CSourceLocation(filename="api.h").display == "api.h"
    composed = CComposedType(components=[CPointer(), CArray(bound="4"), CInt()])
    assert composed.pointer_depth == 1
    assert composed.array_rank == 1


def test_c_parse_error_color_and_no_color_formatting():
    from x2py.parsers.c import CParseError

    err = CParseError(
        "unexpected token",
        filename="bad.h",
        line_number=2,
        column=5,
        source_line="int broken(;",
    )

    plain = err.format_diagnostic(color=False)
    colored = err.format_diagnostic(color=True)

    assert "\x1b[" not in plain
    assert "\x1b[" in colored
