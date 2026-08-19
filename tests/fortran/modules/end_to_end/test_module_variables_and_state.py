"""Module variables, parameters, saved state, and synchronization tests."""

import importlib
import sys
from pathlib import Path

import numpy as np
import pytest
from tests.fortran._support.wrapper_build import (
    _build_source_or_generated_pyi_and_import,
    _build_text_and_import,
    _sole_native_module,
)

FIXTURES = Path(__file__).parent / "fixtures"
MODULE_VARIABLES_F90_SOURCE = FIXTURES / "fmodule_vars_f90.f90"
CONTRACT_FIXTURES = FIXTURES / "contracts"
pytestmark = pytest.mark.fortran_end_to_end


def _module_variables_build_dir(tmp_path: Path, build_mode: str) -> Path:
    if build_mode == "source":
        return tmp_path / "source_build"
    return tmp_path / "generated_pyi_build" / "pyi_build"


def test_scalar_module_variables_use_attributes_and_parameters_have_no_native_setter(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    module = _build_source_or_generated_pyi_and_import(
        MODULE_VARIABLES_F90_SOURCE,
        tmp_path,
        {
            "bind_c_fmodule_vars_f90_wrapper.f90",
            "fmodule_vars_f90_wrapper.c",
            "fmodule_vars_f90_wrapper.h",
        },
        CONTRACT_FIXTURES / "fmodule_vars_f90",
        pyi_parity_build_mode,
    )

    module_docstring = module.__doc__
    assert module_docstring.startswith("fmodule_vars_f90\n\nModule Attributes")
    assert "fmodule_vars_f90.fmodule_vars_f90" not in module_docstring
    assert module_docstring.index("Module Attributes") < module_docstring.index("Functions")
    assert module_docstring.index("Functions") < module_docstring.index("Classes")
    assert "nmax : int32\n    Read-only constant." in module_docstring
    assert "counter : int32" in module_docstring
    assert "scale : float64" in module_docstring
    assert "saved_counter : int32" in module_docstring
    assert "Assignment writes through to native storage." not in module_docstring

    assert module.nmax == np.int32(12)
    assert isinstance(module.black, module.rgb_color)
    assert module.black.r == np.int32(0)
    assert module.black.g == np.int32(0)
    assert module.black.b == np.int32(0)
    assert module.black_sum() == np.int32(0)
    assert module.counter == np.int32(3)
    assert module.scale == np.float64(1.5)
    assert not hasattr(module, "get_counter")
    assert not hasattr(module, "set_counter")
    assert not hasattr(module, "get_scale")
    assert not hasattr(module, "set_scale")
    assert not hasattr(module, "set_nmax")
    assert not hasattr(module, "set_red")
    assert not hasattr(module, "set_black")
    assert not hasattr(module, "hidden_counter")
    assert not hasattr(module, "get_hidden_counter")

    assert module.summarize() == np.int32(15)
    module.counter = np.int32(9)
    assert module.counter == np.int32(9)
    assert module.summarize() == np.int32(21)

    module.scale = np.float64(2.0)
    assert module.scaled_counter() == np.float64(18.0)

    assert module.saved_counter == np.int32(6)
    module.saved_counter = np.int32(8)
    assert module.saved_counter == np.int32(8)
    assert module.next_local() == np.int32(1)
    assert module.next_local() == np.int32(2)

    build_dir = _module_variables_build_dir(tmp_path, pyi_parity_build_mode)
    if pyi_parity_build_mode == "source":
        wrapper_source = (build_dir / "fmodule_vars_f90_wrapper.c").read_text(encoding="utf-8")
        summarize_start = wrapper_source.index("static PyObject * wrap_summarize")
        scaled_start = wrapper_source.index("static PyObject * wrap_scaled_counter")
        getter_start = wrapper_source.index("static PyObject * module_get_counter")
        setter_start = wrapper_source.index("static int module_set_counter")
        next_getter_start = wrapper_source.index("static PyObject * module_get_scale")
        assert "Py_BEGIN_ALLOW_THREADS" not in wrapper_source[summarize_start:scaled_start]
        assert "Py_END_ALLOW_THREADS" not in wrapper_source[summarize_start:scaled_start]
        assert "Py_BEGIN_ALLOW_THREADS" not in wrapper_source[getter_start:setter_start]
        assert "Py_END_ALLOW_THREADS" not in wrapper_source[getter_start:setter_start]
        assert "Py_BEGIN_ALLOW_THREADS" not in wrapper_source[setter_start:next_getter_start]
        assert "Py_END_ALLOW_THREADS" not in wrapper_source[setter_start:next_getter_start]
    assert not hasattr(module, "get_local_counter")

    sys.modules.pop("fmodule_vars_f90", None)
    sys.path.insert(0, str(build_dir))
    try:
        second_module = _sole_native_module(importlib.import_module("fmodule_vars_f90"))
    finally:
        sys.path.remove(str(build_dir))

    assert second_module is not module
    assert second_module.counter == np.int32(9)
    assert second_module.saved_counter == np.int32(8)
    second_module.counter = np.int32(4)
    assert module.counter == np.int32(4)

    module.nmax = np.int32(99)
    assert module.nmax == np.int32(99)
    assert second_module.nmax == np.int32(12)
    assert module.summarize() == np.int32(16)
    assert second_module.summarize() == np.int32(16)

    black_copy = module.black
    black_copy.r = np.int32(17)
    assert black_copy.r == np.int32(17)
    assert module.black.r == np.int32(0)
    assert module.black_sum() == np.int32(0)
    assert second_module.black.r == np.int32(0)


CHARACTER_MODULE_ARRAY_SOURCE = """
module fchar_module_arrays_f90
  implicit none
  character(len=8), target :: labels(3) = ['alpha   ', 'beta    ', 'gamma   ']
  character(len=4), target :: grid(2, 2) = reshape(['aa  ', 'bb  ', 'cc  ', 'dd  '], [2, 2])
contains
  subroutine relabel_first()
    labels(1) = 'ALPHA!!!'
  end subroutine relabel_first

  function read_label(index) result(value)
    integer(4), intent(in) :: index
    character(len=8) :: value
    value = labels(index)
  end function read_label

  function read_grid(row, column) result(value)
    integer(4), intent(in) :: row, column
    character(len=4) :: value
    value = grid(row, column)
  end function read_grid
end module fchar_module_arrays_f90
"""


def test_fixed_shape_character_module_arrays_expose_one_live_bytes_view(tmp_path: Path):
    """A character module array borrows the same fixed-width view a numeric one does.

    The element type only changes the dtype width, so the live-view contract is
    what has to hold: native writes appear without re-reading the attribute, and
    Python writes are visible to Fortran through the same storage.
    """
    module = _build_text_and_import(
        CHARACTER_MODULE_ARRAY_SOURCE,
        "fchar_module_arrays_f90.f90",
        tmp_path,
        {
            "bind_c_fchar_module_arrays_f90_wrapper.f90",
            "fchar_module_arrays_f90_wrapper.c",
            "fchar_module_arrays_f90_wrapper.h",
        },
    )

    assert module.labels.dtype == np.dtype("S8")
    assert module.grid.dtype == np.dtype("S4")
    assert module.grid.shape == (2, 2)
    assert module.grid.flags["F_CONTIGUOUS"] is True
    np.testing.assert_array_equal(module.labels, np.array([b"alpha   ", b"beta    ", b"gamma   "], dtype="S8"))

    # A native write reaches the view the attribute already handed out.
    module.relabel_first()
    assert module.labels[0] == b"ALPHA!!!"

    # A Python write reaches the storage Fortran reads.
    module.labels[1] = b"PYTHON!!"
    assert module.read_label(np.int32(2)) == "PYTHON!!"
    module.grid[1, 0] = b"ZZ  "
    assert module.read_grid(np.int32(2), np.int32(1)) == "ZZ  "


CHARACTER_MODULE_SCALAR_SOURCE = """
module fchar_module_scalars_f90
  implicit none
  character(len=8) :: label = 'alpha   '
  character(len=3) :: code = 'abc'
  character(len=*), parameter :: tag = 'fixed'
contains
  subroutine relabel()
    label = 'ALPHA!!!'
  end subroutine relabel

  function read_label() result(value)
    character(len=8) :: value
    value = label
  end function read_label
end module fchar_module_scalars_f90
"""


def test_scalar_character_module_variables_read_and_write_through(tmp_path: Path):
    """A character module variable is a `str` property, as a numeric one is a value.

    A character value has no by-value C ABI, so the accessors copy through a
    fixed-width buffer; what has to hold is that the copy runs in both
    directions and that a wrong width is refused rather than truncated.
    """
    module = _build_text_and_import(
        CHARACTER_MODULE_SCALAR_SOURCE,
        "fchar_module_scalars_f90.f90",
        tmp_path,
        {
            "bind_c_fchar_module_scalars_f90_wrapper.f90",
            "fchar_module_scalars_f90_wrapper.c",
            "fchar_module_scalars_f90_wrapper.h",
        },
    )

    assert module.label == "alpha   "
    assert module.code == "abc"
    assert module.tag == "fixed"

    # A native write is observed by the next read, not cached from import.
    module.relabel()
    assert module.label == "ALPHA!!!"

    # A Python write reaches the storage Fortran reads.
    module.label = "PYTHON!!"
    assert module.read_label() == "PYTHON!!"

    # The declared length is a byte width, so a multi-byte encoding still fits exactly.
    module.label = "café!!!"
    assert module.label == "café!!!"
    assert module.read_label() == "café!!!"


@pytest.mark.parametrize("value", ["ab", "abcd"])
def test_scalar_character_module_variable_rejects_a_wrong_encoded_width(value: str, tmp_path: Path):
    """Truncating or padding silently would corrupt native state, so the width is exact."""
    module = _build_text_and_import(
        CHARACTER_MODULE_SCALAR_SOURCE,
        "fchar_module_scalars_f90.f90",
        tmp_path,
        {
            "bind_c_fchar_module_scalars_f90_wrapper.f90",
            "fchar_module_scalars_f90_wrapper.c",
            "fchar_module_scalars_f90_wrapper.h",
        },
    )

    with pytest.raises(TypeError, match="exactly 3 bytes"):
        module.code = value
    assert module.code == "abc"


CHARACTER_MODULE_DESCRIPTOR_SOURCE = """
module fchar_module_descriptors_f90
  implicit none
  character(len=:), allocatable :: deferred
  character(len=6), allocatable :: fixed
  character(len=:), pointer :: link => null()
  character(len=6), target :: store = 'STORED'
  character(len=2), parameter :: pair(2) = ['ab', 'cd']
  character(len=3), parameter :: grid(2, 2) = reshape(['aaa', 'bbb', 'ccc', 'ddd'], [2, 2])
contains
  subroutine setup()
    deferred = 'alpha'
    fixed = 'FIXEDV'
    link => store
  end subroutine setup

  subroutine grow()
    deferred = deferred // '-more'
  end subroutine grow

  subroutine clear()
    if (allocated(deferred)) deallocate(deferred)
    if (allocated(fixed)) deallocate(fixed)
    nullify(link)
  end subroutine clear
end module fchar_module_descriptors_f90
"""


def _character_descriptor_module(tmp_path: Path):
    return _build_text_and_import(
        CHARACTER_MODULE_DESCRIPTOR_SOURCE,
        "fchar_module_descriptors_f90.f90",
        tmp_path,
        {
            "bind_c_fchar_module_descriptors_f90_wrapper.f90",
            "fchar_module_descriptors_f90_wrapper.c",
            "fchar_module_descriptors_f90_wrapper.h",
        },
    )


def test_descriptor_character_module_variables_snapshot_their_runtime_value(tmp_path: Path):
    """An allocatable or pointer character module variable reads as a detached `str`.

    Its width is established at runtime, so the snapshot has to report the
    length the descriptor currently holds rather than a width fixed at build
    time, and re-reading after native code changes it must observe the change.
    """
    module = _character_descriptor_module(tmp_path)

    assert module.deferred is None
    assert module.fixed is None
    assert module.link is None

    module.setup()
    assert module.deferred == "alpha"
    assert module.fixed == "FIXEDV"
    assert module.link == "STORED"

    # A reallocation to a different width is observed by the next read.
    module.grow()
    assert module.deferred == "alpha-more"


def test_descriptor_character_module_variables_report_absence_as_none(tmp_path: Path):
    """Deallocation and nullification are values Python observes, not stale reads."""
    module = _character_descriptor_module(tmp_path)

    module.setup()
    module.clear()
    assert module.deferred is None
    assert module.fixed is None
    assert module.link is None


def test_character_parameter_arrays_are_read_only_fixed_width_snapshots(tmp_path: Path):
    """A character parameter array is copied once, like a numeric one.

    A Fortran parameter has no addressable storage, so the value is a
    Python-owned copy taken at import; it must therefore be read-only and keep
    the declared element width as its dtype.
    """
    module = _character_descriptor_module(tmp_path)

    assert module.pair.dtype == np.dtype("S2")
    assert module.grid.dtype == np.dtype("S3")
    assert module.grid.shape == (2, 2)
    assert module.pair.flags["WRITEABLE"] is False
    assert module.grid.flags["WRITEABLE"] is False
    np.testing.assert_array_equal(module.pair, np.array([b"ab", b"cd"], dtype="S2"))
    np.testing.assert_array_equal(
        module.grid,
        np.array([[b"aaa", b"ccc"], [b"bbb", b"ddd"]], dtype="S3"),
    )
