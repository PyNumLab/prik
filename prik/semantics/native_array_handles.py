"""Semantic facts for native allocatable and pointer array descriptors."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass

from prik.semantics.metadata import (
    MAYBE_UNALLOCATED_METADATA,
    NATIVE_ARRAY_DESCRIPTOR_METADATA,
    NATIVE_ARRAY_HANDLE_POLICY_METADATA,
    OPTIONAL_ABSENT_HANDLE_METADATA,
)
from prik.semantics.models import PYTHON_VALUE_MUTABILITY_METADATA, SemanticType
from prik.semantics.ownership_metadata import OWNERSHIP_POLICY_METADATA, POINTER_POLICY_METADATA


_HANDLE_ONLY_METADATA = (
    NATIVE_ARRAY_DESCRIPTOR_METADATA,
    NATIVE_ARRAY_HANDLE_POLICY_METADATA,
    MAYBE_UNALLOCATED_METADATA,
    OPTIONAL_ABSENT_HANDLE_METADATA,
    OWNERSHIP_POLICY_METADATA,
    POINTER_POLICY_METADATA,
    PYTHON_VALUE_MUTABILITY_METADATA,
    "aliased",
    "fortran_allocatable",
    "fortran_pointer",
    "fortran_pointer_association",
)


@dataclass(frozen=True)
class NativeArrayHandleFacts:
    """Common semantic facts carried by any native array descriptor handle."""

    descriptor_kind: str
    element_type: SemanticType
    data_type: SemanticType
    dtype: str | None
    rank: int
    shape: tuple[str, ...]
    fortran_character_length: object | None = None


def native_array_descriptor_kind(semantic_type: SemanticType | None) -> str | None:
    """Return the native descriptor kind for an array handle type."""
    if semantic_type is None:
        return None
    storage = semantic_type.storage
    if semantic_type.rank <= 0 or storage is None or storage.array is None:
        return None
    descriptor = semantic_type.metadata.get(NATIVE_ARRAY_DESCRIPTOR_METADATA)
    if descriptor in {"allocatable", "pointer"}:
        return str(descriptor)
    if storage.array.allocatable and storage.array.pointer:
        raise ValueError(f"Array type {semantic_type.name!r} cannot be both allocatable and pointer")
    if storage.array.allocatable:
        return "allocatable"
    if storage.array.pointer:
        return "pointer"
    return None


def is_native_array_handle(semantic_type: SemanticType | None) -> bool:
    """Return whether a semantic type is a native array descriptor handle."""
    return native_array_descriptor_kind(semantic_type) is not None


def mark_native_array_handle(semantic_type: SemanticType, descriptor: str) -> None:
    """Mark an array semantic type as an allocatable or pointer handle."""
    storage = semantic_type.storage
    if storage is None or storage.array is None or semantic_type.rank <= 0:
        raise ValueError(f"{descriptor.capitalize()} array handles require array storage")
    if descriptor not in {"allocatable", "pointer"}:
        raise ValueError(f"Unsupported native array descriptor kind: {descriptor!r}")
    existing = native_array_descriptor_kind(semantic_type)
    if existing is not None and existing != descriptor:
        raise ValueError(
            f"Array descriptor handle cannot be both {existing!r} and {descriptor!r}: {semantic_type.name}"
        )
    storage.array.allocatable = descriptor == "allocatable"
    storage.array.pointer = descriptor == "pointer"
    semantic_type.metadata[NATIVE_ARRAY_DESCRIPTOR_METADATA] = descriptor


def native_array_data_type(semantic_type: SemanticType) -> SemanticType:
    """Return the ordinary array data facet for a native array handle type."""
    if native_array_descriptor_kind(semantic_type) is None:
        raise ValueError(f"Semantic type {semantic_type.name!r} is not a native array handle")
    data_type = deepcopy(semantic_type)
    for key in _HANDLE_ONLY_METADATA:
        data_type.metadata.pop(key, None)
    storage = data_type.storage
    if storage is not None and storage.array is not None:
        storage.array.allocatable = False
        storage.array.pointer = False
    return data_type


def native_array_handle_facts(semantic_type: SemanticType) -> NativeArrayHandleFacts:
    """Return the common semantic facts for a native array descriptor handle."""
    descriptor_kind = native_array_descriptor_kind(semantic_type)
    if descriptor_kind is None:
        raise ValueError(f"Semantic type {semantic_type.name!r} is not a native array handle")
    data_type = native_array_data_type(semantic_type)
    element_type = deepcopy(data_type)
    element_type.rank = 0
    element_type.shape = []
    element_type.storage = None
    return NativeArrayHandleFacts(
        descriptor_kind=descriptor_kind,
        element_type=element_type,
        data_type=data_type,
        dtype=data_type.dtype,
        rank=data_type.rank,
        shape=tuple(data_type.shape),
        fortran_character_length=data_type.metadata.get("fortran_character_length"),
    )


__all__ = (
    "NativeArrayHandleFacts",
    "is_native_array_handle",
    "mark_native_array_handle",
    "native_array_data_type",
    "native_array_descriptor_kind",
    "native_array_handle_facts",
)


if __name__ == "__main__":
    from prik.semantics.models import SemanticArrayContract, SemanticStorageContract

    example_type = SemanticType(
        "Float64",
        rank=2,
        dtype="float64",
        shape=["rows", "columns"],
        storage=SemanticStorageContract(
            kind="array",
            array=SemanticArrayContract(rank=2, shape=["rows", "columns"], order="F"),
        ),
    )
    mark_native_array_handle(example_type, "allocatable")
    example_facts = native_array_handle_facts(example_type)

    print(f"Descriptor kind: {example_facts.descriptor_kind}")
    print(f"Data facet: {example_facts.data_type.name}, rank={example_facts.rank}, shape={example_facts.shape}")
    print(f"Element facet: {example_facts.element_type.name}, rank={example_facts.element_type.rank}")
    print(f"Handle marker retained by data facet: {is_native_array_handle(example_facts.data_type)}")
