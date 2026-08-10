"""Shared support for Fortran wrapper policy and lowering tests."""

import pytest

from prik.contracts import CONTRACT_SYMBOLS

from prik.semantics.metadata import (
    ADDRESS_ROLE_METADATA,
    ADDRESS_ROLE_PROJECTION,
    ADDRESS_ROLE_RAW,
    PROJECTED_OUTPUT_METADATA,
    SCALAR_STORAGE_CATEGORY,
)

from prik.codegen.printers import PyiPrinter

from prik.semantics.ownership import (
    AssignmentMode,
    CodegenAction,
    DestructionPolicy,
    NativeBarrierAction,
    NativeBarrierDispatcher,
    ObjectKind,
    OwnershipContext,
    OwnershipDecision,
    OwnershipOwner,
    OwnershipPolicyResolver,
    PolicyActionDispatcher,
    PythonBarrierAction,
    PythonBarrierDispatcher,
    SetterAction,
    StorageMode,
    TransferMode,
    default_ownership_policy,
    set_ownership_metadata,
)

from prik.semantics.models import (
    POLICY_COMPLETION_PREPARED_METADATA,
    PYTHON_EXPORTS_METADATA,
    PYTHON_EXPORTS_PREPARED_METADATA,
    RESOLVED_GETTER_OWNERSHIP_POLICY_METADATA,
    RESOLVED_MODULE_VARIABLE_INITIALIZER_METADATA,
    RESOLVED_NATIVE_ARRAY_HANDLE_POLICY_METADATA,
    RESOLVED_SETTER_OWNERSHIP_POLICY_METADATA,
    RESOLVED_OWNERSHIP_POLICY_METADATA,
    RESOLVED_RETURN_OWNERSHIP_POLICY_METADATA,
    ProjectionMapping,
    SemanticArgument,
    SemanticArrayContract,
    SemanticClass,
    SemanticConstraint,
    SemanticField,
    SemanticFunction,
    SemanticModule,
    SemanticStorageContract,
    SemanticType,
    SemanticVariable,
)

from prik.semantics.native_array_handles import (
    ArrayInteropPolicy,
    ArrayInteropPolicyDispatcher,
    NativeArrayBuildRequirement,
    NativeArrayHandlePolicy,
    NativeArrayHandlePolicyDispatcher,
    native_array_descriptor_kind,
    native_array_handle_build_requirements,
)

from prik.semantics.policy_completion import complete_semantic_policies

from prik.pipeline.pyi import pyi_text_to_semantic_module as _parse_pyi_text

CONTRACT_IMPORT = f"from prik.contracts import {', '.join(sorted(CONTRACT_SYMBOLS))}\n"


def parse_pyi_text(source: str, *args, **kwargs):
    if "prik.contracts" in source:
        return _parse_pyi_text(source, *args, **kwargs)
    return _parse_pyi_text(f"{CONTRACT_IMPORT}{source}", *args, **kwargs)


def _scalar_type(name: str = "Int32") -> SemanticType:
    return SemanticType(name=name, dtype=name)


def _string_type() -> SemanticType:
    return SemanticType(name="String", dtype="String")


def _array_type(
    *,
    allocatable: bool = False,
    pointer: bool = False,
    metadata: dict[str, object] | None = None,
) -> SemanticType:
    return SemanticType(
        name="Float64",
        dtype="Float64",
        rank=1,
        shape=[":"],
        metadata=metadata or {},
        storage=SemanticStorageContract(
            kind="array",
            array=SemanticArrayContract(
                rank=1,
                shape=[":"],
                allocatable=allocatable,
                pointer=pointer,
            ),
        ),
    )


def _scalar_storage_type() -> SemanticType:
    return SemanticType(
        name="Int32",
        dtype="Int32",
        rank=0,
        storage=SemanticStorageContract(
            kind="array",
            array=SemanticArrayContract(rank=0, shape=[], category=SCALAR_STORAGE_CATEGORY),
        ),
    )


def _string_storage_type() -> SemanticType:
    return SemanticType(
        name="String",
        dtype="String",
        rank=0,
        metadata={"fortran_character_length": "8"},
        storage=SemanticStorageContract(
            kind="array",
            array=SemanticArrayContract(rank=0, shape=[], category=SCALAR_STORAGE_CATEGORY),
        ),
    )


def _address_type(role: str) -> SemanticType:
    return SemanticType(
        name="Int32",
        dtype="Int32",
        storage=SemanticStorageContract(kind="address", metadata={ADDRESS_ROLE_METADATA: role}),
    )


def _derived_type(
    name: str = "point",
    *,
    metadata: dict[str, object] | None = None,
) -> SemanticType:
    return SemanticType(name=name, dtype=name, metadata=metadata or {})


def _read_only_argument_context(**kwargs) -> OwnershipContext:
    return OwnershipContext.argument(**kwargs)


def _writable_argument_context(**kwargs) -> OwnershipContext:
    return OwnershipContext.argument(writes_argument=True, **kwargs)


def _hidden_output_context(**kwargs) -> OwnershipContext:
    return OwnershipContext.argument(reads_argument=False, writes_argument=True, **kwargs)


def _native_array_policy(
    *,
    descriptor_kind: str = "allocatable",
    handle_kind: str = "borrowed_module_descriptor",
    to_numpy: str = "borrowed_view",
    descriptor_interop: str = "none",
    nullable: bool = False,
    optional_absent: bool = False,
    operations: tuple[str, ...] = ("allocated", "to_numpy"),
) -> NativeArrayHandlePolicy:
    return NativeArrayHandlePolicy(
        descriptor_kind=descriptor_kind,
        handle_kind=handle_kind,
        origin="module_variable",
        owner="native",
        owner_retention="native_module",
        descriptor_ownership="borrowed",
        borrowed=True,
        getter_behavior="handle",
        python_setter="none",
        native_setter="none",
        output_projection="none",
        result_allocation="not_applicable",
        release="native_owner",
        target_lifetime="module",
        destroy_behavior="none",
        to_numpy=to_numpy,
        descriptor_interop=descriptor_interop,
        nullable=nullable,
        optional_absent=optional_absent,
        storage_mode="alias",
        operations=operations,
    )


__all__ = (
    "ADDRESS_ROLE_METADATA",
    "ADDRESS_ROLE_PROJECTION",
    "ADDRESS_ROLE_RAW",
    "POLICY_COMPLETION_PREPARED_METADATA",
    "PROJECTED_OUTPUT_METADATA",
    "PYTHON_EXPORTS_METADATA",
    "PYTHON_EXPORTS_PREPARED_METADATA",
    "RESOLVED_GETTER_OWNERSHIP_POLICY_METADATA",
    "RESOLVED_MODULE_VARIABLE_INITIALIZER_METADATA",
    "RESOLVED_NATIVE_ARRAY_HANDLE_POLICY_METADATA",
    "RESOLVED_OWNERSHIP_POLICY_METADATA",
    "RESOLVED_RETURN_OWNERSHIP_POLICY_METADATA",
    "RESOLVED_SETTER_OWNERSHIP_POLICY_METADATA",
    "ArrayInteropPolicy",
    "ArrayInteropPolicyDispatcher",
    "AssignmentMode",
    "CodegenAction",
    "DestructionPolicy",
    "NativeArrayBuildRequirement",
    "NativeArrayHandlePolicyDispatcher",
    "NativeBarrierAction",
    "NativeBarrierDispatcher",
    "ObjectKind",
    "OwnershipContext",
    "OwnershipDecision",
    "OwnershipOwner",
    "OwnershipPolicyResolver",
    "PolicyActionDispatcher",
    "ProjectionMapping",
    "PyiPrinter",
    "PythonBarrierAction",
    "PythonBarrierDispatcher",
    "SemanticArgument",
    "SemanticClass",
    "SemanticConstraint",
    "SemanticField",
    "SemanticFunction",
    "SemanticModule",
    "SemanticType",
    "SemanticVariable",
    "SetterAction",
    "StorageMode",
    "TransferMode",
    "_address_type",
    "_array_type",
    "_derived_type",
    "_hidden_output_context",
    "_native_array_policy",
    "_read_only_argument_context",
    "_scalar_storage_type",
    "_scalar_type",
    "_string_storage_type",
    "_string_type",
    "_writable_argument_context",
    "complete_semantic_policies",
    "default_ownership_policy",
    "native_array_descriptor_kind",
    "native_array_handle_build_requirements",
    "parse_pyi_text",
    "pytest",
    "set_ownership_metadata",
)
