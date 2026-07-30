"""Completed ownership, transfer, and destruction policy for native storage."""

from tests.fortran._support.ownership_policy import parse_pyi_text
from x2py.semantics.models import RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA
from x2py.semantics.policy_completion import complete_semantic_policies


def test_scalar_storage_rejects_incompatible_explicit_ownership_metadata():
    module = parse_pyi_text(
        """
def invalid(
    value: Annotated[
        Int32[()],
        Ownership("python"),
        Transfer("snapshot_copy"),
        Destruction("python_refcount"),
    ],
) -> None: ...
""",
        module_name="invalid_scalar_storage_ownership",
    )
    complete_semantic_policies(module)
    policy = module.functions[0].metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]

    assert policy.supported is False
    assert policy.blockers[:4] == (
        "argument 'value' scalar-storage owner is python, not caller",
        "argument 'value' scalar-storage transfer is snapshot_copy, not in_place",
        "argument 'value' scalar-storage destruction is python_refcount, not caller",
        "argument 'value' scalar-storage action is snapshot_copy, not a storage-address action",
    )


def test_contradictory_ownership_contract_fails_before_lowering():
    module = parse_pyi_text(
        """
def scale_with_status(
    values: Annotated[
        Float64[:],
        Ownership("native"),
        Transfer("copy_return"),
        Destruction("native_owner"),
    ],
    status: Addr(Int32),
) -> Returns["values", Float64[:]]: ...
""",
        module_name="contradictory_ownership",
    )
    complete_semantic_policies(module)
    policy = module.functions[0].metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]

    assert policy.supported is False
    assert policy.arguments[0].ownership.blocker == (
        "ownership policy native/copy_return/native_owner is contradictory or unsupported; "
        "no supported destruction policy"
    )
    assert "argument 'values' has no completed bridge data action" in policy.blockers
