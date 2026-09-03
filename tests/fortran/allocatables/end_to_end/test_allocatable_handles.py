"""Allocatable result, module-array, and component-view ownership tests."""

import gc
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import (
    _build_source_or_generated_pyi_and_import,
    _build_text_and_import,
    _compile_native_object,
    _import_from_build_dir,
    _require_maybe_unallocated_function_result_support,
    _sole_native_module,
)
from prik import build_pyi_extension
from prik.contracts import Allocatable, Float64
from prik.runtime.handles import AllocatableArray

FIXTURES = Path(__file__).parent / "fixtures"
ALLOCATABLE_VIEW_F90_SOURCE = FIXTURES / "native" / "fallocatable_views_f90.f90"
CONTRACT_FIXTURES = FIXTURES / "contracts"
pytestmark = pytest.mark.fortran_end_to_end


def _allocatable_dummy_handoff_supported() -> bool:
    """Report whether this compiler accepts a handle at an allocatable dummy.

    ifx rejects the established descriptor for that argument form regardless of
    the bounds it carries, so the round-trip below is checked where it works.
    The descriptor facts themselves are asserted on every compiler.
    """
    return "ifx" not in os.environ.get("PRIK_TEST_FORTRAN_COMPILER", "gfortran")


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
            "prik",
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


def _maybe_unallocated_direct_result_module(tmp_path: Path):
    native_object = _compile_native_object(ALLOCATABLE_VIEW_F90_SOURCE, tmp_path / "native")
    contract_dir = tmp_path / "contracts" / "fallocatable_views_f90"
    contract_dir.mkdir(parents=True)
    (contract_dir / "__init__.pyi").write_text("from . import fallocatable_views_f90\n", encoding="utf-8")
    contract_text = (CONTRACT_FIXTURES / "fallocatable_views_f90" / "fallocatable_views_f90.pyi").read_text(
        encoding="utf-8"
    )
    contract_text = contract_text.replace(
        "Int32, Pass",
        "Annotated, Int32, MaybeUnallocated, Pass",
    )
    contract_text = contract_text.replace(
        "def maybe_alloc_vector(\n    n: Int32\n) -> Allocatable[Float64[:]]: ...",
        "def maybe_alloc_vector(\n    n: Int32\n) -> Annotated[Allocatable[Float64[:]], MaybeUnallocated]: ...",
    )
    contract_text = contract_text.replace(
        "def maybe_alloc_matrix(\n    rows: Int32,\n    cols: Int32\n) -> Allocatable[Float64[:, :]]: ...",
        "def maybe_alloc_matrix(\n"
        "    rows: Int32,\n"
        "    cols: Int32\n"
        ") -> Annotated[Allocatable[Float64[:, :]], MaybeUnallocated]: ...",
    )
    (contract_dir / "fallocatable_views_f90.pyi").write_text(contract_text, encoding="utf-8")
    result = build_pyi_extension(
        contract_dir / "__init__.pyi",
        native_objects=[native_object],
        native_include_dirs=[native_object.parent],
        output_dir=tmp_path / "pyi_build",
    )
    return _sole_native_module(_import_from_build_dir(result.module_name, result.output_dir))


@pytest.fixture
def compiled_allocatable_module(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    return _build_source_or_generated_pyi_and_import(
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


def test_allocatable_module_fields_and_results_expose_lifetime_safe_handles(
    compiled_allocatable_module,
):
    module = compiled_allocatable_module

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
    zero_values = module.make_values(np.int32(0))
    assert zero_values.allocated is True
    assert zero_values.shape == (0,)
    assert zero_values.to_numpy().shape == (0,)

    made_matrix = module.make_matrix(np.int32(2), np.int32(2))
    np.testing.assert_allclose(
        made_matrix.to_numpy(),
        np.array([[111.0, 121.0], [112.0, 122.0]], dtype=np.float64),
    )
    maybe_vector = module.maybe_alloc_vector(np.int32(3))
    np.testing.assert_allclose(maybe_vector.to_numpy(), np.array([5.0, 10.0, 15.0], dtype=np.float64))
    zero_vector = module.zero_alloc_vector()
    assert zero_vector.allocated is True
    assert zero_vector.shape == (0,)
    assert zero_vector.to_numpy().shape == (0,)
    maybe_matrix = module.maybe_alloc_matrix(np.int32(2), np.int32(3))
    np.testing.assert_allclose(
        maybe_matrix.to_numpy(),
        np.array([[110.0, 120.0, 130.0], [210.0, 220.0, 230.0]], dtype=np.float64),
    )
    zero_matrix = module.zero_alloc_matrix(np.int32(2))
    assert zero_matrix.allocated is True
    assert zero_matrix.shape == (0, 2)
    assert zero_matrix.to_numpy().shape == (0, 2)

    replacement = module.build_values(np.int32(2))
    assert module.replace_values(replacement, np.int32(1)) is replacement
    np.testing.assert_allclose(replacement.to_numpy(), np.array([12.0, 14.0], dtype=np.float64))
    assert module.replace_values(replacement, np.int32(3)) is replacement
    np.testing.assert_allclose(replacement.to_numpy(), np.array([3.0, 6.0, 9.0], dtype=np.float64))
    assert module.replace_values(replacement, np.int32(0)) is replacement
    assert replacement.allocated is False
    assert replacement.to_numpy() is None
    assert module.replace_values(replacement, np.int32(1)) is replacement
    np.testing.assert_allclose(replacement.to_numpy(), np.array([1.0, 2.0], dtype=np.float64))

    fresh = Allocatable[Float64[:]]()
    assert fresh.allocated is False
    assert module.replace_values(fresh, np.int32(3)) is fresh
    np.testing.assert_allclose(fresh.to_numpy(), np.array([3.0, 6.0, 9.0], dtype=np.float64))
    with pytest.raises(TypeError):
        module.replace_values(np.array([1.0], dtype=np.float32), np.int32(1))
    with pytest.raises(TypeError):
        module.replace_values(np.array([[1.0]], dtype=np.float64), np.int32(1))
    fresh.close()
    replacement.close()

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
    _require_maybe_unallocated_function_result_support()
    module = _maybe_unallocated_direct_result_module(tmp_path)

    made_values = module.maybe_alloc_vector(np.int32(3))
    np.testing.assert_allclose(made_values.to_numpy(), np.array([5.0, 10.0, 15.0], dtype=np.float64))
    assert module.maybe_alloc_vector(np.int32(0)).allocated is False

    made_matrix = module.maybe_alloc_matrix(np.int32(2), np.int32(2))
    np.testing.assert_allclose(
        made_matrix.to_numpy(),
        np.array([[110.0, 120.0], [210.0, 220.0]], dtype=np.float64),
    )
    assert module.maybe_alloc_matrix(np.int32(0), np.int32(2)).allocated is False


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


LOWER_BOUND_SOURCE = """
module falloc_lower_bounds_f90
  use iso_fortran_env, only: int32, real64
  implicit none
  real(real64), allocatable :: plain_a(:)
  real(real64), allocatable, target :: tgt_a(:)
  real(real64), allocatable, target :: defaulted(:)
  character(len=5), allocatable, target :: fixed_words(:)
  character(len=:), allocatable, target :: deferred_words(:)
contains
  function lower_bound_of(x) result(bound)
    real(real64), allocatable, intent(in) :: x(:)
    integer(int32) :: bound
    bound = lbound(x, 1)
  end function lower_bound_of

  function element_at(x, index) result(value)
    real(real64), allocatable, intent(in) :: x(:)
    integer(int32), intent(in) :: index
    real(real64) :: value
    value = x(index)
  end function element_at

  subroutine setup()
    allocate(plain_a(5:8))
    plain_a = 1.0d0
    allocate(tgt_a(5:8))
    tgt_a = 2.0d0
    allocate(defaulted(4))
    defaulted = 3.0d0
    allocate(character(len=5) :: fixed_words(5:8))
    fixed_words = 'aaaaa'
    allocate(character(len=6) :: deferred_words(5:8))
    deferred_words = 'bbbbbb'
  end subroutine setup
end module falloc_lower_bounds_f90
"""


def test_module_allocatable_reports_its_real_lower_bound_with_or_without_target(tmp_path: Path):
    """A module allocatable reports the bounds it actually has, either way.

    `target` allows `c_loc` on the variable, but that yields only a base address:
    the bounds, strides and element length then have to come from somewhere else.
    Reconstructing them hardcoded a lower bound of zero, which is wrong for every
    Fortran array — the default is one — and further wrong for a declared `(5:8)`.
    Both declarations read the descriptor, so both report 5.
    """
    module = _build_text_and_import(
        LOWER_BOUND_SOURCE,
        "falloc_lower_bounds_f90.f90",
        tmp_path,
        {
            "bind_c_falloc_lower_bounds_f90_wrapper.f90",
            "falloc_lower_bounds_f90_wrapper.c",
            "falloc_lower_bounds_f90_wrapper.h",
        },
    )
    module.setup()

    for name in ("plain_a", "tgt_a", "defaulted"):
        handle = getattr(module, name)
        record = handle._descriptor_record_for_binding()
        # A defaulted allocation still starts at one, which the reconstruction
        # also got wrong by reporting zero.
        assert record["dim"][0]["lower_bound"] == (1 if name == "defaulted" else 5), name
        assert record["dim"][0]["extent"] == 4, name
        assert record["elem_len"] == 8, name
        # The Python view is unaffected: NumPy indexing stays zero-based.
        assert handle.to_numpy().shape == (4,)

    # A character allocatable reads the same descriptor, and its element length
    # comes from the array rather than from a width the binding assumed.
    for name, width in (("fixed_words", 5), ("deferred_words", 6)):
        record = getattr(module, name)._descriptor_record_for_binding()
        assert record["dim"][0]["lower_bound"] == 5, name
        assert record["elem_len"] == width, name

    # The bound is not a reported fact but part of the value: an allocatable
    # dummy adopts the bounds of the descriptor it is given, so a wrong one
    # makes the callee index the wrong elements.
    if not _allocatable_dummy_handoff_supported():
        return
    for name in ("plain_a", "tgt_a"):
        handle = getattr(module, name)
        assert module.lower_bound_of(handle) == np.int32(5), name
        assert module.element_at(handle, np.int32(5)) == handle.to_numpy()[0], name


BORROWED_DESCRIPTOR_SOURCE = """\
module fallocatable_borrowed_f90
  implicit none
  type :: box
    real(8), allocatable :: field(:)
  end type box
  real(8), allocatable :: modvar(:)
  type(box) :: thebox
contains
  subroutine grow(values)
    real(8), allocatable, intent(inout) :: values(:)

    if (allocated(values)) deallocate(values)
    allocate(values(6))
    values = 9.0_8
  end subroutine grow

  function total(values) result(sum_out)
    real(8), allocatable, intent(in) :: values(:)
    real(8) :: sum_out

    sum_out = sum(values)
  end function total

  function make(n) result(values)
    integer(4), intent(in) :: n
    real(8), allocatable :: values(:)
    integer(4) :: i

    allocate(values(n))
    values = [(1.0_8 * i, i = 1, n)]
  end function make
end module fallocatable_borrowed_f90
"""


def test_every_allocatable_handle_kind_reaches_a_read_only_allocatable_dummy(tmp_path: Path):
    """An allocatable actual borrows the descriptor the Fortran runtime built.

    A read-only allocatable dummy requires an allocatable actual, and C may not
    establish one: F2018 18.5.5.6 reserves that descriptor for the runtime.  The
    binding therefore copies the descriptor handed to its callback rather than
    rebuilding one from facts, so module, derived-field and result handles all
    reach the dummy on every compiler instead of only where an invalid
    descriptor happens to be tolerated.
    """
    workdir = tmp_path / "borrowed"
    workdir.mkdir(parents=True)
    module = _build_text_and_import(
        BORROWED_DESCRIPTOR_SOURCE,
        "fallocatable_borrowed_f90.f90",
        workdir,
        {
            "bind_c_fallocatable_borrowed_f90_wrapper.f90",
            "fallocatable_borrowed_f90_wrapper.c",
            "fallocatable_borrowed_f90_wrapper.h",
        },
    )
    namespace = _sole_native_module(module)

    namespace.modvar.resize(4)
    namespace.modvar.to_numpy()[:] = [1.0, 2.0, 3.0, 4.0]
    namespace.thebox.field.resize(4)
    namespace.thebox.field.to_numpy()[:] = [1.0, 2.0, 3.0, 4.0]

    assert namespace.total(namespace.modvar) == np.float64(10.0)
    assert namespace.total(namespace.thebox.field) == np.float64(10.0)
    assert namespace.total(namespace.make(np.int32(4))) == np.float64(10.0)

    # The copy is remade per call, so reallocating the native entity between
    # calls cannot leave the previous descriptor behind.
    namespace.modvar.resize(3)
    namespace.modvar.to_numpy()[:] = [100.0, 200.0, 300.0]
    assert namespace.total(namespace.modvar) == np.float64(600.0)


def test_a_writable_allocatable_dummy_refuses_a_borrowed_descriptor(tmp_path: Path):
    """A borrowed descriptor copy may not stand in where the callee reallocates.

    A read-only allocatable actual can be a per-call copy of the runtime's
    descriptor, because the callee cannot change its allocation.  An
    ``intent(inout)`` allocatable can: the callee may deallocate and reallocate
    it, and through a copy that would land in the copy and leave the caller's
    entity pointing at released storage.  Such an argument is refused instead.
    """
    workdir = tmp_path / "writable"
    workdir.mkdir(parents=True)
    module = _build_text_and_import(
        BORROWED_DESCRIPTOR_SOURCE,
        "fallocatable_borrowed_f90.f90",
        workdir,
        {
            "bind_c_fallocatable_borrowed_f90_wrapper.f90",
            "fallocatable_borrowed_f90_wrapper.c",
            "fallocatable_borrowed_f90_wrapper.h",
        },
    )
    namespace = _sole_native_module(module)

    namespace.modvar.resize(2)
    namespace.modvar.to_numpy()[:] = [1.0, 2.0]
    with pytest.raises(TypeError, match="requires a generated direct descriptor handoff"):
        namespace.grow(namespace.modvar)

    # The module variable is untouched by the refusal.
    assert namespace.modvar.shape == (2,)
    assert namespace.modvar.to_numpy().tolist() == [1.0, 2.0]

    # A handle that owns its descriptor still works, and the callee's
    # reallocation reaches it.
    owned = namespace.make(np.int32(2))
    namespace.grow(owned)
    assert owned.shape == (6,)
    assert owned.to_numpy().tolist() == [9.0] * 6
