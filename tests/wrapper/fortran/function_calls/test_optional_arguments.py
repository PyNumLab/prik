"""Optional argument runtime wrapper tests."""

from pathlib import Path
import shutil

import numpy as np
import pytest

from x2py import build_pyi_extension
from tests.wrapper.fortran._support import (
    _compile_native_object,
    _build_source_or_generated_pyi_and_import,
    _build_source_wrapper_plan_and_import,
    _import_from_build_dir,
    _sole_native_module,
    wrapper_source,
)
from x2py.runtime.handles import _NativeArrayHandoff, AllocatableArray, PointerArray

OPTIONAL_F90_SOURCE = wrapper_source("foptional_f90.f90")
OPTIONAL_FIXED_SOURCE = wrapper_source("foptional_fixed.f")
CONTRACT_FIXTURES = Path(__file__).parent / "contracts"


def _unallocated_handle_for_rejected_optional_array():
    return AllocatableArray(
        dtype=np.dtype(np.float64),
        rank=1,
        ops={
            "array_actual": lambda _handle: pytest.fail("optional array path must reject handles before handoff"),
            "descriptor": lambda _handle: _NativeArrayHandoff(501),
            "shape": lambda _handle: None,
            "to_numpy": lambda _handle: None,
            "allocated": lambda _handle: False,
            "deallocate": lambda _handle: None,
            "resize": lambda _handle, _shape: None,
        },
    )


def _unassociated_handle_for_rejected_optional_array():
    return PointerArray(
        dtype=np.dtype(np.float64),
        rank=1,
        ops={
            "array_actual": lambda _handle: pytest.fail("optional array path must reject handles before handoff"),
            "descriptor": lambda _handle: _NativeArrayHandoff(502),
            "shape": lambda _handle: None,
            "to_numpy": lambda _handle: None,
            "associated": lambda _handle: False,
            "nullify": lambda _handle: None,
        },
    )


def _optional_descriptor_handle(value: np.ndarray | None, *, pointer: bool):
    descriptor = {
        "base_addr": 0 if value is None else value.ctypes.data,
        "elem_len": np.dtype(np.float64).itemsize,
        "rank": 1,
        "dim": [
            {
                "lower_bound": 0,
                "extent": 0 if value is None else value.size,
                "sm": np.dtype(np.float64).itemsize,
            }
        ],
    }
    operations = {
        "array_actual": lambda _handle: _NativeArrayHandoff(value.ctypes.data),
        "descriptor": lambda _handle: descriptor,
        "shape": lambda _handle: None if value is None else value.shape,
        "to_numpy": lambda _handle: value,
        "associated" if pointer else "allocated": lambda _handle: value is not None,
        "nullify" if pointer else "deallocate": lambda _handle: None,
    }
    handle_type = PointerArray if pointer else AllocatableArray
    return handle_type(dtype=np.dtype(np.float64), rank=1, ops=operations)


def test_optional_allocatable_scalar_descriptor_distinguishes_omitted_none_and_value(tmp_path: Path):
    source = tmp_path / "scalar_optional_descriptors.f90"
    source.write_text(
        """
module scalar_optional_descriptors
contains
  integer(4) function alloc_state(value) result(state)
    real(8), allocatable, optional, intent(in) :: value

    if (.not. present(value)) then
      state = 0
    else if (.not. allocated(value)) then
      state = 1
    else if (abs(value - 2.5_8) < 1.0e-12_8) then
      state = 2
    else
      state = -1
    end if
  end function alloc_state
end module scalar_optional_descriptors
""",
        encoding="utf-8",
    )
    native_object = _compile_native_object(source, tmp_path / "native")
    contract_dir = tmp_path / "contracts"
    contract_dir.mkdir()
    entry = contract_dir / "scalar_optional_descriptors.pyi"
    entry.write_text(
        """
from x2py.contracts import Allocatable, Annotated, Arg, Float64, Immutable, Int32, native_call

@native_call([Allocatable(Arg(0))])
def alloc_state(value: Annotated[Float64, Immutable] | None = ...) -> Int32: ...
""",
        encoding="utf-8",
    )

    result = build_pyi_extension(
        entry,
        native_objects=[native_object],
        native_include_dirs=[native_object.parent],
        output_dir=tmp_path / "build",
    )
    module = _sole_native_module(_import_from_build_dir(result.module_name, result.output_dir))

    assert tuple(path.name for path in result.generated_sources) == (
        "bind_c_scalar_optional_descriptors_wrapper.f90",
        "scalar_optional_descriptors_wrapper.c",
        "scalar_optional_descriptors_wrapper.h",
    )
    assert module.alloc_state() == np.int32(0)
    assert module.alloc_state(None) == np.int32(1)
    assert module.alloc_state(np.float64(2.5)) == np.int32(2)
    with pytest.raises(TypeError):
        module.alloc_state("bad")
    plan_c = (result.output_dir / "scalar_optional_descriptors_wrapper.c").read_text(encoding="utf-8")
    assert "int32_t bind_c_alloc_state(void * value, void * value_present);" in plan_c
    assert "Omit to make the native optional dummy absent." in module.alloc_state.__doc__
    assert "Pass None for a present unallocated or unassociated descriptor." in module.alloc_state.__doc__
    assert "Default is None." not in module.alloc_state.__doc__


def test_optional_array_descriptors_preserve_presence_and_storage_state(tmp_path: Path):
    """Distinguish omitted/None from present absent-state descriptor handles."""
    source = tmp_path / "optional_array_descriptors.f90"
    source.write_text(
        """
module optional_array_descriptors
contains
  integer(4) function alloc_state(values) result(state)
    real(8), allocatable, optional, intent(in) :: values(:)
    if (.not. present(values)) then
      state = 0
    else if (.not. allocated(values)) then
      state = 1
    else
      state = int(sum(values), kind=4)
    end if
  end function alloc_state

  integer(4) function pointer_state(values) result(state)
    real(8), pointer, optional, intent(in) :: values(:)
    if (.not. present(values)) then
      state = 0
    else if (.not. associated(values)) then
      state = 1
    else
      state = int(sum(values), kind=4)
    end if
  end function pointer_state
end module optional_array_descriptors
""",
        encoding="utf-8",
    )
    native_object = _compile_native_object(source, tmp_path / "native_array_descriptors")
    contract = tmp_path / "optional_array_descriptors.pyi"
    contract.write_text(
        """from x2py.contracts import Allocatable, Float64, Int32, Pointer

def alloc_state(values: Allocatable[Float64[:]] | None = ...) -> Int32: ...
def pointer_state(values: Pointer[Float64[:]] | None = ...) -> Int32: ...
""",
        encoding="utf-8",
    )

    result = build_pyi_extension(
        contract,
        native_objects=[native_object],
        native_include_dirs=[native_object.parent],
        output_dir=tmp_path / "array_descriptors",
    )
    module = _sole_native_module(_import_from_build_dir(result.module_name, result.output_dir))

    values = np.array([1.0, 2.0, 3.0], dtype=np.float64)
    for function_name in ("alloc_state", "pointer_state"):
        function = getattr(module, function_name)
        assert function() == np.int32(0)
        assert function(None) == np.int32(0)

    for function_name, pointer in (("alloc_state", False), ("pointer_state", True)):
        function = getattr(module, function_name)
        assert function(_optional_descriptor_handle(None, pointer=pointer)) == np.int32(1)
        assert function(_optional_descriptor_handle(values, pointer=pointer)) == np.int32(6)


def test_optional_arguments_drive_fortran_present_behavior(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    module = _build_source_or_generated_pyi_and_import(
        OPTIONAL_F90_SOURCE,
        tmp_path,
        {
            "bind_c_foptional_f90_wrapper.f90",
            "foptional_f90_wrapper.c",
            "foptional_f90_wrapper.h",
        },
        CONTRACT_FIXTURES / "foptional_f90",
        pyi_parity_build_mode,
    )

    assert "scale : int32 or None" in module.summarize.__doc__
    assert "May be omitted or passed as None." in module.summarize.__doc__

    values = np.array([1.0, 2.0, 3.0], dtype=np.float64)
    item = module.sample()
    item.value = np.int32(7)

    assert module.summarize(np.int32(5)) == np.int32(5)
    assert module.summarize(np.int32(5), np.int32(4)) == np.int32(9)
    assert module.summarize(np.int32(5), None) == np.int32(5)
    assert module.summarize(np.int32(5), scale=None) == np.int32(5)
    assert module.summarize(np.int32(5), values=values) == np.int32(11)
    assert module.summarize(np.int32(5), label="trimmed") == np.int32(12)
    assert module.summarize(np.int32(5), item=item) == np.int32(12)
    assert module.summarize(np.int32(5), item=item, values=values, label="abc") == np.int32(21)
    assert module.summarize(np.int32(5), None, values=values, item=item) == np.int32(18)

    mutable = np.array([1.0, 2.0], dtype=np.float64)
    assert module.mutate_optional() is None
    assert module.mutate_optional(None, np.float64(100.0)) is None
    assert module.mutate_optional(mutable) is None
    np.testing.assert_allclose(mutable, np.array([2.0, 3.0], dtype=np.float64))
    assert module.mutate_optional(mutable, None) is None
    np.testing.assert_allclose(mutable, np.array([3.0, 4.0], dtype=np.float64))
    assert module.mutate_optional(mutable, np.float64(2.5)) is None
    np.testing.assert_allclose(mutable, np.array([5.5, 6.5], dtype=np.float64))

    output = np.empty(3, dtype=np.float64)
    assert module.fill_optional(np.int32(3), output) is None
    np.testing.assert_allclose(output, np.array([11.0, 12.0, 13.0], dtype=np.float64))
    assert module.fill_optional(np.int32(3)) is None
    assert module.fill_optional(np.int32(3), None) is None
    assert module.optional_status(np.int32(8)) == (np.int32(8), None)
    assert module.optional_status(np.int32(8), None) == (np.int32(8), None)
    status = np.empty((), dtype=np.int32)
    returned_base, returned_status = module.optional_status(np.int32(8), status)
    assert returned_base == np.int32(8)
    assert returned_status is status
    assert status[()] == np.int32(58)

    with pytest.raises(TypeError):
        module.summarize(np.int32(5), scale="bad")
    with pytest.raises(TypeError):
        module.fill_optional(np.int32(3), np.empty(3, dtype=np.float32))
    with pytest.raises(TypeError):
        module.fill_optional(np.int32(3), _unallocated_handle_for_rejected_optional_array())
    with pytest.raises(TypeError):
        module.fill_optional(np.int32(3), _unassociated_handle_for_rejected_optional_array())


def test_fixed_form_optional_arguments_drive_fortran_present_behavior(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    module = _build_source_or_generated_pyi_and_import(
        OPTIONAL_FIXED_SOURCE,
        tmp_path,
        {
            "bind_c_foptional_fixed_wrapper.f90",
            "foptional_fixed_wrapper.c",
            "foptional_fixed_wrapper.h",
        },
        CONTRACT_FIXTURES / "foptional_fixed",
        pyi_parity_build_mode,
    )

    assert module.optional_scale(np.int32(3)) == np.int32(3)
    assert module.optional_scale(np.int32(3), np.int32(4)) == np.int32(7)
    assert module.optional_scale(np.int32(3), None) == np.int32(3)
    assert module.optional_scale(base=np.int32(3), factor=np.int32(6)) == np.int32(9)


def test_fixed_optional_scalar_plan_matches_all_presence_states(tmp_path: Path):
    wrapper_plan, result = _build_source_wrapper_plan_and_import(
        OPTIONAL_FIXED_SOURCE,
        tmp_path / "wrapper_plan",
    )

    assert {path.name for path in result.generated_sources} == {
        "bind_c_foptional_fixed_wrapper.f90",
        "foptional_fixed_wrapper.c",
        "foptional_fixed_wrapper.h",
    }
    plan_c = (tmp_path / "wrapper_plan" / "wrapper_plan_build" / "foptional_fixed_wrapper.c").read_text(
        encoding="utf-8"
    )
    assert "int32_t bind_c_optional_scale(int32_t base, void * factor);" in plan_c
    assert wrapper_plan.optional_scale(np.int32(3)) == np.int32(3)
    assert wrapper_plan.optional_scale(np.int32(3), None) == np.int32(3)
    assert wrapper_plan.optional_scale(np.int32(3), np.int32(4)) == np.int32(7)
    assert wrapper_plan.optional_scale(base=np.int32(3), factor=np.int32(6)) == np.int32(9)
    with pytest.raises(TypeError):
        wrapper_plan.optional_scale(np.int32(3), "bad")


def test_optional_array_buffers_preserve_omission_and_identity(tmp_path: Path):
    """Replay omitted, explicit-None, and present ordinary array storage."""
    native_object = _compile_native_object(OPTIONAL_F90_SOURCE, tmp_path / "native")
    contract_package = tmp_path / "optional_arrays"
    shutil.copytree(CONTRACT_FIXTURES / "foptional_f90", contract_package)
    (contract_package / "foptional_f90.pyi").write_text(
        """from x2py.contracts import Addr, Arg, Float64, Int32, Returns, native_call

@native_call([Arg(0), Addr(Arg(1))])
def mutate_optional(
    values: Float64[::] = ...,
    amount: Float64 = ...
) -> None: ...

@native_call([Addr(Arg(0)), Arg(1)])
def fill_optional(
    n: Int32,
    values: Float64[::] = ...
) -> Returns["values", Float64[::]] | None: ...
""",
        encoding="utf-8",
    )
    (contract_package / "__init__.pyi").write_text(
        "from .foptional_f90 import mutate_optional\nfrom .foptional_f90 import fill_optional\n",
        encoding="utf-8",
    )
    result = build_pyi_extension(
        contract_package / "__init__.pyi",
        native_objects=[native_object],
        native_include_dirs=[native_object.parent],
        output_dir=tmp_path / "build",
    )
    imported = _import_from_build_dir(result.module_name, result.output_dir)
    module = imported if hasattr(imported, "mutate_optional") else _sole_native_module(imported)

    assert module.mutate_optional() is None
    assert module.mutate_optional(None, np.float64(2.0)) is None
    values = np.array([1.0, 2.0], dtype=np.float64)
    assert module.mutate_optional(values, np.float64(2.5)) is None
    np.testing.assert_array_equal(values, np.array([3.5, 4.5]))

    output = np.empty(3, dtype=np.float64)
    assert module.fill_optional(np.int32(3), output) is output
    np.testing.assert_array_equal(output, np.array([11.0, 12.0, 13.0]))
    assert module.fill_optional(np.int32(3)) is None
    assert module.fill_optional(np.int32(3), None) is None

    with pytest.raises(TypeError):
        module.fill_optional(np.int32(3), np.empty(3, dtype=np.float32))
