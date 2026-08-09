"""Exact generic dispatch evidence at the shared wrapper-plan boundary."""

from dataclasses import replace

import pytest

from tests.fortran._support.ownership_policy import parse_pyi_text
from prik.semantics.policy_completion import complete_semantic_policies
from prik.semantics.wrapper_policy import OverloadMatchKind
from prik.codegen import WrapperCodeGenerator, WrapperPlanner


def _plan():
    module = parse_pyi_text(
        """
def convert_integer(value: Int32) -> Int32: ...
def convert_real(value: Float64) -> Float64: ...

@overload("convert_integer")
def convert(value: Int32) -> Int32: ...

@overload("convert_real")
def convert(value: Float64) -> Float64: ...
""",
        module_name="generic_api",
    )
    complete_semantic_policies(module)
    return WrapperPlanner().build(module)


def test_plan_records_one_exact_numpy_scalar_predicate_per_candidate():
    overload = _plan().namespaces[0].overloads[0]

    assert overload.python_name == "convert"
    assert [matches[0].kind for matches in overload.candidate_matches] == [
        OverloadMatchKind.NUMPY_SCALAR,
        OverloadMatchKind.NUMPY_SCALAR,
    ]
    assert [matches[0].semantic_type_name for matches in overload.candidate_matches] == [
        "Int32",
        "Float64",
    ]
    assert [matches[0].rank for matches in overload.candidate_matches] == [0, 0]


def test_generator_rejects_ambiguous_edited_overload_plan_before_emission():
    plan = _plan()
    namespace = plan.namespaces[0]
    overload = namespace.overloads[0]
    ambiguous = replace(
        overload,
        candidate_matches=(overload.candidate_matches[0], overload.candidate_matches[0]),
    )
    invalid = replace(plan, namespaces=(replace(namespace, overloads=(ambiguous,)),))

    with pytest.raises(ValueError, match="ambiguous-overload"):
        WrapperCodeGenerator().generate(invalid)


def test_generic_candidate_with_array_of_derived_values_is_blocked_before_lowering():
    module = parse_pyi_text(
        """
class item:
    value: Int32

@private
def inspect_items(values: item[:]) -> None: ...

@overload("inspect_items")
def inspect(values: item[:]) -> None: ...
""",
        module_name="unsupported_generic",
    )
    complete_semantic_policies(module)

    with pytest.raises(ValueError, match="unsupported array of derived values"):
        WrapperPlanner().build(module)
