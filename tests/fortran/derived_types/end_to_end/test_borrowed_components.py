"""Borrowed derived-type component lifetime and finalization evidence."""

import gc
from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import _build_source_or_generated_pyi_and_import

FIXTURES = Path(__file__).parent / "fixtures"
BORROWED_FINALIZER_F90_SOURCE = FIXTURES / "fborrowed_finalizer_f90.f90"
CONTRACT_FIXTURES = FIXTURES / "contracts"
pytestmark = pytest.mark.fortran_end_to_end


@pytest.fixture
def compiled_borrowed_component_module(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    return _build_source_or_generated_pyi_and_import(
        BORROWED_FINALIZER_F90_SOURCE,
        tmp_path,
        {
            "bind_c_fborrowed_finalizer_f90_wrapper.f90",
            "fborrowed_finalizer_f90_wrapper.c",
            "fborrowed_finalizer_f90_wrapper.h",
        },
        CONTRACT_FIXTURES / "fborrowed_finalizer_f90",
        pyi_parity_build_mode,
    )


def test_borrowed_child_wrapper_never_finalizes_native_component(
    compiled_borrowed_component_module,
):
    module = compiled_borrowed_component_module

    module.reset_final_count()
    owner = module.parent()
    borrowed = owner.value

    del borrowed
    gc.collect()
    assert module.get_final_count() == np.int32(0)

    borrowed = owner.value
    del owner
    gc.collect()
    assert module.get_final_count() == np.int32(0)

    del borrowed
    gc.collect()
    gc.collect()
    assert module.get_final_count() == np.int32(1)
