"""Tests split by stable ownership concept from `test_cli.py`."""

import json
from pathlib import Path

import prik.pipeline.preprocessing as preprocessing
from prik.pipeline.preprocessing import PreprocessingConfig, build_compile_commands_invocation


def test_compile_commands_filters_dependency_and_windows_compile_flags(tmp_path: Path):
    source = tmp_path / "src" / "api.c"
    source.parent.mkdir()
    source.write_text("int api(void);\n", encoding="utf-8")
    compiler = tmp_path / "cc"
    database = tmp_path / "compile_commands.json"
    database.write_text(
        json.dumps(
            [
                {
                    "directory": str(tmp_path),
                    "file": str(source),
                    "arguments": [
                        str(compiler),
                        "-MF",
                        "deps.d",
                        "-MT",
                        "api.o",
                        "-MQtarget",
                        "-MFdeps2.d",
                        "/c",
                        "src/api.c",
                        "-Wall",
                    ],
                }
            ]
        ),
        encoding="utf-8",
    )

    invocation = build_compile_commands_invocation(
        source,
        config=PreprocessingConfig(mode="compiler", compile_commands=str(database)),
    )

    assert invocation.argv == [str(compiler), "-E", "-Wall", str(source)]


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
    assert preprocessing._unescape_linemarker_filename(r"a\nb\rc\td\\e\"f\x") == 'a\nb\rc\td\\e"fx'
    assert preprocessing._unescape_linemarker_filename("trailing\\") == "trailing\\"
    assert preprocessing._parse_linemarker('# 12 "api.h" 1 3') == (12, "api.h", [1, 3])
    assert preprocessing._parse_linemarker("#line 14 api.h") == (14, "api.h", [])
    assert preprocessing._parse_linemarker("int api;") is None
    assert preprocessing._dependency_kind("api.h", [3]) == "system"
    assert preprocessing._dependency_kind("<command-line>") == "system"
    assert preprocessing._dependency_kind("api.h") == "project"
    assert preprocessing._exposure_for(
        "private/api.h", "project", PreprocessingConfig(private_includes=["private"])
    ) == ("private")
    assert preprocessing._exposure_for("public/api.h", "project", PreprocessingConfig(public_includes=["public"])) == (
        "public"
    )
    assert preprocessing._exposure_for("api.h", "system", PreprocessingConfig()) == "private"
    assert preprocessing._exposure_for("api.h", "project", PreprocessingConfig(include_exposure="roots-only")) == (
        "private"
    )
    assert preprocessing._exposure_for("api.h", "root", PreprocessingConfig(include_exposure="roots-only")) == "public"
    assert preprocessing._line_marker(3, 'dir\\api".h') == '# 3 "dir\\\\api\\".h"'
    assert preprocessing._line_marker(3, "api.h", 1) == '# 3 "api.h" 1'
    assert preprocessing._mapping_for_generated_line(mappings, mappings[0].generated_line, root) == mappings[0]
    fallback = preprocessing._mapping_for_generated_line([], 99, root)
    assert fallback.generated_line == 99
    assert fallback.original_path == str(root)
    assert fallback.original_line == 99
    assert fallback.include_stack == [str(root)]
    no_filename_mappings = preprocessing.parse_linemarker_mappings("#line 42\nint next;\n", filename=str(root))
    assert no_filename_mappings[0].original_path == str(root)
    assert no_filename_mappings[0].original_line == 42
    assert preprocessing._included_files_from_linemarkers(
        "#line 5\nint next;\n",
        root_path=root,
        language="c",
        config=PreprocessingConfig(),
    ) == [files[0]]
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


def test_linemarker_parser_accepts_bare_filename():
    assert preprocessing._parse_linemarker("# 14 api.h") == (14, "api.h", [])


def test_dependency_kind_requires_both_system_filename_brackets():
    assert preprocessing._dependency_kind("<api.h") == "project"
    assert preprocessing._dependency_kind("api.h>") == "project"


def test_line_marker_escapes_paths_and_omits_absent_flag():
    assert preprocessing._line_marker(3, 'dir\\api".h') == '# 3 "dir\\\\api\\".h"'


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
