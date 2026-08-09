"""Completed array extent-reference policy."""

import pytest

from tests.fortran._support.semantic_conversion import (
    fortran_module_to_semantic_module,
    get_function,
    parse_fortran_source,
)
from tests.fortran._support.ownership_policy import parse_pyi_text
from prik.semantics.models import (
    RESOLVED_DERIVED_TYPE_POLICY_METADATA,
    RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA,
    RESOLVED_MODULE_VARIABLE_POLICY_METADATA,
)
from prik.semantics.policy_completion import complete_semantic_policies
from prik.semantics.wrapper_policy import DeclarationCallableAction


def test_array_extent_reference_requires_a_visible_scalar_argument():
    module = parse_pyi_text(
        """
from prik.contracts import Float64

def values() -> Float64[missing]: ...
""",
        module_name="missing_extent",
    )
    complete_semantic_policies(module)

    policy = module.functions[0].metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]
    assert policy.supported is False
    assert (
        "array owner 'missing_extent.values.return' extent axis 0 has unavailable scalar references ('missing',)"
        in policy.blockers
    )


def test_python_array_properties_and_integer_helpers_resolve_to_extent_roles():
    module = parse_pyi_text(
        """
from prik.contracts import Float64

def values(source: Float64[:, :]) -> Float64[
    source.size,
    source.shape[1],
    source.ndim,
    len(source),
    max(1, source.shape[0] - 1),
    2 ** source.shape[1],
]: ...
""",
        module_name="property_extents",
    )
    complete_semantic_policies(module)

    policy = module.functions[0].metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]
    assert policy.supported is True
    assert policy.results[0].array.shape == (
        "__prik_extent_source_0 * __prik_extent_source_1",
        "__prik_extent_source_1",
        "2",
        "__prik_extent_source_0",
        "max(1, __prik_extent_source_0 - 1)",
        "2 ** __prik_extent_source_1",
    )


def test_persistent_array_extents_reject_unavailable_runtime_values():
    module = parse_pyi_text(
        """
from prik.contracts import Aliased, Annotated, Float64

values: Annotated[Float64[missing], Aliased]

class record:
    values: Float64[missing]
""",
        module_name="persistent_extents",
    )
    complete_semantic_policies(module)

    variable_policy = module.variables[0].metadata[RESOLVED_MODULE_VARIABLE_POLICY_METADATA]
    class_policy = module.classes[0].metadata[RESOLVED_DERIVED_TYPE_POLICY_METADATA]

    assert variable_policy.supported is False
    assert (
        "module variable 'values' extent axis 0 depends on unavailable declaration values ('missing',)"
        in variable_policy.blockers
    )
    assert class_policy.supported is False
    assert any(
        "field 'values' extent axis 0 depends on unavailable declaration values ('missing',)" in blocker
        for blocker in class_policy.blockers
    )


def test_source_specification_function_completes_as_a_module_bridge_dependency():
    module = fortran_module_to_semantic_module(
        parse_fortran_source(
            """
module pure_extent_mod
contains
pure integer function extent_for(n) result(extent)
  integer, intent(in) :: n
  extent = max(1, n)
end function extent_for

function values(n) result(output)
  integer, intent(in) :: n
  real(8) :: output(extent_for(n))
end function values
end module pure_extent_mod
"""
        )
    )
    function = get_function(module, "values")

    assert function.return_type.storage.array.source_shape == ["extent_for(n)"]
    assert function.return_type.storage.array.shape == ["extent_for(n)"]

    complete_semantic_policies(module)

    policy = function.metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]
    assert policy.supported is True
    assert policy.results[0].array.extent_blockers == ((),)
    assert policy.results[0].array.extent_evaluation == ("bridge",)
    assert len(policy.declaration_callables) == 1
    declaration = policy.declaration_callables[0]
    assert declaration.action is DeclarationCallableAction.MODULE_IMPORT
    assert declaration.native_scope == "pure_extent_mod"
    assert declaration.native_name == "extent_for"
    assert declaration.prototype is None
    assert declaration.blockers == ()


def test_called_pure_prototype_completes_as_an_exact_standalone_procedure():
    module = parse_pyi_text(
        """
@pure
@prototype
def extent_for(n: In(Addr(Int32))) -> Int32: ...

def values(n: Int32) -> Float64[extent_for(n)]: ...
""",
        module_name="external_extent",
    )
    complete_semantic_policies(module)

    policy = module.functions[0].metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]
    declaration = policy.declaration_callables[0]

    assert policy.supported is True
    assert declaration.action is DeclarationCallableAction.STANDALONE_PROCEDURE
    assert declaration.native_scope is None
    assert declaration.prototype is not None
    assert declaration.prototype.result.semantic_type_name == "Int32"
    assert [(argument.intent, argument.passed_by_value) for argument in declaration.prototype.arguments] == [
        ("in", False)
    ]


def test_pure_prototype_used_as_callback_and_dummy_extent_is_blocked_before_planning():
    module = parse_pyi_text(
        """
@pure
@prototype
def extent_for(n: In(Addr(Int32))) -> Int32: ...

def apply(
    callback: extent_for,
    n: Int32,
    values: Float64[extent_for(n)],
) -> None: ...
""",
        module_name="mixed_prototype_roles",
    )
    complete_semantic_policies(module)

    policy = module.functions[0].metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]
    callback = policy.arguments[0].callback
    declaration = policy.declaration_callables[0]

    assert policy.supported is False
    assert callback is not None
    assert callback.prototype.identity == declaration.prototype.identity
    assert callback.prototype.pure is True
    assert declaration.prototype.pure is True
    assert any("cannot be used as a Python callback" in item for item in policy.blockers)


@pytest.mark.parametrize(
    ("prototype_decorators", "argument", "result", "call", "blocker"),
    [
        ("@prototype", "n: In(Addr(Int32))", "Int32", "extent_for(n)", "must be @pure"),
        (
            "@pure\n@prototype",
            "n: Addr(Int32)",
            "Int32",
            "extent_for(n)",
            "requires exact In(...) direction",
        ),
        (
            "@pure\n@prototype",
            "n: In(Addr(Int32))",
            "Float64",
            "extent_for(n)",
            "must return one scalar integer",
        ),
        (
            "@pure\n@prototype",
            "n: In(Addr(Int32))",
            "Int32",
            "extent_for(n, n)",
            "expects 1 arguments",
        ),
    ],
)
def test_invalid_declaration_callable_contracts_block_before_planning(
    prototype_decorators: str,
    argument: str,
    result: str,
    call: str,
    blocker: str,
):
    module = parse_pyi_text(
        f"""
{prototype_decorators}
def extent_for({argument}) -> {result}: ...

def values(n: Int32) -> Float64[{call}]: ...
""",
        module_name="invalid_external_extent",
    )
    complete_semantic_policies(module)

    policy = module.functions[0].metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]

    assert policy.supported is False
    assert any(blocker in item for item in policy.blockers)
