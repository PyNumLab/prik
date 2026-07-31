"""Tests split by stable ownership concept from `test_c_conversion_properties.py`."""

from tests.fortran._support.semantic_properties import (
    EXTERNAL_TYPE_REF_METADATA,
    ProjectionMapping,
    SemanticArgument,
    SemanticFunction,
    SemanticModule,
    SemanticType,
    _NATIVE_NAMES,
    _PYI_IDENTIFIER_STEMS,
    canonical_semantic_types,
    emit_module,
    given,
    parse_pyi_text,
    pytest,
    st,
)


@pytest.mark.property
@given(_NATIVE_NAMES)
def test_generated_pyi_escaping_round_trips_native_names(native_name):
    module = SemanticModule(
        name="generated",
        variables=[SemanticArgument(native_name, SemanticType("Int32", dtype="Int32"))],
        functions=[
            SemanticFunction(
                name="consume",
                native_name="consume",
                arguments=[SemanticArgument(native_name, SemanticType("Int32", dtype="Int32"))],
            )
        ],
    )

    emitted = emit_module(module)
    reparsed = parse_pyi_text(emitted, module_name="generated")

    assert reparsed.variables[0].name == native_name
    assert reparsed.functions[0].arguments[0].name == native_name


@pytest.mark.property
@given(st.lists(_PYI_IDENTIFIER_STEMS, min_size=1, max_size=6, unique=True))
def test_generated_pyi_synthetic_imports_are_stably_sorted(type_stems):
    type_names = [f"type_{stem}" for stem in type_stems]

    def import_lines(names):
        module = SemanticModule(
            name="generated",
            variables=[
                SemanticArgument(
                    f"value_{index}",
                    SemanticType(
                        type_name,
                        dtype=type_name,
                        metadata={
                            EXTERNAL_TYPE_REF_METADATA: {
                                "name": type_name,
                                "local_name": type_name,
                                "origin_module": "types",
                                "representation": "opaque",
                            }
                        },
                    ),
                )
                for index, type_name in enumerate(names)
            ],
        )
        return [line for line in emit_module(module).splitlines() if line.startswith("from ")]

    expected = [f"from types import {', '.join(sorted(type_names))}"]
    assert import_lines(type_names) == expected
    assert import_lines(reversed(type_names)) == expected


@pytest.mark.property
@given(st.lists(canonical_semantic_types(), max_size=5))
def test_generated_semantic_ir_round_trips_through_pyi(arguments):
    semantic_arguments = [
        SemanticArgument(f"value_{index}", semantic_type) for index, semantic_type in enumerate(arguments)
    ]
    module = SemanticModule(
        name="generated",
        functions=[
            SemanticFunction(
                name="consume",
                native_name="consume",
                arguments=semantic_arguments,
                projection=[
                    ProjectionMapping(
                        python_name=argument.name,
                        native_name=argument.name,
                        native_position=index,
                        python_position=index,
                    )
                    for index, argument in enumerate(semantic_arguments)
                ],
            )
        ],
    )

    emitted = emit_module(module)
    reparsed = parse_pyi_text(emitted, module_name="generated")

    assert emit_module(reparsed) == emitted
    assert parse_pyi_text(emit_module(reparsed), module_name="generated") == reparsed
