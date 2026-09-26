"""Exact generic dispatch evidence at the shared wrapper-plan boundary."""

from dataclasses import replace
from pathlib import Path

import pytest

from tests.fortran._support.ownership_policy import parse_pyi_text
from prik.pipeline.pyi import pyi_file_to_semantic_module
from prik.policy.completion import complete_semantic_policies
from prik.policy.models import OverloadMatchKind
from prik.codegen import CBindingGenerator
from prik.pipeline.wrapper import WrapperGenerator
from prik.planning import WrapperPlanner


DEFINED_OPERATORS = Path(__file__).parents[1] / "end_to_end/fixtures/contracts/foperators_f90/foperators_f90.pyi"


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
    assert overload.candidate_ids == (0, 1)


def test_policy_completes_builtin_scalar_family_only_for_reflected_dispatch():
    module = pyi_file_to_semantic_module(DEFINED_OPERATORS)
    complete_semantic_policies(module)
    plan = WrapperPlanner().build(module)
    vector = next(
        surface
        for namespace in plan.namespaces
        for surface in namespace.classes
        if surface.type_identity[1] == "Vector"
    )
    overloads = {overload.python_name: overload for overload in vector.overloads}

    assert [
        match.builtin_scalar_family for candidate in overloads["__radd__"].candidate_matches for match in candidate
    ] == ["float"]
    assert all(
        match.builtin_scalar_family is None
        for candidate in overloads["__add__"].candidate_matches
        for match in candidate
    )


def test_binding_uses_numpy_bool_scalar_predicate_for_storage_specific_logicals():
    """Every logical storage width dispatches on `numpy.bool_`; only the default kind is built end to end."""
    assert {
        name: CBindingGenerator._overload_numpy_scalar_kind(name)
        for name in ("Bool", "Bool8", "Bool16", "Bool32", "Bool64")
    } == dict.fromkeys(("Bool", "Bool8", "Bool16", "Bool32", "Bool64"), "Bool")


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
        WrapperGenerator().generate(invalid)


@pytest.mark.parametrize(
    ("candidate_ids", "code"),
    [
        pytest.param((0, 0), "duplicate-overload-candidate-id", id="duplicate-ids"),
        pytest.param((-1, 1), "invalid-overload-candidate-id", id="id-reserved-for-no-match"),
    ],
)
def test_generator_rejects_invalid_candidate_ids_before_emission(candidate_ids, code: str):
    """`-1` means no candidate matched, so every candidate needs its own non-negative id."""
    plan = _plan()
    namespace = plan.namespaces[0]
    invalid_overload = replace(namespace.overloads[0], candidate_ids=candidate_ids)
    invalid = replace(plan, namespaces=(replace(namespace, overloads=(invalid_overload,)),))

    with pytest.raises(ValueError, match=code):
        WrapperGenerator().generate(invalid)


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
