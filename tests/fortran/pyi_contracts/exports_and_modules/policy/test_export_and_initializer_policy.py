"""Completed policy for editable exports and module initialization."""

from prik.semantics.models import (
    POLICY_COMPLETION_PREPARED_METADATA,
    PYTHON_EXPORTS_METADATA,
    PYTHON_EXPORTS_PREPARED_METADATA,
    RESOLVED_MODULE_VARIABLE_INITIALIZER_METADATA,
    RESOLVED_SETTER_OWNERSHIP_POLICY_METADATA,
    SemanticFunction,
    SemanticModule,
    SemanticType,
    SemanticVariable,
)
from prik.semantics.ownership import SetterAction
from prik.semantics.policy_completion import complete_semantic_policies
from tests.fortran._support.ownership_policy import _scalar_type
from prik.semantics.models import RESOLVED_MODULE_VARIABLE_POLICY_METADATA


def test_module_variable_initializer_policy_is_complete_before_ir_lowering():
    module = SemanticModule(
        name="state",
        variables=[SemanticVariable("counter", _scalar_type(), default_value="41")],
    )

    complete_semantic_policies(module)

    variable = module.variables[0]
    assert variable.metadata[RESOLVED_MODULE_VARIABLE_INITIALIZER_METADATA] == "41"
    assert variable.metadata[RESOLVED_SETTER_OWNERSHIP_POLICY_METADATA].setter_action is SetterAction.WRITE_THROUGH


def test_unsupported_module_variable_initializer_completes_an_unsupported_policy():
    module = SemanticModule(
        name="labels",
        variables=[SemanticVariable("label", SemanticType("String"), default_value='"ready"')],
    )

    complete_semantic_policies(module)

    variable = module.variables[0]
    assert RESOLVED_MODULE_VARIABLE_INITIALIZER_METADATA not in variable.metadata
    policy = variable.metadata[RESOLVED_MODULE_VARIABLE_POLICY_METADATA]
    assert policy.supported is False
    assert (
        "module variable initializer requires a write-through native setter; "
        "completed setter action is 'reject_replacement'"
    ) in policy.blockers


def test_policy_completion_prunes_unexported_entry_declarations_before_lowering():
    exported_variable = SemanticVariable(
        "counter",
        _scalar_type(),
        metadata={PYTHON_EXPORTS_METADATA: [{"namespace": (), "name": "counter"}]},
    )
    omitted_variable = SemanticVariable(
        "scale",
        _scalar_type("Float64"),
        metadata={PYTHON_EXPORTS_METADATA: []},
    )
    exported_function = SemanticFunction(
        "summarize",
        return_type=_scalar_type(),
        metadata={PYTHON_EXPORTS_METADATA: [{"namespace": (), "name": "summarize"}]},
    )
    omitted_function = SemanticFunction("scaled_counter", return_type=_scalar_type("Float64"))
    private_helper = SemanticFunction(
        "hidden_helper",
        return_type=_scalar_type(),
        visibility="private",
        metadata={PYTHON_EXPORTS_METADATA: []},
    )
    module = SemanticModule(
        name="entry_contract",
        variables=[exported_variable, omitted_variable],
        functions=[exported_function, omitted_function, private_helper],
        metadata={PYTHON_EXPORTS_PREPARED_METADATA: True},
    )

    complete_semantic_policies(module)

    assert module.variables == [exported_variable]
    assert module.functions == [exported_function, private_helper]
    assert POLICY_COMPLETION_PREPARED_METADATA in module.metadata
