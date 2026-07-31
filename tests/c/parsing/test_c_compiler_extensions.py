from __future__ import annotations

from pathlib import Path
import shutil

import pytest


def test_raw_mode_keeps_compiler_extension_declarations_conservative():
    from x2py.parsers.c import parse_c_file

    parsed = parse_c_file(
        'int exported(void) __attribute__((visibility("default")));\n',
        filename="raw_extensions.h",
        preprocessing="raw",
    )

    assert parsed.functions == []
    assert [(diagnostic.code, diagnostic.unit_kind) for diagnostic in parsed.diagnostics] == [
        ("C_UNSUPPORTED_DECLARATION", "attribute_declaration"),
    ]


def test_gnu_header_spelling_aliases_and_harmless_attributes_are_tolerated():
    from x2py.parsers.c import CComposedType, CConst, CRestrict, parse_c_file

    parsed = parse_c_file(
        """
__extension__ typedef __signed__ long int signed_long;
extern __inline__ int inlined(__const char *__restrict__ input)
    __attribute__((__nothrow__, __nonnull__(1)));
__thread int per_thread;
struct annotated {
    __const__ char *name __attribute__((deprecated));
};
""",
        filename="gnu_aliases.h",
        preprocessing="compiler",
    )

    assert [typedef.name for typedef in parsed.typedefs] == ["signed_long"]
    assert [function.name for function in parsed.functions] == ["inlined"]
    assert [variable.name for variable in parsed.variables] == ["per_thread"]
    assert parsed.variables[0].storage == ["_Thread_local"]
    parameter_type = parsed.functions[0].parameters[0].type
    assert isinstance(parameter_type, CComposedType)
    assert parameter_type.components[0].qualifiers == [CRestrict()]
    assert parameter_type.components[1].qualifiers == [CConst()]
    assert [struct.name for struct in parsed.structs] == ["annotated"]
    assert [member.name for member in parsed.structs[0].members] == ["name"]
    assert parsed.diagnostics == []


def test_layout_and_abi_attributes_are_parsed_with_explicit_warnings():
    from x2py.parsers.c import parse_c_file

    parsed = parse_c_file(
        """
struct __attribute__((packed)) packet {
    int value __attribute__((aligned(8)));
};
typedef int vector4 __attribute__((__vector_size__(16)));
extern int abi_call(void) __attribute__((ms_abi));
""",
        filename="abi_attributes.h",
        preprocessing="compiler",
    )

    assert [struct.name for struct in parsed.structs] == ["packet"]
    assert [member.name for member in parsed.structs[0].members] == ["value"]
    assert [typedef.name for typedef in parsed.typedefs] == ["vector4"]
    assert [function.name for function in parsed.functions] == ["abi_call"]
    assert [(diagnostic.code, diagnostic.unit_kind, diagnostic.unit_name) for diagnostic in parsed.diagnostics] == [
        ("C_UNMODELED_COMPILER_EXTENSION", "compiler_attribute", "packed"),
        ("C_UNMODELED_COMPILER_EXTENSION", "compiler_attribute", "aligned"),
        ("C_UNMODELED_COMPILER_EXTENSION", "compiler_attribute", "vector_size"),
        ("C_UNMODELED_COMPILER_EXTENSION", "compiler_attribute", "ms_abi"),
    ]


def test_declspec_calling_conventions_asm_labels_and_top_level_asm_are_tolerated():
    from x2py.parsers.c import parse_c_file

    parsed = parse_c_file(
        """
__declspec(align(16)) struct block { int value; };
extern __declspec(dllimport) int __stdcall imported(int value);
__declspec(thread) extern int tls_value;
extern int renamed(void) __asm__("renamed_v2");
__asm__(".ident \\"compiler metadata\\"");
""",
        filename="vendor_extensions.h",
        preprocessing="compiler",
    )

    assert [struct.name for struct in parsed.structs] == ["block"]
    assert [function.name for function in parsed.functions] == ["imported", "renamed"]
    assert [variable.name for variable in parsed.variables] == ["tls_value"]
    assert [(diagnostic.unit_kind, diagnostic.unit_name) for diagnostic in parsed.diagnostics] == [
        ("compiler_attribute", "align"),
        ("calling_convention", "__stdcall"),
        ("compiler_attribute", "thread"),
        ("asm_label", "__asm__"),
        ("asm_label", "__asm__"),
    ]


def test_bare_compiler_extensions_and_comments_are_tolerated():
    from x2py.parsers.c import parse_c_file

    parsed = parse_c_file(
        """
/* block
   comment */
__attribute__ int attributed;
// line comment
_Alignas int aligned;
extern int renamed __asm__;
""",
        filename="bare_extensions.h",
        preprocessing="compiler",
    )

    assert [variable.name for variable in parsed.variables] == ["attributed", "aligned", "renamed"]
    assert [(diagnostic.unit_kind, diagnostic.unit_name) for diagnostic in parsed.diagnostics] == [
        ("alignment_specifier", "_Alignas"),
        ("asm_label", "__asm__"),
    ]


def test_compiler_extension_normalization_preserves_coordinates_and_source_states():
    from x2py.parsers.c import CParser

    source = (
        'const char *s = "__attribute__((packed))";\n'
        "// __attribute__((unused)) ignored\n"
        "/* keep * __declspec(dllexport) */\n"
        "extern int packed_call(void) __attribute__((packed, ms_abi));\n"
        "__extension__ extern __inline__ int __stdcall run(__const char *__restrict p) "
        '__attribute__((visibility("default")));\n'
        "_Alignas(16) int aligned;\n"
        'extern int renamed __asm__("renamed_v2");\n'
        "_BitInt(17) bits;\n"
        "__typeof__(errno) err;\n"
        "int *__ptr64 ptr;\n"
    )

    normalized, extensions = CParser()._normalize_compiler_extensions(source)

    assert len(normalized) == len(source)
    assert normalized == (
        'const char *s = "__attribute__((packed))";\n'
        "// __attribute__((unused)) ignored\n"
        "/* keep * __declspec(dllexport) */\n"
        "extern int packed_call(void)                                ;\n"
        "              extern inline     int           run(const   char *restrict   p) "
        "                                      ;\n"
        "             int aligned;\n"
        "extern int renamed                      ;\n"
        "_bitint     bits;\n"
        "_typeof           err;\n"
        "int *        ptr;\n"
    )
    assert [(extension.kind, extension.name, extension.offset) for extension in extensions] == [
        ("compiler_attribute", "packed", source.index("__attribute__((packed, ms_abi))")),
        ("compiler_attribute", "ms_abi", source.index("__attribute__((packed, ms_abi))")),
        ("calling_convention", "__stdcall", source.index("__stdcall")),
        ("alignment_specifier", "_Alignas", source.index("_Alignas")),
        ("asm_label", "__asm__", source.index("__asm__")),
        ("compiler_type", "_BitInt", source.index("_BitInt")),
        ("compiler_type", "__typeof__", source.index("__typeof__")),
        ("compiler_qualifier", "__ptr64", source.index("__ptr64")),
    ]


def test_compiler_extension_only_segment_does_not_stop_later_declarations():
    from x2py.parsers.c import parse_c_file

    parsed = parse_c_file(
        "__attribute__((deprecated));\nint kept;\n",
        filename="blank_extension_segment.h",
        preprocessing="compiler",
    )

    assert [variable.name for variable in parsed.variables] == ["kept"]
    assert parsed.diagnostics == []


def test_abi_pointer_qualifiers_are_accepted_with_explicit_warning():
    from x2py.parsers.c import parse_c_file

    parsed = parse_c_file(
        "int *__ptr64 global_ptr;\n",
        filename="abi_pointer_qualifier.h",
        preprocessing="compiler",
    )

    assert [variable.name for variable in parsed.variables] == ["global_ptr"]
    assert [(diagnostic.code, diagnostic.unit_kind, diagnostic.unit_name) for diagnostic in parsed.diagnostics] == [
        ("C_UNMODELED_COMPILER_EXTENSION", "compiler_qualifier", "__ptr64"),
    ]


def test_double_bracket_attribute_scanner_ignores_quoted_closers():
    from x2py.parsers.c import CParser

    text = '[[vendor::attr("escaped \\" quote and ]] text")]] int value;'

    end = CParser._find_double_bracket_end(text, 0)

    assert end == text.index(" int value")
    assert CParser._find_double_bracket_end("[[unterminated", 0) is None


def test_typeof_bitint_and_extended_scalars_remain_parseable_as_opaque_types():
    from x2py.parsers.c import CTypedef, CUnknownType, parse_c_file

    parsed = parse_c_file(
        """
extern __typeof__(errno) errno_alias;
_BitInt(17) bit_counter;
unsigned __int128 wide_counter;
_Float128 wide_float;
""",
        filename="compiler_types.h",
        preprocessing="compiler",
    )

    variables = {variable.name: variable for variable in parsed.variables}
    assert isinstance(variables["errno_alias"].type, CTypedef)
    assert variables["errno_alias"].type.name == "_typeof"
    assert isinstance(variables["bit_counter"].type, CTypedef)
    assert variables["bit_counter"].type.name == "_bitint"
    assert isinstance(variables["wide_counter"].type, CUnknownType)
    assert variables["wide_counter"].type.spelling == "unsigned __int128"
    assert isinstance(variables["wide_float"].type, CUnknownType)
    assert variables["wide_float"].type.spelling == "_Float128"
    assert [(diagnostic.unit_kind, diagnostic.unit_name) for diagnostic in parsed.diagnostics] == [
        ("compiler_type", "__typeof__"),
        ("compiler_type", "_BitInt"),
    ]


def test_preprocessed_extension_diagnostics_and_declarations_use_linemarkers():
    from x2py.parsers.c import parse_c_file

    parsed = parse_c_file(
        """
# 1 "private_types.h" 1
struct __attribute__((packed)) wire_value { int value; };
# 20 "api.h" 2
extern int consume_wire(struct wire_value *value)
    __attribute__((visibility("default")));
""",
        filename="generated.i",
        preprocessing="preprocessed",
    )

    assert parsed.structs[0].source_location.filename == "private_types.h"
    assert parsed.structs[0].source_location.line == 1
    assert parsed.functions[0].source_location.filename == "api.h"
    assert parsed.functions[0].source_location.line == 20
    assert len(parsed.diagnostics) == 1
    assert parsed.diagnostics[0].unit_name == "packed"
    assert parsed.diagnostics[0].location.filename == "private_types.h"
    assert parsed.diagnostics[0].location.line == 1


def test_gcc_preprocessed_standard_headers_remain_parseable(tmp_path: Path):
    from x2py.parsers.c import parse_c_file
    from x2py.pipeline.preprocessing import PreprocessingConfig, preprocess_source

    compiler = shutil.which("cc")
    if compiler is None:
        pytest.skip("cc is not available")

    header = tmp_path / "system_api.h"
    header.write_text(
        """
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
int consume_file(FILE *stream);
uint32_t hash_bytes(const void *data, size_t size);
""",
        encoding="utf-8",
    )
    preprocessed = preprocess_source(
        header,
        language="c",
        config=PreprocessingConfig(mode="compiler", compiler=compiler),
    )
    parsed = parse_c_file(
        preprocessed.source,
        filename=str(header),
        preprocessing="compiler",
    )

    function_names = {function.name for function in parsed.functions}
    assert {"consume_file", "hash_bytes"} <= function_names
    assert len(parsed.typedefs) >= 50
    assert any(
        included.dependency_kind == "system" and included.exposure == "private"
        for included in preprocessed.included_files
    )
    assert not any(diagnostic.severity == "error" for diagnostic in parsed.diagnostics)
