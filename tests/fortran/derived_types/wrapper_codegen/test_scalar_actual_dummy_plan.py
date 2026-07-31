"""Exhaustive rank-zero scalar-derived actual/dummy policy proof."""

from __future__ import annotations

from dataclasses import replace

import pytest

from tests.fortran._support.ownership_policy import parse_pyi_text
from x2py.semantics.policy_completion import complete_semantic_policies
from x2py.semantics.wrapper_policy import (
    DerivedActualAccess,
    DerivedCallAction,
    DerivedDummyCategory,
    DerivedObjectStorage,
    DerivedOwnerRetention,
    DerivedRelease,
)
from x2py.wrapper_codegen import WrapperCodeGenerator, WrapperPlanner


CONTRACT = """
from x2py.contracts import Aliased, Allocatable, Annotated, Arg, Int32, Pointer, Return, Returns, Value, native_call

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


def _accesses(call):
    return {case.actual_storage: case.access for case in call.cases}


@pytest.mark.parametrize(
    ("function_name", "dummy"),
    [
        ("object_dummy", DerivedDummyCategory.OBJECT),
        ("target_dummy", DerivedDummyCategory.TARGET),
        ("allocatable_dummy", DerivedDummyCategory.ALLOCATABLE),
        ("allocatable_target_dummy", DerivedDummyCategory.ALLOCATABLE_TARGET),
        ("pointer_dummy", DerivedDummyCategory.POINTER),
        ("value_dummy", DerivedDummyCategory.VALUE),
    ],
)
def test_every_dummy_form_has_one_exhaustive_completed_matrix(function_name, dummy):
    call = _plans()[function_name]

    assert call.dummy_category is dummy
    assert tuple(case.actual_storage for case in call.cases) == STORAGES
    assert len({case.abi_code for case in call.cases if case.action is not DerivedCallAction.INCOMPATIBLE}) <= 6
    for case in call.cases:
        incompatible = case.action is DerivedCallAction.INCOMPATIBLE
        assert incompatible is (case.access is DerivedActualAccess.NONE)
        assert incompatible is bool(case.failure_kind and case.failure_message)
        assert incompatible is (case.abi_code == 0)


@pytest.mark.parametrize("function_name", ["object_dummy", "target_dummy"])
def test_object_and_target_dummies_cover_direct_scoped_holder_and_pointee_actuals(function_name):
    call = _plans()[function_name]
    actions = _actions(call)

    assert actions == {
        DerivedObjectStorage.DIRECT: DerivedCallAction.DIRECT_REFERENCE,
        DerivedObjectStorage.ALLOCATABLE_HOLDER: DerivedCallAction.HOLDER_REFERENCE,
        DerivedObjectStorage.POINTER_HOLDER: DerivedCallAction.POINTEE_REFERENCE,
        DerivedObjectStorage.MODULE_PROXY: DerivedCallAction.SCOPED_REFERENCE,
        DerivedObjectStorage.MODULE_TARGET: DerivedCallAction.MODULE_ADDRESS,
        DerivedObjectStorage.MODULE_ALLOCATABLE: DerivedCallAction.SCOPED_REFERENCE,
        DerivedObjectStorage.MODULE_ALLOCATABLE_TARGET: DerivedCallAction.MODULE_ADDRESS,
        DerivedObjectStorage.MODULE_POINTER: DerivedCallAction.POINTEE_REFERENCE,
    }
    required = {case.actual_storage for case in call.cases if case.requires_present}
    assert required == {
        DerivedObjectStorage.ALLOCATABLE_HOLDER,
        DerivedObjectStorage.POINTER_HOLDER,
        DerivedObjectStorage.MODULE_ALLOCATABLE,
        DerivedObjectStorage.MODULE_ALLOCATABLE_TARGET,
        DerivedObjectStorage.MODULE_POINTER,
    }


@pytest.mark.parametrize("function_name", ["allocatable_dummy", "allocatable_target_dummy"])
def test_allocatable_dummies_accept_only_holders_and_module_transactions(function_name):
    call = _plans()[function_name]
    actions = _actions(call)
    compatible = {
        storage: action for storage, action in actions.items() if action is not DerivedCallAction.INCOMPATIBLE
    }

    assert compatible == {
        DerivedObjectStorage.ALLOCATABLE_HOLDER: DerivedCallAction.ALLOCATABLE_HOLDER,
        DerivedObjectStorage.MODULE_ALLOCATABLE: DerivedCallAction.MODULE_ALLOCATABLE_TRANSACTION,
        DerivedObjectStorage.MODULE_ALLOCATABLE_TARGET: DerivedCallAction.MODULE_ALLOCATABLE_TRANSACTION,
    }
    assert all(not case.requires_present for case in call.cases if case.action is not DerivedCallAction.INCOMPATIBLE)


def test_nonprojecting_pointer_dummy_uses_call_local_adapters_for_nonpointer_storage():
    call = _plans()["pointer_dummy"]
    actions = _actions(call)

    assert actions[DerivedObjectStorage.POINTER_HOLDER] is DerivedCallAction.POINTER_HOLDER
    assert actions[DerivedObjectStorage.MODULE_POINTER] is DerivedCallAction.MODULE_POINTER_TRANSACTION
    assert all(
        actions[storage] is DerivedCallAction.POINTER_INPUT_ADAPTER
        for storage in STORAGES
        if storage not in {DerivedObjectStorage.POINTER_HOLDER, DerivedObjectStorage.MODULE_POINTER}
    )


def test_projected_pointer_writeback_requires_persistent_pointer_storage():
    call = _plans()["projected_pointer_dummy"]
    actions = _actions(call)

    assert actions[DerivedObjectStorage.POINTER_HOLDER] is DerivedCallAction.POINTER_HOLDER
    assert actions[DerivedObjectStorage.MODULE_POINTER] is DerivedCallAction.MODULE_POINTER_TRANSACTION
    assert all(
        actions[storage] is DerivedCallAction.INCOMPATIBLE
        for storage in STORAGES
        if storage not in {DerivedObjectStorage.POINTER_HOLDER, DerivedObjectStorage.MODULE_POINTER}
    )


def test_exact_typed_value_is_not_restricted_to_bind_c_layout():
    call = _plans()["value_dummy"]
    assert all(case.action is DerivedCallAction.TYPED_VALUE_COPY for case in call.cases)


def test_module_actual_declarations_keep_distinct_runtime_storage():
    namespace = WrapperPlanner().build(_module()).namespaces[0]
    storages = {
        variable.symbol_name: variable.derived.handoff.storage
        for variable in namespace.variables
        if variable.derived is not None
    }
    assert storages == {
        "ordinary_module": DerivedObjectStorage.MODULE_PROXY,
        "target_module": DerivedObjectStorage.MODULE_TARGET,
        "allocatable_module": DerivedObjectStorage.MODULE_ALLOCATABLE,
        "allocatable_target_module": DerivedObjectStorage.MODULE_ALLOCATABLE_TARGET,
        "pointer_module": DerivedObjectStorage.MODULE_POINTER,
    }


def test_pointer_result_uses_a_persistent_holder_instead_of_the_removed_blocker():
    module = _module()
    result = next(
        function.results[0]
        for function in WrapperPlanner().build(module).namespaces[0].functions
        if function.symbol_name == "make_pointer"
    )

    assert result.derived.storage is DerivedObjectStorage.POINTER_HOLDER
    assert result.derived.target_owner_retention is DerivedOwnerRetention.NATIVE_MODULE
    assert result.derived.target_release is DerivedRelease.NATIVE_OWNER


def test_class_only_derived_methods_do_not_emit_unreachable_scoped_trampolines():
    module = parse_pyi_text(
        """
from x2py.contracts import Int32

class item:
    value: Int32

    def read(self) -> Int32: ...
""",
        module_name="class_only",
    )
    complete_semantic_policies(module)
    bridge = next(
        source.text
        for source in WrapperCodeGenerator().generate(WrapperPlanner().build(module)).sources
        if source.path.suffix == ".f90"
    )

    assert "c_funloc(x2py_derived_consumer" not in bridge
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
        WrapperCodeGenerator().generate(plan)


def test_validation_rejects_a_backend_invented_matrix_gap():
    plan = WrapperPlanner().build(_module())
    argument = next(
        function for function in plan.namespaces[0].functions if function.symbol_name == "object_dummy"
    ).arguments[0]
    argument.derived_call = replace(argument.derived_call, cases=argument.derived_call.cases[:-1])

    with pytest.raises(ValueError, match="incomplete-derived-call-matrix"):
        WrapperCodeGenerator().generate(plan)


def test_artifacts_emit_shared_holders_typed_origin_operations_and_one_native_call():
    artifacts = WrapperCodeGenerator().generate(WrapperPlanner().build(_module()))
    c_source = next(source.text for source in artifacts.sources if source.path.suffix == ".c")
    bridge = next(source.text for source in artifacts.sources if source.path.suffix == ".f90")

    assert bridge.count("type :: x2py_item_allocatable_holder") == 1
    assert bridge.count("type :: x2py_item_pointer_holder") == 1
    assert "abstract interface" in bridge
    assert "c_f_procpointer" in bridge
    assert "c_funloc(x2py_derived_consumer" in bridge
    assert "move_alloc" in bridge
    assert bridge.count("native_object_dummy(") == 1
    assert "x2py_derived_origin_ops" in c_source
    assert "atomic_compare_exchange_strong" in c_source
    assert "CFI_cdesc_t" not in bridge
