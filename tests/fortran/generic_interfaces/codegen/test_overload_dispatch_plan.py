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
from prik.codegen.c.naming import CBindingNames


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
        if surface.type_identity[1] == "vector"
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


def test_binding_lowers_public_overload_to_candidate_id_switch():
    plan = _plan()
    overload = plan.namespaces[0].overloads[0]

    artifacts = WrapperGenerator().generate(plan)
    c_source = next(source.text for source in artifacts.sources if source.path.suffix == ".c")
    dispatcher = CBindingNames.overload_dispatch_function(overload)

    assert f'{{"convert", (PyCFunction){dispatcher}, METH_VARARGS | METH_KEYWORDS' in c_source
    assert "int candidate_id = -1;" in c_source
    assert "switch (candidate_id)" in c_source
    assert "case 0: {" in c_source
    assert "case 1: {" in c_source
    assert "wrap__prik_overload_convert_0(self, candidate_args, candidate_kwargs)" in c_source
    assert "wrap__prik_overload_convert_1(self, candidate_args, candidate_kwargs)" in c_source
    assert "PyRun_String" not in c_source


def test_binding_uses_numpy_bool_scalar_predicate_for_storage_specific_logicals():
    assert {
        name: CBindingGenerator._overload_numpy_scalar_kind(name)
        for name in ("Bool", "Bool8", "Bool16", "Bool32", "Bool64")
    } == {
        "Bool": "Bool",
        "Bool8": "Bool",
        "Bool16": "Bool",
        "Bool32": "Bool",
        "Bool64": "Bool",
    }


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


def test_generator_rejects_duplicate_candidate_ids_before_emission():
    plan = _plan()
    namespace = plan.namespaces[0]
    overload = namespace.overloads[0]
    duplicate_ids = replace(overload, candidate_ids=(0, 0))
    invalid = replace(plan, namespaces=(replace(namespace, overloads=(duplicate_ids,)),))

    with pytest.raises(ValueError, match="duplicate-overload-candidate-id"):
        WrapperGenerator().generate(invalid)


def test_generator_rejects_candidate_id_reserved_for_no_match():
    plan = _plan()
    namespace = plan.namespaces[0]
    overload = namespace.overloads[0]
    invalid_ids = replace(overload, candidate_ids=(-1, 1))
    invalid = replace(plan, namespaces=(replace(namespace, overloads=(invalid_ids,)),))

    with pytest.raises(ValueError, match="invalid-overload-candidate-id"):
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
