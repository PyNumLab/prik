"""Tests split by stable ownership concept from `test_functions_and_callbacks.py`."""

from dataclasses import asdict

import pytest

from prik.pipeline.pyi import emit_module_stubs
from prik.parsers.c import parse_c_file, parse_c_project
from prik.parsers.c.models import (
    CEnum,
    CFile,
    CFunction,
    CInt,
    CParameter,
    CProject,
    CSourceLocation,
    CStruct,
    CTypedef,
    CUnion,
    CVariable,
)
from prik.semantics.c2ir import (
    CToIRConverter,
    c_file_to_semantic_module,
    c_parameter_to_semantic_argument,
    c_project_to_semantic_module,
    c_project_to_semantic_modules,
    c_struct_to_semantic_class,
    c_type_to_semantic_type,
)
from prik.semantics.models import SemanticArgument, SemanticModule, SemanticOrigin, SemanticType
from tests.c.semantics.conversion._support import (
    _c_origin,
    _function,
)


def test_c2ir_explicit_project_headers_import_types_from_their_owner_module():
    project = parse_c_project(
        {
            "a_empty.h": "",
            "types.h": "struct state { int id; };\nvoid local_step(struct state *state);\n",
            "api.h": "struct state;\nvoid step(int count, struct state *state);\n",
        }
    )
    project.structs = {
        "ignored": CStruct(),
        "detached": CStruct(name="detached", source_location=CSourceLocation(filename="detached.h")),
        **project.structs,
    }
    modules = {module.name: module for module in c_project_to_semantic_modules(project)}
    api = modules["api"]
    state = _function(api, "step").arguments[1].semantic_type
    local_state = _function(modules["types"], "local_step").arguments[0].semantic_type
    stubs = emit_module_stubs(api, available_modules=modules.values())

    assert all(cls.name != "state" for cls in api.classes)
    assert any(cls.name == "state" for cls in modules["types"].classes)
    assert state.metadata["external_type_ref"] == {
        "name": "state",
        "local_name": "state",
        "origin_module": "types",
        "wrapped": True,
        "representation": "wrapped",
    }
    assert "external_type_ref" not in local_state.metadata
    assert "from types import state" in stubs["api"]
    assert "class state" not in stubs["api"]


def test_c2ir_classifies_external_types_after_owner_modules_without_rewriting_local_references():
    converter = CToIRConverter()
    local_reference = SemanticArgument(name="local", semantic_type=SemanticType(name="state"))
    external_reference = SemanticArgument(name="external", semantic_type=SemanticType(name="state"))
    owner_module = SemanticModule(
        name="types",
        variables=[local_reference],
        origin=SemanticOrigin(native_name="types.h"),
    )
    consumer_module = SemanticModule(
        name="api",
        variables=[external_reference],
        origin=SemanticOrigin(native_name="api.h"),
    )
    project = CProject(structs={"state": CStruct(name="state", source_location=CSourceLocation(filename="types.h"))})

    converter._classify_project_external_types([owner_module, consumer_module], project)

    assert "external_type_ref" not in local_reference.semantic_type.metadata
    assert external_reference.semantic_type.metadata["external_type_ref"] == {
        "name": "state",
        "local_name": "state",
        "origin_module": "types",
        "wrapped": True,
        "representation": "wrapped",
    }


def test_c2ir_visitor_and_project_compatibility_entrypoints_cover_supported_nodes():
    first = parse_c_file("struct point { int x; };\nint value;\nint f(int x);\n", filename="a.h")
    second = parse_c_file("double g(double y);\n", filename="b.h")
    project = CProject(
        files={"b.h": second, "a.h": first},
        functions={"f": first.functions[0], "g": second.functions[0]},
        structs={"point": first.structs[0]},
        variables={"value": first.variables[0]},
    )
    converter = CToIRConverter()

    assert [module.name for module in converter.visit(project)] == ["a", "b"]
    assert converter.visit(first).name == "a"
    assert converter.visit(first.functions[0]).name == "f"
    assert converter.visit(first.functions[0].parameters[0], position=3).metadata["native_position"] == 3
    assert converter.visit(CParameter(name=None, type=CInt())).metadata["native_position"] == 0
    assert converter.visit(first.structs[0]).name == "point"
    assert converter.visit(CUnion(name="loose_union")).name == "loose_union"
    assert converter.visit(first.variables[0]).name == "value"
    assert converter.visit(CInt()).name == "Int"
    enum_type = converter.visit(CEnum(name="status"))
    assert enum_type.name == "Int"
    assert enum_type.dtype == "Int32"
    assert enum_type.metadata["c_kind"] == "enum"
    assert enum_type.metadata["c_enum"] == "enum status"
    assert enum_type.metadata["c_enum_name"] == "status"
    assert enum_type.metadata["c_underlying_type"] == "Int"
    assert enum_type.origin.native_name == "enum status"
    assert enum_type.origin.metadata["c_type"] == "CEnum"
    with pytest.raises(TypeError) as error:
        converter.visit(object())
    assert str(error.value) == "Unsupported C parse object: <class 'object'>"

    contextual_union = CUnion(name="context_union", members=[CVariable(name="value", type=CInt())])
    contextual_file = CFile(
        filename="contextual.h",
        functions=[
            CFunction(name="contextual", result_type=CTypedef(name="contextual_t")),
            CFunction(
                name="use_context_union",
                parameters=[CParameter(name="value", type=CUnion(name="context_union", is_incomplete=True))],
            ),
        ],
        unions=[contextual_union],
    )
    contextual_module = converter.visit(
        contextual_file,
        typedefs={"contextual_t": CTypedef(name="contextual_t", type=CInt())},
        unions={"context_union": contextual_union},
    )
    assert _function(contextual_module, "contextual").return_type.name == "Int"
    assert _function(contextual_module, "use_context_union").arguments[0].semantic_type.metadata["incomplete"] is False
    assert [cls.name for cls in contextual_module.classes] == ["context_union"]

    assert c_file_to_semantic_module(first).name == "a"
    assert c_type_to_semantic_type(CInt()).name == "Int"
    assert c_parameter_to_semantic_argument(CParameter(name=None, type=CInt()), position=2).name == "arg2"
    default_argument = c_parameter_to_semantic_argument(CParameter(name=None, type=CInt()))
    assert default_argument.name == "arg0"
    assert default_argument.metadata == {"native_position": 0}
    assert c_struct_to_semantic_class(first.structs[0]).name == "point"
    assert [module.name for module in c_project_to_semantic_modules(project)] == ["a", "b"]
    merged = c_project_to_semantic_module(project, name="42 api/project")
    assert merged.name == "_42_api_project"
    assert {function.name for function in merged.functions} == {"f", "g"}
    assert [cls.name for cls in merged.classes] == ["point"]
    assert [variable.name for variable in merged.variables] == ["value"]
    assert merged.metadata == {
        "source_language": "c",
        "counts": {
            "files": 2,
            "functions": 2,
            "structs": 1,
            "unions": 0,
            "enums": 0,
            "typedefs": 0,
            "macros": 0,
            "includes": 0,
            "diagnostics": 0,
        },
    }
    assert asdict(merged.origin) == _c_origin(
        native_name="42 api/project",
        native_scope="42 api/project",
        source_kind="project",
        metadata={"files": ["a.h", "b.h"]},
    )
    assert converter.project_to_semantic_module(project).name == "c_project"
    typedef_project = parse_c_project(
        {
            "types.h": "typedef unsigned long count_t;\n",
            "api.h": "count_t count(void);\n",
        }
    )
    typedef_modules = {module.name: module for module in converter.visit(typedef_project)}
    assert _function(typedef_modules["api"], "count").return_type.name == "UInt64"
    assert _function(typedef_modules["api"], "count").return_type.metadata == {"c_typedefs": ["count_t"]}
    typedef_merged = converter.project_to_semantic_module(typedef_project)
    assert _function(typedef_merged, "count").return_type.name == "UInt64"
    assert _function(typedef_merged, "count").return_type.metadata == {"c_typedefs": ["count_t"]}
    count_reference = CTypedef(name="global_count_t")
    count_function = CFunction(name="global_count", result_type=count_reference)
    reference_project = CProject(
        files={"api.h": CFile(filename="api.h", functions=[count_function])},
        functions={"global_count": count_function},
        typedefs={"global_count_t": CTypedef(name="global_count_t", type=CInt())},
    )
    reference_modules = converter.visit(reference_project)
    assert _function(reference_modules[0], "global_count").return_type.name == "Int"
    reference_merged = converter.project_to_semantic_module(reference_project)
    assert _function(reference_merged, "global_count").return_type.name == "Int"
    record = CStruct(name="global_record", members=[CVariable(name="value", type=CInt())])
    choice = CUnion(name="global_choice", members=[CVariable(name="value", type=CInt())])
    registry_function = CFunction(
        name="use_global_types",
        parameters=[
            CParameter(name="record", type=CStruct(name="global_record", is_incomplete=True)),
            CParameter(name="choice", type=CUnion(name="global_choice", is_incomplete=True)),
        ],
    )
    registry_project = CProject(
        files={"api.h": CFile(filename="api.h", functions=[registry_function])},
        functions={"use_global_types": registry_function},
        structs={"global_record": record},
        unions={"global_choice": choice},
    )
    registry_modules = converter.visit(registry_project)
    registry_args = _function(registry_modules[0], "use_global_types").arguments
    assert registry_args[0].semantic_type.metadata == {"c_kind": "struct", "incomplete": False}
    assert registry_args[1].semantic_type.metadata["incomplete"] is False
    registry_merged = converter.project_to_semantic_module(registry_project)
    registry_merged_args = _function(registry_merged, "use_global_types").arguments
    assert [arg.semantic_type.name for arg in registry_merged_args] == [
        "global_record",
        "global_choice",
    ]
    assert [arg.semantic_type.metadata["incomplete"] for arg in registry_merged_args] == [False, False]
