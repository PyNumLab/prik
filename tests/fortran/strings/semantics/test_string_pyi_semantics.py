"""Tests split by stable ownership concept from `test_python_ast_contracts.py`."""

import pytest
from prik.printers import emit_module
from tests.fortran._support.pyi_conversion import parse_pyi_text


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
def scalar_deferred(value: String[:]) -> None: ...
def array_assumed(values: String[...][:]) -> None: ...
def array_assumed_strided(values: String[...][::]) -> None: ...
""",
        module_name="string_axes",
    )

    (
        scalar_unknown,
        scalar_fixed,
        array_unknown,
        array_fixed,
        scalar_storage,
        scalar_deferred,
        array_assumed,
        array_assumed_strided,
    ) = module.functions

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

    deferred_type = scalar_deferred.arguments[0].semantic_type
    assert deferred_type.metadata["fortran_character_length"] == ":"
    assert deferred_type.rank == 0

    assumed_type = array_assumed.arguments[0].semantic_type
    assert assumed_type.metadata["fortran_character_length"] == "*"
    assert assumed_type.rank == 1
    assert assumed_type.shape == [":"]
    assert array_assumed_strided.arguments[0].semantic_type.shape == ["::Strided"]

    emitted = emit_module(module)
    assert "value: String" in emitted
    assert "value: String[8]" in emitted
    assert "values: String[:][:]" in emitted
    assert "values: String[8][:]" in emitted
    assert "value: String[8][()]" in emitted
    assert "value: String[:]" in emitted
    assert "values: String[...][:]" in emitted
    assert "values: String[...][::]" in emitted
    assert parse_pyi_text(emitted, module_name="string_axes") == module


def test_scalar_string_length_subscription_spells_every_character_length():
    """One subscription after ``String`` is the character length, never a shape.

    A scalar carries assumed, explicit, or deferred length in that slot, so a
    reader never has to infer which axis a single bracket describes.
    """
    module = parse_pyi_text(
        """
def assumed(value: String) -> None: ...
def spelled_assumed(value: String[...]) -> None: ...
def explicit(value: String[8]) -> None: ...
def deferred(value: String[:]) -> None: ...
""",
        module_name="string_lengths",
    )
    lengths = [
        function.arguments[0].semantic_type.metadata.get("fortran_character_length") for function in module.functions
    ]
    assert lengths == [None, "*", "8", ":"]
    assert all(function.arguments[0].semantic_type.rank == 0 for function in module.functions)


@pytest.mark.parametrize("spelling", ["String[::]", "String[1:8]"])
def test_shape_spellings_are_rejected_in_the_character_length_slot(spelling: str):
    """A shape belongs to the second subscription, so the first rejects one.

    ``String[:]`` and ``String[::]`` parse to the same Python AST, so the
    contract's own text decides which of the two a length slot accepts.
    """
    with pytest.raises(ValueError, match=r"is not a character length"):
        parse_pyi_text(
            f"""
def invalid(value: {spelling}) -> None: ...
""",
            module_name="string_axes",
        )
