"""Active coverage for current C project include/index behavior."""

from pathlib import Path

import pytest


def test_project_include_graph_tracks_local_system_missing_and_cycles(tmp_path: Path):
    from prik.parsers.c import parse_c_project

    (tmp_path / "a.h").write_text('#include "b.h"\n#include "missing.h"\n', encoding="utf-8")
    (tmp_path / "b.h").write_text('#include "a.h"\n#include <stddef.h>\n', encoding="utf-8")

    project = parse_c_project(tmp_path)

    assert project.include_graph["a.h"] == {"b.h", "missing.h"}
    assert project.include_graph["b.h"] == {"a.h"}
    assert project.system_includes["b.h"] == {"stddef.h"}
    assert project.unresolved_includes["a.h"] == {"missing.h"}
    assert any(diag.code == "C_UNRESOLVED_INCLUDE" for diag in project.files["a.h"].diagnostics)


def test_project_resolves_quoted_includes_through_include_dirs_without_parsing_them(tmp_path: Path):
    """A quoted include resolves through ``include_dirs``; a system include is only recorded.

    Neither header is parsed into the project: the resolved local header is an
    edge in the include graph, and a local file shadowing a system header is
    neither searched for nor read.
    """
    from prik.parsers.c import parse_c_project

    include_dir = tmp_path / "include"
    src_dir = tmp_path / "src"
    include_dir.mkdir()
    src_dir.mkdir()
    types = include_dir / "types.h"
    api = src_dir / "api.h"
    types.write_text("typedef int api_int;\n", encoding="utf-8")
    (include_dir / "stddef.h").write_text("typedef unsigned long size_t;\n", encoding="utf-8")
    api.write_text('#include "types.h"\n#include <stddef.h>\napi_int answer(void);\n', encoding="utf-8")

    project = parse_c_project([api], include_dirs=[include_dir])

    quoted, system = project.files[str(api)].includes
    assert (quoted.target, quoted.resolved_path) == ("types.h", str(types))
    assert (system.target, system.resolved_path) == ("stddef.h", None)
    assert set(project.files) == {str(api)}
    assert project.include_graph[str(api)] == {str(types)}
    assert project.system_includes[str(api)] == {"stddef.h"}
    assert project.unresolved_includes[str(api)] == set()
    assert "api_int" not in project.typedefs
    assert "size_t" not in project.typedefs


def test_parse_c_project_directory_discovers_preprocessed_i_files(tmp_path: Path):
    from prik.parsers.c import parse_c_project

    (tmp_path / "api.c").write_text("int from_source(void);\n", encoding="utf-8")
    (tmp_path / "generated.i").write_text(
        '# 8 "include/generated_api.h"\nint generated(void);\n',
        encoding="utf-8",
    )

    project = parse_c_project(tmp_path)

    assert set(project.files) == {"api.c", "generated.i"}
    generated = project.files["generated.i"]
    assert generated.preprocessing == "preprocessed"
    assert generated.preprocessed_source_path == "generated.i"
    assert generated.original_source_paths == ["include/generated_api.h"]
    assert generated.functions[0].origin == "preprocessed"
    assert generated.functions[0].source_location.filename == "include/generated_api.h"
    assert generated.functions[0].source_location.line == 8
    assert "origin" not in generated.to_dict()["functions"][0]


def test_project_function_index_prefers_definition_over_compatible_prototype(tmp_path: Path):
    from prik.parsers.c import parse_c_project

    (tmp_path / "api.h").write_text("int solve(int value);\n", encoding="utf-8")
    (tmp_path / "api.c").write_text("int solve(int value) { return value; }\n", encoding="utf-8")

    project = parse_c_project(tmp_path)

    assert project.functions["solve"].is_definition is True
    assert project.functions["solve"].declaration_locations
    assert not any(diag.code.startswith("C_CONFLICTING") for diag in project.diagnostics)


def test_project_reports_conflicting_function_declarations(tmp_path: Path):
    from prik.parsers.c import parse_c_project

    (tmp_path / "a.h").write_text("int work(int value);\n", encoding="utf-8")
    (tmp_path / "b.h").write_text("double work(double value);\n", encoding="utf-8")

    project = parse_c_project(tmp_path)

    assert any(diag.code == "C_CONFLICTING_FUNCTION_DECLARATION" for diag in project.diagnostics)


def test_project_completes_forward_struct_tags_regardless_of_file_order():
    from prik.parsers.c import CComposedType, parse_c_project

    project = parse_c_project(
        {
            "forward.h": "struct state;\nvoid step(struct state *s);\n",
            "definition.h": "struct state { int id; };\n",
        }
    )

    assert project.structs["state"].is_incomplete is False
    assert project.structs["state"].members[0].name == "id"
    param_type = project.functions["step"].parameters[0].type
    assert isinstance(param_type, CComposedType)
    assert param_type.components[-1] is project.structs["state"]


def test_project_keeps_complete_union_definition_when_forward_seen_later():
    from prik.parsers.c import CComposedType, parse_c_project

    project = parse_c_project(
        {
            "definition.h": "union value { int i; };\n",
            "forward.h": "union value;\nvoid set_value(union value *v);\n",
        }
    )

    assert project.unions["value"].is_incomplete is False
    assert project.unions["value"].members[0].name == "i"
    param_type = project.functions["set_value"].parameters[0].type
    assert isinstance(param_type, CComposedType)
    assert param_type.components[-1] is project.unions["value"]


def test_project_resolves_typedef_chains_while_preserving_alias_objects(tmp_path: Path):
    from prik.parsers.c import CTypedef, CUnsignedLong, parse_c_project

    (tmp_path / "types.h").write_text(
        "typedef unsigned long raw_size;\ntypedef raw_size api_size;\n",
        encoding="utf-8",
    )
    (tmp_path / "api.h").write_text("api_size count(void);\n", encoding="utf-8")

    project = parse_c_project(tmp_path)

    assert project.typedefs["api_size"].type is project.typedefs["raw_size"]
    assert isinstance(project.typedefs["raw_size"].type, CUnsignedLong)
    assert isinstance(project.functions["count"].result_type, CTypedef)
    assert project.functions["count"].result_type is project.typedefs["api_size"]
    assert project.functions["count"].result_type.source_text == "api_size"


def test_project_resolves_typedefs_for_variables_and_aggregate_members():
    from prik.parsers.c import parse_c_project

    project = parse_c_project(
        {
            "types.h": ("typedef unsigned long api_size;\nstruct packet { api_size count; };\n"),
            "api.h": "extern api_size total;\n",
        }
    )

    assert project.variables["total"].type is project.typedefs["api_size"]
    assert project.structs["packet"].members[0].type is project.typedefs["api_size"]


def test_project_resolves_function_typedef_signature_references():
    from prik.parsers.c import CComposedType, CFunctionType, parse_c_project

    project = parse_c_project(
        {
            "callbacks.h": (
                "typedef unsigned long api_size;\n"
                "typedef api_size (*measure_fn)(api_size);\n"
                "measure_fn select_measure(void);\n"
            )
        }
    )

    callback_type = project.typedefs["measure_fn"].type
    assert isinstance(callback_type, CComposedType)
    signature = callback_type.components[1]
    assert isinstance(signature, CFunctionType)
    assert signature.result_type is project.typedefs["api_size"]
    assert signature.parameter_types == [project.typedefs["api_size"]]
    assert project.functions["select_measure"].result_type is project.typedefs["measure_fn"]


def test_project_resolves_opaque_pointer_typedefs_across_files(tmp_path: Path):
    from prik.parsers.c import CComposedType, CTypedef, parse_c_project

    (tmp_path / "types.h").write_text(
        "struct handle;\ntypedef struct handle *handle_t;\n",
        encoding="utf-8",
    )
    (tmp_path / "api.h").write_text("handle_t open_handle(void);\n", encoding="utf-8")

    project = parse_c_project(tmp_path)

    assert project.typedefs["handle_t"].type.components[-1] is project.structs["handle"]
    assert project.structs["handle"].is_incomplete is True
    assert isinstance(project.functions["open_handle"].result_type, CTypedef)
    assert project.functions["open_handle"].result_type is project.typedefs["handle_t"]
    assert isinstance(project.typedefs["handle_t"].type, CComposedType)


def test_project_serialization_keeps_include_indexes_json_stable(tmp_path: Path):
    from prik.parsers.c import parse_c_project

    (tmp_path / "api.h").write_text("#include <stddef.h>\nint run(void);\n", encoding="utf-8")

    payload = parse_c_project(tmp_path).to_dict()

    assert payload["include_graph"] == {"api.h": []}
    assert payload["system_includes"] == {"api.h": ["stddef.h"]}
    assert payload["functions_by_file"] == {"api.h": ["run"]}


def test_project_indexes_functions_by_file_enum_constants_and_variables(tmp_path: Path):
    from prik.parsers.c import parse_c_project

    (tmp_path / "api.h").write_text(
        "enum status { STATUS_OK = 0, STATUS_ERROR = -1 };\nint run(void);\nint stop(void);\nextern int global_count;\n",
        encoding="utf-8",
    )

    project = parse_c_project(tmp_path)

    assert project.functions_by_file["api.h"] == ["run", "stop"]
    assert set(project.enum_constants) == {"STATUS_OK", "STATUS_ERROR"}
    assert project.enum_constants["STATUS_OK"].value == "0"
    assert project.variables["global_count"].storage == ["extern"]


def test_project_resolves_typedefs_and_struct_union_enum_tags_across_files(tmp_path: Path):
    from prik.parsers.c import CComposedType, CTypedef, parse_c_project

    (tmp_path / "types.h").write_text(
        "typedef unsigned long api_size;\nstruct state { int id; };\nunion value { int i; };\n"
        "enum status { STATUS_OK = 0 };\n",
        encoding="utf-8",
    )
    (tmp_path / "api.h").write_text(
        '#include "types.h"\napi_size count(void);\nvoid step(struct state *s);\n'
        "void set_value(union value *v);\nenum status current_status(void);\n",
        encoding="utf-8",
    )

    project = parse_c_project(tmp_path)

    assert isinstance(project.functions["count"].result_type, CTypedef)
    assert project.functions["count"].result_type is project.typedefs["api_size"]
    for function, tag in (("step", project.structs["state"]), ("set_value", project.unions["value"])):
        param_type = project.functions[function].parameters[0].type
        assert isinstance(param_type, CComposedType)
        assert param_type.components[-1] is tag
    assert project.functions["current_status"].result_type is project.enums["status"]


def test_project_resolves_typedefs_inside_adjusted_parameter_declarations():
    from prik.parsers.c import CComposedType, CFunctionType, parse_c_project

    project = parse_c_project(
        {
            "callbacks.h": (
                "typedef unsigned long api_size;\n"
                "void apply(api_size callback(api_size));\n"
                "void collect(api_size values[4]);\n"
            )
        }
    )
    api_size = project.typedefs["api_size"]

    callback = project.functions["apply"].parameters[0]
    assert isinstance(callback.declared_type, CFunctionType)
    assert callback.declared_type.result_type is api_size
    assert callback.declared_type.parameter_types == [api_size]
    assert isinstance(callback.type, CComposedType)
    assert callback.type.components[1] is callback.declared_type

    values = project.functions["collect"].parameters[0]
    assert values.declared_type.components[-1] is api_size
    assert values.type.components[-1] is api_size
    assert values.declared_type is not values.type


@pytest.mark.parametrize(
    ("source", "message", "unit_name"),
    [
        pytest.param(
            "typedef b a;\ntypedef a b;\n", "Typedef cycle detected: a -> b -> a.", "a", id="two-typedef-cycle"
        ),
        pytest.param(
            "typedef inner_a alias;\ntypedef inner_b inner_a;\ntypedef inner_a inner_b;\n",
            "Typedef cycle detected: inner_a -> inner_b -> inner_a.",
            "inner_a",
            id="acyclic-alias-into-a-cycle-is-not-part-of-it",
        ),
        pytest.param(
            "typedef b a;\ntypedef a b;\ntypedef a (*cycle_callback)(a);\na get_value(void);\n"
            "void set_value(a value);\nextern a *global_value;\nstruct packet { a field; };\n",
            "Typedef cycle detected: a -> b -> a.",
            "a",
            id="every-use-site-reuses-one-cycle-report",
        ),
    ],
)
def test_project_reports_each_typedef_cycle_once_with_structured_diagnostic(source, message, unit_name):
    from prik.parsers.c import parse_c_project

    project = parse_c_project({"cycle.h": source})

    cycles = [diagnostic for diagnostic in project.diagnostics if diagnostic.code == "C_TYPEDEF_CYCLE"]
    assert len(cycles) == 1
    assert cycles[0].message == message
    assert cycles[0].severity == "error"
    assert cycles[0].location.filename == "cycle.h"
    assert cycles[0].unit_kind == "typedef"
    assert cycles[0].unit_name == unit_name


def test_project_preserves_unresolved_type_and_tag_references_for_later_diagnostics():
    from prik.parsers.c import CComposedType, CEnum, CStruct, CTypedef, CUnion, parse_c_project

    project = parse_c_project(
        {
            "api.h": (
                "missing_type value(void);\nstruct missing *get_struct(void);\n"
                "union absent *get_union(void);\nenum unknown get_enum(void);\n"
            )
        }
    )

    missing = project.functions["value"].result_type
    assert isinstance(missing, CTypedef)
    assert (missing.name, missing.type) == ("missing_type", None)
    for function, model, name in (("get_struct", CStruct, "missing"), ("get_union", CUnion, "absent")):
        result = project.functions[function].result_type
        assert isinstance(result, CComposedType)
        assert isinstance(result.components[-1], model)
        assert result.components[-1].name == name
    enum_type = project.functions["get_enum"].result_type
    assert isinstance(enum_type, CEnum)
    assert enum_type.name == "unknown"


def test_project_header_source_pairs_use_matching_stems_and_direct_includes(tmp_path: Path):
    from prik.parsers.c import parse_c_project

    (tmp_path / "solver.h").write_text("int solve(void);\n", encoding="utf-8")
    (tmp_path / "solver.c").write_text('#include "solver.h"\n', encoding="utf-8")
    (tmp_path / "driver.h").write_text("int drive(void);\n", encoding="utf-8")
    (tmp_path / "shared.h").write_text("int shared(void);\n", encoding="utf-8")
    (tmp_path / "main.c").write_text('#include "driver.h"\n#include "shared.h"\n', encoding="utf-8")
    (tmp_path / "tool.c").write_text('#include "shared.h"\n', encoding="utf-8")

    project = parse_c_project(tmp_path)

    assert project.header_source_pairs["solver.h"] == {"solver.c"}
    assert project.header_source_pairs["driver.h"] == {"main.c"}
    # One header can pair with many sources, and one source with many headers.
    assert project.header_source_pairs["shared.h"] == {"main.c", "tool.c"}
