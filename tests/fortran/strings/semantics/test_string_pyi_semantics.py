"""Tests split by stable ownership concept from `test_python_ast_contracts.py`."""

from tests.fortran._support.pyi_conversion import (
    emit_module,
    parse_pyi_text,
    pytest,
)


def test_rank_zero_string_storage_round_trips_as_empty_tuple_array():
    module = parse_pyi_text(
        """
def rewrite_label(label: String[8][()]) -> None: ...
""",
        module_name="string_storage",
    )

    label_type = module.functions[0].arguments[0].semantic_type

    assert label_type.name == "String"
    assert label_type.rank == 0
    assert label_type.shape == []
    assert label_type.metadata["fortran_character_length"] == "8"
    assert label_type.storage.kind == "array"
    assert label_type.storage.array.category == "scalar_storage"

    emitted = emit_module(module)
    assert "label: String[8][()]" in emitted
    assert parse_pyi_text(emitted, module_name="string_storage") == module


def test_string_length_and_shape_axes_round_trip():
    module = parse_pyi_text(
        """
def scalar_unknown(value: String) -> None: ...
def scalar_fixed(value: String[8]) -> None: ...
def array_unknown(values: String[:][:]) -> None: ...
def array_fixed(values: String[8][:]) -> None: ...
def scalar_storage(value: String[8][()]) -> None: ...
""",
        module_name="string_axes",
    )

    scalar_unknown, scalar_fixed, array_unknown, array_fixed, scalar_storage = module.functions

    assert "fortran_character_length" not in scalar_unknown.arguments[0].semantic_type.metadata
    assert scalar_fixed.arguments[0].semantic_type.metadata["fortran_character_length"] == "8"

    array_unknown_type = array_unknown.arguments[0].semantic_type
    assert array_unknown_type.metadata["fortran_character_length"] == ":"
    assert array_unknown_type.rank == 1
    assert array_unknown_type.shape == [":"]
    assert array_unknown_type.storage.kind == "array"

    array_fixed_type = array_fixed.arguments[0].semantic_type
    assert array_fixed_type.metadata["fortran_character_length"] == "8"
    assert array_fixed_type.rank == 1
    assert array_fixed_type.shape == [":"]

    scalar_storage_type = scalar_storage.arguments[0].semantic_type
    assert scalar_storage_type.metadata["fortran_character_length"] == "8"
    assert scalar_storage_type.storage.array.category == "scalar_storage"

    emitted = emit_module(module)
    assert "value: String" in emitted
    assert "value: String[8]" in emitted
    assert "values: String[:][:]" in emitted
    assert "values: String[8][:]" in emitted
    assert "value: String[8][()]" in emitted
    assert parse_pyi_text(emitted, module_name="string_axes") == module


def test_bare_string_slice_is_rejected_as_ambiguous():
    with pytest.raises(ValueError, match=r"String\[:\] is ambiguous.*String\[:\]\[:\].*String\[n\]"):
        parse_pyi_text(
            """
def invalid(value: String[:]) -> None: ...
""",
            module_name="string_axes",
        )
