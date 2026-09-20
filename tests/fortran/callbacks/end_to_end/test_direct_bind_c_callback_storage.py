"""Writable scalar callback storage on the bridge-free direct `bind(C)` route."""

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import _build_source_and_import

pytestmark = pytest.mark.fortran_end_to_end

NATIVE_FIXTURES = Path(__file__).parent / "fixtures" / "native"

SOURCE = NATIVE_FIXTURES / "fcallback_direct_storage_f90.f90"


def _direct_module(tmp_path: Path):
    # A bind(C) entry point needs no generated Fortran adapter, so the expected
    # source set is exactly the binding pair.
    return _build_source_and_import(
        SOURCE,
        tmp_path / "build",
        {
            "fcallback_direct_storage_f90_wrapper.c",
            "fcallback_direct_storage_f90_wrapper.h",
        },
    )


def test_direct_bind_c_callbacks_receive_writable_rank_zero_storage(tmp_path: Path):
    """The projection must work where no Fortran bridge exists at all.

    A direct entry point calls the trampoline as a plain C function pointer, so
    writable storage has to be the binding's doing rather than an adapter's.
    """
    module = _direct_module(tmp_path)
    observed = {}

    def update(value):
        observed["writeable"] = value.flags.writeable
        observed["incoming"] = float(value)
        value[...] *= 2

    def emit(value):
        observed["emit_writeable"] = value.flags.writeable
        value[...] = 42.0

    assert module.drive_update(update, np.float64(5.0)) == np.float64(10.0)
    assert module.drive_emit(emit) == np.float64(42.0)
    assert observed == {"writeable": True, "incoming": 5.0, "emit_writeable": True}


def test_direct_bind_c_callback_storage_adds_no_fortran_bridge(tmp_path: Path):
    """Scalar callback storage must not drag a bridge onto the direct route."""
    _direct_module(tmp_path)
    generated = {path.name for path in (tmp_path / "build").glob("*_wrapper.f90")}

    assert generated == set()
