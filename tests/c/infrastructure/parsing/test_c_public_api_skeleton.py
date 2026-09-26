"""C parser public entry points and JSON serialization of parsed models."""

from pathlib import Path


def test_c_parser_entry_points_accept_inline_path_mapping_and_directory_inputs(tmp_path: Path):
    from prik.parsers.c import CFile, CParser, CProject, parse_c_file, parse_c_project

    inline = parse_c_file("int add(int a, int b);\n", filename="inline.h")
    assert isinstance(inline, CFile)
    assert (inline.filename, inline.language, [fn.name for fn in inline.functions]) == ("inline.h", "c", ["add"])
    empty = parse_c_file("", filename="empty.src")
    assert (empty.functions, empty.diagnostics) == ([], [])

    header = tmp_path / "api.h"
    source = tmp_path / "api.c"
    header.write_text("double scale(double x);\n", encoding="utf-8")
    source.write_text('#include "api.h"\nint answer(void);\n', encoding="utf-8")
    (tmp_path / "notes.txt").write_text("ignored\n", encoding="utf-8")
    parsed_path = parse_c_file(header)
    assert parsed_path.filename == str(header)
    assert [fn.name for fn in parsed_path.functions] == ["scale"]

    mapping = parse_c_project(
        {"types.h": "typedef int api_int;\n", "api.h": '#include "types.h"\napi_int answer(void);\n'}
    )
    assert isinstance(mapping, CProject)
    assert set(mapping.files) == {"types.h", "api.h"}
    assert set(mapping.functions) == {"answer"}
    assert set(parse_c_project(source).files) == {str(source)}
    # A directory holds C inputs only, keyed relative to it.
    assert set(parse_c_project(tmp_path).files) == {"api.h", "api.c"}

    parser = CParser()
    assert parser.parse_file("int answer(void);\n", filename="api.h") == parse_c_file(
        "int answer(void);\n", filename="api.h"
    )
    assert parser.parse_project({"api.h": "int answer(void);\n"}) == parse_c_project({"api.h": "int answer(void);\n"})


def test_parse_c_file_rejects_unknown_preprocessing_mode():
    import pytest

    from prik.parsers.c import parse_c_file

    with pytest.raises(ValueError, match="preprocessing mode"):
        parse_c_file("int answer(void);\n", filename="api.h", preprocessing="unknown")


def test_concrete_type_serialization_preserves_semantic_type_fields_and_locations():
    from prik.parsers.c import parse_c_file

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
    from prik.parsers.c import parse_c_file

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
    from prik.parsers.c import parse_c_file

    payload = parse_c_file(
        "typedef struct node { struct node *next; } node_t;\n",
        filename="node.h",
    ).to_dict()

    assert payload["structs"][0]["model"] == "CStruct"
    assert payload["structs"][0]["members"][0]["type"]["components"][-1]["model"] == "CStruct"
    assert payload["typedefs"][0]["model"] == "CTypedef"
    assert payload["typedefs"][0]["type"] == {"reference": "struct node"}


def test_unresolved_typedef_reference_metadata_is_preserved_in_json():
    from prik.parsers.c import parse_c_file

    payload = parse_c_file("api_size count(void);\n", filename="unresolved.h").to_dict()

    result_type = payload["functions"][0]["result_type"]
    assert result_type["model"] == "CTypedef"
    assert result_type["name"] == "api_size"
    assert result_type["type"] is None
