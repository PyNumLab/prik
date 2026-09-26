"""Module variables, parameters, saved state, and synchronization tests."""

import importlib
import sys
from pathlib import Path

import numpy as np
import pytest
from tests.fortran._support.wrapper_build import (
    _build_generated_pyi_and_import,
    _build_source_and_import,
    _build_source_or_generated_pyi_and_import,
    _build_text_and_import,
    _sole_native_module,
)

FIXTURES = Path(__file__).parent / "fixtures"
MODULE_VARIABLES_F90_SOURCE = FIXTURES / "native" / "fmodule_vars_f90.f90"
CONTRACT_FIXTURES = FIXTURES / "contracts"
pytestmark = pytest.mark.fortran_end_to_end

NATIVE_FIXTURES = Path(__file__).parent / "fixtures" / "native"


MODULE_VARIABLE_REEXPORT_SOURCE = (NATIVE_FIXTURES / "module_variable_reexports.f90").read_text(encoding="utf-8")


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
    # A mutable module scalar is a live rank-zero view, and the docstring says so.
    assert "counter : ndarray[int32]\n    Rank: 0\n    Live view" in module_docstring
    assert "scale : ndarray[float64]\n    Rank: 0\n    Live view" in module_docstring
    assert "saved_counter : ndarray[int32]" in module_docstring
    assert "Assignment writes through to native storage." not in module_docstring

    assert module.nmax == np.int32(12)
    assert isinstance(module.black, module.Rgb_Color)
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


PLAIN_MODULE_ARRAY_SOURCE = (NATIVE_FIXTURES / "fplain_module_arrays_f90.f90").read_text(encoding="utf-8")


def test_fixed_module_arrays_without_target_expose_the_same_live_view(tmp_path: Path):
    """A fixed module array is borrowed live whether or not it declares `target`.

    `target` is what lets `c_loc` name the array, not what gives the array a
    stable address, so withholding it changes the route to the base address and
    nothing the caller can observe. The claim here is that both declarations
    produce one live view over the real module storage: Fortran writes appear
    without re-reading the attribute, Python writes are visible to Fortran, and
    neither form accepts whole-array replacement.
    """
    module = _build_text_and_import(
        PLAIN_MODULE_ARRAY_SOURCE,
        "fplain_module_arrays_f90.f90",
        tmp_path,
        {
            "bind_c_fplain_module_arrays_f90_wrapper.f90",
            "fplain_module_arrays_f90_wrapper.c",
            "fplain_module_arrays_f90_wrapper.h",
        },
    )

    assert module.grid.shape == (2, 3)
    assert module.grid.dtype == np.dtype(np.float64)
    assert module.grid.flags["F_CONTIGUOUS"] is True
    np.testing.assert_array_equal(module.counts, np.array([7, 8, 9], dtype=np.int32))
    np.testing.assert_array_equal(module.labels, np.array([b"alpha", b"bravo"], dtype="S5"))

    # A view handed out earlier still names the storage Fortran writes.
    view = module.grid
    view[0, 0] = np.float64(10.0)
    module.bump()
    assert view[0, 0] == np.float64(11.0)
    assert module.grid[0, 0] == np.float64(11.0)

    # A Python write reaches the storage Fortran reads, for every element type.
    module.grid[1, 2] = np.float64(4.5)
    assert module.read_grid(np.int32(2), np.int32(3)) == np.float64(4.5)
    module.counts[1] = np.int32(99)
    assert module.read_count(np.int32(2)) == np.int32(99)
    module.labels[0] = b"omega"
    assert module.read_label(np.int32(1)) == "omega"

    # The addressable declaration borrows identically.
    module.addressable[0] = np.float64(6.0)
    assert module.addressable[0] == np.float64(6.0)

    # Neither form hands the whole variable back to be reassigned.
    for name in ("grid", "counts", "addressable"):
        with pytest.raises(AttributeError, match="read-only"):
            setattr(module, name, np.zeros(2))


CHARACTER_MODULE_ARRAY_SOURCE = (NATIVE_FIXTURES / "fchar_module_arrays_f90.f90").read_text(encoding="utf-8")


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


def test_scalar_character_module_variables_read_and_write_through(pyi_parity_build_mode: str, tmp_path: Path):
    """Fixed character storage keeps one native address across reads and writes."""
    module = _build_source_or_generated_pyi_and_import(
        NATIVE_FIXTURES / "fchar_module_scalars_f90.f90",
        tmp_path,
        {
            "bind_c_fchar_module_scalars_f90_wrapper.f90",
            "fchar_module_scalars_f90_wrapper.c",
            "fchar_module_scalars_f90_wrapper.h",
        },
        CONTRACT_FIXTURES / "fchar_module_scalars_f90",
        pyi_parity_build_mode,
    )

    label = module.label
    assert label.shape == () and label.dtype == np.dtype("S8")
    assert label[()] == b"alpha   "
    assert module.code[()] == b"abc"
    assert module.tag == "fixed"

    # A native write is observed by the next read, not cached from import.
    module.relabel()
    assert label[()] == b"ALPHA!!!"

    # A Python write reaches the storage Fortran reads.
    module.label = "PYTHON!!"
    assert label[()] == b"PYTHON!!"
    assert module.read_label() == "PYTHON!!"
    label[()] = b"VIEW!!!!"
    assert module.read_label() == "VIEW!!!!"

    # The declared length is a byte width, so a multi-byte encoding still fits exactly.
    module.label = "café!!!"
    assert label[()] == "café!!!".encode()
    assert module.read_label() == "café!!!"

    # Truncating or padding silently would corrupt native state, so the width is exact.
    for value in ("ab", "abcd"):
        with pytest.raises(TypeError, match="exactly 3 bytes"):
            module.code = value
    assert module.code[()] == b"abc"


def test_descriptor_character_module_variables_follow_current_storage(pyi_parity_build_mode: str, tmp_path: Path):
    """Each read lends the current storage read-only; assignment writes through the descriptor.

    Deallocation and nullification are values Python observes, not stale reads.
    A character parameter array has no addressable storage, so it is a
    read-only Python-owned copy taken at import with the declared element width
    as its dtype; a `len=*` parameter reports the width the Fortran side infers
    from its initializer.
    """
    module = _build_source_or_generated_pyi_and_import(
        NATIVE_FIXTURES / "fchar_module_descriptors_f90.f90",
        tmp_path,
        {
            "bind_c_fchar_module_descriptors_f90_wrapper.f90",
            "fchar_module_descriptors_f90_wrapper.c",
            "fchar_module_descriptors_f90_wrapper.h",
        },
        CONTRACT_FIXTURES / "fchar_module_descriptors_f90",
        pyi_parity_build_mode,
    )
    assert module.pair.dtype == np.dtype("S2")
    assert module.grid.dtype == np.dtype("S3")
    assert module.grid.shape == (2, 2)
    assert module.pair.flags["WRITEABLE"] is False
    assert module.grid.flags["WRITEABLE"] is False
    np.testing.assert_array_equal(module.pair, np.array([b"ab", b"cd"], dtype="S2"))
    np.testing.assert_array_equal(module.grid, np.array([[b"aaa", b"ccc"], [b"bbb", b"ddd"]], dtype="S3"))
    assert module.inferred.dtype == np.dtype("S5")
    np.testing.assert_array_equal(module.inferred, np.array([b"alpha", b"beta ", b"gamma"], dtype="S5"))

    assert module.deferred is None
    assert module.fixed is None
    assert module.link is None

    module.setup()
    deferred = module.deferred
    fixed = module.fixed
    view = module.link
    assert deferred is not None and deferred.shape == () and deferred.dtype == np.dtype("S5")
    assert deferred[()] == b"alpha"
    assert fixed is not None and fixed[()] == b"FIXEDV"
    assert view is not None and view.shape == () and view.dtype == np.dtype("S6")
    assert view[()] == b"STORED"
    with pytest.raises(ValueError, match="read-only"):
        view[()] = b"PYTHON"
    module.link = "PYTHON"
    assert view[()] == b"PYTHON"
    assert module.store[()] == b"PYTHON"
    with pytest.raises(TypeError, match="pointer target's width"):
        module.link = "SHORT"

    module.grow()
    grown = module.deferred
    assert grown is not None and grown.shape == () and grown.dtype == np.dtype("S10")
    assert grown[()] == b"alpha-more"

    # A deferred-length assignment reallocates to the encoded width, including zero.
    module.deferred = "omega"
    assert module.deferred[()] == b"omega"
    module.deferred = ""
    assert module.deferred is not None and module.deferred[()] == b""
    with pytest.raises(TypeError, match="exactly 6 bytes"):
        module.fixed = "WIDE!!!"
    module.fixed = "NARROW"
    assert module.fixed[()] == b"NARROW"

    module.clear()
    assert module.deferred is None
    assert module.fixed is None
    assert module.link is None
    # The documented type admits the ``None`` those reads return.
    for name in ("deferred", "fixed", "link"):
        assert f"{name} : ndarray[bytes] or None" in module.__doc__


DECLARED_LENGTH_CHARACTER_ARRAY_SOURCE = (NATIVE_FIXTURES / "fchar_declared_arrays_f90.f90").read_text(encoding="utf-8")


def test_declared_length_character_module_arrays_compile_and_expose_their_width(tmp_path: Path):
    """A descriptor dummy accepts a deferred-length actual only if it declares one.

    The generated descriptor-consumer interface and descriptor ABI both have to
    spell the width the module array actually declares; deferring it
    unconditionally is rejected by the Fortran compiler, so building the module
    at all is the evidence here.

    A deferred-length *allocatable* character array is left out: GNU Fortran
    11.4 fails with an internal compiler error on that declaration, which is a
    compiler defect rather than a wrapper contract.
    """
    module = _build_text_and_import(
        DECLARED_LENGTH_CHARACTER_ARRAY_SOURCE,
        "fchar_declared_arrays_f90.f90",
        tmp_path,
        {
            "bind_c_fchar_declared_arrays_f90_wrapper.f90",
            "fchar_declared_arrays_f90_wrapper.c",
            "fchar_declared_arrays_f90_wrapper.h",
        },
    )

    assert module.fixed_alloc.allocated is False
    module.setup()

    assert module.fixed_alloc.allocated is True
    np.testing.assert_array_equal(
        module.fixed_alloc.to_numpy(),
        np.array([b"xxxx", b"yyyy"], dtype="S4"),
    )
    # A pointer array reports its shape and association; extracting its target
    # stays gated behind PointerPolicy, as it is for a numeric pointer array.
    assert module.fixed_ptr.associated is True
    assert module.fixed_ptr.shape == (2,)
    assert module.deferred_ptr.associated is True
    assert module.deferred_ptr.shape == (2,)
    assert module.deferred_ptr.dtype == np.dtype("S4")

    module.deferred_ptr.nullify()
    assert module.deferred_ptr.associated is False
    assert module.deferred_ptr.shape is None

    module.allocate_deferred()
    assert module.deferred_ptr.associated is True
    assert module.deferred_ptr.shape == (3,)
    assert module.deferred_ptr.dtype == np.dtype("S6")
    module.deferred_ptr.deallocate()
    assert module.deferred_ptr.associated is False
    assert module.deferred_ptr.shape is None


REEXPORT_SOURCE = NATIVE_FIXTURES / "reexport.f90"


def test_module_variable_reexports_share_one_native_entity_from_source_and_contract(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    """Every publication reads one variable plan and its live native state."""
    source = tmp_path / "module_variable_reexports.f90"
    source.write_text(MODULE_VARIABLE_REEXPORT_SOURCE, encoding="utf-8")

    if pyi_parity_build_mode == "source":
        build_dir = tmp_path / "source_build"
        module = _build_source_and_import(
            source,
            build_dir,
            {
                "bind_c_module_variable_reexports_wrapper.f90",
                "module_variable_reexports_wrapper.c",
                "module_variable_reexports_wrapper.h",
            },
        )
    else:
        workdir = tmp_path / "generated_pyi_build"
        module = _build_generated_pyi_and_import(source, workdir)
        build_dir = workdir / "pyi_build"

        contracts = workdir / "contracts" / source.stem
        home_contract = (contracts / "reexport_state_home.pyi").read_text(encoding="utf-8")
        facade_contract = (contracts / "reexport_state_facade.pyi").read_text(encoding="utf-8")
        assert "counter: Int32" in home_contract
        assert "limit: Final[Int32]" in home_contract
        assert "from .reexport_state_home import " in facade_contract
        imported_names = facade_contract.partition("import ")[2].partition("\n")[0].split(", ")
        assert {"counter", "limit"}.issubset(imported_names)
        assert '"counter"' in facade_contract.partition("__all__ = ")[2]
        assert '"limit"' in facade_contract.partition("__all__ = ")[2]

    home = module.reexport_state_home
    facade = module.reexport_state_facade
    home.setup()

    assert home.limit == facade.limit == np.int32(7)

    home.counter = np.int32(10)
    assert facade.counter == np.int32(10)
    facade.counter = np.int32(25)
    assert home.counter == np.int32(25)

    home.numbers[0] = np.int32(21)
    assert facade.numbers[0] == np.int32(21)
    facade.numbers[1] = np.int32(22)
    assert home.numbers[1] == np.int32(22)

    home.values.to_numpy()[0] = np.float64(31.0)
    assert facade.values.to_numpy()[0] == np.float64(31.0)
    facade.values.to_numpy()[1] = np.float64(32.0)
    assert home.values.to_numpy()[1] == np.float64(32.0)

    assert home.selected.associated is True
    facade.selected.nullify()
    assert home.selected.associated is False

    home.current.value = np.int32(41)
    assert facade.current.value == np.int32(41)
    facade.current.value = np.int32(42)
    assert home.current.value == np.int32(42)

    home.optional_item.value = np.int32(51)
    assert facade.optional_item.value == np.int32(51)
    facade.optional_item.value = np.int32(52)
    assert home.optional_item.value == np.int32(52)

    generated = next(build_dir.glob("*_wrapper.c")).read_text(encoding="utf-8")
    assert "module_get_limit" not in generated
    assert "module_set_limit" not in generated
    for name in ("counter", "numbers", "values", "selected", "current", "optional_item"):
        assert generated.count(f"static PyObject * module_get_{name}(void) {{") == 1
    assert generated.count("static int module_set_counter(PyObject * value_obj) {") == 1

    bridge = next(build_dir.glob("bind_c_*_wrapper.f90")).read_text(encoding="utf-8")
    assert "bind_c_get_limit" not in bridge
    assert "bind_c_set_limit" not in bridge
    for signature in (
        "function bind_c_get_counter(",
        "subroutine bind_c_set_counter(",
        "function bind_c_get_numbers(",
        "subroutine bind_c_values_descriptor(",
        "subroutine bind_c_selected_descriptor(",
        "function bind_c_prik_module_field_current_value_get(",
        "subroutine bind_c_prik_module_field_current_value_set(",
        "function bind_c_prik_module_field_optional_item_value_get(",
        "subroutine bind_c_prik_module_field_optional_item_value_set(",
    ):
        assert bridge.count(signature) == 1


def test_published_imports_bind_the_declaring_modules_callable(pyi_parity_build_mode: str, tmp_path: Path):
    """A published name is an alias, so every route binds the one wrapped callable.

    The declaration is never repeated, whichever way the build was described:
    an explicit `public` of an import, a default-public or plain-`use`
    republication, a rename, and a further hop all bind the object the
    declaring module exposes. A re-export binds a Python attribute, so it
    reaches the name the declaring module settled on -- the Python spelling of
    a name written in capitals, or `lambda__2` when `lambda` and `lambda_`
    collide -- rather than the source spelling.
    """
    module = _build_source_or_generated_pyi_and_import(
        REEXPORT_SOURCE,
        tmp_path,
        {"bind_c_reexport_wrapper.f90", "reexport_wrapper.c", "reexport_wrapper.h"},
        None,
        pyi_parity_build_mode,
    )
    scale_value = module.reexport_home_mod.scale_value

    assert module.reexport_facade_mod.scale_value is scale_value
    assert module.reexport_facade_mod.scale_value(np.int32(4)) == np.int32(8)
    assert module.reexport_default_mod.scale_value is scale_value
    assert module.reexport_wildcard_mod.scale_value is scale_value
    assert module.reexport_wildcard_mod.scale_value(np.int32(5)) == np.int32(10)
    assert module.reexport_renamed_mod.public_scale is scale_value
    assert module.reexport_renamed_mod.public_scale(np.int32(6)) == np.int32(12)
    assert module.reexport_hop_mod.scale_value is scale_value
    assert module.reexport_hop_mod.scale_value(np.int32(7)) == np.int32(14)

    assert module.reexport_case_mod.scale_loud is module.reexport_shout_mod.scale_loud
    assert module.reexport_case_mod.scale_loud(np.int32(4)) == np.int32(12)
    assert not hasattr(module.reexport_case_mod, "SCALE_LOUD")

    assert module.reexport_collide_mod.lambda_(np.int32(0)) == np.int32(1)
    assert module.reexport_collide_mod.lambda__2(np.int32(0)) == np.int32(100)
    assert module.reexport_collide_user_mod.lambda_ is module.reexport_collide_mod.lambda__2
    assert module.reexport_collide_user_mod.lambda_(np.int32(0)) == np.int32(100)

    # One wrapper defines the procedure on either route; the facades only name it again.
    generated = next(_module_variables_build_dir(tmp_path, pyi_parity_build_mode).glob("*_wrapper.c"))
    assert generated.read_text(encoding="utf-8").count("static PyObject * wrap_scale_value") == 1


def test_a_derived_module_variable_argument_is_the_variable_itself(pyi_parity_build_mode: str, tmp_path: Path):
    """A procedure given a module variable receives that variable's storage, not a copy.

    Libraries recognize predefined objects by address -- Open MPI's
    ``MPI_STATUS_IGNORE`` is one -- so passing one must pass the object itself.
    """
    module = _build_source_or_generated_pyi_and_import(
        NATIVE_FIXTURES / "module_variable_arguments.f90",
        tmp_path,
        {
            "bind_c_module_variable_arguments_wrapper.f90",
            "module_variable_arguments_wrapper.c",
            "module_variable_arguments_wrapper.h",
        },
        None,
        pyi_parity_build_mode,
    )

    assert module.is_shared(module.shared)
    assert module.is_shared_c(module.shared_c)
    assert not module.is_shared(module.Box())
