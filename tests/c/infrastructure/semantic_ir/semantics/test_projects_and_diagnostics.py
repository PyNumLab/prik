"""C project semantic IR: cross-header type ownership and project-wide type resolution."""

from prik.pipeline.pyi import emit_module_stubs
from prik.parsers.c import parse_c_project
from prik.parsers.c.models import (
    CSourceLocation,
    CStruct,
)
from prik.semantics.c2ir import (
    c_project_to_semantic_modules,
)
from tests.c._support.semantic_conversion import (
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
    assert "from .types import state" in stubs["api"]
    assert "class state" not in stubs["api"]


def test_c2ir_resolves_typedefs_and_forward_tags_through_the_project_registry():
    """A header that only forward-declares a tag or names a typedef sees the owner's definition."""
    project = parse_c_project(
        {
            "types.h": (
                "typedef unsigned long count_t;\nstruct record { int value; };\nunion choice { int value; };\n"
            ),
            "api.h": (
                "struct record;\nunion choice;\ncount_t count(void);\n"
                "void use(struct record *record, union choice *choice);\n"
            ),
        }
    )

    api = {module.name: module for module in c_project_to_semantic_modules(project)}["api"]
    count = _function(api, "count").return_type
    record, choice = (argument.semantic_type for argument in _function(api, "use").arguments)

    assert count.name == "UInt64"
    assert count.metadata == {"c_typedefs": ["count_t"]}
    assert (record.metadata["c_kind"], record.metadata["incomplete"]) == ("struct", False)
    assert (choice.metadata["c_kind"], choice.metadata["incomplete"]) == ("union", False)
