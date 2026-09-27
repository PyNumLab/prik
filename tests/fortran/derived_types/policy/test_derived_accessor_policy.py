"""Tests split by stable ownership concept from `test_handle_policy_dispatch.py`."""

import pytest

from prik.semantics.models import (
    RESOLVED_SETTER_OWNERSHIP_POLICY_METADATA,
    SemanticClass,
    SemanticField,
    SemanticModule,
)
from prik.policy.ownership import (
    ObjectKind,
    SetterAction,
    TransferMode,
)
from prik.semantics.ownership_metadata import set_ownership_metadata
from prik.policy.completion import complete_semantic_policies
from tests.fortran._support.ownership_policy import (
    _derived_type,
    parse_pyi_text,
)

from prik.semantics.models import (
    RESOLVED_DERIVED_TYPE_POLICY_METADATA,
    RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA,
)


def test_deferred_binding_without_an_abstract_type_is_refused():
    """Only an abstract type may declare a binding it does not implement."""
    semantic_class = SemanticClass("shape", metadata={"fortran_deferred_bindings": ["area"]})
    module = SemanticModule("shapes", classes=[semantic_class])

    complete_semantic_policies(module)

    policy = semantic_class.metadata[RESOLVED_DERIVED_TYPE_POLICY_METADATA]
    assert policy.supported is False
    assert policy.blockers == ("deferred type-bound procedure 'area' needs a declaring abstract type",)


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


@pytest.mark.parametrize("holder", ["Allocatable", "Pointer"])
def test_descriptor_holder_rejects_fields_it_cannot_reach(holder):
    """A held object reaches only scalar-value fields, whichever descriptor holds it."""
    module = parse_pyi_text(
        f"""
class item:
    tag: String[4]
    scale: Allocatable[Float64]

@native_call([{holder}(Arg(0))])
def attach(value: item | None) -> None: ...
""",
        module_name="descriptor_holder",
    )
    complete_semantic_policies(module)

    policy = module.functions[0].metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]
    assert "argument 'value' holder field 'tag' requires unsupported fixed_string_copy access" in policy.blockers
    assert "argument 'value' holder field 'scale' requires unsupported scalar_descriptor_view access" in policy.blockers
