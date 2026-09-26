"""Exhaustive rank-zero scalar-derived actual/dummy policy proof."""

from __future__ import annotations

from dataclasses import replace

import pytest

from tests.fortran._support.ownership_policy import parse_pyi_text
from prik.policy.completion import complete_semantic_policies
from prik.policy.models import (
    DerivedActualAccess,
    DerivedCallAction,
    DerivedDummyCategory,
    DerivedObjectStorage,
    DerivedOwnerRetention,
    DerivedRelease,
)
from prik.pipeline.wrapper import WrapperGenerator
from prik.planning import WrapperPlanner


CONTRACT = """
from prik.contracts import Aliased, Allocatable, Annotated, Arg, Int32, Pointer, Return, Returns, Value, native_call

class item:
    value: Int32

ordinary_module: item
target_module: Annotated[item, Aliased]
allocatable_module: Allocatable[item]
allocatable_target_module: Allocatable[Annotated[item, Aliased]]
pointer_module: Pointer[item]

def object_dummy(value: item) -> Int32: ...
def target_dummy(value: Annotated[item, Aliased]) -> Int32: ...

@native_call([Allocatable(Arg(0))])
def allocatable_dummy(value: item | None) -> Returns["value", item] | None: ...

@native_call([Allocatable(Arg(0))])
def allocatable_target_dummy(
    value: Annotated[item, Aliased] | None,
) -> Returns["value", Annotated[item, Aliased]] | None: ...

@native_call([Pointer(Arg(0))])
def pointer_dummy(value: item | None) -> Int32: ...

@native_call([Pointer(Arg(0))])
def projected_pointer_dummy(value: item | None) -> Returns["value", item] | None: ...

@native_call([Value(Arg(0))])
def value_dummy(value: item) -> Int32: ...

@native_call([], result=Pointer(Return(0)))
def make_pointer() -> item | None: ...
"""


STORAGES = tuple(DerivedObjectStorage)


def _module():
    module = parse_pyi_text(CONTRACT, module_name="scalar_matrix")
    complete_semantic_policies(module)
    return module


def _plans():
    plan = WrapperPlanner().build(_module())
    return {
        function.symbol_name: function.arguments[0].derived_call
        for function in plan.namespaces[0].functions
        if function.arguments
    }


def _actions(call):
    return {case.actual_storage: case.action for case in call.cases}


S = DerivedObjectStorage
A = DerivedCallAction
_REFERENCE_ACTIONS = {
    S.DIRECT: A.DIRECT_REFERENCE,
    S.ALLOCATABLE_HOLDER: A.HOLDER_REFERENCE,
    S.POINTER_HOLDER: A.POINTEE_REFERENCE,
    S.MODULE_PROXY: A.SCOPED_REFERENCE,
    S.MODULE_TARGET: A.MODULE_ADDRESS,
    S.MODULE_ALLOCATABLE: A.SCOPED_REFERENCE,
    S.MODULE_ALLOCATABLE_TARGET: A.MODULE_ADDRESS,
    S.MODULE_POINTER: A.POINTEE_REFERENCE,
}
_ALLOCATABLE_ACTIONS = {
    storage: A.INCOMPATIBLE
    for storage in STORAGES
    if storage not in {S.ALLOCATABLE_HOLDER, S.MODULE_ALLOCATABLE, S.MODULE_ALLOCATABLE_TARGET}
} | {
    S.ALLOCATABLE_HOLDER: A.ALLOCATABLE_HOLDER,
    S.MODULE_ALLOCATABLE: A.MODULE_ALLOCATABLE_TRANSACTION,
    S.MODULE_ALLOCATABLE_TARGET: A.MODULE_ALLOCATABLE_TRANSACTION,
}
_POINTER_STORAGE_ACTIONS = {S.POINTER_HOLDER: A.POINTER_HOLDER, S.MODULE_POINTER: A.MODULE_POINTER_TRANSACTION}
_REQUIRED_PRESENT = {
    S.ALLOCATABLE_HOLDER,
    S.POINTER_HOLDER,
    S.MODULE_ALLOCATABLE,
    S.MODULE_ALLOCATABLE_TARGET,
    S.MODULE_POINTER,
}

# Each dummy form, the action completed for every actual storage, and which storages must carry a payload.
DUMMY_MATRIX = {
    "object_dummy": (DerivedDummyCategory.OBJECT, _REFERENCE_ACTIONS, _REQUIRED_PRESENT),
    "target_dummy": (DerivedDummyCategory.TARGET, _REFERENCE_ACTIONS, _REQUIRED_PRESENT),
    "allocatable_dummy": (DerivedDummyCategory.ALLOCATABLE, _ALLOCATABLE_ACTIONS, set()),
    "allocatable_target_dummy": (DerivedDummyCategory.ALLOCATABLE_TARGET, _ALLOCATABLE_ACTIONS, set()),
    # A nonprojecting pointer dummy adapts nonpointer storage through a call-local pointer.
    "pointer_dummy": (
        DerivedDummyCategory.POINTER,
        dict.fromkeys(STORAGES, A.POINTER_INPUT_ADAPTER) | _POINTER_STORAGE_ACTIONS,
        None,
    ),
    # Projected pointer writeback requires persistent pointer storage.
    "projected_pointer_dummy": (
        DerivedDummyCategory.POINTER,
        dict.fromkeys(STORAGES, A.INCOMPATIBLE) | _POINTER_STORAGE_ACTIONS,
        None,
    ),
    # An exact typed value is not restricted to bind(C) layout.
    "value_dummy": (DerivedDummyCategory.VALUE, dict.fromkeys(STORAGES, A.TYPED_VALUE_COPY), None),
}


@pytest.mark.parametrize("function_name", tuple(DUMMY_MATRIX))
def test_every_dummy_form_completes_one_exhaustive_action_matrix(function_name):
    dummy, expected_actions, required_present = DUMMY_MATRIX[function_name]
    call = _plans()[function_name]

    assert call.dummy_category is dummy
    assert tuple(case.actual_storage for case in call.cases) == STORAGES
    assert _actions(call) == expected_actions
    assert len({case.abi_code for case in call.cases if case.action is not A.INCOMPATIBLE}) <= 6
    for case in call.cases:
        incompatible = case.action is A.INCOMPATIBLE
        assert incompatible is (case.access is DerivedActualAccess.NONE)
        assert incompatible is bool(case.failure_kind and case.failure_message)
        assert incompatible is (case.abi_code == 0)
    if required_present is not None:
        assert {case.actual_storage for case in call.cases if case.requires_present} == required_present


def test_module_actual_declarations_keep_distinct_runtime_storage():
    plan = WrapperPlanner().build(_module())
    storages = {
        variable.symbol_name: variable.derived.handoff.storage
        for variable in plan.variables
        if variable.derived is not None
    }
    assert storages == {
        "ordinary_module": DerivedObjectStorage.MODULE_PROXY,
        "target_module": DerivedObjectStorage.MODULE_TARGET,
        "allocatable_module": DerivedObjectStorage.MODULE_ALLOCATABLE,
        "allocatable_target_module": DerivedObjectStorage.MODULE_ALLOCATABLE_TARGET,
        "pointer_module": DerivedObjectStorage.MODULE_POINTER,
    }


def test_class_only_derived_methods_do_not_emit_unreachable_scoped_trampolines():
    module = parse_pyi_text(
        """
from prik.contracts import Int32

class item:
    value: Int32

    def read(self) -> Int32: ...
""",
        module_name="class_only",
    )
    complete_semantic_policies(module)
    bridge = next(
        source.text
        for source in WrapperGenerator().generate(WrapperPlanner().build(module)).sources
        if source.path.suffix == ".f90"
    )

    assert "c_funloc(prik_derived_consumer" not in bridge
    assert "bound_self_access == 2_c_int" not in bridge


def test_validation_rejects_a_pointer_holder_without_completed_target_ownership():
    plan = WrapperPlanner().build(_module())
    function = next(item for item in plan.namespaces[0].functions if item.symbol_name == "make_pointer")
    function.results[0].derived = replace(
        function.results[0].derived,
        target_owner_retention=DerivedOwnerRetention.NONE,
        target_release=DerivedRelease.NONE,
    )

    with pytest.raises(ValueError, match="missing-derived-pointer-target-owner"):
        WrapperGenerator().generate(plan)


def test_validation_rejects_a_backend_invented_matrix_gap():
    plan = WrapperPlanner().build(_module())
    argument = next(
        function for function in plan.namespaces[0].functions if function.symbol_name == "object_dummy"
    ).arguments[0]
    argument.derived_call = replace(argument.derived_call, cases=argument.derived_call.cases[:-1])

    with pytest.raises(ValueError, match="incomplete-derived-call-matrix"):
        WrapperGenerator().generate(plan)
