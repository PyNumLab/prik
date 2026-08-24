"""Pointer argument, result, association, and handle-policy tests."""

import gc
import resource
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import (
    _build_and_import,
    _build_text_and_import,
    _build_source_or_generated_pyi_and_import,
    _compile_native_object,
    _import_from_build_dir,
    _sole_native_module,
)
from prik import build_pyi_extension
from prik.contracts import Float64, Pointer
from prik.runtime.handles import AllocatableArray, PointerArray

pytestmark = pytest.mark.fortran_end_to_end

FIXTURES = Path(__file__).parent / "fixtures"
POINTERS_F90_SOURCE = FIXTURES / "native" / "fpointers_f90.f90"
CONTRACT_FIXTURES = FIXTURES / "contracts"
POINTER_CROSS_A_SOURCE = """\
module fpointer_cross_a
  real(8), target :: storage_a(2) = [1.0_8, 2.0_8]
contains
  subroutine select_a(values)
    real(8), pointer, intent(inout) :: values(:)
    values => storage_a
  end subroutine select_a

  function total_a(values) result(total)
    real(8), pointer, intent(in) :: values(:)
    real(8) :: total
    if (associated(values)) then
      total = sum(values)
    else
      total = -1.0_8
    end if
  end function total_a
end module fpointer_cross_a
"""
POINTER_CROSS_B_SOURCE = """\
module fpointer_cross_b
  real(8), target :: storage_b(3) = [10.0_8, 20.0_8, 30.0_8]
contains
  subroutine select_b(values)
    real(8), pointer, intent(inout) :: values(:)
    values => storage_b
  end subroutine select_b

  function total_b(values) result(total)
    real(8), pointer, intent(in) :: values(:)
    real(8) :: total
    if (associated(values)) then
      total = sum(values)
    else
      total = -1.0_8
    end if
  end function total_b
end module fpointer_cross_b
"""
POINTER_HANDLE_SOURCE = """\
module fpointer_handles_f90
  implicit none

  real(8), target :: module_storage(5) = [1.0_8, 2.0_8, 3.0_8, 4.0_8, 5.0_8]
  real(8), target :: field_storage(4) = [6.0_8, 7.0_8, 8.0_8, 9.0_8]
  real(8), pointer :: module_values(:) => null()
  real(8), allocatable, target :: module_allocatable(:)

  type :: pointer_box
    real(8), pointer :: values(:) => null()
  contains
    procedure :: associate_values => box_associate_values
    procedure :: associate_values_strided => box_associate_values_strided
  end type pointer_box

contains

  subroutine associate_module_slice()
    module_values => module_storage(2:5:2)
  end subroutine associate_module_slice

  subroutine associate_module_contiguous()
    module_values => module_storage(2:4)
  end subroutine associate_module_contiguous

  subroutine select_module_values(values)
    real(8), pointer, intent(out) :: values(:)
    values => module_storage(2:4)
  end subroutine select_module_values

  subroutine select_no_values(values)
    real(8), pointer, intent(out) :: values(:)
    nullify(values)
  end subroutine select_no_values

  subroutine allocate_module_values()
    if (allocated(module_allocatable)) deallocate(module_allocatable)
    allocate(module_allocatable(3))
    module_allocatable = [10.0_8, 20.0_8, 30.0_8]
  end subroutine allocate_module_values

  subroutine box_associate_values(self)
    class(pointer_box), intent(inout) :: self
    self%values => field_storage(2:4)
  end subroutine box_associate_values

  subroutine box_associate_values_strided(self)
    class(pointer_box), intent(inout) :: self
    self%values => field_storage(1:4:2)
  end subroutine box_associate_values_strided

  function sum_values(values) result(total)
    real(8), intent(in) :: values(:)
    real(8) :: total
    total = sum(values)
  end function sum_values

  function sum_pointer_descriptor(values) result(total)
    real(8), pointer, intent(in) :: values(:)
    real(8) :: total
    if (associated(values)) then
      total = sum(values)
    else
      total = -1.0_8
    end if
  end function sum_pointer_descriptor

  function sum_allocatable_descriptor(values) result(total)
    real(8), allocatable, intent(in) :: values(:)
    real(8) :: total
    if (allocated(values)) then
      total = sum(values)
    else
      total = -1.0_8
    end if
  end function sum_allocatable_descriptor

end module fpointer_handles_f90
"""


def _build_pointer_cross_extension(
    source_text: str,
    module_name: str,
    select_name: str,
    total_name: str,
    workdir: Path,
):
    source = workdir / f"{module_name}.f90"
    source.write_text(source_text, encoding="utf-8")
    native_object = _compile_native_object(source, workdir / "native")
    contract_dir = workdir / "contracts"
    contract_dir.mkdir()
    (contract_dir / "__init__.pyi").write_text(
        f"from .{module_name} import {select_name}, {total_name}\n",
        encoding="utf-8",
    )
    pointer_type = """Annotated[
    Pointer[Float64[:]],
    PointerAssociation("runtime"),
    PointerPolicy(
        nullable=True,
        transfer="call_local",
        target_owner="module",
        lifetime="module",
        deallocation="never",
        shape_source="pointer_bounds",
        contiguity="contiguous",
        reassociation="native",
        aliasing="borrowed",
        mutability="view",
    ),
]"""
    (contract_dir / f"{module_name}.pyi").write_text(
        f"""from prik.contracts import Annotated, Float64, Pointer, PointerAssociation, PointerPolicy, Returns

def {select_name}(
    values: {pointer_type},
) -> Returns["values", {pointer_type}]: ...

def {total_name}(values: Pointer[Float64[:]]) -> Float64: ...
""",
        encoding="utf-8",
    )
    result = build_pyi_extension(
        contract_dir / "__init__.pyi",
        native_objects=[native_object],
        native_include_dirs=[native_object.parent],
        output_dir=workdir / "build",
    )
    return _sole_native_module(_import_from_build_dir(result.module_name, result.output_dir))


def _pointer_handle_module(build_mode: str, tmp_path: Path):
    filename = "fpointer_handles_f90.f90"
    expected_sources = {
        "bind_c_fpointer_handles_f90_wrapper.f90",
        "fpointer_handles_f90_wrapper.c",
        "fpointer_handles_f90_wrapper.h",
    }
    if build_mode == "source":
        source_build_dir = tmp_path / "source_build"
        source_build_dir.mkdir(parents=True)
        return _build_text_and_import(
            POINTER_HANDLE_SOURCE,
            filename,
            source_build_dir,
            expected_sources,
        )

    source_dir = tmp_path / "source"
    source_dir.mkdir(parents=True)
    source = source_dir / filename
    source.write_text(POINTER_HANDLE_SOURCE, encoding="utf-8")
    contract_dir = tmp_path / "contracts" / source.stem
    subprocess.run(
        [sys.executable, "-m", "prik", "generate", "--pyi", str(source), "--out", str(contract_dir)],
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


def _pointer_descriptor_view_module(tmp_path: Path):
    source_dir = tmp_path / "source"
    source_dir.mkdir(parents=True)
    source = source_dir / "fpointer_handles_f90.f90"
    source.write_text(POINTER_HANDLE_SOURCE, encoding="utf-8")
    native_object = _compile_native_object(source, tmp_path / "native")
    contract = CONTRACT_FIXTURES / "fpointer_handles_policy" / "__init__.pyi"
    result = build_pyi_extension(
        contract,
        native_objects=[native_object],
        native_include_dirs=[native_object.parent],
        output_dir=tmp_path / "pyi_build",
    )
    return _sole_native_module(_import_from_build_dir(result.module_name, result.output_dir))


def test_module_and_derived_pointer_handles_track_native_association(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    module = _pointer_handle_module(pyi_parity_build_mode, tmp_path)

    module_handle = module.module_values
    assert isinstance(module_handle, PointerArray)
    assert module_handle.owner.__name__ == module.__name__.split(".", maxsplit=1)[0]
    assert module_handle.associated is False
    assert module_handle.shape is None
    assert module_handle.to_numpy() is None

    module.associate_module_slice()
    assert module.module_values is module_handle
    assert module_handle.associated is True
    assert module_handle.shape == (2,)
    with pytest.raises(ValueError, match="target is noncontiguous"):
        module.sum_values(module_handle)
    with pytest.raises(NotImplementedError, match="to_numpy extraction is unsupported"):
        module_handle.to_numpy()

    module.associate_module_contiguous()
    assert module_handle.shape == (3,)
    assert module.sum_values(module_handle) == np.float64(9.0)

    selected = module.select_module_values()
    assert isinstance(selected, PointerArray)
    assert selected.owned is True
    assert selected.associated is True
    assert selected.shape == (3,)
    assert module.sum_pointer_descriptor(selected) == np.float64(9.0)

    no_values = module.select_no_values()
    assert isinstance(no_values, PointerArray)
    assert no_values.owned is True
    assert no_values.associated is False
    assert no_values.shape is None

    module_handle.associate(no_values)
    assert module_handle.associated is False
    module_handle.associate(selected)
    assert module_handle.associated is True
    assert module.sum_pointer_descriptor(module_handle) == np.float64(9.0)
    selected.nullify()
    assert module_handle.associated is True
    module_handle.associate(selected)
    assert module_handle.associated is False
    module.associate_module_contiguous()

    selected.close()
    no_values.close()
    assert selected.closed is True
    assert no_values.closed is True
    assert module.sum_values(module_handle) == np.float64(9.0)

    module_handle.nullify()
    assert module_handle.associated is False
    assert module_handle.shape is None

    owner = module.pointer_box()
    field_handle = owner.values
    assert isinstance(field_handle, PointerArray)
    assert field_handle.owner is owner
    assert field_handle.associated is False
    assert field_handle.shape is None
    owner.associate_values()
    assert field_handle.associated is True
    assert field_handle.shape == (3,)
    assert module.sum_values(field_handle) == np.float64(24.0)

    module.associate_module_contiguous()
    field_handle.associate(module_handle)
    assert module.sum_pointer_descriptor(field_handle) == np.float64(9.0)
    module_handle.nullify()
    assert field_handle.associated is True
    field_handle.associate(module_handle)
    assert field_handle.associated is False
    owner.associate_values()

    owner_id = id(owner)
    del owner
    gc.collect()
    assert id(field_handle.owner) == owner_id
    assert field_handle.associated is True
    field_handle.nullify()
    assert field_handle.associated is False


def test_caller_created_pointer_crosses_separately_built_extensions(tmp_path: Path):
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    first_dir.mkdir()
    second_dir.mkdir()
    first = _build_pointer_cross_extension(
        POINTER_CROSS_A_SOURCE,
        "fpointer_cross_a",
        "select_a",
        "total_a",
        first_dir,
    )
    second = _build_pointer_cross_extension(
        POINTER_CROSS_B_SOURCE,
        "fpointer_cross_b",
        "select_b",
        "total_b",
        second_dir,
    )
    values = Pointer[Float64[:]]()

    assert first.select_a(values) is values
    np.testing.assert_array_equal(values.to_numpy(), np.array([1.0, 2.0]))
    assert second.total_b(values) == np.float64(3.0)

    assert second.select_b(values) is values
    np.testing.assert_array_equal(values.to_numpy(), np.array([10.0, 20.0, 30.0]))
    assert first.total_a(values) == np.float64(60.0)

    first_values = Pointer[Float64[:]]()
    second_values = Pointer[Float64[:]]()
    assert first.select_a(first_values) is first_values
    assert second.select_b(second_values) is second_values

    first_values.associate(second_values)
    assert first.total_a(first_values) == np.float64(60.0)
    second_values.nullify()
    assert first_values.associated is True
    first_values.associate(second_values)
    assert first_values.associated is False

    first_values.close()
    second_values.close()
    values.close()
    assert values.closed is True


def test_pointer_descriptor_views_preserve_slice_shape_strides_and_parent_lifetime(tmp_path: Path):
    module = _pointer_descriptor_view_module(tmp_path)

    module_handle = module.module_values
    module.associate_module_slice()
    module_view = module_handle.to_numpy()
    np.testing.assert_allclose(module_view, np.array([2.0, 4.0], dtype=np.float64))
    assert module_view.shape == (2,)
    assert module_view.strides == (16,)
    module_view[1] = np.float64(12.0)
    np.testing.assert_allclose(module_handle.to_numpy(), np.array([2.0, 12.0], dtype=np.float64))
    assert module.sum_pointer_descriptor(module_handle) == np.float64(14.0)

    allocatable_handle = module.module_allocatable
    assert isinstance(allocatable_handle, AllocatableArray)
    assert allocatable_handle.allocated is False
    assert module.sum_allocatable_descriptor(allocatable_handle) == np.float64(-1.0)
    module.allocate_module_values()
    assert allocatable_handle.allocated is True
    assert module.sum_allocatable_descriptor(allocatable_handle) == np.float64(60.0)

    owner = module.pointer_box()
    owner.associate_values_strided()
    field_handle = owner.values
    field_view = field_handle.to_numpy()
    np.testing.assert_allclose(field_view, np.array([6.0, 8.0], dtype=np.float64))
    assert field_view.shape == (2,)
    assert field_view.strides == (16,)
    field_view[1] = np.float64(12.0)
    assert module.sum_pointer_descriptor(field_handle) == np.float64(18.0)

    independent = field_view.copy()
    with pytest.raises(AttributeError):
        owner.values = field_handle
    field_handle.nullify()
    assert field_handle.to_numpy() is None
    np.testing.assert_allclose(independent, np.array([6.0, 12.0], dtype=np.float64))

    owner.associate_values_strided()
    field_view = field_handle.to_numpy()

    del field_handle
    del owner
    gc.collect()
    np.testing.assert_allclose(field_view, np.array([6.0, 12.0], dtype=np.float64))


def test_module_native_array_handles_use_canonical_plan(tmp_path: Path):
    """Replay module pointer/allocatable handles without derived-field owners."""
    source = tmp_path / "native" / "fpointer_handles_f90.f90"
    source.parent.mkdir()
    source.write_text(POINTER_HANDLE_SOURCE, encoding="utf-8")
    native_object = _compile_native_object(source, tmp_path / "native_build")
    contract = tmp_path / "pointer_handles" / "fpointer_handles_f90.pyi"
    contract.parent.mkdir()
    contract.write_text(
        """from prik.contracts import Aliased, Allocatable, Annotated, Float64, Pointer, PointerAssociation, PointerPolicy

module_values: Annotated[
    Pointer[Float64[:]],
    PointerAssociation("runtime"),
    PointerPolicy(
        nullable=True,
        transfer="call_local",
        target_owner="module",
        lifetime="module",
        deallocation="never",
        shape_source="pointer_bounds",
        contiguity="strided",
        reassociation="never",
        aliasing="borrowed",
        mutability="view",
    ),
]
module_allocatable: Annotated[Allocatable[Float64[:]], Aliased]

def associate_module_slice() -> None: ...
def associate_module_contiguous() -> None: ...
def allocate_module_values() -> None: ...
def sum_values(values: Float64[:]) -> Float64: ...
def sum_pointer_descriptor(values: Pointer[Float64[:]]) -> Float64: ...
def sum_allocatable_descriptor(values: Allocatable[Float64[:]]) -> Float64: ...
""",
        encoding="utf-8",
    )
    result = build_pyi_extension(
        contract,
        native_objects=[native_object],
        native_include_dirs=[native_object.parent],
        output_dir=tmp_path / "build",
    )
    module = _sole_native_module(_import_from_build_dir(result.module_name, result.output_dir))

    pointer_handle = module.module_values
    allocatable_handle = module.module_allocatable
    assert isinstance(pointer_handle, PointerArray)
    assert isinstance(allocatable_handle, AllocatableArray)
    assert module.module_values is pointer_handle
    assert module.module_allocatable is allocatable_handle
    assert module.sum_pointer_descriptor(pointer_handle) == np.float64(-1.0)
    assert module.sum_allocatable_descriptor(allocatable_handle) == np.float64(-1.0)

    module.associate_module_slice()
    assert pointer_handle.associated is True
    np.testing.assert_allclose(pointer_handle.to_numpy(), np.array([2.0, 4.0]))
    assert module.sum_pointer_descriptor(pointer_handle) == np.float64(6.0)
    with pytest.raises(ValueError, match="noncontiguous"):
        module.sum_values(pointer_handle)

    module.associate_module_contiguous()
    assert module.sum_values(pointer_handle) == np.float64(9.0)
    pointer_handle.nullify()
    assert pointer_handle.associated is False

    module.allocate_module_values()
    assert allocatable_handle.allocated is True
    np.testing.assert_allclose(allocatable_handle.to_numpy(), np.array([10.0, 20.0, 30.0]))
    assert module.sum_allocatable_descriptor(allocatable_handle) == np.float64(60.0)
    allocatable_handle.deallocate()
    assert allocatable_handle.allocated is False


def test_caller_created_pointer_handle_tracks_native_output_association(tmp_path: Path):
    source = tmp_path / "native" / "fpointer_handles_f90.f90"
    source.parent.mkdir()
    source.write_text(POINTER_HANDLE_SOURCE, encoding="utf-8")
    native_object = _compile_native_object(source, tmp_path / "native_build")
    contract = tmp_path / "contracts" / "fpointer_handles_f90.pyi"
    contract.parent.mkdir()
    pointer_type = """Annotated[
    Pointer[Float64[:]],
    PointerAssociation("runtime"),
    PointerPolicy(
        nullable=True,
        transfer="call_local",
        target_owner="module",
        lifetime="module",
        deallocation="never",
        shape_source="pointer_bounds",
        contiguity="contiguous",
        reassociation="native",
        aliasing="borrowed",
        mutability="view",
    ),
]"""
    contract.write_text(
        f"""from prik.contracts import Annotated, Float64, Pointer, PointerAssociation, PointerPolicy, Returns

def select_module_values(
    values: {pointer_type},
) -> Returns["values", {pointer_type}]: ...

def sum_pointer_descriptor(values: Pointer[Float64[:]]) -> Float64: ...
""",
        encoding="utf-8",
    )
    result = build_pyi_extension(
        contract,
        native_objects=[native_object],
        native_include_dirs=[native_object.parent],
        output_dir=tmp_path / "build",
    )
    module = _sole_native_module(_import_from_build_dir(result.module_name, result.output_dir))

    handle = Pointer[Float64[:]]()
    assert handle.associated is False
    assert module.sum_pointer_descriptor(handle) == np.float64(-1.0)
    assert module.select_module_values(handle) is handle
    assert handle.associated is True
    assert handle.shape == (3,)
    np.testing.assert_allclose(handle.to_numpy(), np.array([2.0, 3.0, 4.0]))
    assert module.sum_pointer_descriptor(handle) == np.float64(9.0)

    source = Pointer[Float64[:]]()
    assert module.select_module_values(source) is source
    alias = Pointer[Float64[:]]()
    alias.associate(source)
    assert alias.associated is True
    assert module.sum_pointer_descriptor(alias) == np.float64(9.0)
    source.nullify()
    assert alias.associated is True
    alias.associate(source)
    assert alias.associated is False

    source.close()
    alias.close()
    handle.close()
    assert handle.closed is True


def test_pointer_array_results_use_owned_descriptors_without_owning_targets(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    module = _build_source_or_generated_pyi_and_import(
        POINTERS_F90_SOURCE,
        tmp_path,
        {
            "bind_c_fpointers_f90_wrapper.f90",
            "fpointers_f90_wrapper.c",
            "fpointers_f90_wrapper.h",
        },
        CONTRACT_FIXTURES / "fpointers_f90",
        pyi_parity_build_mode,
    )
    values = np.array([1.0, 2.0, 3.0], dtype=np.float64)

    selected = module.pointer_to_values(values, np.int32(1))
    assert isinstance(selected, PointerArray)
    assert selected.owned is True
    assert selected.associated is True
    assert selected.shape == (3,)
    assert module.sum_pointer(selected) == np.float64(6.0)

    absent = module.pointer_to_values(values, np.int32(0))
    assert isinstance(absent, PointerArray)
    assert absent.associated is False
    assert absent.shape is None

    selected.close()
    absent.close()
    assert selected.closed is True
    assert absent.closed is True
    np.testing.assert_array_equal(values, np.array([1.0, 2.0, 3.0], dtype=np.float64))


POINTER_RELEASE_SOURCE = """
module fpointer_release_f90
  implicit none
  real(8), allocatable, target :: pool(:)
contains
  function mint(n) result(values)
    integer(4), intent(in) :: n
    real(8), pointer :: values(:)
    allocate(values(n))
    values = 1.0d0
  end function mint

  function borrow(n) result(values)
    integer(4), intent(in) :: n
    real(8), pointer :: values(:)
    if (.not. allocated(pool)) allocate(pool(n))
    pool = 2.0d0
    values => pool
  end function borrow
end module fpointer_release_f90
"""


@pytest.mark.fortran_end_to_end
def test_pointer_handle_releases_native_storage_when_the_caller_asks(tmp_path: Path):
    """A pointer handle offers the release a Fortran caller would write itself.

    prik never frees a native target on its own, so withholding the operation
    only removes the caller's ability to free storage the procedure handed
    over.  Reclaiming it has to be observable in the process, because an
    unreleased target still reports the same handle state.
    """
    source = tmp_path / "native" / "fpointer_release_f90.f90"
    source.parent.mkdir()
    source.write_text(POINTER_RELEASE_SOURCE, encoding="utf-8")
    module = _build_and_import(
        source,
        tmp_path,
        {
            "bind_c_fpointer_release_f90_wrapper.f90",
            "fpointer_release_f90_wrapper.c",
            "fpointer_release_f90_wrapper.h",
        },
    )

    handle = module.mint(np.int32(4))
    assert handle.associated is True
    handle.deallocate()
    assert handle.associated is False

    def peak_kib() -> int:
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

    extent = np.int32(4096)
    for _ in range(200):
        module.mint(extent).deallocate()
    baseline = peak_kib()
    for _ in range(4000):
        module.mint(extent).deallocate()
    assert peak_kib() - baseline == 0

    # A borrowed target is module storage the library keeps; releasing is the
    # caller's decision there too, so only the untouched path is asserted.
    assert module.borrow(np.int32(4)).associated is True
