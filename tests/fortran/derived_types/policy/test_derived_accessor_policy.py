"""Tests split by stable ownership concept from `test_handle_policy_dispatch.py`."""

from tests.fortran._support.ownership_policy import (
    AssignmentMode,
    CodegenAction,
    DestructionPolicy,
    ObjectKind,
    OwnershipOwner,
    RESOLVED_GETTER_OWNERSHIP_POLICY_METADATA,
    RESOLVED_OWNERSHIP_POLICY_METADATA,
    RESOLVED_SETTER_OWNERSHIP_POLICY_METADATA,
    SemanticClass,
    SemanticConstraint,
    SemanticField,
    SemanticModule,
    SemanticVariable,
    SetterAction,
    StorageMode,
    TransferMode,
    _array_type,
    _derived_type,
    _scalar_type,
    complete_semantic_policies,
    parse_pyi_text,
    set_ownership_metadata,
)

from prik.semantics.models import (
    RESOLVED_DERIVED_TYPE_POLICY_METADATA,
    RESOLVED_MODULE_VARIABLE_POLICY_METADATA,
)
from prik.semantics.wrapper_policy import ModuleObjectAccessMechanism


def test_abstract_type_and_deferred_binding_fail_in_completed_derived_policy():
    semantic_class = SemanticClass(
        "shape",
        metadata={
            "fortran_type_attributes": ["abstract"],
            "fortran_deferred_bindings": ["area"],
        },
    )
    module = SemanticModule("shapes", classes=[semantic_class])

    complete_semantic_policies(module)

    policy = semantic_class.metadata[RESOLVED_DERIVED_TYPE_POLICY_METADATA]
    assert policy.supported is False
    assert policy.blockers == (
        "abstract derived types need a non-instantiable Python class policy",
        "deferred type-bound procedure 'area' needs an override and dispatch policy",
    )


def test_derived_field_setter_policy_uses_value_copy_write_through():
    module = SemanticModule(
        name="layout",
        classes=[
            SemanticClass("point"),
            SemanticClass("tagged_point", fields=[SemanticField("position", _derived_type("point"))]),
        ],
    )

    complete_semantic_policies(module)

    setter = module.classes[1].fields[0].metadata[RESOLVED_SETTER_OWNERSHIP_POLICY_METADATA]
    assert setter.kind is ObjectKind.DERIVED_TYPE
    assert setter.assignment_mode is AssignmentMode.VALUE_COPY
    assert setter.setter_action is SetterAction.WRITE_THROUGH


def test_aliased_derived_module_object_is_borrowed_and_rejects_replacement():
    module = SemanticModule(
        name="state",
        variables=[SemanticVariable("current", _derived_type("box", metadata={"aliased": True}))],
        classes=[SemanticClass("box", fields=[SemanticField("value", _scalar_type())])],
    )

    complete_semantic_policies(module)

    variable = module.variables[0]
    storage = variable.metadata[RESOLVED_OWNERSHIP_POLICY_METADATA]
    getter = variable.metadata[RESOLVED_GETTER_OWNERSHIP_POLICY_METADATA]
    setter = variable.metadata[RESOLVED_SETTER_OWNERSHIP_POLICY_METADATA]
    assert storage.owner is OwnershipOwner.NATIVE
    assert storage.transfer is TransferMode.BORROWED_VIEW
    assert storage.boundary_storage_mode is StorageMode.ALIAS
    assert getter.codegen_action is CodegenAction.BORROWED_VIEW
    assert setter.setter_action is SetterAction.REJECT_REPLACEMENT


def test_plain_derived_module_object_completes_live_member_proxy_policy():
    module = SemanticModule(
        name="state",
        variables=[SemanticVariable("current", _derived_type("box"))],
        classes=[
            SemanticClass("point", fields=[SemanticField("x", _scalar_type())]),
            SemanticClass(
                "box",
                fields=[
                    SemanticField("value", _scalar_type()),
                    SemanticField("origin", _derived_type("point")),
                    SemanticField("values", _array_type(allocatable=True, metadata={"aliased": True})),
                ],
            ),
        ],
    )

    complete_semantic_policies(module)

    variable = module.variables[0]
    storage = variable.metadata[RESOLVED_OWNERSHIP_POLICY_METADATA]
    getter = variable.metadata[RESOLVED_GETTER_OWNERSHIP_POLICY_METADATA]
    setter = variable.metadata[RESOLVED_SETTER_OWNERSHIP_POLICY_METADATA]
    assert storage.owner is OwnershipOwner.NATIVE
    assert storage.transfer is TransferMode.BORROWED_VIEW
    assert storage.codegen_action is CodegenAction.BORROWED_VIEW
    assert getter.codegen_action is CodegenAction.BORROWED_VIEW
    assert setter.setter_action is SetterAction.REJECT_REPLACEMENT
    policy = variable.metadata[RESOLVED_MODULE_VARIABLE_POLICY_METADATA]
    assert policy.derived.access is ModuleObjectAccessMechanism.MEMBER_PROXY
    assert policy.owner_path == "state.current"


def test_derived_module_constant_uses_wrapper_owned_copy_without_setter():
    constant_type = _derived_type("rgb_color")
    constant_type.constraints.append(SemanticConstraint("Constant"))
    module = SemanticModule(
        name="colors",
        variables=[SemanticVariable("black", constant_type)],
        classes=[
            SemanticClass(
                "rgb_color",
                fields=[
                    SemanticField("r", _scalar_type()),
                    SemanticField("g", _scalar_type()),
                    SemanticField("b", _scalar_type()),
                ],
            )
        ],
    )

    complete_semantic_policies(module)

    variable = module.variables[0]
    storage = variable.metadata[RESOLVED_OWNERSHIP_POLICY_METADATA]
    getter = variable.metadata[RESOLVED_GETTER_OWNERSHIP_POLICY_METADATA]
    setter = variable.metadata[RESOLVED_SETTER_OWNERSHIP_POLICY_METADATA]
    assert storage.kind is ObjectKind.DERIVED_TYPE
    assert storage.owner is OwnershipOwner.WRAPPER
    assert storage.transfer is TransferMode.WRAPPER_INSTANCE
    assert storage.destruction is DestructionPolicy.WRAPPER_DEALLOC
    assert getter.transfer is TransferMode.WRAPPER_INSTANCE
    assert setter.setter_action is SetterAction.OMIT


def test_explicit_borrowed_derived_field_setter_rejects_replacement():
    child_type = _derived_type("child")
    set_ownership_metadata(
        child_type.metadata,
        owner="wrapper",
        transfer="borrowed_view",
        destruction="wrapper_dealloc",
    )
    module = SemanticModule(
        name="finalizer",
        classes=[
            SemanticClass("child"),
            SemanticClass("parent", fields=[SemanticField("value", child_type)]),
        ],
    )

    complete_semantic_policies(module)

    setter = module.classes[1].fields[0].metadata[RESOLVED_SETTER_OWNERSHIP_POLICY_METADATA]
    assert setter.kind is ObjectKind.DERIVED_TYPE
    assert setter.transfer is TransferMode.BORROWED_VIEW
    assert setter.setter_action is SetterAction.REJECT_REPLACEMENT


def test_derived_field_array_is_blocked_in_completed_type_policy():
    module = parse_pyi_text(
        """
class item:
    value: Int32

class holder:
    values: item[:]
""",
        module_name="derived_field_array",
    )
    complete_semantic_policies(module)

    policy = module.classes[1].metadata[RESOLVED_DERIVED_TYPE_POLICY_METADATA]
    assert policy.supported is False
    assert "field 'values' is an unsupported array of derived values" in policy.blockers
