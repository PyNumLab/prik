"""C enum conversion into the semantic IR."""

from dataclasses import asdict

from prik.printers import emit_module
from prik.parsers.c import parse_c_file, parse_c_project
from prik.parsers.c.models import (
    CMacro,
)
from prik.pipeline.pyi import pyi_text_to_semantic_module as parse_pyi_text
from prik.semantics.c2ir import (
    CToIRConverter,
    c_file_to_semantic_module,
    c_file_to_semantic_modules,
    c_project_to_semantic_module,
    c_project_to_semantic_modules,
)
from prik.semantics.models import (
    SemanticVariable,
)
from tests.c._support.semantic_conversion import (
    _assert_c_origin,
    _function,
)


def test_c2ir_converts_enum_constants_and_simple_macro_constants():
    parsed = parse_c_file(
        """
enum status { STATUS_OK = 0, STATUS_WARN, STATUS_ERROR = 10 };
""",
        filename="constants.h",
    )
    parsed.macros = [CMacro(name="API_VERSION", value="3")]
    module = c_file_to_semantic_modules(parsed)[0]

    constants = {var.name: var for var in module.variables}
    assert constants["API_VERSION"].default_value == "3"
    assert constants["API_VERSION"].semantic_type.constraints[0].name == "Constant"
    assert constants["STATUS_WARN"].default_value == "1"
    assert constants["STATUS_ERROR"].default_value == "10"
    api_version = constants["API_VERSION"]
    assert isinstance(api_version, SemanticVariable)
    assert api_version.semantic_type.name == "Int32"
    assert api_version.semantic_type.dtype == "Int32"
    assert [asdict(constraint) for constraint in api_version.semantic_type.constraints] == [
        {"name": "Constant", "arguments": []}
    ]
    _assert_c_origin(
        api_version.origin,
        native_name="API_VERSION",
        source_kind="macro",
    )
    status_ok = constants["STATUS_OK"]
    assert module.classes == []
    assert status_ok.semantic_type.name == "Int"
    assert status_ok.semantic_type.dtype == "Int32"
    assert status_ok.semantic_type.metadata["enum_name"] == "status"
    assert status_ok.semantic_type.metadata["c_kind"] == "enum"
    assert status_ok.semantic_type.metadata["c_enum"] == "enum status"
    assert status_ok.semantic_type.metadata["c_underlying_type"] == "Int"
    assert status_ok.semantic_type.coercions == []
    _assert_c_origin(
        status_ok.origin,
        native_name="STATUS_OK",
        native_scope="enum status",
        source_kind="enum_constant",
        source_location={
            "filename": "constants.h",
            "line": 2,
            "column": 1,
            "source_line": "enum status { STATUS_OK = 0, STATUS_WARN, STATUS_ERROR = 10 };",
        },
    )


def test_c2ir_names_anonymous_typedef_enums_and_keeps_enumerators_unscoped():
    source = "typedef enum { FLAG_NONE = 0, FLAG_READ = 1 } flag_t; flag_t get_flags(void);"
    parsed = parse_c_file(source, filename="flags.h")

    module = c_file_to_semantic_module(parsed)
    project_module = c_project_to_semantic_module(parse_c_project({"flags.h": source}), name="flags")

    assert module.classes == []
    assert project_module.classes == []
    assert [variable.name for variable in module.variables] == ["FLAG_NONE", "FLAG_READ"]
    assert [variable.name for variable in project_module.variables] == ["FLAG_NONE", "FLAG_READ"]
    assert [variable.semantic_type.name for variable in module.variables] == ["Int", "Int"]
    assert module.variables[0].semantic_type.metadata["enum_name"] == "flag_t"
    assert _function(module, "get_flags").return_type.name == "Int"
    assert _function(project_module, "get_flags").return_type.name == "Int"


def test_c2ir_enum_values_emit_only_python_compatible_expressions():
    parsed = parse_c_file(
        "enum flags { FLAG_ONE = 1U, FLAG_OCTAL = 010, FLAG_SHIFT = FLAG_ONE << 1, FLAG_CHAR = 'A' };",
        filename="flags.h",
    )
    module = c_file_to_semantic_module(parsed)

    code = emit_module(module)

    assert "FLAG_ONE: Final[Int] = 1" in code
    assert "FLAG_OCTAL: Final[Int] = 8" in code
    assert "FLAG_SHIFT: Final[Int] = FLAG_ONE << 1" in code
    assert "FLAG_CHAR: Final[Int]" in code
    assert {variable.name: variable.default_value for variable in module.variables} == {
        "FLAG_ONE": "1U",
        "FLAG_OCTAL": "010",
        "FLAG_SHIFT": "FLAG_ONE << 1",
        "FLAG_CHAR": "'A'",
    }
    assert [variable.name for variable in parse_pyi_text(code, module_name="flags").variables] == [
        "FLAG_ONE",
        "FLAG_OCTAL",
        "FLAG_SHIFT",
        "FLAG_CHAR",
    ]


def test_c2ir_cross_header_enum_references_import_the_owner_enum():
    project = parse_c_project(
        {
            "types.h": "enum status { STATUS_OK = 0 };",
            "api.h": "enum status get_status(void);",
        }
    )

    modules = {module.name: module for module in c_project_to_semantic_modules(project)}

    assert modules["api"].classes == []
    assert modules["types"].classes == []
    assert _function(modules["api"], "get_status").return_type.name == "Int"
    assert _function(modules["api"], "get_status").return_type.metadata["c_enum"] == "enum status"

    anonymous_project = parse_c_project(
        {
            "types.h": "typedef enum { FLAG_NONE = 0 } flag_t;",
            "api.h": "flag_t get_flags(void);",
        }
    )
    anonymous_modules = {module.name: module for module in c_project_to_semantic_modules(anonymous_project)}
    assert _function(anonymous_modules["api"], "get_flags").return_type.name == "Int"


def test_c2ir_uses_enum_specific_underlying_type_facts_when_supplied():
    parsed = parse_c_file(
        "enum status { STATUS_OK = 0, STATUS_ERROR = 255 }; enum status get_status(void);",
        filename="status.h",
    )
    module = CToIRConverter(
        standard_type_report={
            "types": {
                "enum status": {
                    "available": True,
                    "kind": "integer",
                    "signed": False,
                    "bits": 8,
                    "underlying_c_type": "unsigned char",
                }
            }
        }
    ).visit(parsed)

    return_type = _function(module, "get_status").return_type
    assert module.classes == []
    assert return_type.name == "UInt8"
    assert return_type.dtype == "UInt8"
    assert return_type.metadata["c_kind"] == "enum"
    assert return_type.metadata["c_enum_type_fact_source"] == "compiler_probe"
