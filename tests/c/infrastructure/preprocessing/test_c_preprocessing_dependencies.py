"""Compiler linemarkers become include dependencies, exposure, source mappings, and macros."""

from pathlib import Path

import prik.preprocessing.source as preprocessing
from prik.preprocessing import PreprocessingConfig


def test_linemarker_dependency_exposure_and_macro_edges(tmp_path: Path):
    root = tmp_path / "root.c"
    source = "\n".join(
        [
            '#line 7 "src\\\\api\\".h"',
            "int from_line;",
            '# 1 "<built-in>" 1 3',
            "#define BUILTIN 1",
            '# 2 "<built-in>" 2',
            '# 2 "src/api.h" 2',
            '# 1 "public/api.h" 1',
            "int public_api;",
            '# 1 "private/internal.h" 1',
            "int private_api;",
            '# 1 "project/hidden.h" 1',
            "int hidden_api;",
        ]
    )

    mappings = preprocessing.parse_linemarker_mappings(source, filename=str(root))
    macros = preprocessing._parse_macro_definitions(source, mappings)
    files = preprocessing._included_files_from_linemarkers(
        source,
        root_path=root,
        language="c",
        config=PreprocessingConfig(
            include_exposure="roots-only",
            public_includes=["public"],
            private_includes=["private"],
        ),
    )
    by_path = {item.path: item for item in files}

    assert mappings[0].original_line == 7
    assert 'api".h' in mappings[0].original_path
    no_filename_mappings = preprocessing.parse_linemarker_mappings("#line 42\nint next;\n", filename=str(root))
    assert no_filename_mappings[0].original_path == str(root)
    assert no_filename_mappings[0].original_line == 42
    assert macros[0].name == "BUILTIN"
    assert macros[0].builtin is True
    assert by_path[str(root)].dependency_kind == "root"
    assert by_path["<built-in>"].dependency_kind == "system"
    assert by_path["public/api.h"].exposure == "public"
    assert by_path["private/internal.h"].exposure == "private"
    assert by_path["project/hidden.h"].exposure == "private"
    assert [mapping.to_dict() for mapping in mappings] == [
        {
            "generated_line": 2,
            "original_path": 'src\\api".h',
            "original_line": 7,
            "include_stack": ['src\\api".h'],
        },
        {
            "generated_line": 4,
            "original_path": "<built-in>",
            "original_line": 1,
            "include_stack": ['src\\api".h', "<built-in>"],
        },
        {
            "generated_line": 8,
            "original_path": "public/api.h",
            "original_line": 1,
            "include_stack": ["src/api.h", "public/api.h"],
        },
        {
            "generated_line": 10,
            "original_path": "private/internal.h",
            "original_line": 1,
            "include_stack": ["src/api.h", "public/api.h", "private/internal.h"],
        },
        {
            "generated_line": 12,
            "original_path": "project/hidden.h",
            "original_line": 1,
            "include_stack": ["src/api.h", "public/api.h", "private/internal.h", "project/hidden.h"],
        },
    ]
    assert [item.to_dict() for item in files] == [
        {
            "path": str(root),
            "included_by": None,
            "include_line": None,
            "mechanism": "c_include",
            "dependency_kind": "root",
            "exposure": "public",
        },
        {
            "path": "<built-in>",
            "included_by": 'src\\api".h',
            "include_line": 8,
            "mechanism": "c_include",
            "dependency_kind": "system",
            "exposure": "private",
        },
        {
            "path": "public/api.h",
            "included_by": "src/api.h",
            "include_line": 2,
            "mechanism": "c_include",
            "dependency_kind": "project",
            "exposure": "public",
        },
        {
            "path": "private/internal.h",
            "included_by": "public/api.h",
            "include_line": 2,
            "mechanism": "c_include",
            "dependency_kind": "project",
            "exposure": "private",
        },
        {
            "path": "project/hidden.h",
            "included_by": "private/internal.h",
            "include_line": 2,
            "mechanism": "c_include",
            "dependency_kind": "project",
            "exposure": "private",
        },
    ]
    assert [macro.to_dict() for macro in macros] == [
        {
            "name": "BUILTIN",
            "value": "1",
            "function_like": False,
            "parameters": None,
            "path": "<built-in>",
            "line": 1,
            "builtin": True,
        }
    ]


def test_linemarker_mapping_and_macro_helpers_cover_default_and_return_edges():
    source = "\n".join(
        [
            "int before;",
            '# 1 "same.h" 1',
            '# 2 "same.h" 1',
            "int nested;",
            '# 8 "root.c" 2',
            "int returned;",
            '# 3 "unknown.h" 2',
            "int unknown;",
            '# 9 "replacement.h"',
            "int replacement;",
            "#define EMPTY",
            "#define NOARGS() value",
            "#define ARGS(left, right) left + right",
        ]
    )

    mappings = preprocessing.parse_linemarker_mappings(source)

    assert mappings[0].to_dict() == {
        "generated_line": 1,
        "original_path": "<preprocessed>",
        "original_line": 1,
        "include_stack": ["<preprocessed>"],
    }
    assert mappings[1].include_stack == ["<preprocessed>", "same.h"]
    assert mappings[2].include_stack == ["root.c"]
    assert mappings[3].include_stack == ["unknown.h"]
    assert mappings[4].include_stack == ["replacement.h"]
    assert [macro.to_dict() for macro in preprocessing._parse_macro_definitions(source, mappings)] == [
        {
            "name": "EMPTY",
            "value": None,
            "function_like": False,
            "parameters": None,
            "path": "replacement.h",
            "line": 10,
            "builtin": False,
        },
        {
            "name": "NOARGS",
            "value": "value",
            "function_like": True,
            "parameters": [],
            "path": "replacement.h",
            "line": 11,
            "builtin": False,
        },
        {
            "name": "ARGS",
            "value": "left + right",
            "function_like": True,
            "parameters": ["left", "right"],
            "path": "replacement.h",
            "line": 12,
            "builtin": False,
        },
    ]
    assert preprocessing._parse_macro_definitions("#define UNMAPPED 1", []) == [
        preprocessing.MacroDefinition(name="UNMAPPED", value="1")
    ]
