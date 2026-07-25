"""Compiled Phase 8 proof for every scalar-derived actual/dummy cell."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

import numpy as np
import pytest

from tests.wrapper.fortran._support import _import_from_build_dir, wrapper_source
from x2py import build_pyi_extension

SOURCE = wrapper_source("fscalar_derived_actual_dummy_matrix_f90.f90")
CONTRACT = Path(__file__).parent / "contracts" / "fscalar_derived_actual_dummy_matrix_phase8" / "__init__.pyi"


@dataclass(frozen=True)
class ActualCase:
    """One documented declaration row and its runtime carrier family."""

    name: str
    declaration: str
    origin: str
    storage: str
    expected: int


ACTUAL_CASES = (
    ActualCase("nonmodule_object", "type(item) :: var", "nonmodule", "direct", 11),
    ActualCase("module_object", "type(item) :: var", "module", "direct", 10),
    ActualCase("nonmodule_target", "type(item), target :: var", "nonmodule", "direct", 13),
    ActualCase("module_target", "type(item), target :: var", "module", "direct", 20),
    ActualCase("nonmodule_allocatable", "type(item), allocatable :: var", "nonmodule", "allocatable", 15),
    ActualCase("module_allocatable", "type(item), allocatable :: var", "module", "allocatable", 30),
    ActualCase(
        "nonmodule_allocatable_target",
        "type(item), allocatable, target :: var",
        "nonmodule",
        "allocatable",
        17,
    ),
    ActualCase(
        "module_allocatable_target",
        "type(item), allocatable, target :: var",
        "module",
        "allocatable",
        40,
    ),
    ActualCase("nonmodule_pointer", "type(item), pointer :: var", "nonmodule", "pointer", 50),
    ActualCase("module_pointer", "type(item), pointer :: var", "module", "pointer", 50),
)

DUMMY_READERS = {
    "O": "read_object",
    "T": "read_target",
    "A": "read_allocatable",
    "AT": "read_allocatable_target",
    "P": "read_pointer_input",
    "V": "read_value",
}


@dataclass(frozen=True)
class MatrixBuild:
    module: object
    left_module: object
    right_module: object
    result: object


@pytest.fixture(scope="module")
def scalar_matrix(tmp_path_factory) -> MatrixBuild:
    output_dir = tmp_path_factory.mktemp("phase8_scalar_derived_matrix")
    result = build_pyi_extension(
        CONTRACT,
        native_fortran_sources=[SOURCE],
        output_dir=output_dir,
    )
    package = _import_from_build_dir(result.module_name, result.output_dir)
    return MatrixBuild(
        package.fscalar_derived_actual_dummy_matrix_f90,
        package.phase8_left_types,
        package.phase8_right_types,
        result,
    )


def _actual(module, case: ActualCase):
    """Construct the exact row without hiding storage selection in a test fixture."""
    if case.name == "nonmodule_object":
        return module.make_item(np.int32(case.expected))
    if case.name == "module_object":
        return module.ordinary_module
    if case.name == "nonmodule_target":
        return module.make_target_item(np.int32(case.expected))
    if case.name == "module_target":
        return module.target_module
    if case.name == "nonmodule_allocatable":
        return module.make_allocatable_item(np.int32(case.expected), True)
    if case.name == "module_allocatable":
        return module.allocatable_module
    if case.name == "nonmodule_allocatable_target":
        return module.make_allocatable_target_item(np.int32(case.expected), True)
    if case.name == "module_allocatable_target":
        return module.allocatable_target_module
    if case.name == "nonmodule_pointer":
        return module.make_pointer_item(np.int32(1))
    if case.name == "module_pointer":
        return module.pointer_module
    raise AssertionError(f"unhandled actual case {case.name!r}")


def _matrix_cell_is_legal(case: ActualCase, dummy: str) -> bool:
    if dummy in {"O", "T", "P", "V"}:
        return True
    return case.storage == "allocatable"


@pytest.mark.parametrize("case", ACTUAL_CASES, ids=lambda case: case.name)
@pytest.mark.parametrize("dummy", tuple(DUMMY_READERS))
def test_all_sixty_actual_dummy_cells(scalar_matrix, case: ActualCase, dummy: str):
    """Exercise every cell of the documented 10-row by 6-column matrix."""
    module = scalar_matrix.module
    module.reset_state()
    actual = _actual(module, case)
    reader = getattr(module, DUMMY_READERS[dummy])

    if _matrix_cell_is_legal(case, dummy):
        assert reader(actual) == case.expected
    else:
        with pytest.raises(TypeError, match="allocatable-derived-actual-required"):
            reader(actual)


@pytest.mark.parametrize("case", ACTUAL_CASES, ids=lambda case: case.name)
def test_reassociable_pointer_dummy_requires_pointer_storage(scalar_matrix, case: ActualCase):
    """Known pointer writeback accepts P rows and rejects every nonpointer row."""
    module = scalar_matrix.module
    module.reset_state()
    actual = _actual(module, case)

    if case.storage == "pointer":
        returned = module.set_pointer(actual, np.int32(2))
        assert returned is actual
        assert actual.value == 60
    else:
        with pytest.raises(TypeError, match="pointer-derived-actual-required"):
            module.set_pointer(actual, np.int32(2))


@dataclass(frozen=True)
class EmptyCase:
    name: str
    storage: str


EMPTY_CASES = (
    EmptyCase("nonmodule_allocatable", "allocatable"),
    EmptyCase("module_allocatable", "allocatable"),
    EmptyCase("module_allocatable_target", "allocatable"),
    EmptyCase("nonmodule_pointer", "pointer"),
    EmptyCase("module_pointer", "pointer"),
)


def _empty_actual(module, case: EmptyCase):
    module.reset_state()
    if case.name == "nonmodule_allocatable":
        return module.make_allocatable_item(np.int32(1), False)
    if case.name == "module_allocatable":
        value = module.allocatable_module
        module.clear_allocatable_module()
        return value
    if case.name == "module_allocatable_target":
        value = module.allocatable_target_module
        module.clear_allocatable_target_module()
        return value
    if case.name == "nonmodule_pointer":
        return module.make_pointer_item(np.int32(0))
    if case.name == "module_pointer":
        value = module.pointer_module
        module.clear_pointer_module()
        return value
    raise AssertionError(f"unhandled empty case {case.name!r}")


@pytest.mark.parametrize("case", EMPTY_CASES, ids=lambda case: case.name)
@pytest.mark.parametrize("dummy", tuple(DUMMY_READERS))
def test_empty_descriptor_states_follow_dummy_requirements(scalar_matrix, case: EmptyCase, dummy: str):
    """Absent payloads fail only where a payload, not a descriptor, is required."""
    module = scalar_matrix.module
    actual = _empty_actual(module, case)
    reader = getattr(module, DUMMY_READERS[dummy])

    if dummy in {"O", "T", "V"}:
        with pytest.raises(ValueError, match=r"derived payload.*not present"):
            reader(actual)
        return
    if dummy == "P":
        if case.storage == "pointer":
            assert reader(actual) == -1
        else:
            with pytest.raises(ValueError, match=r"derived payload.*not present"):
                reader(actual)
        return
    if case.storage == "allocatable":
        assert reader(actual) == -1
    else:
        with pytest.raises(TypeError, match="allocatable-derived-actual-required"):
            reader(actual)


def test_empty_module_getters_return_persistent_live_proxies(scalar_matrix):
    module = scalar_matrix.module
    module.reset_state()
    old_allocatable = module.allocatable_module
    old_pointer = module.pointer_module
    module.clear_allocatable_module()
    module.clear_pointer_module()

    for value in (old_allocatable, module.allocatable_module):
        assert isinstance(value, module.item)
        with pytest.raises(ReferenceError, match="not currently present"):
            _ = value.value
    for value in (old_pointer, module.pointer_module):
        assert isinstance(value, module.item)
        with pytest.raises(ReferenceError, match="not currently present"):
            _ = value.value


def test_wrapper_owned_empty_holders_can_be_filled_without_replacement(scalar_matrix):
    module = scalar_matrix.module
    module.reset_state()
    allocatable = module.make_allocatable_item(np.int32(1), False)
    allocatable_target = module.make_allocatable_target_item(np.int32(2), False)
    pointer = module.make_pointer_item(np.int32(0))

    with pytest.raises(ReferenceError, match="unallocated"):
        _ = allocatable.value
    with pytest.raises(ReferenceError, match="unallocated"):
        _ = allocatable_target.value
    with pytest.raises(ReferenceError, match="disassociated"):
        _ = pointer.value

    assert module.set_allocatable(allocatable, np.int32(7)) is allocatable
    assert module.set_allocatable_target(allocatable_target, np.int32(8)) is allocatable_target
    assert module.set_pointer(pointer, np.int32(2)) is pointer
    assert (allocatable.value, allocatable_target.value, pointer.value) == (7, 8, 60)


def test_pointer_holder_retains_native_owner_and_tracks_allocated_target_lifetime(scalar_matrix):
    module = scalar_matrix.module
    module.reset_state()
    pointer = module.make_pointer_item(np.int32(0))

    assert pointer._x2py_owner is module
    assert module.set_pointer(pointer, np.int32(3)) is pointer
    assert pointer.value == 70
    assert module.set_pointer(pointer, np.int32(4)) is pointer
    with pytest.raises(ReferenceError, match="disassociated"):
        _ = pointer.value


def test_module_descriptor_transactions_preserve_empty_and_recreated_state(scalar_matrix):
    module = scalar_matrix.module
    module.reset_state()
    allocatable = module.allocatable_module
    pointer = module.pointer_module

    assert module.set_allocatable(allocatable, np.int32(-1)) is allocatable
    with pytest.raises(ReferenceError, match="not currently present"):
        _ = allocatable.value
    assert module.set_allocatable(allocatable, np.int32(81)) is allocatable
    assert allocatable.value == 81

    assert module.set_pointer(pointer, np.int32(0)) is pointer
    with pytest.raises(ReferenceError, match="not currently present"):
        _ = pointer.value
    assert module.set_pointer(pointer, np.int32(2)) is pointer
    assert pointer.value == 60
    assert module.set_pointer(pointer, np.int32(3)) is pointer
    assert pointer.value == 70
    assert module.set_pointer(pointer, np.int32(4)) is pointer
    with pytest.raises(ReferenceError, match="not currently present"):
        _ = pointer.value


@pytest.mark.parametrize("origin", ("nonmodule", "module"))
def test_one_call_mutates_three_distinct_descriptor_origins(scalar_matrix, origin: str):
    module = scalar_matrix.module
    module.reset_state()
    if origin == "nonmodule":
        first = module.make_allocatable_item(np.int32(3), True)
        second = module.make_allocatable_target_item(np.int32(4), True)
        third = module.make_pointer_item(np.int32(1))
        expected = (8, 9, 60)
    else:
        first = module.allocatable_module
        second = module.allocatable_target_module
        third = module.pointer_module
        expected = (35, 45, 60)

    returned = module.mutate_three_descriptors(first, second, third, np.int32(5))
    assert returned == (first, second, third)
    assert all(value is original for value, original in zip(returned, (first, second, third), strict=True))
    assert tuple(int(value.value) for value in returned) == expected


def test_one_call_uses_all_six_dummy_forms_and_optional_arguments_stay_linear(scalar_matrix):
    module = scalar_matrix.module
    module.reset_state()
    arguments = (
        module.make_item(np.int32(1)),
        module.target_module,
        module.make_allocatable_item(np.int32(3), True),
        module.allocatable_target_module,
        module.make_pointer_item(np.int32(2)),
        module.ordinary_module,
    )
    assert module.read_six_forms(*arguments) == 134

    first = module.ordinary_module
    second = module.allocatable_module
    assert module.read_optional() == 0
    assert module.read_optional(first) == 10
    assert module.read_optional(None, second) == 30
    assert module.read_optional(first, second) == 40


def test_sequence_derived_value_uses_the_same_typed_opaque_call_path(scalar_matrix):
    module = scalar_matrix.module
    value = module.make_sequence_item(np.int32(23))

    assert isinstance(value, module.sequence_item)
    assert module.read_sequence_value(value) == 23


def test_qualified_same_short_name_types_keep_exact_native_identity(scalar_matrix):
    module = scalar_matrix.module
    left = scalar_matrix.left_module.make_item(np.int32(3))
    right = scalar_matrix.right_module.make_item(np.int32(7))

    assert type(left) is not type(right)
    assert module.read_qualified(left, right) == 307
    for values, expected in (
        ((right, left), "left_item.*left"),
        ((left, left), "right_item.*right"),
        ((right, right), "left_item.*left"),
    ):
        with pytest.raises(TypeError, match=expected):
            module.read_qualified(*values)


def test_module_origins_from_separate_modules_keep_type_specific_callbacks(scalar_matrix):
    module = scalar_matrix.module
    left = scalar_matrix.left_module.state
    right = scalar_matrix.right_module.state

    assert module.read_qualified(left, right) == 307
    with pytest.raises(TypeError, match=r"left_item.*left"):
        module.read_qualified(right, left)


def test_duplicate_origins_share_reads_and_reject_writes_before_native_call(scalar_matrix):
    module = scalar_matrix.module
    module.reset_state()
    value = module.ordinary_module
    assert module.read_duplicate(value, value) == 20

    with pytest.raises(TypeError, match="repeated in writable arguments first and second"):
        module.mutate_duplicate(value, value)
    assert module.get_writable_call_count() == 0
    assert value.value == 10

    other = module.target_module
    returned = module.mutate_duplicate(value, other)
    assert returned == (value, other)
    assert returned[0] is value
    assert returned[1] is other
    assert (value.value, other.value) == (11, 21)
    assert module.get_writable_call_count() == 1


def test_move_alloc_round_trip_preserves_target_association(scalar_matrix):
    module = scalar_matrix.module
    module.reset_state()
    value = module.allocatable_target_module
    module.associate_allocation_follower()
    assert module.allocation_follower_value() == 40

    assert module.set_allocatable_target(value, np.int32(77)) is value
    assert value.value == 77
    assert module.allocation_follower_value() == 77


def _start_busy_origin(module, value):
    errors = []

    def hold():
        try:
            module.hold_allocatable(value, np.int32(500))
        except BaseException as exc:  # pragma: no cover - asserted in the caller
            errors.append(exc)

    thread = threading.Thread(target=hold)
    thread.start()
    deadline = time.monotonic() + 0.3
    while time.monotonic() < deadline:
        try:
            module.read_allocatable(value)
        except RuntimeError:
            return thread, errors
        time.sleep(0.005)
    thread.join()
    pytest.fail("module descriptor origin never entered its active transaction state")


def _start_busy_scoped_origin(module, value):
    errors = []

    def hold():
        try:
            module.hold_object(value, np.int32(500))
        except BaseException as exc:  # pragma: no cover - asserted in the caller
            errors.append(exc)

    thread = threading.Thread(target=hold)
    thread.start()
    deadline = time.monotonic() + 0.3
    while time.monotonic() < deadline:
        try:
            module.read_object(value)
        except RuntimeError:
            return thread, errors
        time.sleep(0.005)
    thread.join()
    pytest.fail("module object origin never entered its active scoped state")


def test_concurrent_origin_use_is_rejected_and_restored(scalar_matrix):
    module = scalar_matrix.module
    module.reset_state()
    value = module.allocatable_module
    thread, errors = _start_busy_origin(module, value)
    try:
        with pytest.raises(RuntimeError, match=r"origin failure.*status 2"):
            module.read_allocatable(value)
    finally:
        thread.join()
    assert errors == []
    assert value.value == 31


def test_later_acquisition_failure_rolls_back_earlier_origins(scalar_matrix):
    module = scalar_matrix.module
    module.reset_state()
    first = module.allocatable_module
    busy_second = module.allocatable_target_module
    third = module.pointer_module
    thread, errors = _start_busy_origin(module, busy_second)
    try:
        with pytest.raises(RuntimeError, match=r"argument second.*status 2"):
            module.mutate_three_descriptors(first, busy_second, third, np.int32(5))
        assert first.value == 30
        assert third.value == 50
    finally:
        thread.join()
    assert errors == []
    assert (first.value, busy_second.value, third.value) == (30, 41, 50)


def test_nested_scoped_failure_releases_every_entered_origin(scalar_matrix):
    module = scalar_matrix.module
    module.reset_state()
    first = module.ordinary_module_two
    busy_second = module.ordinary_module
    thread, errors = _start_busy_scoped_origin(module, busy_second)
    try:
        with pytest.raises(RuntimeError, match=r"argument second.*status 2"):
            module.read_duplicate(first, busy_second)
        assert first.value == 12
    finally:
        thread.join()
    assert errors == []
    assert busy_second.value == 11
    assert module.read_duplicate(first, busy_second) == 23


def test_injected_first_acquisition_failure_leaves_origin_usable(scalar_matrix, monkeypatch):
    module = scalar_matrix.module
    module.reset_state()
    value = module.allocatable_module
    monkeypatch.setenv(
        "X2PY_WRAPPER_FAIL_DERIVED_ORIGIN",
        "checkout:before:allocatable_module",
    )
    with pytest.raises(RuntimeError, match=r"argument value.*status 7"):
        module.set_allocatable(value, np.int32(55))
    assert value.value == 30

    monkeypatch.delenv("X2PY_WRAPPER_FAIL_DERIVED_ORIGIN")
    assert module.set_allocatable(value, np.int32(55)) is value
    assert value.value == 55


def test_injected_scoped_and_post_native_failures_restore_before_raising(scalar_matrix, monkeypatch):
    module = scalar_matrix.module
    module.reset_state()
    ordinary = module.ordinary_module
    monkeypatch.setenv(
        "X2PY_WRAPPER_FAIL_DERIVED_ORIGIN",
        "scoped:after:ordinary_module",
    )
    with pytest.raises(RuntimeError, match=r"argument value.*status 7"):
        module.increment_object(ordinary, np.int32(2))
    monkeypatch.delenv("X2PY_WRAPPER_FAIL_DERIVED_ORIGIN")
    assert ordinary.value == 12
    assert module.read_object(ordinary) == 12

    first = module.allocatable_module
    second = module.allocatable_target_module
    third = module.pointer_module
    monkeypatch.setenv("X2PY_WRAPPER_FAIL_DERIVED_AFTER_NATIVE", "1")
    with pytest.raises(RuntimeError, match="injected derived failure after native return"):
        module.mutate_three_descriptors(first, second, third, np.int32(5))
    monkeypatch.delenv("X2PY_WRAPPER_FAIL_DERIVED_AFTER_NATIVE")
    assert (first.value, second.value, third.value) == (35, 45, 60)


@pytest.mark.parametrize(
    ("selector", "argument", "poisoned_reader"),
    (
        ("restore:after:allocatable_module", "first", "read_allocatable"),
        ("restore:after:pointer_module", "third", "read_pointer_input"),
    ),
)
def test_injected_restoration_failure_poison_isolated_origin_and_continues_cleanup(
    scalar_matrix,
    selector: str,
    argument: str,
    poisoned_reader: str,
):
    result = scalar_matrix.result
    script = """
from pathlib import Path
import numpy as np
from tests.wrapper.fortran._support import _import_from_build_dir

package = _import_from_build_dir(__import__('sys').argv[1], Path(__import__('sys').argv[2]))
module = package.fscalar_derived_actual_dummy_matrix_f90
module.reset_state()
first = module.allocatable_module
second = module.allocatable_target_module
third = module.pointer_module
try:
    module.mutate_three_descriptors(first, second, third, np.int32(5))
except RuntimeError as exc:
    assert f"argument {__import__('sys').argv[4]}" in str(exc)
    assert "status 7" in str(exc)
else:
    raise AssertionError("restoration fault did not propagate")
del __import__('os').environ['X2PY_WRAPPER_FAIL_DERIVED_ORIGIN']
value = first if __import__('sys').argv[5] == 'read_allocatable' else third
try:
    getattr(module, __import__('sys').argv[5])(value)
except RuntimeError as exc:
    assert "status 3" in str(exc)
else:
    raise AssertionError("failed origin was not poisoned")
assert second.value == 45
if __import__('sys').argv[5] == 'read_allocatable':
    assert third.value == 60
else:
    assert first.value == 35
print("cleanup-complete")
"""
    environment = dict(os.environ)
    environment["X2PY_WRAPPER_FAIL_DERIVED_ORIGIN"] = selector
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            script,
            result.module_name,
            str(result.output_dir),
            selector,
            argument,
            poisoned_reader,
        ],
        cwd=Path(__file__).parents[4],
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "cleanup-complete"


def test_generated_artifacts_keep_matrix_dispatch_linear_and_descriptor_free(scalar_matrix):
    result = scalar_matrix.result
    c_source = (result.output_dir / f"{result.module_name}_wrapper.c").read_text(encoding="utf-8")
    bridge = (result.output_dir / f"bind_c_{result.module_name}_wrapper.f90").read_text(encoding="utf-8")

    assert "x2py_extract_derived_argument" in c_source
    assert "x2py_validate_derived_aliases" in c_source
    assert "atomic_compare_exchange_strong" in c_source
    assert "x2py_derived_ready" in bridge
    assert "move_alloc" in bridge
    assert sum(line.lstrip().startswith("result = native_read_six_forms(") for line in bridge.splitlines()) == 1
    assert bridge.count("native_read_optional(") == 1
    assert bridge.count("native_read_sequence_value(") == 1
    assert "x2py_optional_first" in bridge
    assert "x2py_optional_second" in bridge
    type_aliases = {
        line.strip().split(" =>", maxsplit=1)[0]
        for line in bridge.splitlines()
        if line.strip().startswith("x2py_type_") and "=> item" in line
    }
    assert len(type_aliases) == 3
    assert "const char * type_symbol" in c_source
    assert "CFI_cdesc_t" not in bridge
    assert max(map(len, bridge.splitlines())) <= 132
