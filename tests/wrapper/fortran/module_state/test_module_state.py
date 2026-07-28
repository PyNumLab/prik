"""Module variables, parameters, saved state, and synchronization tests."""

import gc
import importlib
import sys
from pathlib import Path

import numpy as np
from x2py.runtime.handles import AllocatableArray
from tests.wrapper.fortran._support import (
    _build_source_or_generated_pyi_and_import,
    wrapper_source,
    _sole_native_module,
)

MODULE_VARIABLES_F90_SOURCE = wrapper_source("fmodule_vars_f90.f90")
DERIVED_ALIAS_F90_SOURCE = wrapper_source("fmodule_derived_alias_f90.f90")
PLAIN_DERIVED_F90_SOURCE = wrapper_source("fmodule_derived_snapshot_f90.f90")
CONTRACT_FIXTURES = Path(__file__).parent / "contracts"


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
        assert "Py_BEGIN_ALLOW_THREADS" in wrapper_source[summarize_start:scaled_start]
        assert "Py_END_ALLOW_THREADS" in wrapper_source[summarize_start:scaled_start]
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


def test_aliased_derived_module_object_borrows_native_state(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    module = _build_source_or_generated_pyi_and_import(
        DERIVED_ALIAS_F90_SOURCE,
        tmp_path,
        {
            "bind_c_fmodule_derived_alias_f90_wrapper.f90",
            "fmodule_derived_alias_f90_wrapper.c",
            "fmodule_derived_alias_f90_wrapper.h",
        },
        CONTRACT_FIXTURES / "fmodule_derived_alias_f90",
        pyi_parity_build_mode,
    )

    current = module.current
    assert isinstance(current, module.box)
    values = current.values
    assert isinstance(values, AllocatableArray)
    assert values.owner is current
    assert values.allocated is False
    assert values.to_numpy() is None

    module.allocate_current(np.int32(3))
    view = values.to_numpy()
    np.testing.assert_allclose(view, np.array([1.0, 2.0, 3.0], dtype=np.float64))

    view[0] = np.float64(10.0)
    assert module.current_sum() == np.float64(15.0)
    assert module.current.values_sum() == np.float64(15.0)

    owned = module.box()
    owned.allocate_values(np.int32(2))
    owned.values.to_numpy()[0] = np.float64(20.0)
    assert owned.values_sum() == np.float64(22.0)
    assert module.current_sum() == np.float64(15.0)

    del view
    del current
    gc.collect()
    assert module.current_sum() == np.float64(15.0)

    with np.testing.assert_raises(AttributeError):
        module.current = owned

    build_dir = _module_variables_build_dir(tmp_path, pyi_parity_build_mode)
    bridge_source = (build_dir / "bind_c_fmodule_derived_alias_f90_wrapper.f90").read_text(encoding="utf-8")
    assert "c_loc(native_current)" in bridge_source
    assert "bind_c_set_current" not in bridge_source

    module.deallocate_current()
    current_values = module.current.values
    assert isinstance(current_values, AllocatableArray)
    assert current_values.allocated is False
    assert current_values.to_numpy() is None
