"""Semantic callback prototype contract printing."""

from tests.fortran._support.printer_models import (
    SemanticArgument,
    SemanticArrayContract,
    SemanticClass,
    SemanticModule,
    SemanticOrigin,
    SemanticPrototype,
    SemanticStorageContract,
    SemanticType,
    emit_module,
)


def test_callback_contract_prints_descriptor_and_derived_value_transports():
    allocatable_array = SemanticType(
        "Float64",
        dtype="Float64",
        rank=1,
        shape=[":"],
        metadata={"fortran_allocatable": True},
        storage=SemanticStorageContract(
            kind="reference",
            array=SemanticArrayContract(rank=1, shape=[":"]),
        ),
    )
    polymorphic_value = SemanticType(
        "item",
        dtype="item",
        rank=0,
        metadata={"fortran_polymorphic": True},
        storage=SemanticStorageContract(kind="reference", pointer_depth=1),
    )
    derived_value = SemanticType(
        "item",
        dtype="item",
        rank=0,
        storage=SemanticStorageContract(kind="value"),
    )
    module = SemanticModule(
        "callback_contracts",
        classes=[SemanticClass("item")],
        prototypes=[
            SemanticPrototype(
                "callback",
                arguments=[
                    SemanticArgument("values", allocatable_array),
                    SemanticArgument("poly", polymorphic_value),
                    SemanticArgument(
                        "value",
                        derived_value,
                        origin=SemanticOrigin(metadata={"value": True}),
                    ),
                ],
                return_type=SemanticType("None", dtype="None"),
            )
        ],
    )

    contract = emit_module(module)

    assert "@prototype\ndef callback(" in contract
    assert "values: Annotated[Addr(Float64[:]), FortranAllocatable]" in contract
    assert "poly: Annotated[item, Polymorphic]" in contract
    assert "value: Value(item)" in contract
