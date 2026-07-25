"""Allocatable result, module-array, and component-view ownership tests."""

import gc
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from tests.wrapper.fortran._support import (
    _build_source_or_generated_pyi_and_import,
    _build_text_and_import,
    _compile_native_object,
    _import_from_build_dir,
    _sole_native_module,
    wrapper_source,
)
from x2py import build_pyi_extension
from x2py.runtime.handles import AllocatableArray

ALLOCATABLE_VIEW_F90_SOURCE = wrapper_source("fallocatable_views_f90.f90")
CONTRACT_FIXTURES = Path(__file__).parent / "contracts"
PLAIN_ALLOCATABLE_MODULE_SOURCE = """\
module fallocatable_plain_f90
  implicit none
  real(8), allocatable :: values(:)
contains
  subroutine allocate_values(n)
    integer(4), intent(in) :: n
    integer(4) :: i

    if (allocated(values)) deallocate(values)
    allocate(values(n))
    values = [(1.0_8 * i, i = 1, n)]
  end subroutine allocate_values

  subroutine scale_values(scale)
    real(8), intent(in) :: scale

    values = scale * values
  end subroutine scale_values

  subroutine deallocate_values()
    if (allocated(values)) deallocate(values)
  end subroutine deallocate_values
end module fallocatable_plain_f90
"""
SCALAR_DESCRIPTOR_MODULE_SOURCE = """\
module fscalar_descriptors_f90
  implicit none
  real(8), allocatable :: optional_scale
  real(8), target :: target_scale
  real(8), pointer :: selected_scale => null()
contains
  subroutine clear_all()
    if (allocated(optional_scale)) deallocate(optional_scale)
    nullify(selected_scale)
  end subroutine clear_all

  subroutine set_allocatable(value)
    real(8), intent(in) :: value

    if (allocated(optional_scale)) deallocate(optional_scale)
    allocate(optional_scale)
    optional_scale = value
  end subroutine set_allocatable

  subroutine point_to_target(value)
    real(8), intent(in) :: value

    target_scale = value
    selected_scale => target_scale
  end subroutine point_to_target

  subroutine bump_native()
    if (allocated(optional_scale)) optional_scale = optional_scale + 10.0_8
    if (associated(selected_scale)) selected_scale = selected_scale + 20.0_8
  end subroutine bump_native

  function echo_allocatable(value) result(out)
    real(8), allocatable, intent(in) :: value
    real(8) :: out

    if (allocated(value)) then
      out = value + 1.0_8
    else
      out = -1.0_8
    end if
  end function echo_allocatable

  function echo_pointer(value) result(out)
    real(8), pointer, intent(in) :: value
    real(8) :: out

    if (associated(value)) then
      out = value + 2.0_8
    else
      out = -2.0_8
    end if
  end function echo_pointer

  subroutine update_allocatable(value)
    real(8), allocatable, intent(inout) :: value

    if (allocated(value)) then
      value = value + 10.0_8
    else
      allocate(value)
      value = 10.0_8
    end if
  end subroutine update_allocatable

  subroutine update_pointer(value)
    real(8), pointer, intent(inout) :: value

    if (associated(value)) then
      value = value + 20.0_8
    else
      target_scale = 20.0_8
      value => target_scale
    end if
  end subroutine update_pointer

  subroutine clear_allocatable_value(value)
    real(8), allocatable, intent(inout) :: value

    if (allocated(value)) deallocate(value)
  end subroutine clear_allocatable_value

  subroutine clear_pointer_value(value)
    real(8), pointer, intent(inout) :: value

    nullify(value)
  end subroutine clear_pointer_value

  subroutine create_allocatable(value)
    real(8), allocatable, intent(out) :: value

    allocate(value)
    value = 30.0_8
  end subroutine create_allocatable

  subroutine create_pointer(value)
    real(8), pointer, intent(out) :: value

    target_scale = 40.0_8
    value => target_scale
  end subroutine create_pointer

  subroutine maybe_allocatable(flag, value)
    integer(4), intent(in) :: flag
    real(8), allocatable, intent(out) :: value

    if (flag /= 0) then
      allocate(value)
      value = 3.5_8
    end if
  end subroutine maybe_allocatable

  function maybe_pointer(flag) result(value)
    integer(4), intent(in) :: flag
    real(8), pointer :: value

    if (flag /= 0) then
      target_scale = 4.5_8
      value => target_scale
    else
      nullify(value)
    end if
  end function maybe_pointer
end module fscalar_descriptors_f90
"""


def _plain_allocatable_module(build_mode: str, tmp_path: Path):
    filename = "fallocatable_plain_f90.f90"
    if build_mode == "source":
        source_build_dir = tmp_path / "source_build"
        source_build_dir.mkdir(parents=True)
        module = _build_text_and_import(
            PLAIN_ALLOCATABLE_MODULE_SOURCE,
            filename,
            source_build_dir,
            {
                "bind_c_fallocatable_plain_f90_wrapper.f90",
                "fallocatable_plain_f90_wrapper.c",
                "fallocatable_plain_f90_wrapper.h",
            },
        )
        return module, (source_build_dir / "fallocatable_plain_f90_wrapper.c").read_text(encoding="utf-8")

    source_dir = tmp_path / "source"
    source_dir.mkdir(parents=True)
    source = source_dir / filename
    source.write_text(PLAIN_ALLOCATABLE_MODULE_SOURCE, encoding="utf-8")
    contract_dir = tmp_path / "contracts" / source.stem
    subprocess.run(
        [
            sys.executable,
            "-m",
            "x2py",
            "generate",
            "--pyi",
            str(source),
            "--out",
            str(contract_dir),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    native_object = _compile_native_object(source, tmp_path / "native")
    result = build_pyi_extension(
        contract_dir / "__init__.pyi",
        native_objects=[native_object],
        native_include_dirs=[native_object.parent],
        output_dir=tmp_path / "pyi_build",
    )
    module = _sole_native_module(_import_from_build_dir(result.module_name, result.output_dir))
    return module, (result.output_dir / "fallocatable_plain_f90_wrapper.c").read_text(encoding="utf-8")


def _scalar_descriptor_module(build_mode: str, tmp_path: Path):
    filename = "fscalar_descriptors_f90.f90"
    expected_sources = {
        "bind_c_fscalar_descriptors_f90_wrapper.f90",
        "fscalar_descriptors_f90_wrapper.c",
        "fscalar_descriptors_f90_wrapper.h",
    }
    if build_mode == "source":
        source_build_dir = tmp_path / "source_build"
        source_build_dir.mkdir(parents=True)
        return _build_text_and_import(
            SCALAR_DESCRIPTOR_MODULE_SOURCE,
            filename,
            source_build_dir,
            expected_sources,
        )

    source_dir = tmp_path / "source"
    source_dir.mkdir(parents=True)
    source = source_dir / filename
    source.write_text(SCALAR_DESCRIPTOR_MODULE_SOURCE, encoding="utf-8")
    contract_dir = tmp_path / "contracts" / source.stem
    subprocess.run(
        [
            sys.executable,
            "-m",
            "x2py",
            "generate",
            "--pyi",
            str(source),
            "--out",
            str(contract_dir),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    native_object = _compile_native_object(source, tmp_path / "native")
    result = build_pyi_extension(
        contract_dir / "__init__.pyi",
        native_objects=[native_object],
        native_include_dirs=[native_object.parent],
        output_dir=tmp_path / "pyi_build",
    )
    return _sole_native_module(_import_from_build_dir(result.module_name, result.output_dir))


def _maybe_unallocated_direct_result_module(tmp_path: Path):
    native_object = _compile_native_object(ALLOCATABLE_VIEW_F90_SOURCE, tmp_path / "native")
    contract_dir = tmp_path / "contracts" / "fallocatable_views_f90"
    contract_dir.mkdir(parents=True)
    (contract_dir / "__init__.pyi").write_text("from . import fallocatable_views_f90\n", encoding="utf-8")
    contract_text = (CONTRACT_FIXTURES / "fallocatable_views_f90" / "fallocatable_views_f90.pyi").read_text(
        encoding="utf-8"
    )
    contract_text = contract_text.replace("Int32, Pass", "Int32, MaybeUnallocated, Pass")
    contract_text = contract_text.replace(
        "def make_values(\n    n: Int32\n) -> Allocatable[Float64[:]]: ...",
        "def make_values(\n    n: Int32\n) -> Annotated[Allocatable[Float64[:]], MaybeUnallocated]: ...",
    )
    (contract_dir / "fallocatable_views_f90.pyi").write_text(contract_text, encoding="utf-8")
    result = build_pyi_extension(
        contract_dir / "__init__.pyi",
        native_objects=[native_object],
        native_include_dirs=[native_object.parent],
        output_dir=tmp_path / "pyi_build",
    )
    return _sole_native_module(_import_from_build_dir(result.module_name, result.output_dir))


def test_allocatable_module_fields_and_results_expose_lifetime_safe_handles(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    module = _build_source_or_generated_pyi_and_import(
        ALLOCATABLE_VIEW_F90_SOURCE,
        tmp_path,
        {
            "bind_c_fallocatable_views_f90_wrapper.f90",
            "fallocatable_views_f90_wrapper.c",
            "fallocatable_views_f90_wrapper.h",
        },
        CONTRACT_FIXTURES / "fallocatable_views_f90",
        pyi_parity_build_mode,
    )

    assert "Functions" in module.__doc__
    assert "Module Attributes" in module.__doc__
    assert "module_values : AllocatableArray[float64]" in module.__doc__
    assert "Persistent allocatable descriptor handle." in module.__doc__
    assert "Replacement assignment is not supported." in module.__doc__
    assert "build_values" in module.__doc__
    assert "buffer" in module.__doc__
    assert "build_values(n) -> AllocatableArray[float64]" in module.build_values.__doc__
    assert "values : AllocatableArray[float64]" in module.build_values.__doc__
    assert "Descriptor ownership: owned" in module.build_values.__doc__
    assert "Unallocated state remains inside the returned handle." in module.build_values.__doc__
    assert not hasattr(module, "get_module_values")
    assert "Fields" in module.buffer.__doc__
    assert "values : AllocatableArray[float64]" in module.buffer.__doc__
    assert "allocatable array descriptor handle" in module.buffer.values.__doc__

    module_values = module.module_values
    assert isinstance(module_values, AllocatableArray)
    assert module_values.allocated is False
    assert module_values.shape is None
    assert module_values.to_numpy() is None
    module.allocate_module_values(np.int32(3))
    assert module.module_values is module_values
    np.testing.assert_allclose(module_values.to_numpy(), np.array([1.0, 2.0, 3.0], dtype=np.float64))

    module_values.to_numpy()[0] = np.float64(10.0)
    assert module.module_values_sum() == np.float64(15.0)
    module.scale_module_values(np.float64(2.0))
    np.testing.assert_allclose(module_values.to_numpy(), np.array([20.0, 4.0, 6.0], dtype=np.float64))

    module.deallocate_module_values()
    assert module_values.allocated is False
    assert module_values.to_numpy() is None

    built_values = module.build_values(np.int32(4))
    assert isinstance(built_values, AllocatableArray)
    assert built_values.descriptor_ownership == "owned"
    np.testing.assert_allclose(built_values.to_numpy(), np.array([2.0, 4.0, 6.0, 8.0], dtype=np.float64))
    built_values.to_numpy()[0] = np.float64(-1.0)
    np.testing.assert_allclose(built_values.to_numpy(), np.array([-1.0, 4.0, 6.0, 8.0], dtype=np.float64))
    empty_values = module.build_values(np.int32(0))
    assert isinstance(empty_values, AllocatableArray)
    assert empty_values.allocated is False
    assert empty_values.to_numpy() is None

    built_matrix = module.build_matrix(np.int32(2), np.int32(2))
    np.testing.assert_allclose(
        built_matrix.to_numpy(),
        np.array([[11.0, 21.0], [12.0, 22.0]], dtype=np.float64),
    )
    empty_matrix = module.build_matrix(np.int32(0), np.int32(2))
    assert isinstance(empty_matrix, AllocatableArray)
    assert empty_matrix.allocated is False

    made_values = module.make_values(np.int32(3))
    np.testing.assert_allclose(made_values.to_numpy(), np.array([3.0, 6.0, 9.0], dtype=np.float64))

    made_matrix = module.make_matrix(np.int32(2), np.int32(2))
    np.testing.assert_allclose(
        made_matrix.to_numpy(),
        np.array([[111.0, 121.0], [112.0, 122.0]], dtype=np.float64),
    )

    retained_result_view = made_values.to_numpy()
    del made_values
    gc.collect()
    np.testing.assert_allclose(retained_result_view, np.array([3.0, 6.0, 9.0], dtype=np.float64))

    values = module.buffer()
    field_handle = values.values
    assert isinstance(field_handle, AllocatableArray)
    assert field_handle.owner is values
    assert field_handle.allocated is False
    values.allocate_values(np.int32(3))
    field_view = field_handle.to_numpy()
    np.testing.assert_allclose(field_view, np.array([1.0, 2.0, 3.0], dtype=np.float64))

    field_view[1] = np.float64(8.0)
    assert values.values_sum() == np.float64(12.0)
    values.scale_values(np.float64(0.5))
    np.testing.assert_allclose(field_handle.to_numpy(), np.array([0.5, 4.0, 1.5], dtype=np.float64))

    with pytest.raises(AttributeError):
        values.values = np.array([1.0, 2.0], dtype=np.float64)

    retained_owner_id = id(values)
    del values
    gc.collect()
    assert id(field_handle.owner) == retained_owner_id
    np.testing.assert_allclose(field_handle.to_numpy(), np.array([0.5, 4.0, 1.5], dtype=np.float64))
    field_handle.deallocate()
    assert field_handle.allocated is False

    built_values.close()
    assert built_values.closed is True
    with pytest.raises(ReferenceError, match="closed"):
        _ = built_values.allocated


def test_maybe_unallocated_direct_allocatable_results_preserve_unallocated_state(tmp_path: Path):
    module = _maybe_unallocated_direct_result_module(tmp_path)

    made_values = module.make_values(np.int32(3))
    np.testing.assert_allclose(made_values.to_numpy(), np.array([3.0, 6.0, 9.0], dtype=np.float64))
    assert module.make_values(np.int32(0)).allocated is False

    made_matrix = module.make_matrix(np.int32(2), np.int32(2))
    np.testing.assert_allclose(
        made_matrix.to_numpy(),
        np.array([[111.0, 121.0], [112.0, 122.0]], dtype=np.float64),
    )


def test_scalar_descriptor_module_variables_return_copied_optional_values(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    module = _scalar_descriptor_module(pyi_parity_build_mode, tmp_path)

    module.clear_all()
    assert module.optional_scale is None
    assert module.selected_scale is None
    assert not hasattr(module, "get_optional_scale")
    assert not hasattr(module, "set_optional_scale")
    assert not hasattr(module, "get_selected_scale")
    assert not hasattr(module, "set_selected_scale")
    with pytest.raises(AttributeError):
        module.optional_scale = np.float64(9.0)
    with pytest.raises(AttributeError):
        module.selected_scale = np.float64(9.0)

    module.set_allocatable(np.float64(1.5))
    alloc_snapshot = module.optional_scale
    assert alloc_snapshot == np.float64(1.5)

    module.point_to_target(np.float64(2.5))
    pointer_snapshot = module.selected_scale
    assert pointer_snapshot == np.float64(2.5)

    module.bump_native()
    assert alloc_snapshot == np.float64(1.5)
    assert pointer_snapshot == np.float64(2.5)
    assert module.optional_scale == np.float64(11.5)
    assert module.selected_scale == np.float64(22.5)
    assert module.echo_allocatable(np.float64(3.0)) == np.float64(4.0)
    assert module.echo_allocatable(None) == np.float64(-1.0)
    assert module.echo_pointer(np.float64(3.0)) == np.float64(5.0)
    assert module.echo_pointer(None) == np.float64(-2.0)
    assert module.update_allocatable(np.float64(3.0)) == np.float64(13.0)
    assert module.update_allocatable(None) == np.float64(10.0)
    assert module.update_pointer(np.float64(3.0)) == np.float64(23.0)
    assert module.update_pointer(None) == np.float64(20.0)
    assert module.clear_allocatable_value(np.float64(3.0)) is None
    assert module.clear_pointer_value(np.float64(3.0)) is None
    assert module.create_allocatable() == np.float64(30.0)
    assert module.create_pointer() == np.float64(40.0)
    assert module.maybe_allocatable(np.int32(1)) == np.float64(3.5)
    assert module.maybe_pointer(np.int32(1)) == np.float64(4.5)
    assert module.maybe_pointer(np.int32(0)) is None

    module.clear_all()
    assert module.optional_scale is None
    assert module.selected_scale is None


def test_plain_allocatable_module_array_exposes_current_live_view(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    module, wrapper_source_text = _plain_allocatable_module(pyi_parity_build_mode, tmp_path)

    assert "void (*callback)(CFI_cdesc_t *, void *)" in wrapper_source_text
    assert "descriptor->base_addr" in wrapper_source_text

    handle = module.values
    assert isinstance(handle, AllocatableArray)
    assert handle.allocated is False
    assert handle.shape is None
    assert handle.to_numpy() is None

    module.allocate_values(np.int32(3))
    assert module.values is handle
    assert handle.allocated is True
    assert handle.shape == (3,)

    view = handle.to_numpy()
    np.testing.assert_allclose(view, np.array([1.0, 2.0, 3.0], dtype=np.float64))
    assert view.flags.writeable is True
    view[0] = np.float64(9.0)
    independent = view.copy()

    module.scale_values(np.float64(2.0))
    np.testing.assert_allclose(view, np.array([18.0, 4.0, 6.0], dtype=np.float64))
    np.testing.assert_allclose(independent, np.array([9.0, 2.0, 3.0], dtype=np.float64))

    fresh = handle.to_numpy()
    assert fresh.flags.writeable is True
    np.testing.assert_allclose(fresh, np.array([18.0, 4.0, 6.0], dtype=np.float64))

    module.allocate_values(np.int32(4))
    reallocated = handle.to_numpy()
    assert reallocated is not view
    np.testing.assert_allclose(reallocated, np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float64))
    np.testing.assert_allclose(independent, np.array([9.0, 2.0, 3.0], dtype=np.float64))

    handle.resize((2,))
    assert handle.allocated is True
    assert handle.shape == (2,)

    handle.deallocate()
    assert handle.allocated is False
    assert handle.shape is None
    assert handle.to_numpy() is None
