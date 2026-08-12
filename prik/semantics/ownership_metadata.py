"""Raw ownership and pointer-policy metadata stored on semantic contracts.

This module owns only contract keys and normalized metadata setters used
during semantic IR construction. Completed ownership vocabulary, resolution,
and lowering actions belong to :mod:`prik.policy.ownership`.
"""

from __future__ import annotations

from enum import Enum
from typing import Any


OWNERSHIP_POLICY_METADATA = "ownership_policy"
POINTER_POLICY_METADATA = "pointer_policy"
POINTER_POLICY_FIELDS = (
    "nullable",
    "transfer",
    "target_owner",
    "lifetime",
    "deallocation",
    "shape_source",
    "contiguity",
    "reassociation",
    "aliasing",
    "mutability",
)


class _OwnershipOwner(str, Enum):
    PYTHON = "python"
    CALLER = "caller"
    NATIVE = "native"
    WRAPPER = "wrapper"
    TEMPORARY = "temporary"
    UNKNOWN = "unknown"


class _TransferMode(str, Enum):
    BY_VALUE = "by_value"
    IN_PLACE = "in_place"
    COPY_RETURN = "copy_return"
    SNAPSHOT_COPY = "snapshot_copy"
    BORROWED_VIEW = "borrowed_view"
    CALL_LOCAL = "call_local"
    WRAPPER_INSTANCE = "wrapper_instance"
    BLOCKED = "blocked"


class _DestructionPolicy(str, Enum):
    PYTHON_REFCOUNT = "python_refcount"
    CALLER = "caller"
    WRAPPER_DEALLOC = "wrapper_dealloc"
    NATIVE_OWNER = "native_owner"
    CALL_LOCAL = "call_local"
    NONE = "none"
    BLOCKED = "blocked"


def set_ownership_metadata(
    metadata: dict[str, Any],
    *,
    owner: str | None = None,
    transfer: str | None = None,
    destruction: str | None = None,
) -> None:
    """Store normalized owner, transfer, and destruction contract metadata."""
    policy = metadata.setdefault(OWNERSHIP_POLICY_METADATA, {})
    if not isinstance(policy, dict):
        raise ValueError(f"{OWNERSHIP_POLICY_METADATA!r} metadata must be a dictionary")
    if owner is not None:
        policy["owner"] = _OwnershipOwner(owner).value
    if transfer is not None:
        policy["transfer"] = _TransferMode(transfer).value
    if destruction is not None:
        policy["destruction"] = _DestructionPolicy(destruction).value


def set_pointer_policy_metadata(metadata: dict[str, Any], **policy_values: Any) -> None:
    """Store a complete semantic pointer policy after validating its shape."""
    missing = [name for name in POINTER_POLICY_FIELDS if name not in policy_values]
    extra = [name for name in policy_values if name not in POINTER_POLICY_FIELDS]
    if missing or extra:
        details = []
        if missing:
            details.append(f"missing: {', '.join(missing)}")
        if extra:
            details.append(f"unexpected: {', '.join(extra)}")
        raise ValueError(f"PointerPolicy requires exactly {', '.join(POINTER_POLICY_FIELDS)} ({'; '.join(details)})")
    if not isinstance(policy_values["nullable"], bool):
        raise ValueError("PointerPolicy nullable must be a boolean")
    for name in POINTER_POLICY_FIELDS[1:]:
        if not isinstance(policy_values[name], str) or not policy_values[name]:
            raise ValueError(f"PointerPolicy {name} must be a non-empty string")
    _TransferMode(policy_values["transfer"])
    metadata[POINTER_POLICY_METADATA] = dict(policy_values)
    metadata["fortran_pointer"] = True


__all__ = (
    "OWNERSHIP_POLICY_METADATA",
    "POINTER_POLICY_FIELDS",
    "POINTER_POLICY_METADATA",
    "set_ownership_metadata",
    "set_pointer_policy_metadata",
)


if __name__ == "__main__":
    example_metadata: dict[str, Any] = {}
    set_ownership_metadata(
        example_metadata,
        owner="caller",
        transfer="in_place",
        destruction="caller",
    )
    set_pointer_policy_metadata(
        example_metadata,
        nullable=True,
        transfer="borrowed_view",
        target_owner="native",
        lifetime="owner",
        deallocation="native",
        shape_source="descriptor",
        contiguity="fortran",
        reassociation="forbidden",
        aliasing="borrowed",
        mutability="mutable",
    )

    ownership = example_metadata[OWNERSHIP_POLICY_METADATA]
    pointer = example_metadata[POINTER_POLICY_METADATA]
    print(
        f"Raw ownership request: owner={ownership['owner']}, "
        f"transfer={ownership['transfer']}, destruction={ownership['destruction']}"
    )
    print(
        f"Pointer contract: nullable={pointer['nullable']}, "
        f"lifetime={pointer['lifetime']}, reassociation={pointer['reassociation']}"
    )
    print("Completed lowering action present: False")
