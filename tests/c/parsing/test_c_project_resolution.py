"""Active coverage for current C project include/index behavior."""

from pathlib import Path


def test_project_include_graph_tracks_local_system_missing_and_cycles(tmp_path: Path):
    from x2py.parsers.c import parse_c_project

    (tmp_path / "a.h").write_text('#include "b.h"\n#include "missing.h"\n', encoding="utf-8")
    (tmp_path / "b.h").write_text('#include "a.h"\n#include <stddef.h>\n', encoding="utf-8")

    project = parse_c_project(tmp_path)

    assert project.include_graph["a.h"] == {"b.h", "missing.h"}
    assert project.include_graph["b.h"] == {"a.h"}
    assert project.system_includes["b.h"] == {"stddef.h"}
    assert project.unresolved_includes["a.h"] == {"missing.h"}
    assert any(diag.code == "C_UNRESOLVED_INCLUDE" for diag in project.files["a.h"].diagnostics)


def test_project_resolves_quoted_includes_through_include_dirs(tmp_path: Path):
    from x2py.parsers.c import parse_c_project

    include_dir = tmp_path / "include"
    src_dir = tmp_path / "src"
    include_dir.mkdir()
    src_dir.mkdir()
    types = include_dir / "types.h"
    api = src_dir / "api.h"
    types.write_text("typedef int api_int;\n", encoding="utf-8")
    api.write_text('#include "types.h"\napi_int answer(void);\n', encoding="utf-8")

    project = parse_c_project([api], include_dirs=[include_dir])

    include = project.files[str(api)].includes[0]
    assert include.target == "types.h"
    assert include.resolved_path == str(types)
    assert project.unresolved_includes[str(api)] == set()


def test_project_records_local_include_without_recursively_parsing_resolved_header(tmp_path: Path):
    from x2py.parsers.c import parse_c_project

    include_dir = tmp_path / "generated"
    include_dir.mkdir()
    generated = include_dir / "generated_types.h"
    api = tmp_path / "api.h"
    generated.write_text("typedef int generated_int;\n", encoding="utf-8")
    api.write_text('#include "generated_types.h"\nint run(void);\n', encoding="utf-8")

    project = parse_c_project([api], include_dirs=[include_dir])

    assert set(project.files) == {str(api)}
    assert project.files[str(api)].includes[0].resolved_path == str(generated)
    assert project.include_graph[str(api)] == {str(generated)}
    assert "generated_int" not in project.typedefs


def test_project_records_system_include_without_searching_or_parsing_local_copy(tmp_path: Path):
    from x2py.parsers.c import parse_c_project

    local_system_header = tmp_path / "stddef.h"
    api = tmp_path / "api.h"
    local_system_header.write_text("typedef unsigned long size_t;\n", encoding="utf-8")
    api.write_text("#include <stddef.h>\nint run(void);\n", encoding="utf-8")

    project = parse_c_project([api], include_dirs=[tmp_path])

    assert set(project.files) == {str(api)}
    assert project.files[str(api)].includes[0].resolved_path is None
    assert project.system_includes[str(api)] == {"stddef.h"}
    assert "size_t" not in project.typedefs


def test_parse_c_project_directory_discovers_preprocessed_i_files(tmp_path: Path):
    from x2py.parsers.c import parse_c_project

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


def test_project_indexes_functions_by_file_and_enum_constants(tmp_path: Path):
    from x2py.parsers.c import parse_c_project

    (tmp_path / "api.h").write_text(
        "enum status { STATUS_OK = 0, STATUS_ERROR = -1 };\nint run(void);\nint stop(void);\n",
        encoding="utf-8",
    )

    project = parse_c_project(tmp_path)

    assert project.functions_by_file["api.h"] == ["run", "stop"]
    assert set(project.enum_constants) == {"STATUS_OK", "STATUS_ERROR"}
    assert project.enum_constants["STATUS_OK"].value == "0"


def test_project_indexes_file_scope_variables(tmp_path: Path):
    from x2py.parsers.c import parse_c_project

    (tmp_path / "api.h").write_text(
        "extern int global_count;\n",
        encoding="utf-8",
    )

    project = parse_c_project(tmp_path)

    assert project.variables["global_count"].storage == ["extern"]


def test_project_function_index_prefers_definition_over_compatible_prototype(tmp_path: Path):
    from x2py.parsers.c import parse_c_project

    (tmp_path / "api.h").write_text("int solve(int value);\n", encoding="utf-8")
    (tmp_path / "api.c").write_text("int solve(int value) { return value; }\n", encoding="utf-8")

    project = parse_c_project(tmp_path)

    assert project.functions["solve"].is_definition is True
    assert project.functions["solve"].declaration_locations
    assert not any(diag.code.startswith("C_CONFLICTING") for diag in project.diagnostics)


def test_project_reports_conflicting_function_declarations(tmp_path: Path):
    from x2py.parsers.c import parse_c_project

    (tmp_path / "a.h").write_text("int work(int value);\n", encoding="utf-8")
    (tmp_path / "b.h").write_text("double work(double value);\n", encoding="utf-8")

    project = parse_c_project(tmp_path)

    assert any(diag.code == "C_CONFLICTING_FUNCTION_DECLARATION" for diag in project.diagnostics)


def test_project_resolves_typedefs_and_struct_tags_across_files(tmp_path: Path):
    from x2py.parsers.c import CComposedType, CTypedef, parse_c_project

    (tmp_path / "types.h").write_text(
        "typedef unsigned long api_size;\nstruct state { int id; };\n",
        encoding="utf-8",
    )
    (tmp_path / "api.h").write_text(
        '#include "types.h"\napi_size count(void);\nvoid step(struct state *s);\n',
        encoding="utf-8",
    )

    project = parse_c_project(tmp_path)

    assert isinstance(project.functions["count"].result_type, CTypedef)
    assert project.functions["count"].result_type is project.typedefs["api_size"]
    param_type = project.functions["step"].parameters[0].type
    assert isinstance(param_type, CComposedType)
    assert param_type.components[-1] is project.structs["state"]


def test_project_completes_forward_struct_tags_regardless_of_file_order():
    from x2py.parsers.c import CComposedType, parse_c_project

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
    from x2py.parsers.c import CComposedType, parse_c_project

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
    from x2py.parsers.c import CTypedef, CUnsignedLong, parse_c_project

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
    from x2py.parsers.c import parse_c_project

    project = parse_c_project(
        {
            "types.h": ("typedef unsigned long api_size;\nstruct packet { api_size count; };\n"),
            "api.h": "extern api_size total;\n",
        }
    )

    assert project.variables["total"].type is project.typedefs["api_size"]
    assert project.structs["packet"].members[0].type is project.typedefs["api_size"]


def test_project_reports_each_typedef_cycle_once_with_structured_diagnostic():
    from x2py.parsers.c import parse_c_project

    project = parse_c_project({"cycle.h": "typedef b a;\ntypedef a b;\n"})

    assert len(project.diagnostics) == 1
    diagnostic = project.diagnostics[0]
    assert diagnostic.code == "C_TYPEDEF_CYCLE"
    assert diagnostic.message == "Typedef cycle detected: a -> b -> a."
    assert diagnostic.severity == "error"
    assert diagnostic.location.filename == "cycle.h"
    assert diagnostic.unit_kind == "typedef"
    assert diagnostic.unit_name == "a"


def test_project_reports_prefixed_typedef_cycle_without_including_acyclic_alias():
    from x2py.parsers.c import parse_c_project

    project = parse_c_project(
        {"cycle.h": ("typedef inner_a alias;\ntypedef inner_b inner_a;\ntypedef inner_a inner_b;\n")}
    )

    cycle_diagnostics = [diagnostic for diagnostic in project.diagnostics if diagnostic.code == "C_TYPEDEF_CYCLE"]
    assert len(cycle_diagnostics) == 1
    assert cycle_diagnostics[0].message == "Typedef cycle detected: inner_a -> inner_b -> inner_a."
    assert cycle_diagnostics[0].unit_name == "inner_a"


def test_project_resolves_function_typedef_signature_references():
    from x2py.parsers.c import CComposedType, CFunctionType, parse_c_project

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


def test_project_resolves_parameter_declared_type_signature_references():
    from x2py.parsers.c import CComposedType, CFunctionType, parse_c_project

    project = parse_c_project(
        {"callbacks.h": ("typedef unsigned long api_size;\nvoid apply(api_size callback(api_size));\n")}
    )

    callback = project.functions["apply"].parameters[0]
    declared = callback.declared_type
    assert isinstance(declared, CFunctionType)
    assert declared.result_type is project.typedefs["api_size"]
    assert declared.parameter_types == [project.typedefs["api_size"]]
    assert isinstance(callback.type, CComposedType)
    assert callback.type.components[1] is declared


def test_project_resolves_parameter_declared_array_references():
    from x2py.parsers.c import CComposedType, parse_c_project

    project = parse_c_project({"arrays.h": ("typedef unsigned long api_size;\nvoid collect(api_size values[4]);\n")})

    values = project.functions["collect"].parameters[0]
    assert isinstance(values.declared_type, CComposedType)
    assert values.declared_type.components[-1] is project.typedefs["api_size"]
    assert isinstance(values.type, CComposedType)
    assert values.type.components[-1] is project.typedefs["api_size"]
    assert values.declared_type is not values.type


def test_project_reuses_typedef_cycle_state_across_resolved_use_sites():
    from x2py.parsers.c import parse_c_project

    project = parse_c_project(
        {
            "cycle_uses.h": (
                "typedef b a;\n"
                "typedef a b;\n"
                "typedef a (*cycle_callback)(a);\n"
                "a get_value(void);\n"
                "void set_value(a value);\n"
                "extern a *global_value;\n"
                "struct packet { a field; };\n"
            )
        }
    )

    assert [diagnostic.code for diagnostic in project.diagnostics].count("C_TYPEDEF_CYCLE") == 1


def test_project_resolves_union_and_enum_tag_references(tmp_path: Path):
    from x2py.parsers.c import CComposedType, parse_c_project

    (tmp_path / "types.h").write_text(
        "union value { int i; };\nenum status { STATUS_OK = 0 };\n",
        encoding="utf-8",
    )
    (tmp_path / "api.h").write_text(
        "void set_value(union value *v);\nenum status current_status(void);\n",
        encoding="utf-8",
    )

    project = parse_c_project(tmp_path)

    value_type = project.functions["set_value"].parameters[0].type
    assert isinstance(value_type, CComposedType)
    assert value_type.components[-1] is project.unions["value"]
    assert project.functions["current_status"].result_type is project.enums["status"]


def test_project_resolves_opaque_pointer_typedefs_across_files(tmp_path: Path):
    from x2py.parsers.c import CComposedType, CTypedef, parse_c_project

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


def test_project_preserves_unresolved_type_references_for_later_diagnostics():
    from x2py.parsers.c import CTypedef, parse_c_project

    project = parse_c_project({"api.h": "missing_type value(void);\n"})

    assert isinstance(project.functions["value"].result_type, CTypedef)
    assert project.functions["value"].result_type.name == "missing_type"
    assert project.functions["value"].result_type.type is None


def test_project_preserves_unresolved_tag_references_for_later_diagnostics():
    from x2py.parsers.c import CComposedType, CEnum, CStruct, CUnion, parse_c_project

    project = parse_c_project(
        {"api.h": ("struct missing *get_struct(void);\nunion absent *get_union(void);\nenum unknown get_enum(void);\n")}
    )

    struct_type = project.functions["get_struct"].result_type
    union_type = project.functions["get_union"].result_type
    enum_type = project.functions["get_enum"].result_type
    assert isinstance(struct_type, CComposedType)
    assert isinstance(struct_type.components[-1], CStruct)
    assert struct_type.components[-1].name == "missing"
    assert isinstance(union_type, CComposedType)
    assert isinstance(union_type.components[-1], CUnion)
    assert union_type.components[-1].name == "absent"
    assert isinstance(enum_type, CEnum)
    assert enum_type.name == "unknown"


def test_project_header_source_pairs_use_matching_stems_and_direct_includes(tmp_path: Path):
    from x2py.parsers.c import parse_c_project

    (tmp_path / "solver.h").write_text("int solve(void);\n", encoding="utf-8")
    (tmp_path / "solver.c").write_text('#include "solver.h"\n', encoding="utf-8")
    (tmp_path / "driver.h").write_text("int drive(void);\n", encoding="utf-8")
    (tmp_path / "main.c").write_text('#include "driver.h"\n', encoding="utf-8")

    project = parse_c_project(tmp_path)

    assert project.header_source_pairs["solver.h"] == {"solver.c"}
    assert project.header_source_pairs["driver.h"] == {"main.c"}


def test_project_header_source_pairs_preserve_many_to_many_relationships(tmp_path: Path):
    from x2py.parsers.c import parse_c_project

    (tmp_path / "a.h").write_text("int a(void);\n", encoding="utf-8")
    (tmp_path / "b.h").write_text("int b(void);\n", encoding="utf-8")
    (tmp_path / "one.c").write_text('#include "a.h"\n#include "b.h"\n', encoding="utf-8")
    (tmp_path / "two.c").write_text('#include "a.h"\n', encoding="utf-8")

    project = parse_c_project(tmp_path)

    assert project.header_source_pairs["a.h"] == {"one.c", "two.c"}
    assert project.header_source_pairs["b.h"] == {"one.c"}


def test_project_serialization_keeps_include_indexes_json_stable(tmp_path: Path):
    from x2py.parsers.c import parse_c_project

    (tmp_path / "api.h").write_text("#include <stddef.h>\nint run(void);\n", encoding="utf-8")

    payload = parse_c_project(tmp_path).to_dict()

    assert payload["include_graph"] == {"api.h": []}
    assert payload["system_includes"] == {"api.h": ["stddef.h"]}
    assert payload["functions_by_file"] == {"api.h": ["run"]}
