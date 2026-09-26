"""The `.pyi` printer refuses semantic IR it cannot write as a loadable contract."""

import pytest
from prik.printers import PyiPrinter, emit_module
from prik.semantics.models import (
    ProjectionMapping,
    SemanticArrayContract,
    SemanticFunction,
    SemanticModule,
    SemanticStorageContract,
    SemanticType,
    SemanticVariable,
)


def test_printer_rejects_each_unresolved_semantic_type_field():
    printer = PyiPrinter()
    message = "Cannot emit .pyi with unresolved semantic type 'Unknown'"

    with pytest.raises(ValueError) as unknown_name:
        printer.emit(SemanticType("Unknown", dtype="Int32"))
    with pytest.raises(ValueError) as unknown_dtype:
        printer.emit(SemanticType("Int32", dtype="Unknown"))

    assert str(unknown_name.value) == message
    assert str(unknown_dtype.value) == message


@pytest.mark.parametrize(
    "projection, message",
    [
        (
            [ProjectionMapping(native_position=0)],
            "native-only projection entry",
        ),
        (
            [ProjectionMapping(native_position=0, value_kind="unknown", value=None)],
            "Unsupported native_call projection entry",
        ),
        (
            [
                ProjectionMapping(
                    native_position=0,
                    value_kind="len",
                    value={"kind": "unknown"},
                )
            ],
            "Unsupported native_call value reference",
        ),
    ],
    ids=["native-only-entry", "unknown-entry-kind", "unknown-value-reference"],
)
def test_emit_native_call_rejects_unrepresentable_projection_entries(projection, message):
    module = SemanticModule(
        name="bad_projection_mod",
        functions=[
            SemanticFunction(
                name="wrapper",
                native_name="wrapper",
                projection=projection,
            )
        ],
    )

    with pytest.raises(ValueError, match=message):
        emit_module(module)


def test_printer_rejects_optional_absent_array_handles_outside_callable_arguments():
    variable = SemanticVariable(
        "values",
        SemanticType(
            "Float64",
            rank=1,
            storage=SemanticStorageContract(
                kind="array",
                array=SemanticArrayContract(rank=1, shape=[":"], allocatable=True),
            ),
        ),
    )
    variable.optional = True
    module = SemanticModule(
        name="bad_optional_handle_mod",
        variables=[variable],
    )

    with pytest.raises(ValueError, match="only be emitted for callable arguments"):
        emit_module(module)
