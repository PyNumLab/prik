"""Compiled evidence for distinct derived-object runtime mechanisms."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import (
    _build_generated_pyi_and_import,
    _build_source_and_import,
    _compile_native_object,
    _import_from_build_dir,
    _sole_native_module,
)
from prik import build_pyi_extension
from prik.runtime.handles import AllocatableArray
from tests.fortran._support.paths import FORTRAN_ROOT

FIXTURES = Path(__file__).parent / "fixtures"
EDITED_CONTRACTS = FIXTURES / "edited_contracts"
PLAIN_MODULE_SOURCE = FIXTURES / "native" / "fmodule_derived_snapshot_f90.f90"
PLAIN_MODULE_CONTRACT = EDITED_CONTRACTS / "module_live_proxy" / "__init__.pyi"
DERIVED_CONSTANT_SOURCE = FORTRAN_ROOT / "modules" / "end_to_end" / "fixtures" / "native" / "fmodule_vars_f90.f90"
pytestmark = pytest.mark.fortran_end_to_end

NATIVE_FIXTURES = Path(__file__).parent / "fixtures" / "native"
DERIVED_CONSTANT_CONTRACT = """\
from prik.contracts import Final, Int32

class rgb_color:
    r: Int32
    g: Int32
    b: Int32

black: Final[rgb_color]

def black_sum() -> Int32: ...
"""
STRING_FIELD_SOURCE = (NATIVE_FIXTURES / "fderived_string_field.f90").read_text(encoding="utf-8")
STRING_FIELD_CONTRACT = """\
from prik.contracts import Aliased, Annotated, String

class record:
    label: String[8]

current: Annotated[record, Aliased]

def current_label() -> String[8]: ...
def reset_label() -> None: ...
"""
VALUE_AND_OPTIONAL_SOURCE = (NATIVE_FIXTURES / "fderived_value_optional.f90").read_text(encoding="utf-8")
SCALAR_DESCRIPTOR_FIELD_SOURCE = NATIVE_FIXTURES / "fderived_scalar_descriptor_fields.f90"
VALUE_AND_OPTIONAL_CONTRACT = """\
from prik.contracts import Arg, Float64, Returns, Value, native_abi, native_call

@native_abi("c")
class point:
    x: Float64
    y: Float64

def make_point(x: Float64, y: Float64) -> point: ...
@native_call([Value(Arg(0))])
def score_by_value(value: point) -> Float64: ...
def optional_sum(value: point | None = ...) -> Float64: ...
def update_point(value: point) -> Returns["value", point]: ...
def fill_point(value: point) -> Returns["value", point]: ...
"""


def test_plain_module_derived_proxy_reads_and_writes_live_members(tmp_path: Path):
    native_object = _compile_native_object(PLAIN_MODULE_SOURCE, tmp_path / "native")
    result = build_pyi_extension(
        PLAIN_MODULE_CONTRACT,
        native_objects=[native_object],
        native_include_dirs=[native_object.parent],
        output_dir=tmp_path / "wrapper_plan",
    )
    module = _sole_native_module(_import_from_build_dir(result.module_name, result.output_dir))

    module.initialise_current(np.int32(2))
    first = module.current
    second = module.current
    assert isinstance(first, module.box)
    assert isinstance(second, module.box)
    assert first is not second
    assert first._prik_owner is module
    assert second._prik_owner is module
    assert first.scalar == np.int32(7)
    first_fixed = first.fixed
    np.testing.assert_allclose(first_fixed, np.array([1.5, 2.5], dtype=np.float64))
    assert first_fixed.base is first
    values = first.values
    assert isinstance(values, AllocatableArray)
    assert values.owner is first
    values_view = values.to_numpy()
    np.testing.assert_allclose(values_view, np.array([1.0, 2.0], dtype=np.float64))
    assert first.nested.id == np.int32(11)
    with pytest.raises(AttributeError):
        first.fixed = np.array([0.0, 0.0], dtype=np.float64)
    with pytest.raises(AttributeError):
        first.values = values

    first.scalar = np.int32(20)
    first_fixed[0] = np.float64(4.5)
    values_view[1] = np.float64(8.0)
    first.nested.id = np.int32(30)
    assert second.scalar == np.int32(20)
    np.testing.assert_allclose(second.fixed, np.array([4.5, 2.5], dtype=np.float64))
    assert second.nested.id == np.int32(30)
    assert module.current_total() == np.float64(66.0)

    child = first.nested
    assert child._prik_owner is first
    del first
    child.id = np.int32(31)
    assert module.current.nested.id == np.int32(31)

    module.mutate_current()
    assert second.scalar == np.int32(30)
    np.testing.assert_allclose(first_fixed, np.array([104.5, 102.5], dtype=np.float64))
    np.testing.assert_allclose(values_view, np.array([1001.0, 1008.0], dtype=np.float64))
    assert child.id == np.int32(131)

    independent = values.to_numpy().copy()
    values.resize((3,))
    replacement = values.to_numpy()
    replacement[:] = np.array([3.0, 4.0, 5.0], dtype=np.float64)
    np.testing.assert_allclose(values.to_numpy(), np.array([3.0, 4.0, 5.0], dtype=np.float64))
    np.testing.assert_allclose(independent, np.array([1001.0, 1008.0], dtype=np.float64))
    values.deallocate()
    assert values.to_numpy() is None
    with pytest.raises(AttributeError):
        module.current = second

    generated_fortran = (result.output_dir / "bind_c_module_live_proxy_wrapper.f90").read_text(encoding="utf-8")
    assert "c_loc(native_current)" not in generated_fortran
    assert "native_current%scalar" in generated_fortran
    assert "native_current%nested%id" in generated_fortran


def test_derived_module_constant_returns_independent_owned_values(tmp_path: Path):
    native_object = _compile_native_object(DERIVED_CONSTANT_SOURCE, tmp_path / "native")
    contract = tmp_path / "contract" / "fmodule_vars_f90.pyi"
    contract.parent.mkdir()
    contract.write_text(DERIVED_CONSTANT_CONTRACT, encoding="utf-8")
    result = build_pyi_extension(
        contract,
        native_objects=[native_object],
        native_include_dirs=[native_object.parent],
        output_dir=tmp_path / "build",
    )
    module = _sole_native_module(_import_from_build_dir(result.module_name, result.output_dir))

    first = module.black
    second = module.black
    assert first is not second
    first.r = np.int32(17)
    assert first.r == np.int32(17)
    assert second.r == np.int32(0)
    assert module.black.r == np.int32(0)
    assert module.black_sum() == np.int32(0)
    with pytest.raises(AttributeError):
        module.black = second

    bridge = (result.output_dir / "bind_c_fmodule_vars_f90_wrapper.f90").read_text(encoding="utf-8")
    assert "result = c_null_ptr" in bridge
    assert "allocate(value, stat=prik_allocation_status)" in bridge
    assert "value = native_black" in bridge
    assert "result = c_loc(value)" in bridge


def test_fixed_string_fields_use_canonical_plan(tmp_path: Path):
    source = tmp_path / "native" / "derived_string_fields.f90"
    source.parent.mkdir()
    source.write_text(STRING_FIELD_SOURCE, encoding="utf-8")
    native_object = _compile_native_object(source, tmp_path / "native_build")

    contract = tmp_path / "contract" / "derived_string_fields.pyi"
    contract.parent.mkdir()
    contract.write_text(STRING_FIELD_CONTRACT, encoding="utf-8")
    result = build_pyi_extension(
        contract,
        native_objects=[native_object],
        native_include_dirs=[native_object.parent],
        output_dir=tmp_path / "build",
    )
    module = _sole_native_module(_import_from_build_dir(result.module_name, result.output_dir))

    current = module.current
    assert current.label == "start   "
    current.label = "edited  "
    assert module.current_label() == "edited  "
    module.reset_label()
    assert current.label == "native  "
    with pytest.raises(TypeError, match="exactly 8 bytes"):
        current.label = "short"


def _assert_scalar_descriptor_fields(module) -> None:
    """Check live storage, assignment, and failures of scalar allocatable and pointer fields."""
    record = module.Record()
    assert (record.scale, record.weight, record.name, record.tag) == (None, None, None, None)
    with pytest.raises(TypeError, match="unexpected keyword argument 'scale'"):
        module.Record(scale=np.float64(1.0))
    with pytest.raises(ValueError, match="Field weight has no pointer target"):
        record.weight = np.float64(1.0)

    module.fill(record)
    weight = record.weight
    assert weight.shape == () and weight.dtype == np.float64 and float(weight) == 2.5
    assert record.name.dtype == np.dtype("S5") and record.name[()] == b"hello"
    with pytest.raises(ValueError, match="read-only"):
        weight[...] = 0.0

    # Assignment allocates or writes the current target, and the earlier view
    # of the pointer target sees the write.
    record.scale = np.float64(10.0)
    record.weight = np.float64(4.0)
    record.name = "longer name"
    assert float(weight) == 4.0
    assert module.total(record) == 14.0
    assert record.name[()] == b"longer name"
    with pytest.raises(TypeError, match="exactly 4 bytes"):
        record.tag = "toolong"
    record.tag = "wxyz"
    assert record.tag[()] == b"wxyz"

    # A view keeps its parent alive.
    scale = record.scale
    del record
    assert float(scale) == 10.0

    # A plain module object reaches the same fields through its members.
    shared = module.shared
    assert shared.name is None
    shared.name = "abc"
    assert module.shared_name() == "abc"


def test_scalar_descriptor_fields_lend_live_storage_in_source_and_contract_builds(tmp_path: Path):
    source_module = _build_source_and_import(
        SCALAR_DESCRIPTOR_FIELD_SOURCE,
        tmp_path / "source",
        {
            "bind_c_fderived_scalar_descriptor_fields_wrapper.f90",
            "fderived_scalar_descriptor_fields_wrapper.c",
            "fderived_scalar_descriptor_fields_wrapper.h",
        },
    )
    contract_module = _build_generated_pyi_and_import(SCALAR_DESCRIPTOR_FIELD_SOURCE, tmp_path / "contract")

    for module in (source_module, contract_module):
        _assert_scalar_descriptor_fields(module)

    # The generated contract's constructor states the keywords both builds accept.
    contract = (tmp_path / "contract" / "contracts" / "fderived_scalar_descriptor_fields").rglob("*.pyi")
    constructor = next(
        text for text in (path.read_text(encoding="utf-8") for path in contract) if "class Record" in text
    )
    assert "plain: Float64 = 0" in constructor
    assert "scale: Allocatable[Float64]\n" in constructor and "scale: Allocatable[Float64] =" not in constructor


def test_value_copy_and_optional_derived_inputs_match_source_oracle(tmp_path: Path):
    source = tmp_path / "source" / "derived_value_arguments.f90"
    source.parent.mkdir()
    source.write_text(VALUE_AND_OPTIONAL_SOURCE, encoding="utf-8")
    source_module = _build_source_and_import(
        source,
        tmp_path / "source_build",
        {
            "bind_c_derived_value_arguments_wrapper.f90",
            "derived_value_arguments_wrapper.c",
            "derived_value_arguments_wrapper.h",
        },
    )

    native_object = _compile_native_object(source, tmp_path / "native")
    contract = tmp_path / "contract" / "derived_value_arguments.pyi"
    contract.parent.mkdir()
    contract.write_text(VALUE_AND_OPTIONAL_CONTRACT, encoding="utf-8")
    result = build_pyi_extension(
        contract,
        native_objects=[native_object],
        native_include_dirs=[native_object.parent],
        output_dir=tmp_path / "contract_build",
    )
    direct_module = _sole_native_module(_import_from_build_dir(result.module_name, result.output_dir))

    for module in (source_module, direct_module):
        point = module.make_point(np.float64(1.0), np.float64(2.0))
        assert module.score_by_value(point) == np.float64(103.0)
        assert point.x == np.float64(1.0)
        assert point.y == np.float64(2.0)
        assert module.optional_sum() == np.float64(-1.0)
        assert module.optional_sum(None) == np.float64(-1.0)
        assert module.optional_sum(point) == np.float64(3.0)

    source_point = source_module.make_point(np.float64(1.0), np.float64(2.0))
    assert source_module.update_point(source_point) is None
    assert source_point.x == np.float64(11.0)
    assert source_point.y == np.float64(22.0)
    source_filled = source_module.Point()
    assert source_module.fill_point(source_filled) is None
    assert source_filled.x == np.float64(31.0)
    assert source_filled.y == np.float64(32.0)

    direct_point = direct_module.make_point(np.float64(1.0), np.float64(2.0))
    assert direct_module.update_point(direct_point) is direct_point
    assert direct_point.x == np.float64(11.0)
    assert direct_point.y == np.float64(22.0)
    assert direct_module.fill_point(direct_point) is direct_point
    assert direct_point.x == np.float64(31.0)
    assert direct_point.y == np.float64(32.0)

    with pytest.raises(TypeError, match="Expected exact wrapper type point"):
        direct_module.optional_sum(object())

    bridge = (result.output_dir / "bind_c_derived_value_arguments_wrapper.f90").read_text(encoding="utf-8")
    assert "type(prik_type_point), pointer :: value" in bridge
    assert "native_score_by_value(value)" in bridge
