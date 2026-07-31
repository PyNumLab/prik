"""Tests split by stable ownership concept from `test_compile_time_values.py`."""

from tests.fortran._support.semantic_conversion import (
    FortranArgument,
    FortranBlockData,
    FortranDerivedType,
    FortranFile,
    FortranModule,
    FortranProcedureSignature,
    FortranProgram,
    FortranProject,
    FortranSubmodule,
    FortranVariable,
    ProjectionMapping,
    SemanticArgument,
    SemanticClass,
    SemanticFunction,
    SemanticMethod,
    SemanticModule,
    SemanticType,
    _compile_time_requirement_message,
    _iter_fortran_variable_contexts,
    collect_semantic_compile_time_requirements,
    fortran_file_to_semantic_modules,
    fortran_module_to_semantic_module,
    fortran_project_to_semantic_modules,
    get_function,
    parse_fortran_source,
    pytest,
    resolve_semantic_compile_time_values,
    semantic_models,
)


def test_semantic_compile_time_requirements_can_be_supplied_for_kind_selection():
    source = """
module solver_mod
  integer, parameter :: rk = selected_real_kind(12)
contains
subroutine scale(x)
  real(kind=rk), intent(inout) :: x
end subroutine scale
end module solver_mod
"""
    parsed = parse_fortran_source(source)

    with pytest.raises(ValueError, match="Unsupported Fortran semantic type"):
        fortran_module_to_semantic_module(parsed)

    requirements = collect_semantic_compile_time_requirements(parsed)
    assert {(item["code"], item["symbol"], item["expression"]) for item in requirements} >= {
        ("parameter_value", "rk", "selected_real_kind(12)"),
        ("unsupported_kind", "x", "selected_real_kind(12)"),
    }

    module = fortran_module_to_semantic_module(
        parsed,
        compile_time_values={"selected_real_kind(12)": 8},
    )
    arg_type = get_function(module, "scale").arguments[0].semantic_type
    assert arg_type.name == "Float64"


def test_semantic_compile_time_requirements_cover_all_parser_contexts():
    proc = FortranProcedureSignature(
        name="step",
        kind="function",
        module="solver_mod",
        arguments=[FortranArgument(name="x", base_type="real", kind="rk")],
        result=FortranArgument(name="r", base_type="real", kind="rk"),
        variables={
            "scratch": FortranVariable(name="scratch", base_type="real", kind="rk"),
        },
    )
    dtype = FortranDerivedType(
        name="state_t",
        module="solver_mod",
        fields=[FortranArgument(name="mass", base_type="real", kind="rk")],
    )
    parsed = FortranFile(
        variables=[FortranVariable(name="file_param", base_type="integer", is_parameter=True, symbolic_value="n + 1")],
        modules=[
            FortranModule(
                name="solver_mod",
                variables=[
                    FortranVariable(
                        name="rk", base_type="integer", is_parameter=True, symbolic_value="selected_real_kind(12)"
                    ),
                    FortranVariable(name="scale", base_type="real", kind="rk"),
                ],
                procedures=[proc],
                derived_types=[dtype],
            )
        ],
        submodules=[
            FortranSubmodule(
                name="solver_child",
                parent="solver_mod",
                variables=[FortranVariable(name="child_scale", base_type="real", kind="rk")],
                procedures=[
                    FortranProcedureSignature(
                        name="child_step",
                        kind="subroutine",
                        arguments=[FortranArgument(name="y", base_type="real", kind="rk")],
                    )
                ],
                derived_types=[
                    FortranDerivedType(
                        name="child_t", fields=[FortranArgument(name="value", base_type="real", kind="rk")]
                    )
                ],
            )
        ],
        programs=[
            FortranProgram(
                variables=[FortranVariable(name="program_scale", base_type="real", kind="rk")],
                procedures=[
                    FortranProcedureSignature(
                        name="program_step",
                        kind="subroutine",
                        arguments=[FortranArgument(name="z", base_type="real", kind="rk")],
                    )
                ],
            )
        ],
        block_data_units=[
            FortranBlockData(variables=[FortranVariable(name="saved_scale", base_type="real", kind="rk")])
        ],
        procedures=[
            FortranProcedureSignature(
                name="free_step", kind="subroutine", arguments=[FortranArgument(name="q", base_type="real", kind="rk")]
            )
        ],
        derived_types=[
            FortranDerivedType(name="free_t", fields=[FortranArgument(name="payload", base_type="real", kind="rk")])
        ],
    )

    contexts = {var.name: ctx for var, ctx in _iter_fortran_variable_contexts(parsed)}
    requirements = collect_semantic_compile_time_requirements(parsed)
    supplied = collect_semantic_compile_time_requirements(
        parsed,
        compile_time_values={"rk": 8, "selected_real_kind(12)": 8, "n": 2},
    )

    assert contexts == {
        "file_param": {
            "unit_kind": "file",
            "unit": "<source>",
            "module": None,
            "symbol": "file_param",
            "role": "variable",
        },
        "rk": {
            "unit_kind": "module",
            "unit": "solver_mod",
            "module": "solver_mod",
            "symbol": "rk",
            "role": "variable",
        },
        "scale": {
            "unit_kind": "module",
            "unit": "solver_mod",
            "module": "solver_mod",
            "symbol": "scale",
            "role": "variable",
        },
        "x": {
            "unit_kind": "procedure",
            "unit": "solver_mod.step",
            "module": "solver_mod",
            "procedure": "step",
            "symbol": "x",
            "role": "argument",
        },
        "r": {
            "unit_kind": "procedure",
            "unit": "solver_mod.step",
            "module": "solver_mod",
            "procedure": "step",
            "symbol": "r",
            "role": "result",
        },
        "scratch": {
            "unit_kind": "procedure",
            "unit": "solver_mod.step",
            "module": "solver_mod",
            "procedure": "step",
            "symbol": "scratch",
            "role": "variable",
        },
        "mass": {
            "unit_kind": "derived_type",
            "unit": "solver_mod.state_t",
            "module": "solver_mod",
            "type_owner": "state_t",
            "symbol": "mass",
            "role": "field",
        },
        "child_scale": {
            "unit_kind": "submodule",
            "unit": "solver_child",
            "module": "solver_child",
            "symbol": "child_scale",
            "role": "variable",
        },
        "y": {
            "unit_kind": "procedure",
            "unit": "solver_child.child_step",
            "module": "solver_child",
            "procedure": "child_step",
            "symbol": "y",
            "role": "argument",
        },
        "value": {
            "unit_kind": "derived_type",
            "unit": "solver_child.child_t",
            "module": "solver_child",
            "type_owner": "child_t",
            "symbol": "value",
            "role": "field",
        },
        "program_scale": {
            "unit_kind": "program",
            "unit": "<program>",
            "module": None,
            "symbol": "program_scale",
            "role": "variable",
        },
        "z": {
            "unit_kind": "procedure",
            "unit": "program_step",
            "module": None,
            "procedure": "program_step",
            "symbol": "z",
            "role": "argument",
        },
        "saved_scale": {
            "unit_kind": "block_data",
            "unit": "<block_data>",
            "module": None,
            "symbol": "saved_scale",
            "role": "variable",
        },
        "q": {
            "unit_kind": "procedure",
            "unit": "free_step",
            "module": None,
            "procedure": "free_step",
            "symbol": "q",
            "role": "argument",
        },
        "payload": {
            "unit_kind": "derived_type",
            "unit": "free_t",
            "module": None,
            "type_owner": "free_t",
            "symbol": "payload",
            "role": "field",
        },
    }
    assert {"file", "module", "submodule", "program", "block_data", "procedure", "derived_type"} <= {
        ctx["unit_kind"] for ctx in contexts.values()
    }
    assert {ctx["role"] for ctx in contexts.values()} >= {"variable", "argument", "result", "field"}
    assert ("parameter_value", "rk", "selected_real_kind(12)") in {
        (item["code"], item["symbol"], item["expression"]) for item in requirements
    }
    assert any(item["code"] == "unsupported_kind" and item["symbol"] == "scale" for item in requirements)
    by_symbol = {(item["code"], item["symbol"]): item for item in requirements}
    assert by_symbol[("parameter_value", "rk")] == {
        "code": "parameter_value",
        "unit_kind": "module",
        "unit": "solver_mod",
        "module": "solver_mod",
        "procedure": None,
        "type_owner": None,
        "role": "variable",
        "symbol": "rk",
        "base_type": None,
        "kind": None,
        "expression": "selected_real_kind(12)",
        "message": "Parameter 'rk' needs a compile-time value for expression 'selected_real_kind(12)'.",
    }
    assert by_symbol[("unsupported_kind", "mass")] == {
        "code": "unsupported_kind",
        "unit_kind": "derived_type",
        "unit": "solver_mod.state_t",
        "module": "solver_mod",
        "procedure": None,
        "type_owner": "state_t",
        "role": "field",
        "symbol": "mass",
        "base_type": "real",
        "kind": "rk",
        "expression": "rk",
        "message": "Kind expression for 'mass' needs a supported compile-time value.",
    }
    assert by_symbol[("unsupported_kind", "x")]["procedure"] == "step"
    assert supplied == []
    assert (
        collect_semantic_compile_time_requirements(
            FortranFile(variables=[FortranVariable(name="custom", base_type="real", kind="rk")]),
            type_map={("real", "rk"): "FloatCustom"},
        )
        == []
    )
    assert (
        collect_semantic_compile_time_requirements(
            FortranFile(variables=[FortranVariable(name="runtime", base_type="integer", value="n + 1")])
        )
        == []
    )
    assert (
        collect_semantic_compile_time_requirements(
            FortranFile(
                variables=[
                    FortranVariable(
                        name="half",
                        base_type="real",
                        is_parameter=True,
                        symbolic_value="0.5_sp",
                    ),
                    FortranVariable(
                        name="czero",
                        base_type="complex",
                        is_parameter=True,
                        symbolic_value="(0.0_sp, 0.0_sp)",
                    ),
                ]
            )
        )
        == []
    )
    assert (
        collect_semantic_compile_time_requirements(
            FortranFile(
                variables=[
                    FortranVariable(
                        name="provided",
                        base_type="integer",
                        is_parameter=True,
                        symbolic_value="external_value()",
                    )
                ]
            ),
            compile_time_values={"provided": 4},
        )
        == []
    )
    unsupported = collect_semantic_compile_time_requirements(
        FortranFile(
            variables=[
                FortranVariable(name="bad_integer", base_type="integer", kind="bad"),
                FortranVariable(name="bad_real", base_type="real", kind="bad"),
                FortranVariable(name="bad_complex", base_type="complex", kind="bad"),
                FortranVariable(name="bad_logical", base_type="logical", kind="bad"),
                FortranVariable(name="bad_character", base_type="character", kind="bad"),
                FortranVariable(name="callback", base_type="procedure", kind="f_iface"),
            ]
        )
    )
    assert {item["symbol"] for item in unsupported} == {
        "bad_integer",
        "bad_real",
        "bad_complex",
        "bad_logical",
        "bad_character",
    }
    resolved_kind = collect_semantic_compile_time_requirements(
        FortranFile(variables=[FortranVariable(name="resolved_bad", base_type="real", kind="rk + 1")]),
        compile_time_values={"rk": 8},
    )
    assert resolved_kind[0]["expression"] == "8 + 1"
    named_contexts = {
        var.name: ctx
        for var, ctx in _iter_fortran_variable_contexts(
            FortranFile(
                filename="units.f90",
                variables=[FortranVariable(name="file_named")],
                programs=[FortranProgram(name="driver", variables=[FortranVariable(name="program_named")])],
                block_data_units=[FortranBlockData(name="saved", variables=[FortranVariable(name="block_named")])],
            )
        )
    }
    assert named_contexts["file_named"]["unit"] == "units.f90"
    assert named_contexts["program_named"]["unit"] == "driver"
    assert named_contexts["block_named"]["unit"] == "saved"
    assert _compile_time_requirement_message("other", "n", "n + 1") == "Compile-time value required for 'n'."


def test_resolve_semantic_compile_time_values_rewrites_shapes_and_constraints():
    module = SemanticModule(
        name="shape_mod",
        variables=[
            SemanticArgument(
                name="values",
                semantic_type=SemanticType(
                    name="Float64",
                    dtype="Float64",
                    rank=1,
                    shape=["1:n"],
                    storage=semantic_models.SemanticStorageContract(
                        kind="array",
                        array=semantic_models.SemanticArrayContract(
                            rank=1,
                            shape=["1:n"],
                            source_shape=["1:n"],
                        ),
                    ),
                ),
            )
        ],
    )

    resolved = resolve_semantic_compile_time_values(module, {"n": 8})

    assert module.variables[0].semantic_type.shape == ["1:n"]
    assert resolved.variables[0].semantic_type.shape == ["1:8"]
    assert resolved.variables[0].semantic_type.storage.array.shape == ["1:8"]


def test_resolve_semantic_compile_time_values_handles_nested_modules():
    module = SemanticModule(
        name="nested_mod",
        variables=[
            SemanticArgument(
                name="values",
                semantic_type=SemanticType(
                    name="Float64",
                    dtype="Float64",
                    rank=1,
                    shape=["n"],
                    storage=semantic_models.SemanticStorageContract(
                        kind="array",
                        array=semantic_models.SemanticArrayContract(
                            rank=1,
                            shape=["n"],
                            source_shape=["1:n"],
                            lower_bounds=["n"],
                            upper_bounds=["n"],
                        ),
                    ),
                    metadata={"bounds": ("n", ["m"])},
                ),
                default_value="n",
                metadata={"alias": "m"},
            )
        ],
        functions=[
            SemanticFunction(
                name="step",
                arguments=[
                    SemanticArgument(
                        name="x",
                        semantic_type=SemanticType("Float64", rank=1, shape=["m"]),
                        metadata={"scale": "n"},
                    )
                ],
                projection=[ProjectionMapping(value={"shape": ["n", ("m",)]})],
                metadata={"work": ["n", {"inner": "m"}]},
            ),
            SemanticFunction(
                name="with_result",
                return_type=SemanticType("Int32", metadata={"extent": "n"}),
            ),
        ],
        classes=[
            SemanticClass(
                name="state_t",
                fields=[
                    SemanticArgument(
                        name="field",
                        semantic_type=SemanticType("Float64", shape=["n"]),
                        default_value="m",
                    )
                ],
                methods=[
                    SemanticMethod(
                        name="touch",
                        arguments=[SemanticArgument("self", SemanticType("state_t", metadata={"n": "n"}))],
                        return_type=SemanticType("Int32", metadata={"m": "m"}),
                        projection=[ProjectionMapping(value=("n", {"m": "m"}))],
                        metadata={"method": "n"},
                    )
                ],
                metadata={"class": "m"},
            )
        ],
        metadata={"module": ["n", ("m",)]},
    )

    resolved = resolve_semantic_compile_time_values([module], {"n": 4, "m": 2})

    assert module.variables[0].semantic_type.shape == ["n"]
    resolved_module = resolved[0]
    assert resolved_module.variables[0].semantic_type.shape == ["4"]
    assert resolved_module.variables[0].semantic_type.storage.array.shape == ["4"]
    assert resolved_module.variables[0].semantic_type.storage.array.source_shape == ["1:4"]
    assert resolved_module.variables[0].semantic_type.storage.array.lower_bounds == ["4"]
    assert resolved_module.variables[0].semantic_type.storage.array.upper_bounds == ["4"]
    assert resolved_module.variables[0].semantic_type.metadata == {"bounds": ("4", ["2"])}
    assert resolved_module.variables[0].default_value == "4"
    assert resolved_module.variables[0].metadata == {"alias": "2"}
    assert resolved_module.functions[0].arguments[0].semantic_type.shape == ["2"]
    assert resolved_module.functions[0].arguments[0].metadata == {"scale": "4"}
    assert resolved_module.functions[0].projection[0].value == {"shape": ["4", ("2",)]}
    assert resolved_module.functions[0].metadata == {"work": ["4", {"inner": "2"}]}
    assert resolved_module.functions[1].return_type.metadata == {"extent": "4"}
    assert resolved_module.classes[0].fields[0].semantic_type.shape == ["4"]
    assert resolved_module.classes[0].fields[0].default_value == "2"
    assert resolved_module.classes[0].methods[0].arguments[0].semantic_type.metadata == {"n": "4"}
    assert resolved_module.classes[0].methods[0].return_type.metadata == {"m": "2"}
    assert resolved_module.classes[0].methods[0].projection[0].value == ("4", {"m": "2"})
    assert resolved_module.classes[0].methods[0].metadata == {"method": "4"}
    assert resolved_module.classes[0].metadata == {"class": "2"}
    assert resolved_module.metadata == {"module": ["4", ("2",)]}


def test_module_parameters_preserve_literal_values_in_semantic_ir():
    source = """
module constants_mod
  integer, parameter :: nmax = 12
end module constants_mod
"""

    module = fortran_module_to_semantic_module(parse_fortran_source(source))

    assert module.variables[0].default_value == "12"


def test_fortran_file_and_project_helpers_forward_compile_time_values():
    proc = FortranProcedureSignature(
        name="scale",
        kind="subroutine",
        arguments=[FortranArgument(name="x", base_type="real", kind="rk")],
    )
    parsed_file = FortranFile(modules=[FortranModule(name="solver", procedures=[proc])])
    project = FortranProject(files=[parsed_file])

    file_module = fortran_file_to_semantic_modules(parsed_file, compile_time_values={"rk": 8})[0]
    project_module = fortran_project_to_semantic_modules(project, compile_time_values={"rk": 8})[0]

    assert get_function(file_module, "scale").arguments[0].semantic_type.name == "Float64"
    assert get_function(project_module, "scale").arguments[0].semantic_type.name == "Float64"
