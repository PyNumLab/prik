"""Tests split by stable ownership concept from `test_c_conversion_properties.py`."""

from tests.c._support.semantic_properties import (
    asdict,
    _C_VALUE_TYPES,
    c_file_to_semantic_modules,
    c_scalar_prototypes,
    given,
    parse_c_file,
    pytest,
)


@pytest.mark.property
@given(c_scalar_prototypes())
def test_generated_c_ast_to_semantic_ir_is_deterministic(case):
    source, expected_result, expected_parameters = case

    first = c_file_to_semantic_modules(parse_c_file(source, filename="generated.h"))[0]
    second = c_file_to_semantic_modules(parse_c_file(source, filename="generated.h"))[0]

    assert asdict(first) == asdict(second)
    assert len(first.functions) == 1
    function = first.functions[0]
    assert function.return_type is not None
    assert function.return_type.name == expected_result
    assert [(arg.name, arg.semantic_type.name) for arg in function.arguments] == expected_parameters


@pytest.mark.property
@given(_C_VALUE_TYPES)
def test_generated_c_value_arguments_have_the_expected_semantic_contract(case):
    c_type, semantic_type = case

    module = c_file_to_semantic_modules(parse_c_file(f"void consume({c_type} value);\n", filename="generated.h"))[0]
    argument = module.functions[0].arguments[0]

    assert argument.semantic_type.name == semantic_type
    assert argument.semantic_type.origin.source_language == "c"
